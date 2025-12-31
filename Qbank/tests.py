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
        self.assertContains(response, _("القائمة المبدئية"))
        self.assertContains(response, _("تدقيق لغوي"))
        self.assertContains(response, _("قائمة الترجمة"))
        self.assertContains(response, _("قواعد التوجيه"))
        self.assertContains(response, _("قواعد الأعمال"))
        self.assertContains(response, _("إنشاء نسخة الاستبيان"))
        self.assertContains(response, _("الموافقة النهائية"))

    def test_pipeline_page_shows_status_markers(self):
        response = self.client.get(reverse('pipeline_overview'))

        for status_label in (_("مكتمل"), _("قيد التنفيذ"), _("لم يبدأ"), _("تم التجاوز")):
            self.assertContains(response, status_label)
