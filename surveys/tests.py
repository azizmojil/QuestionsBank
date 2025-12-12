from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.translation import override

from .models import SurveyQuestion, SurveyVersion


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
