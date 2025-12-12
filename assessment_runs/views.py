from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
import json
from surveys.models import Survey, SurveyVersion, SurveyQuestion
from assessment_flow.models import AssessmentQuestion, AssessmentOption
from indicators.models import IndicatorListItem
from assessment_flow.engine import RoutingEngine

def survey_list(request):
    surveys = Survey.objects.all()
    return render(request, 'assessment_runs/survey_list.html', {'surveys': surveys})

def survey_version_list(request, survey_id):
    survey = get_object_or_404(Survey, pk=survey_id)
    versions = survey.versions.all()
    return render(request, 'assessment_runs/survey_version_list.html', {'survey': survey, 'versions': versions})

def survey_question_list(request, version_id):
    version = get_object_or_404(SurveyVersion, pk=version_id)
    questions = version.questions.all()

    first_assessment_question = AssessmentQuestion.objects.filter(outgoing_rules__isnull=True).first()

    return render(request, 'assessment_runs/survey_question_list.html', {
        'version': version,
        'questions': questions,
        'first_assessment_question': first_assessment_question,
    })

def _prepare_context(question):
    context = {'question': question}
    if question.option_type == AssessmentQuestion.OptionType.INDICATOR_LIST:
        if question.indicator_source:
            context['options'] = question.indicator_source.items.all()
    return context

def assessment_page(request, question_id):
    question = get_object_or_404(AssessmentQuestion, pk=question_id)

    # Start a fresh assessment history
    request.session['assessment_history'] = [{'question_id': question_id, 'rule_id': None}]

    context = _prepare_context(question)
    return render(request, 'assessment_runs/assessment_page.html', context)

@require_POST
def get_next_question_view(request):
    data = json.loads(request.body)
    question_id = int(data.get('question_id'))
    raw_option_ids = data.get('option_ids', [])

    history = request.session.get('assessment_history', [])

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

    answer_texts = []
    if question.option_type == AssessmentQuestion.OptionType.INDICATOR_LIST:
        selected_options = IndicatorListItem.objects.filter(id__in=numeric_option_ids)
        answer_texts = [opt.name for opt in selected_options]
    else:
        selected_options = AssessmentOption.objects.filter(id__in=numeric_option_ids)
        answer_texts = [opt.text for opt in selected_options]

    answer_texts.extend(freeform_answers)

    # Preserve existing structure: store a scalar for single answers, list for multiple;
    # keep empty answers as [] because downstream history consumers expect list-like values.
    def _normalize_answer_payload(values):
        if not values:
            return []
        if len(values) == 1:
            return values[0]
        return values

    answer_to_store = _normalize_answer_payload(answer_texts)

    # Update the current question's entry in history with the answer
    # We need to find the entry for this question. It should be the last one, but let's be safe.
    for item in reversed(history):
        if item['question_id'] == question_id:
            item['answer'] = answer_to_store
            break

    # NOW reconstruct responses and used rules from the UPDATED history
    responses = {str(item['question_id']): item.get('answer') for item in history if 'answer' in item}
    used_rule_ids = [item['rule_id'] for item in history if item.get('rule_id')]

    engine = RoutingEngine()
    result = engine.get_next_question(
        responses=responses,
        used_rule_ids=used_rule_ids
    )

    response = None
    if result and result.next_question:
        # Add the new step to history
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
        # Truncate the history, keeping the rewound question but clearing its answer
        history = history[:rewind_index + 1]
        if 'answer' in history[-1]:
            del history[-1]['answer']
        # Note: We intentionally DO NOT clear rule_id here.
        # The rule_id represents the rule that was used to navigate TO this question.
        # Since we're still at this question, the rule should remain marked as used
        # to prevent it from firing again. Only rules used AFTER this question
        # are removed from history (via the truncation above).

        request.session['assessment_history'] = history
    except StopIteration:
        pass

    return JsonResponse({'status': 'ok'})

def assessment_complete(request):
    request.session.pop('assessment_history', None)
    return render(request, 'assessment_runs/assessment_complete.html')
