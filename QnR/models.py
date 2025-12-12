from django.db import models
from django.utils.translation import gettext_lazy as _


class ResponseType(models.Model):
    """
    Defines a type of response, e.g., 'Single Choice', 'Free Text'.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text=_("نوع الاستجابة (مثل اختيار واحد أو رقمي).")
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("نوع الاستجابة")
        verbose_name_plural = _("أنواع الاستجابة")


class Response(models.Model):
    """
    Represents a single predefined answer/choice.
    """
    text_ar = models.CharField(max_length=255, verbose_name=_("النص بالعربية"))
    text_en = models.CharField(max_length=255, verbose_name=_("النص بالإنجليزية"))

    def __str__(self):
        return f"{self.text_en} / {self.text_ar}"

    class Meta:
        verbose_name = _("إجابة")
        verbose_name_plural = _("إجابات")


class SurveyQuestion(models.Model):
    """
    A single question in a survey.
    """
    text_ar = models.TextField(verbose_name=_("النص بالعربية"))
    text_en = models.TextField(verbose_name=_("النص بالإنجليزية"))
    response_type = models.ForeignKey(
        ResponseType,
        on_delete=models.PROTECT,  # Prevent deleting a type that is in use
        related_name="questions",
    )
    possible_responses = models.ManyToManyField(
        Response,
        blank=True,  # Not all questions have predefined responses (e.g., free text)
        related_name="questions",
        help_text=_("حدد الإجابات المحتملة لأسئلة الاختيار."),
    )

    def __str__(self):
        return self.text_en

    class Meta:
        verbose_name = _("سؤال استبيان")
        verbose_name_plural = _("أسئلة الاستبيان")
