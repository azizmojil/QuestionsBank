from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import IndicatorSource


class IndicatorConstraintTests(TestCase):
    def test_indicator_names_are_unique(self):
        IndicatorSource.objects.create(name_ar="مؤشر", name_en="Indicator", code="IND1")

        with self.assertRaises(IntegrityError), transaction.atomic():
            IndicatorSource.objects.create(name_ar="مؤشر", name_en="Second name", code="IND2")

        with self.assertRaises(IntegrityError), transaction.atomic():
            IndicatorSource.objects.create(name_ar="اسم آخر", name_en="Indicator", code="IND3")
