"""Dashboard app init"""
from django.apps import AppConfig


class DashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.dashboard'
    verbose_name = 'داشبورد و صفحات عمومی'


# Keep backward compatibility
default_app_config = 'apps.dashboard.DashboardConfig'

from .views_public import public_home
from .views_errors import error_404, error_500, error_403, error_401
