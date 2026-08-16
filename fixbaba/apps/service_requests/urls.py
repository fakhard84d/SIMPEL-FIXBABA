"""
URLs for Service Requests
"""

from django.urls import path
from apps.service_requests.views import (
    request_list,
    request_detail,
    request_create,
    request_delete_image,
)

app_name = 'service_requests'

urlpatterns = [
    path('', request_list, name='request_list'),
    path('new/', request_create, name='request_create'),
    path('<int:request_id>/', request_detail, name='request_detail'),
    path('images/<int:image_id>/delete/', request_delete_image, name='request_delete_image'),
]
