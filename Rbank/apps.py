from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class RbankConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "Rbank"
    verbose_name = _("بنك الإجابات")
