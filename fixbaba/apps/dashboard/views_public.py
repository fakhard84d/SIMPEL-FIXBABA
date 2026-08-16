"""
Public Landing Page Views
"""

from django.shortcuts import render


def public_home(request):
    """Public landing page"""
    context = {
        'page_title': 'FixBaba - تعمیر لوازم خانگی',
    }
    return render(request, 'public/home.html', context)
