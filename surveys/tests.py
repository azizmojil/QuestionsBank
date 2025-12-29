from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.translation import override

from .models import Survey, SurveyQuestion, SurveyVersion


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
