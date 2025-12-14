from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
import os
import uuid

from surveys.models import SurveyQuestion, SurveyVersion
from assessment_flow.models import AssessmentOption, get_assessment_file_path

User = get_user_model()


class AssessmentRun(models.Model):
    """A logical run/session of assessing a survey version."""

    class Meta:
        verbose_name = _("عملية تقييم")
        verbose_name_plural = _("عمليات التقييم")
        ordering = ["-created_at"]

    class Status(models.TextChoices):
        DRAFT = "DRAFT", _("مسودة")
        IN_PROGRESS = "IN_PROGRESS", _("قيد التنفيذ")
        COMPLETE = "COMPLETE", _("مكتمل")
        CANCELLED = "CANCELLED", _("ملغي")

    survey_version = models.ForeignKey(SurveyVersion, on_delete=models.CASCADE, related_name="assessment_runs", verbose_name=_("إصدار الاستبيان"))
    label = models.CharField(max_length=100, blank=True, verbose_name=_("تسمية"))
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, verbose_name=_("الحالة"))
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_assessment_runs", verbose_name=_("تم إنشاؤها بواسطة"))
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_assessment_runs", verbose_name=_("معينة ل"))
    started_at = models.DateTimeField(null=True, blank=True, verbose_name=_("بدأت في"))
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name=_("اكتملت في"))
    notes = models.TextField(blank=True, verbose_name=_("ملاحظات"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Run for {self.survey_version} ({self.label})" if self.label else f"Run for {self.survey_version}"


class AssessmentResult(models.Model):
    """Result for a single SurveyQuestion within an AssessmentRun."""

    class Meta:
        verbose_name = _("نتيجة التقييم")
        verbose_name_plural = _("نتائج التقييم")
        unique_together = ("assessment_run", "survey_question")
        ordering = ["assessment_run_id", "survey_question_id"]

    class Status(models.TextChoices):
        NOT_VISITED = "NOT_VISITED", _("لم تتم زيارته")
        IN_PROGRESS = "IN_PROGRESS", _("قيد التنفيذ")
        COMPLETE = "COMPLETE", _("مكتمل")
        PENDING_UPLOAD = "PENDING_UPLOAD", _("بانتظار رفع ملف")

    assessment_run = models.ForeignKey(AssessmentRun, on_delete=models.CASCADE, related_name="results", verbose_name=_("عملية التقييم"))
    survey_question = models.ForeignKey(SurveyQuestion, on_delete=models.CASCADE, related_name="assessment_results", verbose_name=_("سؤال الاستبيان"))
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NOT_VISITED, verbose_name=_("الحالة"))
    assessed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="assessment_results", verbose_name=_("تم تقييمها بواسطة"))
    assessment_path = models.JSONField(default=list, blank=True, verbose_name=_("مسار التقييم"))
    summary_comment = models.TextField(blank=True, verbose_name=_("تعليق موجز"))
    flags = models.JSONField(blank=True, default=dict, verbose_name=_("أعلام"))
    assessed_at = models.DateTimeField(auto_now=True, verbose_name=_("تم تقييمها في"))

    def __str__(self):
        return f"Result: {self.survey_question} in {self.assessment_run}"


class QuestionClassificationRule(models.Model):
    """Rule used to classify a SurveyQuestion after an assessment run."""

    class Meta:
        verbose_name = _("قاعدة تصنيف السؤال")
        verbose_name_plural = _("قواعد تصنيف السؤال")
        ordering = ["survey_question_id", "priority", "id"]

    survey_question = models.ForeignKey(
        SurveyQuestion,
        on_delete=models.CASCADE,
        related_name="classification_rules",
        verbose_name=_("سؤال الاستبيان"),
    )
    classification = models.CharField(max_length=100, verbose_name=_("التصنيف"))
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
        return self.description or f"{self.classification} for {self.survey_question}"


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
