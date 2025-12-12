from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
import os
import uuid

from surveys.models import SurveyQuestion, SurveyVersion
from assessment_flow.models import AssessmentOption, get_assessment_file_path

User = get_user_model()


class AssessmentRun(models.Model):
    """A logical run/session of assessing a survey version."""

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETE = "COMPLETE", "Complete"
        CANCELLED = "CANCELLED", "Cancelled"

    survey_version = models.ForeignKey(SurveyVersion, on_delete=models.CASCADE, related_name="assessment_runs")
    label = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_assessment_runs")
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_assessment_runs")
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Run for {self.survey_version} ({self.label})" if self.label else f"Run for {self.survey_version}"


class AssessmentResult(models.Model):
    """Result for a single SurveyQuestion within an AssessmentRun."""

    class Status(models.TextChoices):
        NOT_VISITED = "NOT_VISITED", "Not Visited"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETE = "COMPLETE", "Complete"
        PENDING_UPLOAD = "PENDING_UPLOAD", "Pending File Upload"

    assessment_run = models.ForeignKey(AssessmentRun, on_delete=models.CASCADE, related_name="results")
    survey_question = models.ForeignKey(SurveyQuestion, on_delete=models.CASCADE, related_name="assessment_results")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NOT_VISITED)
    assessed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="assessment_results")
    assessment_path = models.JSONField(default=list, blank=True)
    summary_comment = models.TextField(blank=True)
    flags = models.JSONField(blank=True, default=dict)
    assessed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("assessment_run", "survey_question")
        ordering = ["assessment_run_id", "survey_question_id"]

    def __str__(self):
        return f"Result: {self.survey_question} in {self.assessment_run}"


class AssessmentFile(models.Model):
    """File uploaded as part of an assessment result."""
    assessment_result = models.ForeignKey(AssessmentResult, on_delete=models.CASCADE, related_name="files")
    triggering_option = models.ForeignKey(AssessmentOption, on_delete=models.SET_NULL, null=True, blank=True, related_name="uploaded_files")
    file = models.FileField(upload_to=get_assessment_file_path)
    original_filename = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="uploaded_assessment_files")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(blank=True, default=dict)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.original_filename or os.path.basename(self.file.name)
