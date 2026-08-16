"""
Public URLs (Landing Page)
"""

from django.urls import path
from .views_public import public_home

urlpatterns = [
    path('', public_home, name='public_home'),
]
