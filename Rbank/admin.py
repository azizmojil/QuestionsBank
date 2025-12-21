from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import ResponseType, Response, ResponseGroup


@admin.register(ResponseType)
class ResponseTypeAdmin(admin.ModelAdmin):
    list_display = ("display_name", "id")
    search_fields = ("name_ar", "name_en")

    def display_name(self, obj):
        return str(obj)

    display_name.short_description = _("نوع الاستجابة")


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ("display_text", "id")
    search_fields = ("text_en", "text_ar")

    def display_text(self, obj):
        return obj.display_text

    display_text.short_description = _("الجواب")


class ResponseInline(admin.TabularInline):
    model = ResponseGroup.responses.through
    verbose_name = _("إجابة")
    verbose_name_plural = _("الإجابات")
    extra = 1


@admin.register(ResponseGroup)
class ResponseGroupAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    inlines = [ResponseInline]
    exclude = ("responses",)
