import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils.translation import gettext_lazy as _
from django.utils.translation import get_language
from django.db.models import Count
from django.views.decorators.csrf import csrf_exempt

from .models import SurveyQuestion, SurveyVersion, SurveySection
from Rbank.models import ResponseGroup, ResponseType
from Qbank.models import MatrixItemGroup, Questions, QuestionStaging
from assessment_runs.models import AssessmentRun


def survey_builder(request):
    available_questions_qs = (
        SurveyQuestion.objects.select_related("survey_version")
        # .exclude(survey_version__status=SurveyVersion.Status.ARCHIVED) # Status field removed
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
        {"value": rt.id, "label": str(rt)}
        for rt in ResponseType.objects.all()
    ]

    response_groups = [
        {"value": rg.id, "label": rg.name}
        for rg in ResponseGroup.objects.all()
    ]

    matrix_item_groups = [
        {"value": mig.id, "label": mig.name}
        for mig in MatrixItemGroup.objects.all()
    ]

    survey_versions = (
        SurveyVersion.objects.select_related('survey')
        .prefetch_related('questions', 'sections__questions')
        .all()
    )
    version_choices = [
        {
            "id": version.id,
            "label": f"{version.survey.display_name} - {version.version_label}"
        }
        for version in survey_versions
    ]

    survey_structures = {}
    for version in survey_versions:
        sections_payload = []

        # Existing sections with their questions
        for section in version.sections.all():
            sections_payload.append({
                "id": section.id,
                "title": section.display_title,
                "description": section.display_description,
                "questions": [
                    {
                        "question_id": q.id,
                        "label": q.display_text,
                        "required": q.is_required,
                        "response_group_id": q.response_group_id,
                        "response_type_id": q.response_type_id,
                        "matrix_item_group_id": q.matrix_item_group_id,
                        "is_matrix": q.is_matrix,
                    }
                    for q in section.questions.all()
                ],
            })

        # Any unsectioned questions fall back to a default section
        unsectioned = [
            q for q in version.questions.all()
            if not q.section_id
        ]
        if unsectioned:
            sections_payload.append({
                "title": _("قسم غير مسمى"),
                "description": "",
                "questions": [
                    {
                        "question_id": q.id,
                        "label": q.display_text,
                        "required": q.is_required,
                        "response_group_id": q.response_group_id,
                        "response_type_id": q.response_type_id,
                        "matrix_item_group_id": q.matrix_item_group_id,
                        "is_matrix": q.is_matrix,
                    }
                    for q in unsectioned
                ],
            })

        survey_structures[version.id] = sections_payload

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


@require_POST
def submit_final_questionnaire(request):
    try:
        data = json.loads(request.body)
        version_id = data.get("version_id")
        sections_data = data.get("sections", [])

        if not version_id:
            return JsonResponse(
                {"status": "error", "message": _("Missing version_id")},
                status=400,
            )

        if not sections_data:
            return JsonResponse(
                {"status": "error", "message": _("لا توجد أقسام لإرسالها")},
                status=400,
            )

        survey_version = get_object_or_404(SurveyVersion, pk=version_id)
        current_lang = (get_language() or "ar")[:2]

        # Replace existing sections with the submitted structure
        survey_version.sections.all().delete()

        created_sections = 0
        for idx, section_data in enumerate(sections_data):
            title_value = section_data.get("title") or ""
            description_value = section_data.get("description") or ""

            section = SurveySection.objects.create(
                survey_version=survey_version,
                title_ar=section_data.get("title_ar") or (title_value if current_lang == "ar" else ""),
                title_en=section_data.get("title_en") or (title_value if current_lang == "en" else ""),
                description_ar=section_data.get("description_ar") or (description_value if current_lang == "ar" else ""),
                description_en=section_data.get("description_en") or (description_value if current_lang == "en" else ""),
                order=idx,
            )
            created_sections += 1

            for q_data in section_data.get("questions", []):
                q_obj = None
                qid = q_data.get("id") or q_data.get("question_id")
                label = q_data.get("label")

                if qid:
                    q_obj = SurveyQuestion.objects.filter(pk=qid).first()
                    if q_obj and q_obj.survey_version_id != survey_version.id:
                        q_obj = SurveyQuestion.objects.create(
                            survey_version=survey_version,
                            text_ar=q_obj.text_ar,
                            text_en=q_obj.text_en,
                            code=q_obj.code,
                        )

                if q_obj is None and label:
                    text_ar = label if current_lang == "ar" else ""
                    text_en = label if current_lang == "en" else ""
                    q_obj = SurveyQuestion.objects.create(
                        survey_version=survey_version,
                        text_ar=text_ar,
                        text_en=text_en,
                    )

                if q_obj is None:
                    continue

                q_obj.section = section
                q_obj.response_group_id = q_data.get("response_group_id")
                q_obj.response_type_id = q_data.get("response_type_id")
                q_obj.matrix_item_group_id = q_data.get("matrix_item_group_id")
                q_obj.is_matrix = bool(q_data.get("is_matrix"))
                if "is_required" in q_data:
                    q_obj.is_required = bool(q_data.get("is_required"))
                q_obj.save()

        return JsonResponse(
            {
                "status": "success",
                "sections_created": created_sections,
            }
        )

    except Exception as exc:  # pragma: no cover - unexpected runtime errors
        return JsonResponse(
            {"status": "error", "message": str(exc)},
            status=500,
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

    return render(
        request,
        "surveys/builder_routing.html",
        {
            "available_questions": available_questions,
            "survey_versions": version_choices,
        },
    )

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
        {"value": rt.id, "label": str(rt)}
        for rt in ResponseType.objects.all()
    ]

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
