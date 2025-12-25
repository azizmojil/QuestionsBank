from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import AssessmentRun, AssessmentResult, AssessmentFile, QuestionClassificationRule

class AssessmentFileInline(admin.TabularInline):
    model = AssessmentFile
    extra = 0
    readonly_fields = ("uploaded_by", "uploaded_at")

class AssessmentResultInline(admin.TabularInline):
    model = AssessmentResult
    extra = 0
    fields = ("survey_question", "results", "get_uploads", "assessed_by", "assessed_at", "classification")
    readonly_fields = ("survey_question", "results", "get_uploads", "assessed_by", "assessed_at", "classification")
    can_delete = True

    def get_uploads(self, obj):
        files = obj.files.all()
        if not files:
            return "-"
        return ", ".join([str(f) for f in files])
    get_uploads.short_description = _("الملفات المرفقة")

@admin.register(AssessmentRun)
class AssessmentRunAdmin(admin.ModelAdmin):
    list_display = ("survey_version", "created_at", "updated_at")
    search_fields = ("survey_version__version_label", "survey_version__survey__name_ar", "survey_version__survey__name_en")
    inlines = [AssessmentResultInline]

@admin.register(QuestionClassificationRule)
class QuestionClassificationRuleAdmin(admin.ModelAdmin):
    list_display = ("survey_question", "classification", "priority", "is_active")
    list_filter = ("is_active", "classification")
    search_fields = ("survey_question__text_ar", "survey_question__text_en", "classification")
