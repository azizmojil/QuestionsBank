from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
import os
import uuid

from surveys.models import SurveyQuestion, SurveyVersion
from indicators.models import Indicator

User = get_user_model()


def get_assessment_file_path(instance, filename: str) -> str:
    """Build a structured, stable path for uploaded assessment files."""
    # This function is now defined in the assessment_runs app,
    # but we keep it here for now to avoid breaking existing migrations.
    # It will be removed in a future step.
    from assessment_runs.models import get_assessment_file_path as new_get_assessment_file_path
    return new_get_assessment_file_path(instance, filename)

class AssessmentQuestion(models.Model):
    """A node in the assessment decision-flow graph."""

    class OptionType(models.TextChoices):
        STATIC = "STATIC", _("خيارات ثابتة")
        DYNAMIC_FROM_PREVIOUS_MULTI_SELECT = "DYNAMIC_FROM_PREVIOUS_MULTI_SELECT", _("ديناميكي (من اختيار متعدد سابق)")
        DYNAMIC_SURVEY_QUESTIONS = "DYNAMIC_SURVEY_QUESTIONS", _("ديناميكي (أسئلة الاستبيان)")
        INDICATOR_LIST = "INDICATOR_LIST", _("قائمة المؤشرات")

    text = models.CharField(max_length=512)
    explanation = models.TextField(blank=True, help_text=_("توضيح اختياري للمقيّمين."))
    option_type = models.CharField(max_length=50, choices=OptionType.choices, default=OptionType.STATIC)
    use_searchable_dropdown = models.BooleanField(default=False)
    allow_multiple_choices = models.BooleanField(default=False)
    dynamic_option_source_question = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="dynamic_option_consumers"
    )
    indicator_source = models.ForeignKey(
        Indicator, on_delete=models.SET_NULL, null=True, blank=True, related_name="assessment_questions"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.text

class AssessmentOption(models.Model):
    """An option/branch from an AssessmentQuestion."""

    class ResponseType(models.TextChoices):
        PREDEFINED = "PREDEFINED", _("خيار محدد مسبقاً")
        FREE_TEXT = "FREE_TEXT", _("إدخال نصي حر")
        NUMERICAL = "NUMERICAL", _("إدخال رقمي")
        URL = "URL", _("إدخال رابط")

    question = models.ForeignKey(AssessmentQuestion, related_name="options", on_delete=models.CASCADE)
    text = models.TextField(blank=True)
    explanation = models.TextField(blank=True)
    response_type = models.CharField(max_length=20, choices=ResponseType.choices, default=ResponseType.PREDEFINED)
    requires_file_upload = models.BooleanField(default=False)
    file_upload_explanation = models.TextField(blank=True)
    metadata = models.JSONField(blank=True, default=dict)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.text[:80]

class AssessmentFlowRule(models.Model):
    """Declarative routing rule for the assessment flow."""
    from_question = models.ForeignKey(
        AssessmentQuestion,
        on_delete=models.CASCADE,
        related_name="outgoing_rules",
    )
    condition = models.TextField(
        blank=True,
        help_text=_("تعبير يُقيّمه محرك التوجيه، مثل \"option == 'CODE_A' -> 'NEXT_Q_CODE'\""),
    )
    priority = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["from_question_id", "priority"]

    def __str__(self):
        return self.description or f"Rule for Q{self.from_question_id}"
