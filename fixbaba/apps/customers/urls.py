"""
URLs for Customer Portal
"""

from django.urls import path
from apps.customers.views import (
    portal_dashboard,
    portal_profile,
    portal_logout,
    logout_all_devices,
)

app_name = 'customers'

urlpatterns = [
    path('', portal_dashboard, name='portal_dashboard'),
    path('profile/', portal_profile, name='portal_profile'),
    path('logout/', portal_logout, name='portal_logout'),
    path('logout-all/', logout_all_devices, name='logout_all_devices'),
]
