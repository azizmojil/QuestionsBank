import json
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.translation import override

from .engine import SurveyRoutingEngine
from .models import Survey, SurveyQuestion, SurveyRoutingRule, SurveyVersion


class SurveyBuilderViewTests(TestCase):
    def test_builder_page_renders(self):
        response = self.client.get(reverse("survey_builder"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, _("منشئ الاستبيان"))
        self.assertIn("response_types", response.context)
        self.assertIn("available_questions", response.context)

    # Removed test_matrix_response_type_is_available because ResponseType is removed from SurveyQuestion

    def test_builder_page_focuses_on_survey_only(self):
        response = self.client.get(reverse("survey_builder"))
        self.assertNotContains(response, "Live blueprint")
        self.assertNotContains(response, "Response types available")
        self.assertNotContains(response, "Design-first")

    def test_builder_uses_question_bank_choices(self):
        survey = Survey.objects.create(
            name_ar="بنك الأسئلة",
            name_en="Question Bank",
            code="BANK1",
        )
        version = SurveyVersion.objects.create(
            survey=survey,
            interval=SurveyVersion.SurveyInterval.MONTHLY,
        )
        question = SurveyQuestion.objects.create(
            survey_version=version,
            text_ar="سؤال من القاعدة",
            text_en="Banked question",
            # response_type removed
        )

        response = self.client.get(reverse("survey_builder"))

        self.assertContains(response, question.display_text)
        self.assertContains(response, f'value="{question.id}"')
        self.assertNotContains(response, 'class="question-text"')


class SurveyVersionStatusTranslationTests(TestCase):
    def test_status_labels_translate_between_languages(self):
        with override("en"):
            self.assertEqual(SurveyVersion.Status.LOCKED.label, "Locked")
        with override("ar"):
            self.assertEqual(SurveyVersion.Status.LOCKED.label, "مقفل")


class SurveyLocalizationTests(TestCase):
    def setUp(self):
        self.survey = Survey.objects.create(
            name_ar="استبيان مترجم",
            name_en="Localized Survey",
            code="LOCALIZED",
        )
        self.version = SurveyVersion.objects.create(
            survey=self.survey,
            interval=SurveyVersion.SurveyInterval.MONTHLY,
        )
        self.question = SurveyQuestion.objects.create(
            survey_version=self.version,
            text_ar="نص السؤال",
            text_en="Question text",
        )

    def test_survey_display_name_switches_language(self):
        with override("ar"):
            self.assertEqual(self.survey.display_name, "استبيان مترجم")
        with override("en"):
            self.assertEqual(self.survey.display_name, "Localized Survey")

    def test_survey_question_display_text_switches_language(self):
        with override("ar"):
            self.assertEqual(self.question.display_text, "نص السؤال")
        with override("en"):
            self.assertEqual(self.question.display_text, "Question text")


class SurveyConstraintTests(TestCase):
    def test_survey_names_are_unique(self):
        Survey.objects.create(
            name_ar="استبيان ١",
            name_en="Survey 1",
            code="SURV1",
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            Survey.objects.create(
                name_ar="استبيان ١",
                name_en="Survey 2",
                code="SURV2",
            )

        with self.assertRaises(IntegrityError), transaction.atomic():
            Survey.objects.create(
                name_ar="استبيان ٢",
                name_en="Survey 1",
                code="SURV3",
            )


class SurveyRoutingEngineTests(TestCase):
    def setUp(self):
        self.survey = Survey.objects.create(
            name_ar="توجيه",
            name_en="Routing",
            code="ROUTE",
        )
        self.version = SurveyVersion.objects.create(
            survey=self.survey,
            interval=SurveyVersion.SurveyInterval.MONTHLY,
        )
        self.q1 = SurveyQuestion.objects.create(
            survey_version=self.version,
            text_ar="س١",
            text_en="Q1",
        )
        self.q2 = SurveyQuestion.objects.create(
            survey_version=self.version,
            text_ar="س٢",
            text_en="Q2",
        )
        self.q3 = SurveyQuestion.objects.create(
            survey_version=self.version,
            text_ar="س٣",
            text_en="Q3",
        )

        SurveyRoutingRule.objects.create(
            to_question=self.q2,
            condition=json.dumps(
                {
                    "conditions": [
                        {"question": self.q1.id, "operator": "==", "value": "Yes"},
                    ]
                }
            ),
            priority=0,
        )
        SurveyRoutingRule.objects.create(
            to_question=self.q3,
            condition=json.dumps({"fallback": True}),
            priority=99,
        )

    def test_condition_rule_applied_before_fallback(self):
        engine = SurveyRoutingEngine(self.version)
        responses = {str(self.q1.id): "Yes"}
        result = engine.get_next_question(responses, used_rule_ids=[])

        self.assertIsNotNone(result.next_question)
        self.assertEqual(result.next_question.id, self.q2.id)
        self.assertEqual(result.rule.to_question_id, self.q2.id)

    def test_used_rule_is_skipped_and_fallback_applies(self):
        engine = SurveyRoutingEngine(self.version)
        responses = {str(self.q1.id): "Yes"}
        first = engine.get_next_question(responses, used_rule_ids=[])

        result = engine.get_next_question(
            responses,
            used_rule_ids=[first.rule.id],
        )

        self.assertIsNotNone(result.next_question)
        self.assertEqual(result.next_question.id, self.q3.id)
        self.assertTrue(result.rule.condition.startswith("{"))

    def test_fallback_used_when_no_condition_matches(self):
        engine = SurveyRoutingEngine(self.version)
        responses = {str(self.q1.id): "No"}
        result = engine.get_next_question(responses, used_rule_ids=[])

        self.assertIsNotNone(result.next_question)
        self.assertEqual(result.next_question.id, self.q3.id)


class SurveyRoutingApiTests(TestCase):
    def setUp(self):
        self.survey = Survey.objects.create(
            name_ar="توجيه",
            name_en="Routing",
            code="ROUTE",
        )
        self.version = SurveyVersion.objects.create(
            survey=self.survey,
            interval=SurveyVersion.SurveyInterval.MONTHLY,
        )
        self.q1 = SurveyQuestion.objects.create(
            survey_version=self.version,
            text_ar="س١",
            text_en="Q1",
        )

    def test_routing_data_endpoint_returns_questions(self):
        SurveyRoutingRule.objects.create(
            to_question=self.q1,
            condition=json.dumps({"fallback": True}),
            priority=0,
            description="entry",
        )
        url = reverse("survey_routing_data")
        response = self.client.get(url, {"version_id": self.version.id})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("questions", payload)
        self.assertEqual(payload["questions"][0]["id"], self.q1.id)
        self.assertEqual(payload["rules"][0]["to_question"], self.q1.id)

    def test_save_routing_endpoint_persists_rules_and_layout(self):
        url = reverse("survey_routing_save")
        payload = {
            "version_id": self.version.id,
            "layout": {str(self.q1.id): {"x": 15, "y": 25}},
            "rules": [
                {
                    "to_question": self.q1.id,
                    "condition": {"fallback": True},
                    "priority": 1,
                    "description": "fallback",
                }
            ],
        }

        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            SurveyRoutingRule.objects.filter(to_question=self.q1).count(),
            1,
        )
        self.version.refresh_from_db()
        self.assertIn(str(self.q1.id), self.version.routing_layout)
        self.assertEqual(self.version.routing_layout[str(self.q1.id)]["x"], 15)
