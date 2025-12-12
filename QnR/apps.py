from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class QnrConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'QnR'
    verbose_name = _('بنك الأسئلة')
