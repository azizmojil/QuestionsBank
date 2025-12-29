from django.contrib import admin

from .models import IndicatorSource, Indicator
from django.utils.translation import gettext_lazy as _


class IndicatorInline(admin.TabularInline):
    model = Indicator
    extra = 0
    fields = ("name_ar", "name_en", "tracking_status")
    show_change_link = True


@admin.register(IndicatorSource)
class IndicatorSourceAdmin(admin.ModelAdmin):
    list_display = ("name_ar", "name_en", "code", "created_at")
    search_fields = ("name_ar", "name_en", "code")

    fieldsets = (
        (None, {
            "fields": ("name_ar", "name_en", "code"),
        }),
    )
    inlines = [IndicatorInline]


@admin.register(Indicator)
class IndicatorAdmin(admin.ModelAdmin):
    list_display = ("name_ar", "name_en", "indicator_source", "tracking_status")
    list_filter = ("tracking_status", "indicator_source")
    search_fields = ("name_ar", "name_en", "indicator_source__name_ar", "indicator_source__name_en")
    autocomplete_fields = ("indicator_source",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
