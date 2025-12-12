from django.contrib import admin
from django.db import models
from django.urls import reverse
from django.utils.html import format_html

from .models import Survey, SurveyVersion, SurveyQuestion


class SurveyVersionInline(admin.TabularInline):
    model = SurveyVersion
    extra = 0
    show_change_link = False
    fields = ("interval", "version_date", "version_label_link", "status", "created_at")
    readonly_fields = ("version_label_link", "created_at")

    def version_label_link(self, obj):
        if obj.pk:
            url = reverse("admin:surveys_surveyversion_change", args=[obj.pk])
            return format_html('<a href="{}">{}</a>', url, obj.version_label)
        return "(Not saved yet)"

    version_label_link.short_description = "Version Label"


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ("display_name", "code", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("name", "name_ar", "name_en", "code", "description")
    prepopulated_fields = {"slug": ("name",)}

    fieldsets = (
        (None, {
            "fields": ("name", "name_ar", "name_en", "code", "slug", "description", "status"),
        }),
    )

    readonly_fields = ("created_at", "updated_at")
    inlines = [SurveyVersionInline]


class SurveyQuestionInline(admin.TabularInline):
    model = SurveyQuestion
    extra = 0
    show_change_link = True
    fields = (
        "text",
        "text_ar",
        "text_en",
        "section_label",
        "code",
    )
    # Make 'text' a textarea
    formfield_overrides = {
        models.TextField: {'widget': admin.widgets.AdminTextareaWidget(attrs={'rows': 1})},
    }


@admin.register(SurveyVersion)
class SurveyVersionAdmin(admin.ModelAdmin):
    inlines = [SurveyQuestionInline]

    def get_fieldsets(self, request, obj=None):
        # Return empty fieldsets to hide all fields
        return []

    def has_add_permission(self, request):
        return False
