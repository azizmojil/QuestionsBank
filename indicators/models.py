from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.translation import get_language

from surveys.models import SurveyVersion, SurveyQuestion


class Indicator(models.Model):
    """A statistical indicator defined on top of survey questions.

    Example: Unemployment rate, Internet penetration, etc.
    """

    class Meta:
        verbose_name = _("المؤشر")
        verbose_name_plural = _("المؤشرات")
        ordering = ["-created_at"]

    name_ar = models.CharField(
        max_length=255,
        verbose_name=_("الاسم [عربية]"),
    )
    name_en = models.CharField(
        max_length=255,
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


class Classification(models.Model):
    name_ar = models.CharField(max_length=100, unique=True, verbose_name=_("الاسم [عربية]"))
    name_en = models.CharField(max_length=100, unique=True, verbose_name=_("الاسم [إنجليزية]"))

    def __str__(self):
        lang = get_language()
        return self.name_en if lang == 'en' else self.name_ar

    class Meta:
        verbose_name = _("تصنيف")
        verbose_name_plural = _("التصنيفات")


class ClassificationIndicatorListItem(models.Model):
    classification = models.ForeignKey(Classification, on_delete=models.CASCADE)
    indicatorlistitem = models.ForeignKey("IndicatorListItem", on_delete=models.CASCADE, verbose_name=_("اسم المؤشر"))

    class Meta:
        verbose_name = _("عنصر قائمة مؤشر التصنيف")
        verbose_name_plural = _("عناصر قائمة مؤشر التصنيف")


class IndicatorClassification(models.Model):
    indicator = models.ForeignKey(
        Indicator,
        on_delete=models.CASCADE,
        related_name="classifications",
        verbose_name=_("المؤشر"),
    )
    classification = models.ForeignKey(
        Classification,
        on_delete=models.CASCADE,
        verbose_name=_("التصنيف"),
    )

    class Meta:
        verbose_name = _("تصنيف المؤشر")
        verbose_name_plural = _("تصنيفات المؤشر")
        unique_together = ("indicator", "classification")


class IndicatorTracking(models.Model):
    class TrackingStatus(models.TextChoices):
        TRACKED = "TRACKED", _("متابع")
        NOT_TRACKED = "NOT_TRACKED", _("غير متابع")

    indicator_list_item = models.ForeignKey(
        "IndicatorListItem",
        on_delete=models.CASCADE,
        related_name="tracking_info",
        verbose_name=_("عنصر قائمة المؤشر"),
    )
    status = models.CharField(
        max_length=20,
        choices=TrackingStatus.choices,
        verbose_name=_("الحالة"),
    )

    class Meta:
        verbose_name = _("تتبع المؤشر")
        verbose_name_plural = _("معلومات تتبع المؤشر")


class IndicatorListItem(models.Model):
    """Individual item within an Indicator, representing a specific survey question or data point."""

    class Meta:
        verbose_name = _("اسم المؤشر")
        verbose_name_plural = _("أسماء المؤشرات")
        ordering = ["id"]
        unique_together = ("indicator", "name")

    indicator = models.ForeignKey(
        Indicator,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("المؤشر"),
    )

    name = models.CharField(
        max_length=255,
        verbose_name=_("الاسم"),
        help_text=_("اسم عنصر قائمة المؤشر."),
    )

    code = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("الرمز"),
        help_text=_("رمز اختياري لعنصر القائمة."),
    )

    def __str__(self) -> str:
        return f"{self.indicator} - {self.name}"
