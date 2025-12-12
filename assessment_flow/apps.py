from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AssessmentFlowConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "assessment_flow"
    verbose_name = _("مسار التقييم")
