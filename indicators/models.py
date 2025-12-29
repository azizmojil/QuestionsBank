from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.translation import get_language

from surveys.models import SurveyVersion, SurveyQuestion


class IndicatorSource(models.Model):
    """A statistical indicator defined on top of survey questions.

    Example: Unemployment rate, Internet penetration, etc.
    """

    class Meta:
        verbose_name = _("مصدر المؤشر")
        verbose_name_plural = _("مصادر المؤشرات")
        ordering = ["code"]

    name_ar = models.CharField(
        max_length=255,
        unique=True,
        verbose_name=_("الاسم [عربية]"),
    )
    name_en = models.CharField(
        max_length=255,
        unique=True,
        verbose_name=_("الاسم [إنجليزية]"),
    )

    code = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("الرمز"),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        lang = get_language()
        name = self.name_en if lang == 'en' else self.name_ar
        if self.code:
            return f"{self.code} - {name}"
        return name


class Indicator(models.Model):
    """Individual item within an IndicatorSource, representing a specific indicator."""

    class TrackingStatus(models.TextChoices):
        TRACKED = "TRACKED", _("متابع")
        NOT_TRACKED = "NOT_TRACKED", _("غير متابع")

    class Meta:
        verbose_name = _("المؤشر")
        verbose_name_plural = _("المؤشرات")
        ordering = ["id"]
        unique_together = ("indicator_source", "name_ar")

    indicator_source = models.ForeignKey(
        IndicatorSource,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("مصدر المؤشر"),
    )

    name_ar = models.CharField(
        max_length=255,
        verbose_name=_("المؤشر [عربية]"),
    )

    name_en = models.CharField(
        max_length=255,
        verbose_name=_("المؤشر [إنجليزية]"),
        blank=True,
    )

    tracking_status = models.CharField(
        max_length=20,
        choices=TrackingStatus.choices,
        default=TrackingStatus.NOT_TRACKED,
        verbose_name=_("حالة التتبع"),
    )

    def __str__(self) -> str:
        lang = get_language()
        name = self.name_en if lang == 'en' and self.name_en else self.name_ar
        return f"{self.indicator_source} - {name}"
