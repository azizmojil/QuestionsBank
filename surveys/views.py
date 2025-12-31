import json
from django.db import transaction
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.translation import get_language
from django.db.models import Count
from .models import SurveyQuestion, SurveyRoutingRule, SurveyVersion
from Rbank.models import ResponseGroup
from Qbank.models import MatrixItemGroup, Questions, QuestionStaging
from assessment_runs.models import AssessmentRun


def survey_builder(request):
    available_questions_qs = (
        SurveyQuestion.objects.select_related("survey_version")
        # .exclude(survey_version__status=SurveyVersion.Status.ARCHIVED) # Status field removed
        .only("id", "text_ar", "text_en", "code", "created_at")
        .order_by("-created_at")
    )
    available_questions = [
        {
            "id": question.id,
            "label": question.display_text,
            "code": question.code,
            "created_at": question.created_at.isoformat(),
        }
        for question in available_questions_qs
    ]

    response_types = [
        {"value": choice.value, "label": choice.label}
        for choice in SurveyQuestion.ResponseType
    ] if hasattr(SurveyQuestion, 'ResponseType') else []

    response_groups = [
        {"value": rg.id, "label": rg.name}
        for rg in ResponseGroup.objects.all()
    ]

    matrix_item_groups = [
        {"value": mig.id, "label": mig.name}
        for mig in MatrixItemGroup.objects.all()
    ]

    survey_versions = SurveyVersion.objects.select_related('survey').prefetch_related('questions').all()
    version_choices = [
        {
            "id": version.id,
            "label": f"{version.survey.display_name} - {version.version_label}"
        }
        for version in survey_versions
    ]

    survey_structures = {}
    for version in survey_versions:
        sections = {}
        for q in version.questions.all():
            # Use a default section title if none is provided
            section_title = _("قسم غير مسمى")
            if section_title not in sections:
                sections[section_title] = {
                    "title": section_title,
                    "description": "",  # No description field on section, can be added if needed
                    "questions": []
                }
            
            # Append question data
            sections[section_title]["questions"].append({
                "question_id": q.id,
                "required": q.is_required,
                # Add other relevant fields here if needed for the builder
            })
        survey_structures[version.id] = list(sections.values())

    return render(
        request,
        "surveys/builder.html",
        {
            "available_questions": available_questions,
            "response_types": response_types,
            "response_groups": response_groups,
            "matrix_item_groups": matrix_item_groups,
            "survey_versions": version_choices,
            "survey_structures": survey_structures,
        },
    )

def survey_builder_routing(request):
    # Reuse logic from survey_builder but render the dedicated routing template
    available_questions_qs = (
        SurveyQuestion.objects.select_related("survey_version")
        # .exclude(survey_version__status=SurveyVersion.Status.ARCHIVED) # Status field removed
        # .only("id", "text_ar", "text_en", "code", "created_at") # Removed .only() to avoid FieldError
        .order_by("-created_at")
    )
    available_questions = [
        {
            "id": question.id,
            "label": question.display_text,
            "code": question.code,
            "created_at": question.created_at.isoformat(),
        }
        for question in available_questions_qs
    ]

    survey_versions = SurveyVersion.objects.select_related('survey').prefetch_related('questions').all()
    version_choices = [
        {
            "id": version.id,
            "label": f"{version.survey.display_name} - {version.version_label}"
        }
        for version in survey_versions
    ]

    routing_locale = {
        "selectVersion": str(_("يرجى اختيار إصدار استبيان.")),
        "fallbackPrompt": str(_("اجعل هذا المسار احتياطياً بدون شروط؟")),
        "operatorPrompt": str(_("أدخل عامل المقارنة (مثل == أو in):")),
        "valuePrompt": str(_("أدخل قيمة الشرط:")),
        "saveSuccess": str(_("تم حفظ قواعد التوجيه بنجاح.")),
        "saveError": str(_("تعذر حفظ قواعد التوجيه.")),
        "duplicateConnection": str(_("هذا الاتصال موجود بالفعل.")),
        "missingVersion": str(_("يجب اختيار الإصدار قبل حفظ القواعد.")),
        "questionLabel": str(_("سؤال")),
        "deleteConnection": str(_("هل تريد حذف هذا الاتصال؟")),
        "removeNode": str(_("هل تريد حذف هذه العقدة ومساراتها؟")),
    }

    return render(
        request,
        "surveys/builder_routing.html",
        {
            "available_questions": available_questions,
            "survey_versions": version_choices,
            "routing_locale": routing_locale,
        },
    )


def survey_routing_data(request):
    version_id = request.GET.get("version_id")
    if not version_id:
        return JsonResponse(
            {"message": str(_("معرّف الإصدار مطلوب."))},
            status=400,
        )

    version = get_object_or_404(SurveyVersion, pk=version_id)

    questions = [
        {
            "id": question.id,
            "label": question.display_text,
            "code": question.code,
        }
        for question in version.questions.all().order_by("id")
    ]

    rules = []
    for rule in SurveyRoutingRule.objects.filter(
        to_question__survey_version=version
    ).order_by("priority", "id"):
        try:
            condition = json.loads(rule.condition) if rule.condition else {}
        except json.JSONDecodeError:
            condition = {}
        rules.append(
            {
                "id": rule.id,
                "to_question": rule.to_question_id,
                "priority": rule.priority,
                "description": rule.description,
                "condition": condition,
            }
        )

    return JsonResponse(
        {
            "questions": questions,
            "rules": rules,
            "layout": version.routing_layout or {},
        }
    )


@require_POST
def save_survey_routing(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse(
            {"message": str(_("تعذر قراءة بيانات الطلب."))},
            status=400,
        )

    version_id = payload.get("version_id")
    if not version_id:
        return JsonResponse(
            {"message": str(_("معرّف الإصدار مطلوب."))},
            status=400,
        )

    version = get_object_or_404(SurveyVersion, pk=version_id)
    rules_payload = payload.get("rules") or []
    if not isinstance(rules_payload, list):
        return JsonResponse(
            {"message": str(_("صيغة القواعد غير صالحة."))},
            status=400,
        )
    layout = payload.get("layout") or {}

    cleaned_rules = []

    for idx, rule in enumerate(rules_payload):
        to_question_id = rule.get("to_question")
        if not to_question_id:
            return JsonResponse(
                {"message": str(_("حقل 'to_question' مطلوب لكل قاعدة."))},
                status=400,
            )

        question = SurveyQuestion.objects.filter(
            pk=to_question_id, survey_version=version
        ).first()
        if not question:
            return JsonResponse(
                {"message": str(_("السؤال المحدد لا ينتمي لهذا الإصدار."))},
                status=400,
            )

        condition = rule.get("condition") or {}
        if not isinstance(condition, dict):
            return JsonResponse(
                {"message": str(_("صيغة الشرط غير صالحة."))},
                status=400,
            )

        cleaned_rules.append(
            SurveyRoutingRule(
                to_question=question,
                condition=json.dumps(condition),
                priority=rule.get("priority", idx),
                description=rule.get("description", "") or "",
            )
        )

    with transaction.atomic():
        SurveyRoutingRule.objects.filter(
            to_question__survey_version=version
        ).delete()
        if cleaned_rules:
            SurveyRoutingRule.objects.bulk_create(cleaned_rules)

        layout_payload = layout if isinstance(layout, dict) else {}
        version.routing_layout = layout_payload
        version.routing_logic_done = True
        version.routing_logic_done_at = timezone.now()
        update_fields = [
            "routing_layout",
            "routing_logic_done",
            "routing_logic_done_at",
        ]
        if request.user.is_authenticated:
            version.routing_logic_done_by = request.user
            update_fields.append("routing_logic_done_by")

        version.save(update_fields=update_fields)

    return JsonResponse({"status": "ok"})

def survey_builder_initial(request):
    # Fetch questions from Qbank.models.Questions instead of SurveyQuestion
    available_questions_qs = Questions.objects.all().order_by("id")
    
    available_questions = [
        {
            "id": question.id,
            "label_ar": question.text_ar,
            "label_en": question.text_en,
            "label": question.display_text, # Fallback/Default
            "code": "", 
            "created_at": "", 
        }
        for question in available_questions_qs
    ]

    response_types = [
        {"value": choice.value, "label": choice.label}
        for choice in SurveyQuestion.ResponseType
    ] if hasattr(SurveyQuestion, 'ResponseType') else []

    response_groups = [
        {"value": rg.id, "label": rg.name}
        for rg in ResponseGroup.objects.all()
    ]

    matrix_item_groups = [
        {"value": mig.id, "label": mig.name}
        for mig in MatrixItemGroup.objects.all()
    ]

    # Only fetch survey versions that have NO questions
    survey_versions = SurveyVersion.objects.select_related('survey').annotate(
        num_questions=Count('questions')
    ).filter(num_questions=0)
    
    version_choices = [
        {
            "id": version.id,
            "label": f"{version.survey.display_name} - {version.version_label}"
        }
        for version in survey_versions
    ]

    survey_structures = {}
    # No need to populate survey_structures with questions since we only show empty ones
    # But we might need it for other logic if it expects it.
    # Since we filter for num_questions=0, this loop will just create empty structures if any.
    for version in survey_versions:
        survey_structures[version.id] = []

    return render(
        request,
        "surveys/builder_initial.html",
        {
            "available_questions": available_questions,
            "response_types": response_types,
            "response_groups": response_groups,
            "matrix_item_groups": matrix_item_groups,
            "survey_versions": version_choices,
            "survey_structures": survey_structures,
        },
    )

@require_POST
def submit_initial_questions(request):
    try:
        data = json.loads(request.body)
        version_id = data.get('version_id')
        questions = data.get('questions', [])
        
        if not version_id:
            return JsonResponse({'status': 'error', 'message': 'Missing version_id'}, status=400)
            
        survey_version = get_object_or_404(SurveyVersion, pk=version_id)
        
        # Backend check: Ensure the survey version has no questions
        if survey_version.questions.exists():
             return JsonResponse({'status': 'error', 'message': 'This survey version already has questions and cannot be modified.'}, status=403)

        current_lang = get_language()
        
        for q_data in questions:
            source = q_data.get('source')
            
            if source == 'bank':
                bank_q_id = q_data.get('id')
                bank_q = Questions.objects.filter(pk=bank_q_id).first()
                if bank_q:
                    SurveyQuestion.objects.create(
                        survey_version=survey_version,
                        text_ar=bank_q.text_ar,
                        text_en=bank_q.text_en,
                    )
            elif source == 'manual':
                text = q_data.get('label')
                if text:
                    text_ar = text if current_lang == 'ar' else ''
                    text_en = text if current_lang == 'en' else ''
                    
                    # Create SurveyQuestion
                    SurveyQuestion.objects.create(
                        survey_version=survey_version,
                        text_ar=text_ar,
                        text_en=text_en,
                    )
                    
                    # Create QuestionStaging entry
                    QuestionStaging.objects.create(
                        text_ar=text_ar,
                        text_en=text_en,
                        survey=survey_version.survey,
                        survey_version=survey_version
                    )
        
        # Create AssessmentRun for the survey version
        AssessmentRun.objects.get_or_create(survey_version=survey_version)

        return JsonResponse({'status': 'success'})
        
    except Exception as e:
        # Log the full exception for debugging
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
