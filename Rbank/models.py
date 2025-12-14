from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.translation import get_language


class ResponseType(models.Model):
    """
    Defines a type of response, e.g., 'Single Choice', 'Free Text'.
    """
    name_ar = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("نوع الاستجابة [عربية]"),
    )
    name_en = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("نوع الاستجابة [إنجليزية]"),
    )

    def __str__(self):
        lang = get_language()
        if lang == 'ar':
            return self.name_ar
        return self.name_en

    class Meta:
        verbose_name = _("نوع الاستجابة")
        verbose_name_plural = _("أنواع الاستجابة")


class Response(models.Model):
    """
    Represents a single predefined answer/choice.
    """
    text_ar = models.CharField(max_length=255, verbose_name=_("الجواب [عربية]"))
    text_en = models.CharField(max_length=255, verbose_name=_("الجواب [إنجليزية]"))

    def __str__(self):
        return self.display_text

    @property
    def display_text(self):
        lang = get_language()
        if lang == 'ar':
            return self.text_ar
        return self.text_en

    class Meta:
        verbose_name = _("إجابة")
        verbose_name_plural = _("إجابات")


class ResponseGroup(models.Model):
    name = models.CharField(max_length=255, verbose_name=_("اسم المجموعة"))
    responses = models.ManyToManyField(Response, verbose_name=_("الإجابات"))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("مجموعة إجابات")
        verbose_name_plural = _("مجموعات الإجابات")
