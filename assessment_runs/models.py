from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
import os
import uuid

from surveys.models import SurveyQuestion, SurveyVersion
from assessment_flow.models import AssessmentOption

User = get_user_model()


def get_assessment_file_path(instance, filename: str) -> str:
    """
    Build a structured upload path for assessment files.
    Files are grouped by assessment run and result to avoid collisions.
    """
    base = "assessment_files"
    ext = os.path.splitext(filename)[1]
    result = getattr(instance, "assessment_result", None)
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

    @property
    def assessment_path(self):
        return self.results

    @property
    def status(self):
        if self.results:
            return "COMPLETE"
        return "NOT_VISITED"


class QuestionClassificationRule(models.Model):
    """Rule used to classify a SurveyQuestion after an assessment run."""

    class Meta:
        verbose_name = _("قاعدة تصنيف")
        verbose_name_plural = _("قواعد التصنيف")
        ordering = ["priority", "id"]

    classification = models.CharField(max_length=100, verbose_name=_("التصنيف"))
    survey_question = models.ForeignKey(
        SurveyQuestion,
        on_delete=models.CASCADE,
        related_name="classification_rules",
        verbose_name=_("سؤال الاستبيان"),
    )
    condition = models.TextField(
        blank=True,
        verbose_name=_("الشرط"),
        help_text=_("منطق JSON يتم تقييمه بواسطة محرك التصنيف."),
    )
    priority = models.IntegerField(default=0, verbose_name=_("الأولوية"))
    is_active = models.BooleanField(default=True, verbose_name=_("نشط"))
    description = models.CharField(max_length=255, blank=True, verbose_name=_("الوصف"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.description or f"Rule for {self.survey_question}"


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
