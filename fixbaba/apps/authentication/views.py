"""
Magic Link Authentication Views
"""

import secrets
from django.shortcuts import render, redirect
from django.http import HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.conf import settings
from django_ratelimit.decorators import ratelimit

from apps.customers.models import MagicLink, CustomerDevice, AuditLog


@ratelimit(key='ip', rate='10/m', block=True)
@ratelimit(key='post:token', rate='5/h', block=True)
@require_http_methods(["GET", "POST"])
def magic_link_access(request, token):
    """
    Handle magic link authentication.
    Validates token and creates device session.
    """
    
    if not token or len(token) < 32:
        AuditLog.log('LOGIN_FAILED', request=request, error='invalid_token_format')
        return render(request, 'errors/401.html', {
            'title': 'لینک نامعتبر',
            'message': 'لینک دسترسی نامعتبر است.',
            'action_text': 'تماس با پشتیبانی',
        }, status=401)
    
    # Check for existing device credential
    device_credential = request.COOKIES.get('fixbaba_device')
    
    # Validate and activate
    result = MagicLink.validate_and_activate(token, device_credential)
    
    if not result['success']:
        error = result.get('error', 'unknown')
        AuditLog.log('LOGIN_FAILED', request=request, error=error)
        
        context = {
            'title': '',
            'message': '',
            'action_text': 'تماس با پشتیبانی',
        }
        
        if error == 'invalid_token':
            context['title'] = 'لینک نامعتبر'
            context['message'] = 'این لینک دسترسی معتبر نیست.'
        elif error == 'expired':
            context['title'] = 'لینک منقضی شده'
            context['message'] = 'مدت اعتبار این لینک به پایان رسیده است.'
        elif error == 'revoked':
            context['title'] = 'لینک غیرفعال شده'
            context['message'] = 'این لینک توسط مدیریت غیرفعال شده است.'
        elif error == 'exhausted':
            context['title'] = 'پایان ظرفیت لینک'
            context['message'] = 'تعداد دفعات استفاده از این لینک به پایان رسیده است.'
        
        return render(request, 'errors/401.html', context, status=401)
    
    customer = result['customer']
    device = result['device']
    is_existing = result.get('is_existing_device', False)
    
    # Log successful login
    AuditLog.log(
        'LOGIN_SUCCESS' if is_existing else 'MAGIC_LINK_USED',
        customer=customer,
        request=request,
        device_id=device.id,
        is_existing_device=is_existing
    )
    
    # Create response - redirect to portal
    response = redirect('portal_dashboard')
    
    # Set secure HttpOnly cookie for device credential
    # We need to get the raw credential somehow
    # For new devices, we generate it in the model but don't return it
    # So we need to modify the flow slightly
    
    if not is_existing:
        # Generate new credential and set cookie
        new_credential = CustomerDevice.generate_credential()
        credential_hash = CustomerDevice.hash_credential(new_credential)
        
        # Update device with new hash (it was created with a temp one)
        device.credential_hash = credential_hash
        device.save(update_fields=['credential_hash'])
        
        response.set_cookie(
            'fixbaba_device',
            new_credential,
            max_age=settings.DEVICE_SESSION_DAYS * 24 * 60 * 60,
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax',
            path='/',
        )
    else:
        # Refresh existing cookie
        response.set_cookie(
            'fixbaba_device',
            device_credential,
            max_age=settings.DEVICE_SESSION_DAYS * 24 * 60 * 60,
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax',
            path='/',
        )
    
    # Set session for Django auth
    request.session['customer_id'] = customer.id
    request.session['authenticated_at'] = timezone.now().isoformat()
    
    return response


@require_http_methods(["POST"])
def revoke_device(request):
    """Revoke current device session"""
    if hasattr(request, 'user') and request.user.is_authenticated:
        device_credential = request.COOKIES.get('fixbaba_device')
        if device_credential:
            try:
                from apps.customers.models import CustomerDevice
                credential_hash = CustomerDevice.hash_credential(device_credential)
                device = CustomerDevice.objects.get(credential_hash=credential_hash)
                device.revoke()
                AuditLog.log('DEVICE_REVOKED', customer=request.user, request=request)
            except CustomerDevice.DoesNotExist:
                pass
    
    response = redirect('portal_logout')
    response.delete_cookie('fixbaba_device')
    return response
