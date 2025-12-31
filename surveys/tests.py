import json

from django.db import IntegrityError, transaction, connection
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.translation import override

from .models import Survey, SurveyQuestion, SurveyVersion, SurveySection, SurveyRoutingRule
from Qbank.models import MatrixItemGroup, MatrixItem
from Rbank.models import ResponseGroup, ResponseType


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


class FinalBuilderSubmissionTests(TestCase):
    def setUp(self):
        self.survey = Survey.objects.create(
            name_ar="استبيان نهائي",
            name_en="Final Survey",
            code="FS1",
        )
        self.version = SurveyVersion.objects.create(
            survey=self.survey,
            interval=SurveyVersion.SurveyInterval.MONTHLY,
        )
        self.question = SurveyQuestion.objects.create(
            survey_version=self.version,
            text_ar="سؤال موجود",
            text_en="Existing question",
        )
        self.response_type = ResponseType.objects.create(name_ar="اختيار", name_en="Choice")
        self.response_group = ResponseGroup.objects.create(name="نعم/لا")
        self.matrix_item = MatrixItem.objects.create(text_ar="صف", text_en="Row")
        self.matrix_group = MatrixItemGroup.objects.create(name="مجموعة مصفوفة")
        self.matrix_group.items.add(self.matrix_item)

    def test_submit_final_questionnaire_creates_sections_and_updates_questions(self):
        payload = {
            "version_id": self.version.id,
            "sections": [
                {
                    "title": "القسم الأول",
                    "description": "وصف",
                    "questions": [
                        {
                            "id": self.question.id,
                            "response_group_id": self.response_group.id,
                            "response_type_id": self.response_type.id,
                            "matrix_item_group_id": self.matrix_group.id,
                            "is_required": True,
                            "is_matrix": True,
                        }
                    ],
                }
            ],
        }

        response = self.client.post(
            reverse("submit_final_questionnaire"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(SurveySection.objects.filter(survey_version=self.version).count(), 1)
        section = SurveySection.objects.first()

        self.question.refresh_from_db()
        self.assertEqual(self.question.section, section)
        self.assertTrue(self.question.is_required)
        self.assertTrue(self.question.is_matrix)
        self.assertEqual(self.question.response_group, self.response_group)
        self.assertEqual(self.question.response_type, self.response_type)
        self.assertEqual(self.question.matrix_item_group, self.matrix_group)

    def test_manual_questions_are_created_in_final_builder(self):
        payload = {
            "version_id": self.version.id,
            "sections": [
                {
                    "title": "قسم جديد",
                    "description": "",
                    "questions": [
                        {
                            "label": "سؤال يدوي",
                            "is_required": False,
                        }
                    ],
                }
            ],
        }

        response = self.client.post(
            reverse("submit_final_questionnaire"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(SurveyQuestion.objects.filter(survey_version=self.version, text_ar="سؤال يدوي").count(), 1)


class SurveyRoutingBuilderTests(TestCase):
    def setUp(self):
        self.survey = Survey.objects.create(
            name_ar="استبيان توجيه",
            name_en="Routing Survey",
            code="ROUTE",
        )
        self.version = SurveyVersion.objects.create(
            survey=self.survey,
            interval=SurveyVersion.SurveyInterval.MONTHLY,
        )
        self.q1 = SurveyQuestion.objects.create(
            survey_version=self.version,
            text_ar="سؤال ١",
            text_en="Question 1",
        )
        self.q2 = SurveyQuestion.objects.create(
            survey_version=self.version,
            text_ar="سؤال ٢",
            text_en="Question 2",
        )

    def test_routing_data_includes_rules_and_layout(self):
        layout = {"1": {"x": 10, "y": 20}}
        self.version.routing_layout = layout
        self.version.save()

        SurveyRoutingRule.objects.create(
            to_question=self.q2,
            condition=json.dumps({"fallback": True}),
            priority=3,
            description="إلى السؤال الثاني",
        )

        response = self.client.get(
            reverse("survey_routing_data"),
            {"version_id": self.version.id},
        )
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertEqual(payload["layout"], layout)
        self.assertEqual(len(payload.get("questions", [])), 2)
        self.assertEqual(len(payload.get("rules", [])), 1)
        rule_payload = payload["rules"][0]
        self.assertEqual(rule_payload["to_question"], self.q2.id)
        self.assertEqual(rule_payload["priority"], 3)
        self.assertEqual(rule_payload["condition"], {"fallback": True})

    def test_save_routing_marks_version_and_persists_rules(self):
        payload = {
            "version_id": self.version.id,
            "layout": {"1": {"x": 5, "y": 6, "label": "Q1"}},
            "rules": [
                {
                    "to_question": self.q2.id,
                    "condition": {
                        "conditions": [
                            {"question": self.q1.id, "operator": "==", "value": "yes"}
                        ]
                    },
                    "priority": 2,
                    "description": "Route to Q2",
                }
            ],
        }

        response = self.client.post(
            reverse("survey_routing_save"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        self.version.refresh_from_db()
        self.assertTrue(self.version.routing_logic_done)
        self.assertIsNotNone(self.version.routing_logic_done_at)
        self.assertEqual(self.version.routing_layout, payload["layout"])

        rules = SurveyRoutingRule.objects.filter(to_question__survey_version=self.version)
        self.assertEqual(rules.count(), 1)
        rule = rules.first()
        self.assertEqual(rule.priority, 2)
        self.assertEqual(json.loads(rule.condition), payload["rules"][0]["condition"])


class SurveySchemaTests(TestCase):
    def _table_columns(self, table_name):
        """Lightweight schema check mirroring the migration guard."""
        with connection.cursor() as cursor:
            return [
                col.name
                for col in connection.introspection.get_table_description(cursor, table_name)
            ]

    def test_section_column_exists(self):
        columns = self._table_columns(SurveyQuestion._meta.db_table)
        self.assertIn("section_id", columns)
