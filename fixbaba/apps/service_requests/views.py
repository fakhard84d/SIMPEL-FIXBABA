"""
Service Request Views for Customer Portal
"""

import uuid
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.files.uploadedfile import UploadedFile
from django.conf import settings
from django.utils import timezone
from PIL import Image
from io import BytesIO

from apps.customers.views import customer_login_required
from apps.customers.models import AuditLog
from apps.service_requests.models import ServiceRequest, ServiceRequestImage


@customer_login_required
def request_list(request):
    """List all service requests for the customer"""
    customer = request.user
    
    requests = ServiceRequest.objects.filter(
        customer=customer
    ).prefetch_related('images').order_by('-created_at')
    
    context = {
        'requests': requests,
        'page_title': 'درخواست‌های من',
    }
    
    return render(request, 'portal/requests/list.html', context)


@customer_login_required
def request_detail(request, request_id):
    """View details of a specific service request"""
    customer = request.user
    
    service_request = get_object_or_404(
        ServiceRequest.objects.prefetch_related('images', 'status_history'),
        id=request_id,
        customer=customer  # Ensure ownership
    )
    
    context = {
        'request_obj': service_request,
        'page_title': f'درخواست {service_request.tracking_code}',
    }
    
    return render(request, 'portal/requests/detail.html', context)


@customer_login_required
def request_create(request):
    """Create a new service request - Wizard style"""
    customer = request.user
    
    if request.method == 'POST':
        # Validate and create request
        appliance_type = request.POST.get('appliance_type')
        brand = request.POST.get('brand', '')
        model = request.POST.get('model', '')
        description = request.POST.get('description', '')
        
        # Validate appliance type
        valid_types = [choice[0] for choice in ServiceRequest.APPLIANCE_CHOICES]
        if appliance_type not in valid_types:
            return render(request, 'portal/requests/create.html', {
                'error': 'نوع وسیله نامعتبر است.',
                'page_title': 'ثبت درخواست جدید',
            })
        
        # Validate description
        if not description or len(description.strip()) < 10:
            return render(request, 'portal/requests/create.html', {
                'error': 'لطفاً شرح مشکل را کامل‌تر بنویسید.',
                'page_title': 'ثبت درخواست جدید',
            })
        
        # Create request
        service_request = ServiceRequest.objects.create(
            customer=customer,
            appliance_type=appliance_type,
            brand=brand[:100] if brand else '',
            model=model[:100] if model else '',
            description=description.strip(),
        )
        
        # Handle image uploads
        images = request.FILES.getlist('images')
        uploaded_count = 0
        
        for img in images[:settings.MAX_IMAGES_PER_REQUEST]:
            if validate_and_save_image(img, service_request):
                uploaded_count += 1
        
        AuditLog.log(
            'REQUEST_CREATED',
            customer=customer,
            request=request,
            request_id=service_request.id,
            tracking_code=service_request.tracking_code,
        )
        
        return render(request, 'portal/requests/success.html', {
            'request_obj': service_request,
            'page_title': 'درخواست ثبت شد',
        })
    
    context = {
        'appliance_choices': ServiceRequest.APPLIANCE_CHOICES,
        'max_images': settings.MAX_IMAGES_PER_REQUEST,
        'max_size_mb': settings.MAX_UPLOAD_SIZE_MB,
        'page_title': 'ثبت درخواست جدید',
    }
    
    return render(request, 'portal/requests/create.html', context)


def validate_and_save_image(uploaded_file: UploadedFile, service_request: ServiceRequest) -> bool:
    """
    Validate and save uploaded image securely.
    Returns True if successful.
    """
    try:
        # Check file size
        if uploaded_file.size > settings.MAX_UPLOAD_SIZE_BYTES:
            return False
        
        # Check MIME type
        allowed_types = ['image/jpeg', 'image/png', 'image/webp']
        content_type = uploaded_file.content_type
        
        if content_type not in allowed_types:
            return False
        
        # Generate safe filename
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
            return False
        
        safe_filename = f"{uuid.uuid4().hex}{ext}"
        
        # Read and validate image
        img = Image.open(uploaded_file)
        
        # Verify it's actually an image
        img.verify()
        
        # Re-open for processing
        uploaded_file.seek(0)
        img = Image.open(uploaded_file)
        
        # Convert to RGB if necessary (removes alpha channel, fixes mode issues)
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        # Remove EXIF data by re-encoding
        output = BytesIO()
        img_format = 'JPEG' if ext in ['.jpg', '.jpeg'] else 'PNG' if ext == '.png' else 'WEBP'
        img.save(output, format=img_format, quality=85, optimize=True)
        output.seek(0)
        
        # Save to model
        image_obj = ServiceRequestImage.objects.create(
            request=service_request,
            original_filename=uploaded_file.name[:255],
            file_size=output.getbuffer().nbytes,
        )
        
        # Save the file
        from django.core.files.base import ContentFile
        image_obj.image.save(
            safe_filename,
            ContentFile(output.read()),
            save=True
        )
        
        # Generate thumbnail
        generate_thumbnail(image_obj)
        
        return True
        
    except Exception as e:
        return False


def generate_thumbnail(image_obj: ServiceRequestImage, size: tuple = (300, 300)):
    """Generate thumbnail for uploaded image"""
    try:
        img_path = image_obj.image.path
        thumb_path = img_path.replace('/requests/', '/requests/thumbnails/')
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(thumb_path), exist_ok=True)
        
        with Image.open(img_path) as img:
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            img.save(thumb_path, quality=80, optimize=True)
            
            # Update model
            rel_path = thumb_path.split('/media_uploads/')[-1]
            image_obj.thumbnail = rel_path
            image_obj.save(update_fields=['thumbnail'])
            
    except Exception:
        pass  # Thumbnail generation is optional


@customer_login_required
@require_http_methods(["DELETE"])
def request_delete_image(request, image_id):
    """Delete an image from a service request"""
    customer = request.user
    
    image = get_object_or_404(
        ServiceRequestImage,
        id=image_id,
        request__customer=customer  # Ensure ownership
    )
    
    # Delete files
    if image.image:
        image.image.delete()
    if image.thumbnail:
        image.thumbnail.delete()
    
    image.delete()
    
    return JsonResponse({'success': True})
