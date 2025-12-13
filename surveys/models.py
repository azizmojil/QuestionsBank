from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
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

    class Status(models.TextChoices):
        DRAFT = "DRAFT", _("مسودة")
        ACTIVE = "ACTIVE", _("نشط")
        ARCHIVED = "ARCHIVED", _("مؤرشف")

    name_ar = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("اسم المسح [عربية]"),
    )
    name_en = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("اسم المسح [انجليزية]"),
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        verbose_name=_("الرمز"),
    )
    description = models.TextField(blank=True, verbose_name=_("الوصف"))

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name=_("الحالة"),
        help_text=_("مسودة: قيد التصميم. نشط: قيد الاستخدام. مؤرشف: لم يعد مستخدماً."),
    )

    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_surveys",
        verbose_name=_("المالك"),
        help_text=_("المسؤول الأساسي عن هذا الاستبيان."),
    )

    editors = models.ManyToManyField(
        User,
        blank=True,
        related_name="editable_surveys",
        verbose_name=_("المحررون"),
        help_text=_("المستخدمون المسموح لهم بتعديل هيكل الاستبيان."),
    )

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

    version_label = models.CharField(
        max_length=50,
        blank=True,
        help_text=_("تسمية ودية مثل '2025-03' أو 'الجولة 1-2025'."),
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

    metadata = models.JSONField(
        blank=True,
        default=dict,
        help_text=_("بيانات وصفية اختيارية مثل معلومات إطار العينة أو الملاحظات."),
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
        self.version_label = self._generate_version_label()
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

    class ResponseType(models.TextChoices):
        BINARY = "BINARY", _("نعم/لا (ثنائي)")
        SINGLE_CHOICE = "SINGLE_CHOICE", _("اختيار واحد")
        MULTIPLE_CHOICE = "MULTIPLE_CHOICE", _("اختيارات متعددة")
        FREE_TEXT = "FREE_TEXT", _("نص حر")
        NUMERIC = "NUMERIC", _("رقمي")
        DATE = "DATE", _("تاريخ")
        DATETIME = "DATETIME", _("تاريخ ووقت")
        SCALE = "SCALE", _("مقياس (مثلاً 1–5)")
        MATRIX = "MATRIX", _("مصفوفة")

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

    section_label = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("مسمى القسم"),
        help_text=_("تسمية قسم منطقية للتقارير فقط."),
    )

    response_type = models.CharField(
        max_length=30,
        choices=ResponseType.choices,
        default=ResponseType.FREE_TEXT,
        help_text=_("النوع الأساسي المتوقع للإجابة؛ يمكن أن تعيش الترميزات أو التحقق التفصيلي في مكان آخر."),
    )

    is_required = models.BooleanField(
        default=False,
        help_text=_("هل يجب الإجابة على السؤال أثناء جمع البيانات."),
    )

    metadata = models.JSONField(
        blank=True,
        default=dict,
        help_text=_("بنية إضافية اختيارية (القيم المسموحة، النطاقات، شروط التخطي، إلخ)."),
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
