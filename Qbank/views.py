import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils.translation import get_language, gettext_lazy as _

from .models import QuestionStaging
from surveys.models import SurveyQuestion, SurveyVersion
from assessment_runs.models import AssessmentRun

def home(request):
    return render(request, 'home.html')


def linguistic_review(request):
    # Filter out questions that are already sent for translation
    staged_questions = QuestionStaging.objects.filter(is_sent_for_translation=False).select_related('survey', 'survey_version').all().order_by('-created_at')
    return render(request, 'Qbank/linguistic_review.html', {'staged_questions': staged_questions})

def translation_queue(request):
    questions_for_translation = QuestionStaging.objects.filter(is_sent_for_translation=True).select_related('survey', 'survey_version').order_by('-created_at')
    return render(request, 'Qbank/translation_queue.html', {'questions': questions_for_translation})

@require_POST
def update_staged_question(request):
    try:
        data = json.loads(request.body)
        question_id = data.get('id')
        text_ar = data.get('text_ar')
        
        if not question_id:
            return JsonResponse({'status': 'error', 'message': 'Missing question ID'}, status=400)
            
        staged_question = get_object_or_404(QuestionStaging, pk=question_id)
        
        # Store old text to find the matching SurveyQuestion
        old_text_ar = staged_question.text_ar
        old_text_en = staged_question.text_en
        
        # 1. Update Question Staging
        staged_question.text_ar = text_ar
        staged_question.save()
        
        # 2. Update Survey Question in the survey version
        # We try to find the SurveyQuestion that matches the OLD state of the staged question
        # We filter by survey_version AND the old text to ensure we target the correct question instance
        
        # Try exact match first
        survey_questions = SurveyQuestion.objects.filter(
            survey_version=staged_question.survey_version,
            text_ar=old_text_ar,
            text_en=old_text_en
        )
        
        count = survey_questions.update(text_ar=text_ar)
        
        # Fallback: If no exact match (maybe text_en was None vs empty string), try matching just text_ar
        if count == 0:
             survey_questions = SurveyQuestion.objects.filter(
                survey_version=staged_question.survey_version,
                text_ar=old_text_ar
            )
             count = survey_questions.update(text_ar=text_ar)

        return JsonResponse({'status': 'success', 'updated_count': count})
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@require_POST
def send_to_translation(request):
    try:
        data = json.loads(request.body)
        question_id = data.get('id')
        
        if not question_id:
            return JsonResponse({'status': 'error', 'message': 'Missing question ID'}, status=400)
            
        staged_question = get_object_or_404(QuestionStaging, pk=question_id)
        staged_question.is_sent_for_translation = True
        staged_question.save()
        
        return JsonResponse({'status': 'success'})
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@require_POST
def save_translation(request):
    try:
        data = json.loads(request.body)
        question_id = data.get('id')
        text_en = data.get('text_en')
        
        if not question_id:
            return JsonResponse({'status': 'error', 'message': 'Missing question ID'}, status=400)
            
        staged_question = get_object_or_404(QuestionStaging, pk=question_id)
        
        # Store old text to find the matching SurveyQuestion
        old_text_ar = staged_question.text_ar
        old_text_en = staged_question.text_en
        
        # 1. Update Question Staging
        staged_question.text_en = text_en
        staged_question.save()
        
        # 2. Update Survey Question in the survey version
        # Try exact match first
        survey_questions = SurveyQuestion.objects.filter(
            survey_version=staged_question.survey_version,
            text_ar=old_text_ar,
            text_en=old_text_en
        )
        
        count = survey_questions.update(text_en=text_en)
        
        # Fallback: If no exact match, try matching just text_ar (assuming AR is correct/unique enough in context)
        if count == 0:
             survey_questions = SurveyQuestion.objects.filter(
                survey_version=staged_question.survey_version,
                text_ar=old_text_ar
            )
             count = survey_questions.update(text_en=text_en)

        return JsonResponse({'status': 'success', 'updated_count': count})
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def pipeline_overview(request):
    """Render the pipeline overview page describing the survey processing paths."""

    def status_value(*, started: bool, done: bool) -> str:
        if done:
            return "done"
        if started:
            return "in_progress"
        return "not_started"

    def pipeline_state(version: SurveyVersion) -> dict:
        questions = list(version.questions.all())
        total_questions = len(questions)
        english_questions = sum(1 for q in questions if (q.text_en or "").strip())
        required_questions = sum(1 for q in questions if q.is_required)

        staged = list(version.staged_questions.all())
        staged_total = len(staged)
        staged_sent = sum(1 for item in staged if item.is_sent_for_translation)
        staged_translated = sum(
            1 for item in staged if item.is_sent_for_translation and (item.text_en or "").strip()
        )

        assessment_run = getattr(version, "assessment_run", None)
        version_status = getattr(version, "status", SurveyVersion.Status.LOCKED)
        results_count = 0
        if assessment_run:
            prefetched = getattr(assessment_run, "_prefetched_objects_cache", {}).get("results")
            results_count = len(prefetched) if prefetched is not None else assessment_run.results.count()

        return {
            "version": status_value(
                started=True, # Always started if the version exists
                done=bool(total_questions),
            ),
            "self": status_value(
                started=bool(assessment_run),
                done=bool(total_questions and results_count >= total_questions),
            ),
            "routing": status_value(
                started=bool(total_questions),
                done=bool(total_questions and assessment_run),
            ),
            "business": status_value(
                started=bool(total_questions),
                done=bool(required_questions),
            ),
            "lang": status_value(
                started=bool(staged_total),
                done=bool(staged_total and staged_sent == staged_total),
            ),
            "translation": status_value(
                started=bool(staged_sent),
                done=bool(staged_sent and staged_translated == staged_sent),
            ),
            "approval": status_value(
                started=version_status
                in {SurveyVersion.Status.ACTIVE, SurveyVersion.Status.LOCKED, SurveyVersion.Status.ARCHIVED},
                done=version_status in {SurveyVersion.Status.LOCKED, SurveyVersion.Status.ARCHIVED},
            ),
            "qbank": status_value(
                started=bool(total_questions),
                done=bool(total_questions and english_questions == total_questions),
            ),
        }

    versions = (
        SurveyVersion.objects.select_related("survey")
        .prefetch_related("questions", "staged_questions", "assessment_run__results")
        .order_by("-version_date", "-id")
    )

    pipelines = [
        {
            "id": str(version.id),
            "survey": version.survey.display_name,
            "version_label": version.version_label or version.version_date.isoformat(),
            "state": pipeline_state(version),
        }
        for version in versions
    ]

    status_labels = {
        "done": str(_("مكتمل")),
        "in_progress": str(_("قيد التنفيذ")),
        "not_started": str(_("لم يبدأ")),
        "blocked": str(_("محجوب")),
    }

    return render(
        request,
        'pipeline.html',
        {
            "pipelines": pipelines,
            "status_labels": status_labels,
        },
    )
