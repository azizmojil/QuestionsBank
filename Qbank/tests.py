from django.db import IntegrityError, transaction
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.translation import gettext as _

from .models import ResponseGroup


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
        self.assertTemplateUsed(response, 'Qbank/pipeline.html')
        self.assertContains(response, _("إنشاء نسخة الاستبيان"))
        self.assertContains(response, _("الموافقة النهائية"))
