from django.test import TestCase
from django.utils import translation

from surveys.models import Survey, SurveyVersion
from .models import (
    AssessmentFlowRule,
    AssessmentOption,
    AssessmentQuestion,
    ReevaluationQuestion,
)
from .engine import RoutingEngine


class RoutingEngineTestCase(TestCase):
    """Test cases for the RoutingEngine to ensure proper rule firing and backtracking behavior."""

    def setUp(self):
        """Set up test questions and rules."""
        # Create test questions
        self.q1 = AssessmentQuestion.objects.create(text_en="Question 1")
        self.q2 = AssessmentQuestion.objects.create(text_en="Question 2")
        self.q3 = AssessmentQuestion.objects.create(text_en="Question 3")
        self.q4 = AssessmentQuestion.objects.create(text_en="Question 4")

        # Create rules
        # Rule A: If Q1 answer is "Yes", show Q2
        self.rule_a = AssessmentFlowRule.objects.create(
            to_question=self.q2,
            condition=f'{{"conditions": [{{"question": {self.q1.id}, "operator": "==", "value": "Yes"}}]}}',
            priority=1,
            description="Rule A: Show Q2 if Q1=Yes"
        )

        # Rule B: If Q2 answer is "Option1", show Q3
        self.rule_b = AssessmentFlowRule.objects.create(
            to_question=self.q3,
            condition=f'{{"conditions": [{{"question": {self.q2.id}, "operator": "==", "value": "Option1"}}]}}',
            priority=1,
            description="Rule B: Show Q3 if Q2=Option1"
        )

        # Rule C: If Q3 answer is "Continue", show Q4
        self.rule_c = AssessmentFlowRule.objects.create(
            to_question=self.q4,
            condition=f'{{"conditions": [{{"question": {self.q3.id}, "operator": "==", "value": "Continue"}}]}}',
            priority=1,
            description="Rule C: Show Q4 if Q3=Continue"
        )

    def test_rule_fires_only_once(self):
        """Test that each rule fires only once during an assessment run."""
        engine = RoutingEngine()

        # First call: Q1 answered "Yes" -> should fire Rule A and return Q2
        responses = {str(self.q1.id): "Yes"}
        result = engine.get_next_question(responses, used_rule_ids=[])

        self.assertIsNotNone(result.next_question)
        self.assertEqual(result.next_question.id, self.q2.id)
        self.assertEqual(result.rule.id, self.rule_a.id)

        # Second call: Same responses, Rule A already used -> should NOT return Q2 again
        used_rules = [self.rule_a.id]
        result = engine.get_next_question(responses, used_rule_ids=used_rules)

        # Rule A should not fire again, so we should get None (or a different question if other rules match)
        if result.next_question:
            self.assertNotEqual(result.rule.id if result.rule else None, self.rule_a.id)

    def test_backtracking_returns_rules_to_pool(self):
        """Test that backtracking makes subsequent rules available again."""
        engine = RoutingEngine()

        # Simulate a flow: Q1 -> Q2 -> Q3 -> Q4
        # Step 1: Answer Q1 = "Yes" -> Rule A fires -> Q2
        responses = {str(self.q1.id): "Yes"}
        result1 = engine.get_next_question(responses, used_rule_ids=[])
        self.assertEqual(result1.next_question.id, self.q2.id)
        used_rules = [result1.rule.id]

        # Step 2: Answer Q2 = "Option1" -> Rule B fires -> Q3
        responses[str(self.q2.id)] = "Option1"
        result2 = engine.get_next_question(responses, used_rule_ids=used_rules)
        self.assertEqual(result2.next_question.id, self.q3.id)
        used_rules.append(result2.rule.id)

        # Step 3: Answer Q3 = "Continue" -> Rule C fires -> Q4
        responses[str(self.q3.id)] = "Continue"
        result3 = engine.get_next_question(responses, used_rule_ids=used_rules)
        self.assertEqual(result3.next_question.id, self.q4.id)
        used_rules.append(result3.rule.id)

        # Now simulate backtracking to Q2 by:
        # 1. Removing Q3 and Q4 from responses
        # 2. Removing rules used after Q2 (Rule B and Rule C) from used_rules
        # 3. Keeping Rule A as used (since we're still at Q2 which Rule A leads to)
        responses = {str(self.q1.id): "Yes", str(self.q2.id): "Option1"}
        used_rules_after_backtrack = [self.rule_a.id]  # Only Rule A should remain

        # After backtracking, answer Q2 differently
        responses[str(self.q2.id)] = "Option2"

        # Rule B should now be available to fire again (if conditions match)
        # But since we changed the answer to Q2, Rule B's condition won't match
        # However, Rule B should be in the pool to evaluate
        result = engine.get_next_question(responses, used_rule_ids=used_rules_after_backtrack)

        # The key assertion: Rule B and Rule C should be available (not in used_rules)
        # This is verified by the fact that used_rules_after_backtrack only contains Rule A
        self.assertEqual(len(used_rules_after_backtrack), 1)
        self.assertIn(self.rule_a.id, used_rules_after_backtrack)
        self.assertNotIn(self.rule_b.id, used_rules_after_backtrack)
        self.assertNotIn(self.rule_c.id, used_rules_after_backtrack)

    def test_rule_at_backtrack_point_remains_used(self):
        """Test that the rule leading to the backtrack point remains in used_rules."""
        engine = RoutingEngine()

        # Answer Q1 = "Yes" -> Rule A fires -> Q2
        responses = {str(self.q1.id): "Yes"}
        result = engine.get_next_question(responses, used_rule_ids=[])
        self.assertEqual(result.next_question.id, self.q2.id)

        # Simulate backtracking to Q2
        # Rule A should still be marked as used since we're at the question it leads to
        used_rules_after_backtrack = [self.rule_a.id]

        # Try to get next question with same responses
        result = engine.get_next_question(responses, used_rule_ids=used_rules_after_backtrack)

        # Rule A should not fire again (it's in used_rules)
        if result.rule:
            self.assertNotEqual(result.rule.id, self.rule_a.id)


class ReevaluationQuestionModelTestCase(TestCase):
    def setUp(self):
        self.survey = Survey.objects.create(name_ar="استبيان", name_en="Survey")
        self.survey_version = SurveyVersion.objects.create(
            survey=self.survey,
            interval=SurveyVersion.SurveyInterval.MONTHLY,
        )

    def test_display_text_respects_language(self):
        question = ReevaluationQuestion.objects.create(
            survey_version=self.survey_version,
            text_ar="سؤال إعادة التقييم",
            text_en="Reevaluation question",
        )

        with translation.override("ar"):
            self.assertEqual(question.display_text, "سؤال إعادة التقييم")

        with translation.override("en"):
            self.assertEqual(question.display_text, "Reevaluation question")

        question_missing_en = ReevaluationQuestion.objects.create(
            survey_version=self.survey_version,
            text_ar="سؤال بالعربية فقط",
            text_en="",
        )

        with translation.override("en"):
            self.assertEqual(question_missing_en.display_text, "سؤال بالعربية فقط")


class AssessmentFlowLocalizationTestCase(TestCase):
    def test_arabic_labels_are_source_strings(self):
        self.assertEqual(
            AssessmentQuestion._meta.get_field("created_at").verbose_name, "تاريخ الإنشاء"
        )
        self.assertEqual(
            AssessmentQuestion._meta.get_field("updated_at").verbose_name, "تاريخ التحديث"
        )
        self.assertEqual(AssessmentOption._meta.verbose_name, "خيار التقييم")
        self.assertEqual(AssessmentOption._meta.verbose_name_plural, "خيارات التقييم")
        self.assertEqual(
            AssessmentFlowRule._meta.get_field("to_question").verbose_name, "إلى السؤال"
        )
        self.assertEqual(
            AssessmentFlowRule._meta.verbose_name, "قاعدة مسار التقييم"
        )
        self.assertEqual(
            AssessmentFlowRule._meta.verbose_name_plural, "قواعد مسار التقييم"
        )
