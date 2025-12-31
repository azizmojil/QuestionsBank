from django.contrib import admin
from django.db import models
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import Survey, SurveyVersion, SurveyQuestion


class SurveyVersionInline(admin.TabularInline):
    model = SurveyVersion
    verbose_name = _("إصدار الاستبيان")
    verbose_name_plural = _("إصدارات الاستبيان")
    extra = 0
    show_change_link = False
    fields = ("interval", "version_date", "version_label_link", "created_at")
    readonly_fields = ("version_label_link", "created_at")

    def version_label_link(self, obj):
        if obj.pk:
            url = reverse("admin:surveys_surveyversion_change", args=[obj.pk])
            return format_html('<a href="{}">{}</a>', url, obj.version_label)
        return _("(لم يتم الحفظ بعد)")

    version_label_link.short_description = _("رمز الإصدار")


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ("display_name", "last_version_created_at")
    search_fields = ("name_ar", "name_en", "code", "description")

    fieldsets = (
        (None, {
            "fields": ("name_ar", "name_en", "code", "description"),
        }),
    )

    readonly_fields = ("created_at", "updated_at")
    inlines = [SurveyVersionInline]

    def last_version_created_at(self, obj):
        last_version = obj.versions.order_by('-created_at').first()
        return last_version.created_at if last_version else None
    last_version_created_at.short_description = _("تاريخ إنشاء آخر إصدار")


class SurveyQuestionInline(admin.TabularInline):
    model = SurveyQuestion
    extra = 0
    show_change_link = True
    fields = (
        "text_ar",
        "text_en",
        "code",
    )
    readonly_fields = ("text_ar", "text_en", "code")
    
    # Make 'text' a textarea
    formfield_overrides = {
        models.TextField: {'widget': admin.widgets.AdminTextareaWidget(attrs={'rows': 1})},
    }

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return True


@admin.register(SurveyVersion)
class SurveyVersionAdmin(admin.ModelAdmin):
    search_fields = ("version_label", "survey__name_ar", "survey__name_en")
    list_display = (
        "__str__", 
        "survey", 
        "initial_questionnaire_built",
        "self_assessment_done",
        "routing_logic_done",
        "business_logic_done",
        "lang_review_status",
        "translation_status"
    )
    inlines = [SurveyQuestionInline]

    def has_add_permission(self, request):
        return False

    def get_fieldsets(self, request, obj=None):
        return []


@admin.register(SurveyQuestion)
class SurveyQuestionAdmin(admin.ModelAdmin):
    search_fields = ("text_ar", "text_en", "code")
    list_display = ("short_text", "survey_version", "code")
    autocomplete_fields = ("survey_version",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def get_fieldsets(self, request, obj=None):
        return []
