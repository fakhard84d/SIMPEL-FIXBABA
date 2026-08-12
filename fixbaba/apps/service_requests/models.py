"""
Service Request models for FixBaba platform.
"""

import uuid
from django.db import models
from django.utils import timezone
from django.conf import settings
from apps.customers.models import Customer


class ServiceRequest(models.Model):
    """Service request submitted by a customer"""
    
    STATUS_CHOICES = [
        ('NEW', 'ثبت شده'),
        ('UNDER_REVIEW', 'در حال بررسی'),
        ('WAITING_COORDINATION', 'در انتظار هماهنگی'),
        ('TECHNICIAN_ASSIGNED', 'تعمیرکار تعیین شد'),
        ('IN_PROGRESS', 'در حال انجام'),
        ('COMPLETED', 'تکمیل شد'),
        ('CANCELLED', 'لغو شد'),
    ]
    
    APPLIANCE_CHOICES = [
        ('GAS_STOVE', 'اجاق گاز'),
        ('HOOD', 'هود'),
        ('OVEN', 'فر'),
        ('PACKAGE', 'پکیج'),
        ('COOLER', 'کولر'),
        ('REFRIGERATOR', 'یخچال'),
        ('FREEZER', 'فریزر'),
        ('WASHING_MACHINE', 'ماشین لباسشویی'),
        ('DISHWASHER', 'ماشین ظرفشویی'),
        ('MICROWAVE', 'مایکروفر'),
        ('OTHER', 'سایر'),
    ]
    
    tracking_code = models.CharField(max_length=50, unique=True, db_index=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='service_requests')
    appliance_type = models.CharField(max_length=50, choices=APPLIANCE_CHOICES)
    brand = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='NEW')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'service_requests'
        indexes = [
            models.Index(fields=['tracking_code']),
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Request {self.tracking_code} - {self.customer}"
    
    @classmethod
    def generate_tracking_code(cls) -> str:
        """Generate human-readable tracking code like FB-2026-000123"""
        year = timezone.now().year
        last_request = cls.objects.filter(
            tracking_code__startswith=f'FB-{year}-'
        ).order_by('-id').first()
        
        if last_request:
            last_num = int(last_request.tracking_code.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        
        return f"FB-{year}-{new_num:06d}"
    
    def save(self, *args, **kwargs):
        if not self.tracking_code:
            self.tracking_code = self.generate_tracking_code()
        super().save(*args, **kwargs)
    
    def get_status_display_persian(self):
        return self.get_status_display()


class ServiceRequestImage(models.Model):
    """Images attached to service requests"""
    
    request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='requests/%Y/%m/')
    thumbnail = models.ImageField(upload_to='requests/thumbnails/%Y/%m/', blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    original_filename = models.CharField(max_length=255)
    
    class Meta:
        db_table = 'service_request_images'
        indexes = [
            models.Index(fields=['request', 'uploaded_at']),
        ]
    
    def __str__(self):
        return f"Image for {self.request.tracking_code}"


class RequestStatusHistory(models.Model):
    """Immutable history of status changes"""
    
    request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name='status_history')
    old_status = models.CharField(max_length=30, null=True, blank=True)
    new_status = models.CharField(max_length=30)
    changed_at = models.DateTimeField(auto_now_add=True)
    changed_by = models.CharField(max_length=255, blank=True)  # Admin username or system
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'request_status_history'
        indexes = [
            models.Index(fields=['request', 'changed_at']),
        ]
        ordering = ['changed_at']
    
    def __str__(self):
        return f"{self.request.tracking_code}: {self.old_status} → {self.new_status}"
