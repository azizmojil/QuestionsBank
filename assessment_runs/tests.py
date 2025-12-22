import json

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.utils.translation import override

from assessment_flow.models import AssessmentQuestion, AssessmentFlowRule, AssessmentOption
from assessment_runs.engine import ClassificationEngine
from assessment_runs.models import QuestionClassificationRule, AssessmentResult, AssessmentRun
from surveys.models import Survey, SurveyVersion, SurveyQuestion

User = get_user_model()


class RewindAssessmentTestCase(TestCase):
    """Test cases for the rewind_assessment view to ensure proper backtracking behavior."""

    def setUp(self):
        """Set up test questions, rules, and client."""
        self.client = Client()

        # Create test questions
        self.q1 = AssessmentQuestion.objects.create(text_en="Question 1", text_ar="سؤال 1")
        self.q2 = AssessmentQuestion.objects.create(text_en="Question 2", text_ar="سؤال 2")
        self.q3 = AssessmentQuestion.objects.create(text_en="Question 3", text_ar="سؤال 3")

        # Create rules
        self.rule_a = AssessmentFlowRule.objects.create(
            from_question=self.q2,
            condition=f'{{"conditions": [{{"question": {self.q1.id}, "operator": "==", "value": "Yes"}}]}}',
            priority=1,
            is_active=True,
            description="Rule A"
        )

        self.rule_b = AssessmentFlowRule.objects.create(
            from_question=self.q3,
            condition=f'{{"conditions": [{{"question": {self.q2.id}, "operator": "==", "value": "Option1"}}]}}',
            priority=1,
            is_active=True,
            description="Rule B"
        )

    def test_rewind_preserves_rule_id(self):
        """Test that rewinding to a question preserves its rule_id."""
        session = self.client.session

        # Simulate a history where we've gone from Q1 -> Q2 -> Q3
        session['assessment_history'] = [
            {'question_id': self.q1.id, 'rule_id': None, 'answer': 'Yes'},
            {'question_id': self.q2.id, 'rule_id': self.rule_a.id, 'answer': 'Option1'},
            {'question_id': self.q3.id, 'rule_id': self.rule_b.id, 'answer': 'Continue'}
        ]
        session.save()

        # Rewind to Q2
        response = self.client.post(
            reverse('rewind_assessment'),
            data=json.dumps({'question_id': self.q2.id}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

        # Check the history after rewind
        history = self.client.session['assessment_history']

        # History should be truncated to Q1 and Q2
        self.assertEqual(len(history), 2)

        # Q2 should still have its rule_id (Rule A) preserved
        q2_entry = history[1]
        self.assertEqual(q2_entry['question_id'], self.q2.id)
        self.assertEqual(q2_entry['rule_id'], self.rule_a.id)

        # Q2's answer should be cleared
        self.assertNotIn('answer', q2_entry)

    def test_rewind_removes_subsequent_questions(self):
        """Test that rewinding removes all questions after the rewind point."""
        session = self.client.session

        # Simulate a history with Q1 -> Q2 -> Q3
        session['assessment_history'] = [
            {'question_id': self.q1.id, 'rule_id': None, 'answer': 'Yes'},
            {'question_id': self.q2.id, 'rule_id': self.rule_a.id, 'answer': 'Option1'},
            {'question_id': self.q3.id, 'rule_id': self.rule_b.id, 'answer': 'Continue'}
        ]
        session.save()

        # Rewind to Q1
        response = self.client.post(
            reverse('rewind_assessment'),
            data=json.dumps({'question_id': self.q1.id}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

        # Check the history after rewind
        history = self.client.session['assessment_history']

        # History should only contain Q1
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['question_id'], self.q1.id)

        # Q1's answer should be cleared
        self.assertNotIn('answer', history[0])

    def test_get_next_question_uses_correct_used_rules(self):
        """Test that get_next_question_view correctly identifies used rules after rewind."""
        session = self.client.session

        # Simulate a history where we've rewound to Q2
        # Q1 -> Q2 (via Rule A), and Q3 was removed
        session['assessment_history'] = [
            {'question_id': self.q1.id, 'rule_id': None, 'answer': 'Yes'},
            {'question_id': self.q2.id, 'rule_id': self.rule_a.id}  # No answer yet (just rewound)
        ]
        session.save()

        # Submit a new answer for Q2
        response = self.client.post(
            reverse('get_next_question'),
            data=json.dumps({
                'question_id': self.q2.id,
                'option_ids': ['test_option']
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 204)

        # Check that Rule A is still in used_rule_ids
        # This is verified by checking the history
        history = self.client.session.get('assessment_history', [])

        # Q2 should still have rule_id = Rule A
        q2_entry = next((item for item in history if item['question_id'] == self.q2.id), None)
        self.assertIsNotNone(q2_entry)
        self.assertEqual(q2_entry['rule_id'], self.rule_a.id)
        self.assertEqual(q2_entry.get('answer'), 'test_option')


class ClassificationEngineTestCase(TestCase):
    """Test cases for the ClassificationEngine to ensure rule evaluation works like routing logic."""

    def setUp(self):
        self.survey = Survey.objects.create(name_ar="استبيان تجريبي", name_en="Demo Survey", code="DEMO")
        self.version = SurveyVersion.objects.create(survey=self.survey, interval=SurveyVersion.SurveyInterval.ANNUALLY)
        self.q1 = SurveyQuestion.objects.create(survey_version=self.version, text_ar="سؤال استبيان 1",
                                                text_en="Survey Question 1")
        self.q2 = SurveyQuestion.objects.create(survey_version=self.version, text_ar="سؤال استبيان 2",
                                                text_en="Survey Question 2")

    def test_classify_question_matches_value_condition(self):
        rule = QuestionClassificationRule.objects.create(
            survey_question=self.q1,
            classification="HIGH",
            condition=json.dumps({
                "conditions": [
                    {"question": self.q1.id, "operator": "==", "value": "Yes"}
                ]
            }),
            priority=1,
            is_active=True,
        )

        engine = ClassificationEngine()
        responses = {str(self.q1.id): "Yes"}

        result = engine.classify_question(self.q1, responses)

        self.assertEqual(result.question, self.q1)
        self.assertEqual(result.classification, "HIGH")
        self.assertEqual(result.rule, rule)

    def test_fallback_rule_used_when_no_conditions_match(self):
        QuestionClassificationRule.objects.create(
            survey_question=self.q2,
            classification="CRITICAL",
            condition=json.dumps({
                "conditions": [
                    {"question": self.q1.id, "operator": "==", "value": "No"}
                ]
            }),
            priority=1,
            is_active=True,
        )
        fallback_rule = QuestionClassificationRule.objects.create(
            survey_question=self.q2,
            classification="LOW",
            condition=json.dumps({"fallback": True}),
            priority=99,
            is_active=True,
        )

        engine = ClassificationEngine()
        responses = {str(self.q1.id): "Yes"}

        result = engine.classify_question(self.q2, responses)

        self.assertEqual(result.classification, "LOW")
        self.assertEqual(result.rule, fallback_rule)


class AssessmentLocalizationTests(TestCase):
    def test_option_display_text_switches_language(self):
        question = AssessmentQuestion.objects.create(text_en="Assess", text_ar="قيّم")
        option = AssessmentOption.objects.create(
            question=question,
            text_en="Yes",
            text_ar="نعم",
        )

        with override("ar"):
            self.assertEqual(option.display_text, "نعم")
            self.assertEqual(question.display_text, "قيّم")

        with override("en"):
            self.assertEqual(option.display_text, "Yes")
            self.assertEqual(question.display_text, "Assess")


class AssessmentCompletionSaveTestCase(TestCase):
    """Ensure completing an assessment stores results and links back to the question list."""

    def setUp(self):
        self.client = Client()
        self.survey = Survey.objects.create(name_ar="استبيان تجريبي", name_en="Demo Survey", code="DEMO-SAVE")
        self.version = SurveyVersion.objects.create(
            survey=self.survey,
            interval=SurveyVersion.SurveyInterval.ANNUALLY,
        )
        self.survey_question = SurveyQuestion.objects.create(
            survey_version=self.version,
            text_en="Survey Question",
            text_ar="سؤال استبيان",
        )
        self.assessment_question = AssessmentQuestion.objects.create(text_en="Assess this", text_ar="قيّم هذا")
        self.option = AssessmentOption.objects.create(
            question=self.assessment_question,
            text_en="Yes",
            text_ar="نعم",
        )

    def test_complete_saves_assessment_result(self):
        start_url = reverse('assessment_page', args=[self.assessment_question.id])
        start_url = f"{start_url}?survey_question_id={self.survey_question.id}"
        self.client.get(start_url)

        self.client.post(
            reverse('get_next_question'),
            data=json.dumps({
                'question_id': self.assessment_question.id,
                'option_ids': [self.option.id],
            }),
            content_type='application/json'
        )

        response = self.client.get(reverse('assessment_complete'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(AssessmentRun.objects.count(), 1)

        run = AssessmentRun.objects.first()
        self.assertEqual(run.survey_version, self.version)
        self.assertEqual(run.status, AssessmentRun.Status.COMPLETE)

        result = AssessmentResult.objects.get(assessment_run=run, survey_question=self.survey_question)
        self.assertEqual(result.status, AssessmentResult.Status.COMPLETE)
        self.assertEqual(result.assessment_path[0]['answer'], self.option.display_text)

        self.assertContains(response, reverse('survey_question_list', args=[self.version.id]))


class DashboardViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.survey = Survey.objects.create(name_ar="استبيان جديد", name_en="New Survey", code="NEW")
        self.version = SurveyVersion.objects.create(
            survey=self.survey,
            interval=SurveyVersion.SurveyInterval.ANNUALLY,
        )
        SurveyQuestion.objects.create(
            survey_version=self.version,
            text_en="Question one",
            text_ar="سؤال واحد",
        )

    def test_dashboard_lists_surveys_and_versions(self):
        response = self.client.get(reverse('assessment_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.survey.display_name)
        self.assertContains(response, self.version.version_label)
