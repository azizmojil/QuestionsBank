from django.db import models
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _

from Rbank.models import ResponseGroup


class Questions(models.Model):
    """
    A single question in a survey.
    """
    text_ar = models.TextField(verbose_name=_("السؤال [عربية]"))
    text_en = models.TextField(verbose_name=_("السؤال [إنجليزية]"))
    response_groups = models.ManyToManyField(
        ResponseGroup,
        related_name="questions",
        verbose_name=_("مجموعات الإجابات"),
    )

    def __str__(self):
        return self.display_text

    @property
    def display_text(self):
        lang = get_language()
        if lang == 'ar':
            return self.text_ar
        return self.text_en

    class Meta:
        verbose_name = _("سؤال")
        verbose_name_plural = _("الأسئلة")


class MatrixItem(models.Model):
    """An item to be used as a row or column in a matrix question."""
    text_ar = models.CharField(max_length=255, verbose_name=_("العنصر [عربية]"))
    text_en = models.CharField(max_length=255, verbose_name=_("العنصر [إنجليزية]"))

    def __str__(self):
        return self.display_text

    @property
    def display_text(self):
        lang = get_language()
        if lang == 'ar' and self.text_ar:
            return self.text_ar
        return self.text_en

    class Meta:
        verbose_name = _("عنصر مصفوفة")
        verbose_name_plural = _("عناصر المصفوفة")


class MatrixItemGroup(models.Model):
    """A group of matrix items, can be used for rows or columns."""
    name = models.CharField(max_length=255, verbose_name=_("اسم المجموعة"))
    items = models.ManyToManyField(MatrixItem, verbose_name=_("العناصر"))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("مجموعة عناصر مصفوفة")
        verbose_name_plural = _("مجموعات عناصر المصفوفة")
