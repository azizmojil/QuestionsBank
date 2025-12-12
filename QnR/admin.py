from django.contrib import admin
from .models import SurveyQuestion, ResponseType, Response


@admin.register(ResponseType)
class ResponseTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ("text_en", "text_ar")
    search_fields = ("text_en", "text_ar")


@admin.register(SurveyQuestion)
class SurveyQuestionAdmin(admin.ModelAdmin):
    list_display = ("text_en", "response_type")
    list_filter = ("response_type",)
    search_fields = ("text_en", "text_ar")
    filter_horizontal = ("possible_responses",)  # Use a more user-friendly widget for many-to-many
