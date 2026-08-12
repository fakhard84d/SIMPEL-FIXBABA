"""
URL Configuration for FixBaba
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    # Custom Admin (secure)
    path(f'{settings.ADMIN_URL_PREFIX}/', admin.site.urls),
    
    # Public pages
    path('', include('apps.dashboard.urls_public')),
    
    # Authentication (Magic Link)
    path('access/', include('apps.authentication.urls')),
    
    # Customer Portal
    path('portal/', include('apps.customers.urls')),
    
    # Service Requests
    path('portal/requests/', include('apps.service_requests.urls')),
    
    # Error pages
    path('401/', TemplateView.as_view(template_name='errors/401.html'), name='error_401'),
    path('403/', TemplateView.as_view(template_name='errors/403.html'), name='error_403'),
    path('404/', TemplateView.as_view(template_name='errors/404.html'), name='error_404'),
    path('429/', TemplateView.as_view(template_name='errors/429.html'), name='error_429'),
    path('500/', TemplateView.as_view(template_name='errors/500.html'), name='error_500'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom error handlers
handler404 = 'apps.dashboard.views.error_404'
handler500 = 'apps.dashboard.views.error_500'
handler403 = 'apps.dashboard.views.error_403'
handler401 = 'apps.dashboard.views.error_401'
