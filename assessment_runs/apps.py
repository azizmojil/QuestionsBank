from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AssessmentRunsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'assessment_runs'
    verbose_name = _('عمليات التقييم')
