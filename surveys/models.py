from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
import datetime

User = get_user_model()


class Survey(models.Model):
    """Top-level survey definition.

    Represents a logical survey instrument (e.g. \"Labor Force Survey\").
    Specific versions / waves are handled by SurveyVersion.
    """

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ACTIVE = "ACTIVE", "Active"
        ARCHIVED = "ARCHIVED", "Archived"

    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        help_text="Optional short code, e.g. LFS_2025.",
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
        help_text="Auto-generated from name if left blank.",
    )
    description = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        help_text="Draft: still being designed. Active: in use. Archived: no longer used.",
    )

    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_surveys",
        help_text="Primary responsible person for this survey.",
    )

    editors = models.ManyToManyField(
        User,
        blank=True,
        related_name="editable_surveys",
        help_text="Users allowed to edit survey structure.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        # Auto-generate slug from name if missing
        if not self.slug and self.name:
            self.slug = slugify(self.name, allow_unicode=True)

        # If code is empty, you can optionally derive a default from slug
        if not self.code and self.slug:
            self.code = self.slug.upper()[:50]

        super().save(*args, **kwargs)


class SurveyVersion(models.Model):
    """Represents a specific wave/version of a survey.

    Example: Labor Force Survey March 2025, or \"2025-Q1\" round.
    """

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ACTIVE = "ACTIVE", "Active"
        LOCKED = "LOCKED", "Locked"
        ARCHIVED = "ARCHIVED", "Archived"

    class SurveyInterval(models.TextChoices):
        MONTHLY = "M", "Monthly"
        QUARTERLY = "Q", "Quarterly"
        BIANNUALLY = "B", "Biannually"
        ANNUALLY = "A", "Annually"

    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name="versions",
    )

    version_label = models.CharField(
        max_length=50,
        blank=True,
        help_text="Human-friendly label, e.g. '2025-03' or 'Round 1-2025'.",
    )

    version_date = models.DateField(
        default=datetime.date.today,
        help_text="Reference date of this version/wave.",
    )

    interval = models.CharField(
        max_length=20,
        choices=SurveyInterval.choices,
        help_text="The frequency of the survey.",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        help_text="Draft: editable; Active: in collection; Locked: structure frozen; Archived: historic.",
    )

    metadata = models.JSONField(
        blank=True,
        default=dict,
        help_text="Optional metadata, e.g. sampling frame info, notes, etc.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-version_date", "-id"]
        unique_together = ("survey", "version_label")

    def __str__(self) -> str:
        return f"{self.survey.name} - {self.version_label or '(new)'}"

    def _generate_version_label(self):
        """Generate a label based on interval and date."""
        if not self.version_date or not self.survey.code:
            return ""

        year = self.version_date.strftime("%y")
        month = self.version_date.strftime("%m")
        
        return f"{year}{self.survey.code}{self.interval}{month}"

    def save(self, *args, **kwargs):
        self.version_label = self._generate_version_label()
        super().save(*args, **kwargs)


class SurveyQuestion(models.Model):
    """Individual question belonging to a specific SurveyVersion.

    This is the canonical question bank for a given wave. Assessment / flows
    live in a different app and reference these questions.
    """

    class ResponseType(models.TextChoices):
        BINARY = "BINARY", "Yes/No (Binary)"
        SINGLE_CHOICE = "SINGLE_CHOICE", "Single Choice"
        MULTIPLE_CHOICE = "MULTIPLE_CHOICE", "Multiple Choice"
        FREE_TEXT = "FREE_TEXT", "Free Text"
        NUMERIC = "NUMERIC", "Numeric"
        DATE = "DATE", "Date"
        DATETIME = "DATETIME", "Date & Time"
        SCALE = "SCALE", "Scale (e.g. 1–5)"

    survey_version = models.ForeignKey(
        SurveyVersion,
        on_delete=models.CASCADE,
        related_name="questions",
    )

    code = models.CharField(
        max_length=50,
        blank=True,
        help_text="Optional question code, e.g. Q1, A01, etc.",
    )

    text = models.TextField(help_text="Full text of the question as seen by the respondent.")

    help_text = models.TextField(
        blank=True,
        help_text="Optional help text / enumerator instructions.",
    )

    section_label = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional logical section/group name for reporting only.",
    )

    response_type = models.CharField(
        max_length=30,
        choices=ResponseType.choices,
        default=ResponseType.FREE_TEXT,
        help_text="Basic expected response type; detailed coding/validation can live elsewhere.",
    )

    is_required = models.BooleanField(
        default=False,
        help_text="Whether the question must be answered in data collection.",
    )

    metadata = models.JSONField(
        blank=True,
        default=dict,
        help_text="Optional extra structure (allowed values, ranges, skip tags, etc.).",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        prefix = f"{self.code} - " if self.code else ""
        short = self.text[:60] + ("..." if len(self.text) > 60 else "")
        return f"{prefix}{short}"

    def short_text(self) -> str:
        return self.text[:150] + ("..." if len(self.text) > 150 else "")

    short_text.short_description = "Question Text"
