import json
import logging
from datetime import datetime
from django.db.models import Count, Prefetch
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from surveys.models import Survey, SurveyVersion, SurveyQuestion
from assessment_flow.models import AssessmentQuestion, AssessmentOption
from indicators.models import Indicator
from assessment_flow.engine import RoutingEngine
from .models import AssessmentRun, AssessmentResult
from .engine import ClassificationEngine

log = logging.getLogger(__name__)


def survey_list(request):
    surveys = Survey.objects.all()
    return render(request, 'assessment_runs/survey_list.html', {'surveys': surveys})


def dashboard(request):
    surveys_qs = (
        Survey.objects.prefetch_related(
            Prefetch(
                "versions",
                queryset=SurveyVersion.objects.annotate(
                    question_total=Count("questions")
                ).order_by("-version_date", "-id"),
            )
        )
        .annotate(version_total=Count("versions"))
        .order_by("name_ar", "name_en")
    )
    survey_count = surveys_qs.count()

    survey_rows = []
    for survey in surveys_qs:
        versions = list(survey.versions.all())
        latest_version = versions[0] if versions else None
        survey_rows.append({
            "id": survey.id,
            "name": survey.display_name,
            "status": survey.get_status_display(),
            "latest_version": latest_version,
            "question_total": latest_version.question_total if latest_version else 0,
        })

    context = {
        "stats": {
            "survey_count": survey_count,
            "version_count": SurveyVersion.objects.count(),
            "question_count": SurveyQuestion.objects.count(),
        },
        "surveys": survey_rows,
    }
    return render(request, "assessment_runs/dashboard.html", context)


def survey_version_list(request, survey_id):
    survey = get_object_or_404(Survey, pk=survey_id)
    versions = survey.versions.all()
    return render(request, 'assessment_runs/survey_version_list.html', {'survey': survey, 'versions': versions})


def survey_question_list(request, version_id):
    version = get_object_or_404(SurveyVersion, pk=version_id)
    questions = version.questions.all()
    total_questions = questions.count()

    # Entry points have no incoming routing rules.
    first_assessment_question = AssessmentQuestion.objects.filter(incoming_rules__isnull=True).first()
    
    assessment_run = getattr(version, 'assessment_run', None)
    completed_question_ids = set()
    
    if assessment_run:
        completed_question_ids = set(
            AssessmentResult.objects.filter(assessment_run=assessment_run)
            .values_list('survey_question_id', flat=True)
        )

    question_list_data = []
    for question in questions:
        status = 'DONE' if question.id in completed_question_ids else 'NOT_STARTED'
        question_list_data.append({
            'question': question,
            'status': status,
        })

    completed_count = len(completed_question_ids)
    progress_percentage = 0
    if total_questions > 0:
        progress_percentage = (completed_count / total_questions) * 100
    
    is_complete = completed_count == total_questions and total_questions > 0

    return render(request, 'assessment_runs/survey_question_list.html', {
        'version': version,
        'question_list_data': question_list_data,
        'first_assessment_question': first_assessment_question,
        'progress_percentage': progress_percentage,
        'completed_count': completed_count,
        'total_questions': total_questions,
        'is_complete': is_complete,
    })


def submit_assessment_run(request, version_id):
    version = get_object_or_404(SurveyVersion, pk=version_id)
    assessment_run = getattr(version, 'assessment_run', None)
    
    if assessment_run:
        # Check if all questions are answered (optional double check)
        # For now, just update status
        # assessment_run.status = AssessmentRun.Status.COMPLETE # Status field was removed?
        # If status field was removed, maybe we don't need to do anything other than redirect?
        # Or maybe we should add a 'submitted_at' field?
        
        # Assuming we just want to redirect for now as per previous instructions about status removal.
        # But usually "Submit" implies a state change.
        # If I removed status, I can't update it.
        pass
        
    return redirect('survey_list')


def _prepare_context(question):
    context = {'question': question}
    if question.option_type == AssessmentQuestion.OptionType.INDICATOR_LIST:
        if question.indicator_source:
            context['options'] = question.indicator_source.items.all()
    return context


def assessment_page(request, question_id):
    question = get_object_or_404(AssessmentQuestion, pk=question_id)

    survey_question_id = request.GET.get('survey_question_id')
    assessment_metadata = {}
    survey_question = None
    try:
        survey_question_id = int(survey_question_id) if survey_question_id else None
        if survey_question_id:
            survey_question = SurveyQuestion.objects.filter(pk=survey_question_id).first()
    except (TypeError, ValueError):
        survey_question_id = None
        survey_question = None
    
    history = []
    if survey_question:
        assessment_metadata = {
            'survey_question_id': survey_question.id,
            'survey_version_id': survey_question.survey_version_id,
        }
        
        # Restore history from DB if available
        survey_version = survey_question.survey_version
        assessment_run = getattr(survey_version, 'assessment_run', None)
        if assessment_run:
            # Get the result for THIS specific question
            target_result = AssessmentResult.objects.filter(
                assessment_run=assessment_run, 
                survey_question=survey_question
            ).first()
            
            if target_result and target_result.results:
                history = target_result.results
                request.session['assessment_history'] = history
            else:
                # If no history for this question, start fresh
                history = [{'question_id': question_id, 'rule_id': None}]
                request.session['assessment_history'] = history
        else:
             history = [{'question_id': question_id, 'rule_id': None}]
             request.session['assessment_history'] = history
    else:
        # Fallback if no survey question context
        history = [{'question_id': question_id, 'rule_id': None}]
        request.session['assessment_history'] = history

    assessment_metadata['started_at'] = timezone.now().timestamp()
    request.session['assessment_metadata'] = assessment_metadata

    # Prepare questions_to_render
    questions_to_render = []
    
    # Fetch all questions in history
    history_q_ids = [item['question_id'] for item in history]
    # If current question is not in history (e.g. new start), add it
    if question_id not in history_q_ids:
         # This happens if we are starting fresh or jumping to a question not in history?
         # If we jump to Q1, and history is empty, it's in history (added above).
         # If we jump to Q1, and history has [Q1, Q2], it's in history.
         pass

    # Bulk fetch questions
    questions_map = {q.id: q for q in AssessmentQuestion.objects.filter(id__in=history_q_ids)}
    
    for item in history:
        q_id = item['question_id']
        q_obj = questions_map.get(q_id)
        if q_obj:
            # Resolve answer text if needed
            answer = item.get('answer')
            # If answer is IDs, we might want to resolve to text for display?
            # The template _question_box.html expects 'answer' to be displayed.
            # If 'answer' is [1, 2], we need to show "Option 1", "Option 2".
            
            # We need to resolve IDs to text for display in collapsed box.
            # This logic was previously in get_next_question_view but now we store IDs.
            
            display_answer = []
            if answer:
                answer_list = answer if isinstance(answer, list) else [answer]
                for ans in answer_list:
                    # Check if it's an ID (int) or text
                    if isinstance(ans, int):
                        # Try to find option
                        if q_obj.option_type == AssessmentQuestion.OptionType.INDICATOR_LIST:
                             opt = Indicator.objects.filter(id=ans).first()
                             if opt: display_answer.append(opt.name_ar)
                        else:
                             opt = AssessmentOption.objects.filter(id=ans).first()
                             if opt: display_answer.append(opt.display_text)
                    else:
                        display_answer.append(ans)
            
            questions_to_render.append({
                'question': q_obj,
                'answer': display_answer,
                'answer_ids': answer # Keep raw IDs for logic if needed
            })

    context = {
        'questions_to_render': questions_to_render,
        'survey_question': survey_question, # Pass the survey question to the template
    }
    
    # We also need options for the active question (last one)
    if questions_to_render:
        active_item = questions_to_render[-1]
        active_q = active_item['question']
        if active_q.option_type == AssessmentQuestion.OptionType.INDICATOR_LIST:
             if active_q.indicator_source:
                 context['options'] = active_q.indicator_source.items.all()

    return render(request, 'assessment_runs/assessment_page.html', context)


@require_POST
def get_next_question_view(request):
    data = json.loads(request.body)
    question_id = int(data.get('question_id'))
    raw_option_ids = data.get('option_ids', [])

    history = request.session.get('assessment_history', [])
    metadata = request.session.get('assessment_metadata', {})

    question = get_object_or_404(AssessmentQuestion, pk=question_id)

    numeric_option_ids = []
    freeform_answers = []
    for raw_id in raw_option_ids:
        raw_str = "" if raw_id is None else str(raw_id).strip()
        if not raw_str:
            continue
        try:
            numeric_option_ids.append(int(raw_str))
        except ValueError:
            freeform_answers.append(raw_str)

    # Store IDs for numeric options, text for freeform
    answers_to_store_list = []
    answers_to_store_list.extend(numeric_option_ids)
    answers_to_store_list.extend(freeform_answers)

    def _normalize_answer_payload(values):
        if not values:
            return []
        if len(values) == 1:
            return values[0]
        return values

    answer_to_store = _normalize_answer_payload(answers_to_store_list)

    # Update the current question's entry in history with the answer
    for item in reversed(history):
        if item['question_id'] == question_id:
            item['answer'] = answer_to_store
            break

    # Save intermediate result to DB
    survey_version_id = metadata.get('survey_version_id')
    survey_question_id = metadata.get('survey_question_id')
    
    if survey_version_id and survey_question_id:
        survey_version = SurveyVersion.objects.filter(pk=survey_version_id).first()
        survey_question = SurveyQuestion.objects.filter(pk=survey_question_id).first()
        
        if survey_version and survey_question:
            assessment_run, _ = AssessmentRun.objects.get_or_create(survey_version=survey_version)

            responses = {}
            # Use survey question id to align with classification rules
            if survey_question_id:
                latest_answer = next(
                    (
                        item.get('answer')
                        for item in reversed(history)
                        if item.get('question_id') == question_id and 'answer' in item
                    ),
                    None,
                )
                responses[str(survey_question_id)] = latest_answer

            classification_engine = ClassificationEngine()
            classification_result = classification_engine.classify_question(survey_question, responses)

            if not classification_result.classification:
                log.debug("No classification resolved for survey question %s", survey_question_id)

            classification_str = classification_result.classification or ""

            AssessmentResult.objects.update_or_create(
                assessment_run=assessment_run,
                survey_question=survey_question,
                defaults={
                    'assessed_by': request.user if request.user.is_authenticated else None,
                    'results': history,
                    'classification': classification_str,
                },
            )

    # Routing logic
    responses = {str(item['question_id']): item.get('answer') for item in history if 'answer' in item}
    used_rule_ids = [item['rule_id'] for item in history if item.get('rule_id')]

    engine = RoutingEngine()
    result = engine.get_next_question(
        responses=responses,
        used_rule_ids=used_rule_ids
    )

    response = None
    if result and result.next_question:
        history.append({'question_id': result.next_question.id, 'rule_id': result.rule.id if result.rule else None})
        context = _prepare_context(result.next_question)
        response = render(request, 'assessment_runs/_question_box.html', context)
    else:
        response = HttpResponse(status=204)

    request.session['assessment_history'] = history
    return response


@require_POST
def rewind_assessment(request):
    data = json.loads(request.body)
    question_id = int(data.get('question_id'))

    history = request.session.get('assessment_history', [])

    try:
        rewind_index = next(i for i, item in enumerate(history) if item['question_id'] == question_id)
        history = history[:rewind_index + 1]
        if 'answer' in history[-1]:
            del history[-1]['answer']
        request.session['assessment_history'] = history
    except StopIteration:
        pass

    return JsonResponse({'status': 'ok'})


def assessment_complete(request):
    metadata = request.session.get('assessment_metadata', {})
    survey_version_id = metadata.get('survey_version_id')
    
    # Clear session data
    request.session.pop('assessment_history', None)
    request.session.pop('assessment_metadata', None)

    survey_version = None
    if survey_version_id:
        survey_version = SurveyVersion.objects.filter(pk=survey_version_id).first()

    return render(
        request,
        "assessment_runs/assessment_complete.html",
        {"survey_version": survey_version},
    )
