from django.urls import path
from . import views

app_name = 'services'

urlpatterns = [
    path('', views.home, name='home'),
    path('service/<uuid:token>/', views.customer_portal, name='customer_portal'),
    path('service/<uuid:token>/submit/', views.submit_service_request, name='submit_request'),
]
