from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.utils.translation import get_language
import os
import uuid

from surveys.models import SurveyQuestion, SurveyVersion
from assessment_flow.models import AssessmentOption, get_assessment_file_path

User = get_user_model()


def get_assessment_file_path(instance, filename: str) -> str:
    """
    Build a structured upload path for assessment files.
    Files are grouped by assessment run and result to avoid collisions.
    """
    base = "assessment_files"
    ext = os.path.splitext(filename)[1]
    result = getattr(instance, "assessment_result", None)
    if result is None:
        return os.path.join(base, "unassigned", f"{uuid.uuid4().hex}{ext}")
    run_id = getattr(result, "assessment_run_id", "run")
    result_id = getattr(result, "id", "result")
    return os.path.join(base, str(run_id), str(result_id), f"{uuid.uuid4().hex}{ext}")


class AssessmentRun(models.Model):
    """A logical run/session of assessing a survey version."""

    class Meta:
        verbose_name = _("عملية تقييم")
        verbose_name_plural = _("عمليات التقييم")
        ordering = ["-created_at"]

    survey_version = models.OneToOneField(SurveyVersion, on_delete=models.CASCADE, related_name="assessment_run", verbose_name=_("إصدار الاستبيان"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Run for {self.survey_version}"


class AssessmentResult(models.Model):
    """Result for a single SurveyQuestion within an AssessmentRun."""

    class Meta:
        verbose_name = _("نتيجة التقييم")
        verbose_name_plural = _("نتائج التقييم")
        unique_together = ("assessment_run", "survey_question")
        ordering = ["assessment_run_id", "survey_question__code"]

    assessment_run = models.ForeignKey(AssessmentRun, on_delete=models.CASCADE, related_name="results", verbose_name=_("عملية التقييم"))
    survey_question = models.ForeignKey(SurveyQuestion, on_delete=models.CASCADE, related_name="assessment_results", verbose_name=_("السؤال"))
    results = models.JSONField(default=list, blank=True, verbose_name=_("النتائج"))
    assessed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="assessment_results", verbose_name=_("بواسطة"))
    assessed_at = models.DateTimeField(auto_now=True, verbose_name=_("في"))
    classification = models.CharField(max_length=100, blank=True, verbose_name=_("التصنيف"))


class QuestionClassification(models.Model):
    """Defines a classification category (e.g., High Risk, Low Risk)."""
    name_ar = models.CharField(max_length=255, verbose_name=_("التصنيف [عربية]"))
    name_en = models.CharField(max_length=255, verbose_name=_("التصنيف [إنجليزية]"))

    class Meta:
        verbose_name = _("تصنيف")
        verbose_name_plural = _("التصنيفات")

    def __str__(self):
        lang = get_language()
        return self.name_ar if lang == 'ar' else self.name_en


class QuestionClassificationRule(models.Model):
    """Rule used to classify a SurveyQuestion based on assessment results."""

    class Meta:
        verbose_name = _("قاعدة تصنيف")
        verbose_name_plural = _("قواعد التصنيف")
        ordering = ["priority", "id"]

    classification = models.ForeignKey(
        QuestionClassification,
        on_delete=models.CASCADE,
        related_name="rules",
        verbose_name=_("التصنيف"),
    )
    condition = models.TextField(
        blank=True,
        verbose_name=_("القاعدة (JSON)"),
        help_text=_("منطق JSON يتم تقييمه بواسطة محرك التصنيف."),
    )
    priority = models.IntegerField(default=0, verbose_name=_("الأولوية"))
    is_active = models.BooleanField(default=True, verbose_name=_("نشط"))
    description = models.CharField(max_length=255, blank=True, verbose_name=_("الوصف"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.description or f"Rule for {self.classification}"


class AssessmentFile(models.Model):
    """File uploaded as part of an assessment result."""

    class Meta:
        verbose_name = _("ملف التقييم")
        verbose_name_plural = _("ملفات التقييم")
        ordering = ["-uploaded_at"]

    assessment_result = models.ForeignKey(AssessmentResult, on_delete=models.CASCADE, related_name="files", verbose_name=_("نتيجة التقييم"))
    triggering_option = models.ForeignKey(AssessmentOption, on_delete=models.SET_NULL, null=True, blank=True, related_name="uploaded_files", verbose_name=_("الخيار المحفز"))
    file = models.FileField(upload_to=get_assessment_file_path, verbose_name=_("الملف"))
    original_filename = models.CharField(max_length=255, verbose_name=_("اسم الملف الأصلي"))
    description = models.TextField(blank=True, verbose_name=_("الوصف"))
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="uploaded_assessment_files", verbose_name=_("تم الرفع بواسطة"))
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name=_("تم الرفع في"))

    def __str__(self):
        return self.original_filename or os.path.basename(self.file.name)
