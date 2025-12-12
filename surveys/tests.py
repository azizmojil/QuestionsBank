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

    def test_matrix_response_type_is_available(self):
        response = self.client.get(reverse("survey_builder"))
        response_types = response.context["response_types"]
        self.assertTrue(
            any(rt["value"] == SurveyQuestion.ResponseType.MATRIX for rt in response_types)
        )

    def test_builder_page_focuses_on_survey_only(self):
        response = self.client.get(reverse("survey_builder"))
        self.assertNotContains(response, "Live blueprint")
        self.assertNotContains(response, "Response types available")
        self.assertNotContains(response, "Design-first")


class SurveyVersionStatusTranslationTests(TestCase):
    def test_status_labels_translate_between_languages(self):
        with override("en"):
            self.assertEqual(SurveyVersion.Status.LOCKED.label, "Locked")
        with override("ar"):
            self.assertEqual(SurveyVersion.Status.LOCKED.label, "مقفل")


class SurveyLocalizationTests(TestCase):
    def setUp(self):
        self.survey = Survey.objects.create(
            name="Localized Survey",
            name_ar="استبيان مترجم",
            name_en="Localized Survey",
        )
        self.version = SurveyVersion.objects.create(
            survey=self.survey,
            interval=SurveyVersion.SurveyInterval.MONTHLY,
        )
        self.question = SurveyQuestion.objects.create(
            survey_version=self.version,
            text="Legacy text",
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
