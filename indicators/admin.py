from django.contrib import admin

from .models import Indicator, IndicatorListItem, IndicatorClassification, IndicatorTracking, Classification, \
    ClassificationIndicatorListItem
from django.utils.translation import gettext_lazy as _


class IndicatorListItemInline(admin.TabularInline):
    model = ClassificationIndicatorListItem
    extra = 0
    autocomplete_fields = ("indicatorlistitem",)


@admin.register(Indicator)
class IndicatorAdmin(admin.ModelAdmin):
    list_display = ("name_ar", "name_en", "code", "created_at")
    search_fields = ("name_ar", "name_en", "code")

    fieldsets = (
        (None, {
            "fields": ("name_ar", "name_en", "code"),
        }),
    )


@admin.register(Classification)
class ClassificationAdmin(admin.ModelAdmin):
    list_display = ("name_ar", "name_en")
    search_fields = ("name_ar", "name_en")
    inlines = [IndicatorListItemInline]
    exclude = ("items",)


@admin.register(IndicatorTracking)
class IndicatorTrackingAdmin(admin.ModelAdmin):
    list_display = ("indicator_list_item", "status")
    list_filter = ("status",)
    search_fields = ("indicator_list_item__name",)
    autocomplete_fields = ("indicator_list_item",)


@admin.register(IndicatorListItem)
class IndicatorListItemAdmin(admin.ModelAdmin):
    list_display = ("name", "indicator", "code")
    search_fields = ("name", "indicator__name_ar", "indicator__name_en", "code")
    autocomplete_fields = ("indicator",)
    readonly_fields = ("indicator", "name")
