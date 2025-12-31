import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils.translation import get_language, gettext_lazy as _

from .models import QuestionStaging
from surveys.models import SurveyQuestion

PIPELINE_STEPS = [
    {"label": _("القائمة المبدئية"), "status": "done"},
    {"label": _("تدقيق لغوي"), "status": "done"},
    {"label": _("قائمة الترجمة"), "status": "in_progress"},
    {"label": _("قواعد التوجيه"), "status": "not_started"},
    {"label": _("قواعد الأعمال"), "status": "skipped"},
    {"label": _("إنشاء نسخة الاستبيان"), "status": "not_started"},
    {"label": _("الموافقة النهائية"), "status": "not_started"},
]

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
    steps = PIPELINE_STEPS
    IN_PROGRESS_WEIGHT = 0.5

    completed = sum(1 for step in steps if step["status"] == "done")
    in_progress = sum(1 for step in steps if step["status"] == "in_progress")
    total_segments = len(steps)
    progress_ratio = (completed + (IN_PROGRESS_WEIGHT * in_progress)) / total_segments
    progress_percentage = min(progress_ratio * 100, 100)

    return render(
        request,
        'pipeline.html',
        {
            "steps": steps,
            "progress_percentage": progress_percentage,
        },
    )
