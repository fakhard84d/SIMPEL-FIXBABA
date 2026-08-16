from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.utils import timezone
from .models import Customer, ServiceRequest
from .forms import ServiceRequestForm


def customer_portal(request, token):
    """پنل اختصاصی مشتری با توکن یک بار مصرف"""
    customer = get_object_or_404(Customer, access_token=token)
    
    # بررسی اعتبار توکن (یک بار مصرف)
    if not customer.is_token_valid():
        return render(request, 'services/token_expired.html', {'customer': customer})
    
    # دریافت درخواست‌های ثبت شده توسط این مشتری
    service_requests = ServiceRequest.objects.filter(customer=customer).order_by('-request_date')
    
    context = {
        'customer': customer,
        'service_requests': service_requests,
    }
    
    return render(request, 'services/customer_portal.html', context)


@require_http_methods(["GET", "POST"])
def submit_service_request(request, token):
    """ثبت درخواست جدید خدمات"""
    customer = get_object_or_404(Customer, access_token=token)
    
    # بررسی اعتبار توکن
    if not customer.is_token_valid():
        return render(request, 'services/token_expired.html', {'customer': customer})
    
    if request.method == 'POST':
        form = ServiceRequestForm(request.POST)
        if form.is_valid():
            service_request = form.save(commit=False)
            service_request.customer = customer
            service_request.save()
            
            # استفاده از توکن بعد از ثبت اولین درخواست
            customer.use_token()
            
            messages.success(request, 'درخواست شما با موفقیت ثبت شد. کد پیگیری: {}'.format(service_request.id))
            return redirect('customer_portal', token=token)
    else:
        form = ServiceRequestForm()
    
    context = {
        'form': form,
        'customer': customer,
    }
    
    return render(request, 'services/submit_request.html', context)


def home(request):
    """صفحه اصلی"""
    return render(request, 'services/home.html')
