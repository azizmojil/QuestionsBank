from django.db import models
from django.utils.translation import gettext_lazy as _

from surveys.models import SurveyVersion, SurveyQuestion


class Indicator(models.Model):
    """A statistical indicator defined on top of survey questions.

    Example: Unemployment rate, Internet penetration, etc.
    """

    class Classification(models.TextChoices):
        NATIONAL = "NATIONAL", _("National")
        REGIONAL = "REGIONAL", _("Regional")
        INTERNATIONAL = "INTERNATIONAL", _("International")

    name = models.CharField(
        max_length=255,
        help_text=_("Human-readable name of the indicator."),
    )

    code = models.CharField(
        max_length=50,
        blank=True,
        help_text=_("Optional code, e.g. IND_01 or SDG_8_5_2."),
    )

    classification = models.CharField(
        max_length=20,
        choices=Classification.choices,
        default=Classification.NATIONAL,
        help_text=_("Classification of the indicator."),
    )

    unit = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Unit of measure, e.g. % or 'persons'."),
    )

    frequency = models.CharField(
        max_length=50,
        blank=True,
        help_text=_("Frequency of publication, e.g. monthly, quarterly."),
    )

    methodology_reference = models.URLField(
        blank=True,
        help_text=_("Optional URL to methodology or metadata documentation."),
    )

    notes = models.TextField(
        blank=True,
        help_text=_("Free-form notes or methodological comments."),
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
        TRACKED = "TRACKED", _("Tracked by the authority")
        NOT_TRACKED = "NOT_TRACKED", _("Not tracked by the authority")

    indicator = models.ForeignKey(
        Indicator,
        on_delete=models.CASCADE,
        related_name="items",
    )

    name = models.CharField(
        max_length=255,
        help_text=_("Name of the indicator list item."),
    )

    code = models.CharField(
        max_length=50,
        blank=True,
        help_text=_("Optional code for the list item."),
    )

    tracking_status = models.CharField(
        max_length=20,
        choices=TrackingStatus.choices,
        blank=True,
        null=True,
        help_text=_("Whether this specific item is tracked by the authority."),
    )

    survey_version = models.ForeignKey(
        SurveyVersion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="indicator_list_items",
        help_text=_("Survey version this indicator list item is defined on."),
    )

    survey_question = models.ForeignKey(
        SurveyQuestion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="indicator_list_items",
        help_text=_("Survey question that defines or feeds this indicator list item."),
    )

    class Meta:
        ordering = ["id"]
        unique_together = ("indicator", "name")

    def __str__(self) -> str:
        return f"{self.indicator.name} - {self.name}"
