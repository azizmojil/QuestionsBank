from django.db import models
from django.utils.translation import gettext_lazy as _

from surveys.models import SurveyVersion, SurveyQuestion


class Indicator(models.Model):
    """A statistical indicator defined on top of survey questions.

    Example: Unemployment rate, Internet penetration, etc.
    """

    class Classification(models.TextChoices):
        NATIONAL = "NATIONAL", _("وطني")
        REGIONAL = "REGIONAL", _("إقليمي")
        INTERNATIONAL = "INTERNATIONAL", _("دولي")

    name = models.CharField(
        max_length=255,
        help_text=_("اسم المؤشر المقروء."),
    )

    code = models.CharField(
        max_length=50,
        blank=True,
        help_text=_("رمز اختياري مثل IND_01 أو SDG_8_5_2."),
    )

    classification = models.CharField(
        max_length=20,
        choices=Classification.choices,
        default=Classification.NATIONAL,
        help_text=_("تصنيف المؤشر."),
    )

    unit = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("وحدة القياس مثل % أو 'أشخاص'."),
    )

    frequency = models.CharField(
        max_length=50,
        blank=True,
        help_text=_("تواتر النشر مثل شهري أو ربع سنوي."),
    )

    methodology_reference = models.URLField(
        blank=True,
        help_text=_("رابط اختياري لمنهجية أو وثائق بيانات."),
    )

    notes = models.TextField(
        blank=True,
        help_text=_("ملاحظات حرة أو تعليقات منهجية."),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        base = self.name
        if self.code:
            base = f"{self.code} - {base}"
        return base


class IndicatorListItem(models.Model):
    """Individual item within an Indicator, representing a specific survey question or data point."""

    class TrackingStatus(models.TextChoices):
        TRACKED = "TRACKED", _("متابع من الجهة المختصة")
        NOT_TRACKED = "NOT_TRACKED", _("غير متابع من الجهة المختصة")

    indicator = models.ForeignKey(
        Indicator,
        on_delete=models.CASCADE,
        related_name="items",
    )

    name = models.CharField(
        max_length=255,
        help_text=_("اسم عنصر قائمة المؤشر."),
    )

    code = models.CharField(
        max_length=50,
        blank=True,
        help_text=_("رمز اختياري لعنصر القائمة."),
    )

    tracking_status = models.CharField(
        max_length=20,
        choices=TrackingStatus.choices,
        blank=True,
        null=True,
        help_text=_("ما إذا كان هذا العنصر متابعاً من الجهة المختصة."),
    )

    survey_version = models.ForeignKey(
        SurveyVersion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="indicator_list_items",
        help_text=_("نسخة الاستبيان التي يُعرَّف عليها هذا العنصر."),
    )

    survey_question = models.ForeignKey(
        SurveyQuestion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="indicator_list_items",
        help_text=_("سؤال الاستبيان الذي يعرّف أو يرفد هذا العنصر."),
    )

    class Meta:
        ordering = ["id"]
        unique_together = ("indicator", "name")

    def __str__(self) -> str:
        return f"{self.indicator.name} - {self.name}"
