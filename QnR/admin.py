from django.contrib import admin
from .models import SurveyQuestion, ResponseType, Response, ResponseGroup
from django.utils.translation import gettext_lazy as _


@admin.register(ResponseType)
class ResponseTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ("text_en", "text_ar")
    search_fields = ("text_en", "text_ar")


class ResponseInline(admin.TabularInline):
    model = ResponseGroup.responses.through
    verbose_name = _("إجابة")
    verbose_name_plural = _("الإجابات")
    extra = 1


@admin.register(ResponseGroup)
class ResponseGroupAdmin(admin.ModelAdmin):
    inlines = [ResponseInline]
    exclude = ("responses",)


@admin.register(SurveyQuestion)
class SurveyQuestionAdmin(admin.ModelAdmin):
    list_display = ("text_en", "response_type")
    list_filter = ("response_type",)
    search_fields = ("text_en", "text_ar")
    filter_horizontal = ("possible_responses",)  # Use a more user-friendly widget for many-to-many
