from django.test import TestCase
from django.urls import reverse

from .models import SurveyQuestion


class SurveyBuilderViewTests(TestCase):
    def test_builder_page_renders(self):
        response = self.client.get(reverse("survey_builder"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Survey builder")
        self.assertIn("response_types", response.context)

    def test_matrix_response_type_is_available(self):
        response = self.client.get(reverse("survey_builder"))
        response_types = response.context["response_types"]
        self.assertTrue(
            any(rt["value"] == SurveyQuestion.ResponseType.MATRIX for rt in response_types)
        )
