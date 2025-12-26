from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils.translation import get_language
import datetime

User = get_user_model()


class Survey(models.Model):
    """Top-level survey definition."""

    class Meta:
        verbose_name = _("استبيان")
        verbose_name_plural = _("الاستبيانات")
        ordering = ["name_ar", "name_en"]

    name_ar = models.CharField(
        max_length=255,
        unique=True,
        verbose_name=_("اسم المسح [عربية]"),
    )
    name_en = models.CharField(
        max_length=255,
        unique=True,
        verbose_name=_("اسم المسح [انجليزية]"),
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        verbose_name=_("الرمز"),
    )
    description = models.TextField(blank=True, verbose_name=_("الوصف"))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.display_name

    @property
    def display_name(self) -> str:
        lang = (get_language() or "ar")[:2]
        if lang == "ar" and self.name_ar:
            return self.name_ar
        if lang == "en" and self.name_en:
            return self.name_en
        # Fallbacks for missing translations
        return self.name_en or self.name_ar
    display_name.fget.short_description = _("اسم الاستبيان")

    def save(self, *args, **kwargs):
        # If code is empty, you can optionally derive a default from slug
        if not self.code:
            base_name = self.name_ar or self.name_en
            self.code = slugify(base_name, allow_unicode=True).upper()[:50]

        super().save(*args, **kwargs)


class SurveyVersion(models.Model):
    """Represents a specific wave/version of a survey.

    Example: Labor Force Survey March 2025, or \"2025-Q1\" round.
    """

    class Meta:
        verbose_name = _("إصدار الاستبيان")
        verbose_name_plural = _("إصدارات الاستبيان")
        ordering = ["-version_date", "-id"]
        unique_together = ("survey", "version_label")

    class Status(models.TextChoices):
        DRAFT = "DRAFT", _("مسودة")
        ACTIVE = "ACTIVE", _("نشط")
        LOCKED = "LOCKED", _("مقفل")
        ARCHIVED = "ARCHIVED", _("مؤرشف")

    class SurveyInterval(models.TextChoices):
        MONTHLY = "M", _("شهري")
        QUARTERLY = "Q", _("ربع سنوي")
        BIANNUALLY = "B", _("نصف سنوي")
        ANNUALLY = "A", _("سنوي")

    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name="versions",
        verbose_name=_("الاستبيان")
    )

    # Auto-generated to avoid collisions; kept non-editable.
    version_label = models.CharField(
        max_length=50,
        blank=True,
        editable=False,
    )

    version_date = models.DateField(
        default=datetime.date.today,
        verbose_name=_("تاريخ الإصدار"),
        help_text=_("تاريخ الإشارة لهذه النسخة/الموجة."),
    )

    interval = models.CharField(
        max_length=20,
        choices=SurveyInterval.choices,
        verbose_name=_("الفاصل الزمني"),
        help_text=_("تواتر الاستبيان."),
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name=_("الحالة"),
        help_text=_("مسودة: قابلة للتحرير؛ نشطة: قيد الجمع؛ مقفلة: هيكل ثابت؛ مؤرشفة: للاطلاع التاريخي."),
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("تاريخ الإنشاء"))
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.survey.display_name} - {self.version_label or '(new)'}"

    def _generate_version_label(self):
        """Generate a label based on interval and date."""
        if not self.version_date or not self.survey.code:
            return ""

        year = self.version_date.strftime("%y")
        month = self.version_date.strftime("%m")

        return f"{year}{self.survey.code}{self.interval}{month}"

    def save(self, *args, **kwargs):
        generated_label = self._generate_version_label()
        if generated_label:
            if SurveyVersion.objects.filter(
                survey=self.survey,
                version_label=generated_label,
            ).exclude(pk=self.pk).exists():
                raise ValidationError({"version_label": _("Duplicate version label for this survey.")})
            self.version_label = generated_label
        super().save(*args, **kwargs)


class SurveyQuestion(models.Model):
    """Individual question belonging to a specific SurveyVersion.

    This is the canonical question bank for a given wave. Assessment / flows
    live in a different app and reference these questions.
    """

    class Meta:
        verbose_name = _("سؤال الاستبيان")
        verbose_name_plural = _("أسئلة الاستبيان")
        ordering = ["id"]

    survey_version = models.ForeignKey(
        SurveyVersion,
        on_delete=models.CASCADE,
        related_name="questions",
        verbose_name=_("إصدار الاستبيان")
    )

    code = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("الرمز"),
        help_text=_("رمز سؤال اختياري مثل Q1 أو A01."),
    )

    text_ar = models.TextField(
        blank=True,
        verbose_name=_("السؤال [عربية]"),
        help_text=_("النص الكامل للسؤال باللغة العربية."),
    )
    text_en = models.TextField(
        blank=True,
        verbose_name=_("السؤال [إنجليزية]"),
        help_text=_("النص الكامل للسؤال باللغة الإنجليزية."),
    )

    help_text = models.TextField(
        blank=True,
        help_text=_("نص مساعدة اختياري أو تعليمات للمُعِد."),
    )

    is_required = models.BooleanField(
        default=False,
        help_text=_("هل يجب الإجابة على السؤال أثناء جمع البيانات."),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        prefix = f"{self.code} - " if self.code else ""
        text = self.display_text
        short = text[:60] + ("..." if len(text) > 60 else "")
        return f"{prefix}{short}"

    def short_text(self) -> str:
        text = self.display_text
        return text[:150] + ("..." if len(text) > 150 else "")
    short_text.short_description = _("السؤال")

    @property
    def display_text(self) -> str:
        lang = (get_language() or "ar")[:2]
        if lang == "ar" and self.text_ar:
            return self.text_ar
        if lang == "en" and self.text_en:
            return self.text_en
        return self.text_en or self.text_ar