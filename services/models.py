from django.db import models
import uuid
from django.utils import timezone


class Customer(models.Model):
    """مدل مشتری بر اساس داده‌های اکسل"""
    
    # فیلدهای اصلی از اکسل
    row_number = models.IntegerField("شماره ردیف", null=True, blank=True)
    bill_number = models.CharField("شماره قبض", max_length=50, unique=True)
    is_warranty = models.BooleanField("گارانتی دارد", default=False)
    operation_type = models.CharField("نوع عملیات", max_length=100)
    customer_name = models.CharField("نام مشتری", max_length=200)
    product_type = models.CharField("نوع محصول", max_length=50)
    acceptance_date = models.CharField("تاریخ پذیرش", max_length=20)
    registration_code = models.CharField("کد ثبت", max_length=50)
    issuer_name = models.CharField("نام صادر کننده قبض", max_length=200)
    product_model = models.CharField("مدل محصول", max_length=200)
    serial_number = models.CharField("شماره سریال محصول", max_length=100)
    completion_date = models.CharField("تاریخ اتمام یا تحویل", max_length=20, null=True, blank=True)
    address = models.TextField("نشانی")
    has_warranty_card = models.BooleanField("شماره کارت گارانتی دارد", default=False)
    warranty_card_number = models.CharField("شماره کارت گارانتی", max_length=50, null=True, blank=True)
    phone_number = models.CharField("شماره تماس", max_length=20)
    service_status = models.CharField("وضعیت سرویس", max_length=100)
    
    # فیلدهای سیستمی
    access_token = models.UUIDField("توکن دسترسی", default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField("تاریخ به‌روزرسانی", auto_now=True)
    token_used = models.BooleanField("توکن استفاده شده", default=False)
    token_used_at = models.DateTimeField("تاریخ استفاده توکن", null=True, blank=True)
    
    class Meta:
        verbose_name = "مشتری"
        verbose_name_plural = "مشتریان"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.customer_name} - {self.bill_number}"
    
    def get_access_url(self):
        """ساخت لینک دسترسی اختصاصی"""
        from django.conf import settings
        return f"{settings.SITE_URL}/service/{self.access_token}/" if hasattr(settings, 'SITE_URL') else f"/service/{self.access_token}/"
    
    def is_token_valid(self):
        """بررسی اعتبار توکن (یک بار مصرف)"""
        return not self.token_used
    
    def use_token(self):
        """استفاده از توکن و غیرفعال کردن آن"""
        if not self.token_used:
            self.token_used = True
            self.token_used_at = timezone.now()
            self.save()
            return True
        return False


class ServiceRequest(models.Model):
    """مدل درخواست تعمیر/خدمات"""
    
    PRODUCT_CHOICES = [
        ('gas_stove', 'اجاق گاز'),
        ('hood', 'هود'),
        ('oven', 'فر'),
        ('package', 'پکیج'),
        ('other', 'سایر'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'در انتظار بررسی'),
        ('contacted', 'تماس گرفته شد'),
        ('in_progress', 'در حال انجام'),
        ('completed', 'انجام شده'),
        ('cancelled', 'لغو شده'),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='service_requests', verbose_name="مشتری")
    product_type = models.CharField("نوع محصول", max_length=20, choices=PRODUCT_CHOICES)
    product_model = models.CharField("مدل محصول", max_length=200)
    problem_description = models.TextField("شرح مشکل")
    request_date = models.DateTimeField("تاریخ درخواست", auto_now_add=True)
    status = models.CharField("وضعیت", max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField("یادداشت‌های ادمین", null=True, blank=True)
    contact_called = models.BooleanField("تماس گرفته شد", default=False)
    called_at = models.DateTimeField("تاریخ تماس", null=True, blank=True)
    
    class Meta:
        verbose_name = "درخواست خدمات"
        verbose_name_plural = "درخواست‌های خدمات"
        ordering = ['-request_date']
    
    def __str__(self):
        return f"درخواست {self.customer.customer_name} - {self.get_product_type_display()}"
    
    def mark_as_called(self):
        """ثبت تماس با مشتری"""
        from django.utils import timezone
        self.contact_called = True
        self.called_at = timezone.now()
        self.save()
