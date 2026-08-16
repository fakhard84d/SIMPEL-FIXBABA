"""
URLs for Authentication app
"""

from django.urls import path
from apps.authentication.views import magic_link_access, revoke_device

app_name = 'authentication'

urlpatterns = [
    path('<str:token>/', magic_link_access, name='magic_link_access'),
    path('revoke-device/', revoke_device, name='revoke_device'),
]
