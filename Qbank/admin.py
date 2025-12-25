from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Questions, MatrixItem, MatrixItemGroup


class ResponseGroupInline(admin.TabularInline):
    model = Questions.response_groups.through
    verbose_name = _("مجموعة الإجابات")
    verbose_name_plural = _("مجموعات الإجابات")
    extra = 0


@admin.register(Questions)
class SurveyQuestionAdmin(admin.ModelAdmin):
    list_display = ("display_text",)
    search_fields = ("text_en", "text_ar")
    inlines = [ResponseGroupInline]
    exclude = ("response_groups",)

    def display_text(self, obj):
        return obj.display_text

    display_text.short_description = _("السؤال")


@admin.register(MatrixItem)
class MatrixItemAdmin(admin.ModelAdmin):
    list_display = ("display_text",)
    search_fields = ("text_ar", "text_en")

    def display_text(self, obj):
        return obj.display_text

    display_text.short_description = _("النص")


class MatrixItemInline(admin.TabularInline):
    model = MatrixItemGroup.items.through
    verbose_name = _("عنصر مصفوفة")
    verbose_name_plural = _("عناصر المصفوفة")
    extra = 0


@admin.register(MatrixItemGroup)
class MatrixItemGroupAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    inlines = [MatrixItemInline]
    exclude = ("items",)
