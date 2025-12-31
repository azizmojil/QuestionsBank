from django.db import IntegrityError, transaction
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.translation import gettext as _

from .models import ResponseGroup, QuestionStaging
from surveys.models import Survey, SurveyVersion, SurveyQuestion
from assessment_runs.models import AssessmentRun, AssessmentResult
import datetime


class ResponseGroupConstraintTests(TestCase):
    def test_name_must_be_unique(self):
        ResponseGroup.objects.create(name="Group A")

        with self.assertRaises(IntegrityError), transaction.atomic():
            ResponseGroup.objects.create(name="Group A")


class PipelineViewTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_pipeline_page_renders(self):
        response = self.client.get(reverse('pipeline_overview'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pipeline.html')
        self.assertIn("pipelines", response.context)

    def test_pipeline_states_reflect_backend(self):
        survey = Survey.objects.create(name_ar="مسح", name_en="Survey", code="SVY")
        version = SurveyVersion.objects.create(
            survey=survey,
            interval=SurveyVersion.SurveyInterval.MONTHLY,
            status=SurveyVersion.Status.LOCKED,
            version_date=datetime.date.today(),
        )

        question = SurveyQuestion.objects.create(
            survey_version=version,
            text_ar="سؤال",
            text_en="Question",
            is_required=True,
        )
        QuestionStaging.objects.create(
            survey=survey,
            survey_version=version,
            text_ar="مسودة",
            text_en="",
            is_sent_for_translation=True,
        )

        assessment_run = version.assessment_run
        AssessmentResult.objects.create(
            assessment_run=assessment_run,
            survey_question=question,
            results=[],
        )

        response = self.client.get(reverse('pipeline_overview'))
        pipeline = response.context["pipelines"][0]
        state = pipeline["state"]

        self.assertEqual(state["self"], "done")
        self.assertEqual(state["routing"], "done")
        self.assertEqual(state["business"], "done")
        self.assertEqual(state["lang"], "done")
        self.assertEqual(state["translation"], "in_progress")
        self.assertEqual(state["qbank"], "done")
        self.assertEqual(state["approval"], "done")
