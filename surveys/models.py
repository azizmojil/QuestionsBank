from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
import datetime

User = get_user_model()


class Survey(models.Model):
    """Top-level survey definition.

    Represents a logical survey instrument (e.g. \"Labor Force Survey\").
    Specific versions / waves are handled by SurveyVersion.
    """

    class Status(models.TextChoices):
        DRAFT = "DRAFT", _("مسودة")
        ACTIVE = "ACTIVE", _("نشط")
        ARCHIVED = "ARCHIVED", _("مؤرشف")

    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        help_text=_("رمز قصير اختياري مثل LFS_2025."),
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
        help_text=_("يُنشأ تلقائياً من الاسم إذا تُرك فارغاً."),
    )
    description = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        help_text=_("مسودة: قيد التصميم. نشط: قيد الاستخدام. مؤرشف: لم يعد مستخدماً."),
    )

    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_surveys",
        help_text=_("المسؤول الأساسي عن هذا الاستبيان."),
    )

    editors = models.ManyToManyField(
        User,
        blank=True,
        related_name="editable_surveys",
        help_text=_("المستخدمون المسموح لهم بتعديل هيكل الاستبيان."),
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
    )

    version_label = models.CharField(
        max_length=50,
        blank=True,
        help_text=_("تسمية ودية مثل '2025-03' أو 'الجولة 1-2025'."),
    )

    version_date = models.DateField(
        default=datetime.date.today,
        help_text=_("تاريخ الإشارة لهذه النسخة/الموجة."),
    )

    interval = models.CharField(
        max_length=20,
        choices=SurveyInterval.choices,
        help_text=_("تواتر الاستبيان."),
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        help_text=_("مسودة: قابلة للتحرير؛ نشطة: قيد الجمع؛ مقفلة: هيكل ثابت؛ مؤرشفة: للاطلاع التاريخي."),
    )

    metadata = models.JSONField(
        blank=True,
        default=dict,
        help_text=_("بيانات وصفية اختيارية مثل معلومات إطار العينة أو الملاحظات."),
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
    )

    code = models.CharField(
        max_length=50,
        blank=True,
        help_text=_("رمز سؤال اختياري مثل Q1 أو A01."),
    )

    text = models.TextField(help_text=_("النص الكامل للسؤال كما يراه المجيب."))

    help_text = models.TextField(
        blank=True,
        help_text=_("نص مساعدة اختياري أو تعليمات للمُعِد."),
    )

    section_label = models.CharField(
        max_length=255,
        blank=True,
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

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        prefix = f"{self.code} - " if self.code else ""
        short = self.text[:60] + ("..." if len(self.text) > 60 else "")
        return f"{prefix}{short}"

    def short_text(self) -> str:
        return self.text[:150] + ("..." if len(self.text) > 150 else "")

    short_text.short_description = "Question Text"
