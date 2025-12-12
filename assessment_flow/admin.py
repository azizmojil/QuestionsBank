from django.contrib import admin
from django.db import models
from django.urls import reverse
from django.utils.html import format_html

from .models import AssessmentQuestion, AssessmentOption, AssessmentFlowRule


# ---------------------------------------------------------------------------
# Admin for Flow Questions & Options
# ---------------------------------------------------------------------------


class StaticOptionsInline(admin.TabularInline):
    model = AssessmentOption
    extra = 0
    fields = ("text", "text_ar", "text_en", "response_type", "explanation", "explanation_ar", "explanation_en")
    verbose_name = "Static Option"
    verbose_name_plural = "Static Options"
    formfield_overrides = {
        models.TextField: {'widget': admin.widgets.AdminTextareaWidget(attrs={'rows': 1})},
    }


class AssessmentFlowRuleInline(admin.TabularInline):
    model = AssessmentFlowRule
    extra = 0
    fk_name = "from_question"
    fields = ("condition",)
    verbose_name = "Routing Rule"
    verbose_name_plural = "Routing Logic"


@admin.register(AssessmentQuestion)
class AssessmentQuestionAdmin(admin.ModelAdmin):
    list_display = ("display_text", "id", "option_type")
    list_filter = ("option_type",)
    search_fields = ("text", "text_ar", "text_en", "id")

    # Define all possible inlines
    inlines = [StaticOptionsInline, AssessmentFlowRuleInline]

    def get_fieldsets(self, request, obj=None):
        base_fields = ("text", "text_ar", "text_en", "explanation", "explanation_ar", "explanation_en", "option_type", "allow_multiple_choices", "use_searchable_dropdown")
        
        fieldsets = [
            ("Question Details", {"fields": base_fields}),
        ]

        if obj:
            if obj.option_type == AssessmentQuestion.OptionType.DYNAMIC_FROM_PREVIOUS_MULTI_SELECT:
                fieldsets.append(
                    ("Dynamic Source", {
                        "fields": ("dynamic_option_source_question",),
                        "description": "Select the question from which to source the options.",
                    })
                )
            elif obj.option_type == AssessmentQuestion.OptionType.INDICATOR_LIST:
                fieldsets.append(
                    ("Indicator Source", {
                        "fields": ("indicator_source",),
                        "description": "Select the indicator from which to source the options.",
                    })
                )

        return fieldsets

    def get_inline_instances(self, request, obj=None):
        inlines = []
        
        # Always show routing logic
        inlines.append(AssessmentFlowRuleInline(self.model, self.admin_site))

        # Conditionally show static options
        if obj and obj.option_type == AssessmentQuestion.OptionType.STATIC:
            inlines.insert(0, StaticOptionsInline(self.model, self.admin_site))

        return inlines

    # Ensure autocomplete works for the dynamically added field
    autocomplete_fields = ("dynamic_option_source_question", "indicator_source")


@admin.register(AssessmentOption)
class AssessmentOptionAdmin(admin.ModelAdmin):
    search_fields = ("text", "text_ar", "text_en", "question__text", "question__text_ar", "question__text_en")
    def get_model_perms(self, request):
        return {}
