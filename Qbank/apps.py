from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class QbankConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Qbank'
    verbose_name = _('بنك الأسئلة')
