from django.contrib import admin

from .models import Indicator, IndicatorListItem


class IndicatorListItemInline(admin.TabularInline):
    model = IndicatorListItem
    extra = 1
    fields = ("name", "code", "tracking_status")


@admin.register(Indicator)
class IndicatorAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "classification", "created_at")
    list_filter = ("classification",)
    search_fields = ("name", "code")

    fieldsets = (
        (None, {
            "fields": ("name", "code", "classification"),
        }),
    )

    inlines = [IndicatorListItemInline]
