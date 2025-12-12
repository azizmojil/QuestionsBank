from django.contrib import admin

from .models import AssessmentRun, AssessmentResult, AssessmentFile


@admin.register(AssessmentRun)
class AssessmentRunAdmin(admin.ModelAdmin):
    list_display = ("survey_version", "label", "status", "assigned_to", "created_at")
    list_filter = ("status", "survey_version__survey")
    search_fields = ("label", "survey_version__survey__name")


@admin.register(AssessmentResult)
class AssessmentResultAdmin(admin.ModelAdmin):
    list_display = ("assessment_run", "survey_question", "status", "assessed_by")
    list_filter = ("status", "assessment_run__survey_version__survey")
    search_fields = ("survey_question__text", "assessment_run__label")


@admin.register(AssessmentFile)
class AssessmentFileAdmin(admin.ModelAdmin):
    list_display = ("original_filename", "assessment_result", "uploaded_by", "uploaded_at")
    search_fields = ("original_filename", "description")
    readonly_fields = ("assessment_result", "triggering_option", "file", "original_filename", "description", "uploaded_by", "uploaded_at", "metadata")

    def has_add_permission(self, request):
        return False
