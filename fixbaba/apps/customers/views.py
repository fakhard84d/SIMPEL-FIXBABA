"""
Customer Portal Views
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings

from apps.customers.models import Customer, CustomerDevice, AuditLog
from apps.service_requests.models import ServiceRequest


def customer_login_required(view_func):
    """Decorator to require customer authentication"""
    def wrapper(request, *args, **kwargs):
        # Check session
        customer_id = request.session.get('customer_id')
        
        if not customer_id:
            # Try cookie-based auth
            device_credential = request.COOKIES.get('fixbaba_device')
            if device_credential:
                customer = CustomerDevice.validate_credential(device_credential)
                if customer:
                    request.session['customer_id'] = customer.id
                    request.user = customer
                    return view_func(request, *args, **kwargs)
            return redirect('error_401')
        
        try:
            customer = Customer.objects.get(id=customer_id, is_active=True)
            request.user = customer
            return view_func(request, *args, **kwargs)
        except Customer.DoesNotExist:
            request.session.flush()
            response = redirect('error_401')
            response.delete_cookie('fixbaba_device')
            return response
    
    return wrapper


@customer_login_required
def portal_dashboard(request):
    """Customer portal dashboard"""
    customer = request.user
    
    # Get recent requests
    recent_requests = ServiceRequest.objects.filter(
        customer=customer
    ).select_related().order_by('-created_at')[:5]
    
    context = {
        'customer': customer,
        'recent_requests': recent_requests,
        'page_title': 'داشبورد',
    }
    
    return render(request, 'portal/dashboard.html', context)


@customer_login_required
def portal_profile(request):
    """Customer profile page"""
    customer = request.user
    
    if request.method == 'POST':
        # Handle profile updates (address, etc.)
        # Note: phone cannot be changed
        pass
    
    context = {
        'customer': customer,
        'page_title': 'پروفایل',
    }
    
    return render(request, 'portal/profile.html', context)


@customer_login_required
@require_http_methods(["POST"])
def logout_all_devices(request):
    """Logout from all devices"""
    customer = request.user
    
    # Revoke all devices
    CustomerDevice.objects.filter(customer=customer).update(
        revoked_at=timezone.now(),
        is_active=False
    )
    
    AuditLog.log('DEVICE_REVOKED', customer=customer, request=request, action='logout_all')
    
    request.session.flush()
    response = redirect('portal_logout')
    response.delete_cookie('fixbaba_device')
    return response


@customer_login_required
def portal_logout(request):
    """Logout customer"""
    request.session.flush()
    response = redirect('public_home')
    response.delete_cookie('fixbaba_device')
    return response
