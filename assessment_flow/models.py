from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.utils.translation import get_language
import os
import uuid

from surveys.models import SurveyQuestion, SurveyVersion
from indicators.models import Indicator

User = get_user_model()


def get_assessment_file_path(instance, filename: str) -> str:
    """Build a structured, stable path for uploaded assessment files."""
    from assessment_runs.models import get_assessment_file_path as new_get_assessment_file_path
    return new_get_assessment_file_path(instance, filename)


class AssessmentQuestion(models.Model):
    """A node in the assessment decision-flow graph."""

    class OptionType(models.TextChoices):
        STATIC = "STATIC", _("خيارات ثابتة")
        DYNAMIC_FROM_PREVIOUS_MULTI_SELECT = "DYNAMIC_FROM_PREVIOUS_MULTI_SELECT", _("ديناميكي (من اختيار متعدد سابق)")
        DYNAMIC_SURVEY_QUESTIONS = "DYNAMIC_SURVEY_QUESTIONS", _("ديناميكي (أسئلة الاستبيان)")
        INDICATOR_LIST = "INDICATOR_LIST", _("قائمة المؤشرات")

    text_ar = models.CharField(max_length=512, blank=True, verbose_name=_("السؤال [عربية]"))
    text_en = models.CharField(max_length=512, blank=True, verbose_name=_("السؤال [إنجليزية]"))
    explanation_ar = models.TextField(blank=True, verbose_name=_("التوضيح [عربية]"))
    explanation_en = models.TextField(blank=True, verbose_name=_("التوضيح [إنجليزية]"))
    option_type = models.CharField(
        max_length=50,
        choices=OptionType.choices,
        default=OptionType.STATIC,
        verbose_name=_("نوع الخيار"),
    )
    use_searchable_dropdown = models.BooleanField(
        default=False, verbose_name=_("استخدام قائمة منسدلة قابلة للبحث")
    )
    allow_multiple_choices = models.BooleanField(
        default=False, verbose_name=_("السماح باختيارات متعددة")
    )
    dynamic_option_source_question = models.ForeignKey(
        "self",
        verbose_name=_("سؤال مصدر الخيارات الديناميكي"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="dynamic_option_consumers",
    )
    indicator_source = models.ForeignKey(
        Indicator,
        verbose_name=_("مصدر المؤشر"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assessment_questions",
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        ordering = ["id"]
        verbose_name = _("سؤال التقييم")
        verbose_name_plural = _("أسئلة التقييم")

    def __str__(self):
        return self.display_text

    @property
    def display_text(self) -> str:
        lang = (get_language() or "ar")[:2]
        if lang == "ar" and self.text_ar:
            return self.text_ar
        if lang == "en" and self.text_en:
            return self.text_en
        return self.text_en or self.text_ar

    display_text.fget.short_description = _("السؤال")

    @property
    def display_explanation(self) -> str:
        lang = (get_language() or "ar")[:2]
        if lang == "ar" and self.explanation_ar:
            return self.explanation_ar
        if lang == "en" and self.explanation_en:
            return self.explanation_en
        return self.explanation_en or self.explanation_ar


class AssessmentOption(models.Model):
    """An option/branch from an AssessmentQuestion."""

    class ResponseType(models.TextChoices):
        PREDEFINED = "PREDEFINED", _("خيار محدد مسبقاً")
        FREE_TEXT = "FREE_TEXT", _("إدخال نصي حر")
        NUMERICAL = "NUMERICAL", _("إدخال رقمي")
        URL = "URL", _("إدخال رابط")

    question = models.ForeignKey(AssessmentQuestion, related_name="options", on_delete=models.CASCADE)
    text_ar = models.TextField(blank=True, verbose_name=_("الجواب [عربية]"))
    text_en = models.TextField(blank=True, verbose_name=_("الجواب [إنجليزية]"))
    explanation_ar = models.TextField(blank=True, verbose_name=_("التوضيح [عربية]"))
    explanation_en = models.TextField(blank=True, verbose_name=_("التوضيح [إنجليزية]"))
    response_type = models.CharField(
        max_length=20,
        choices=ResponseType.choices,
        default=ResponseType.PREDEFINED,
        verbose_name=_("نوع الاستجابة"),
    )
    requires_file_upload = models.BooleanField(default=False)
    file_upload_explanation = models.TextField(blank=True)

    class Meta:
        ordering = ["id"]
        verbose_name = _("Assessment Option")
        verbose_name_plural = _("Assessment Options")

    def __str__(self):
        text = self.display_text
        return text[:80]

    @property
    def display_text(self) -> str:
        lang = (get_language() or "ar")[:2]
        if lang == "ar" and self.text_ar:
            return self.text_ar
        if lang == "en" and self.text_en:
            return self.text_en
        return self.text_en or self.text_ar

    @property
    def display_explanation(self) -> str:
        lang = (get_language() or "ar")[:2]
        if lang == "ar" and self.explanation_ar:
            return self.explanation_ar
        if lang == "en" and self.explanation_en:
            return self.explanation_en
        return self.explanation_en or self.explanation_ar


class AssessmentFlowRule(models.Model):
    """Declarative routing rule for the assessment flow."""
    to_question = models.ForeignKey(
        AssessmentQuestion,
        verbose_name=_("To Question"),
        on_delete=models.CASCADE,
        related_name="incoming_rules",
    )
    condition = models.TextField(
        _("الشرط"),
        blank=True,
        help_text=_("تعبير يُقيّمه محرك التوجيه، مثل \"option == 'CODE_A' -> 'NEXT_Q_CODE'\""),
    )
    priority = models.IntegerField(default=0)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["to_question_id", "priority"]
        verbose_name = _("Assessment Flow Rule")
        verbose_name_plural = _("Assessment Flow Rules")

    def __str__(self):
        return self.description or f"Rule to Q{self.to_question_id}"


class ReevaluationQuestion(models.Model):
    """Questions used when reassessing future survey versions."""

    survey_version = models.ForeignKey(
        SurveyVersion,
        on_delete=models.CASCADE,
        related_name="reevaluation_questions",
        verbose_name=_("إصدار الاستبيان"),
    )
    text_ar = models.CharField(max_length=512, blank=True, verbose_name=_("السؤال [عربية]"))
    text_en = models.CharField(max_length=512, blank=True, verbose_name=_("السؤال [إنجليزية]"))
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        ordering = ["id"]
        verbose_name = _("سؤال إعادة التقييم")
        verbose_name_plural = _("اسئلة إعادة التقييم")

    def __str__(self):
        return self.display_text

    @property
    def display_text(self) -> str:
        lang = (get_language() or "ar")[:2]
        if lang == "ar" and self.text_ar:
            return self.text_ar
        if lang == "en" and self.text_en:
            return self.text_en
        return self.text_en or self.text_ar

    display_text.fget.short_description = _("السؤال")
