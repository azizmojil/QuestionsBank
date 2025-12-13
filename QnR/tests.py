from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import ResponseGroup


class ResponseGroupConstraintTests(TestCase):
    def test_name_must_be_unique(self):
        ResponseGroup.objects.create(name="Group A")

        with self.assertRaises(IntegrityError), transaction.atomic():
            ResponseGroup.objects.create(name="Group A")
