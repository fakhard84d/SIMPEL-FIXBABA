from django.contrib import admin
from .models import Customer, ServiceRequest


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['customer_name', 'bill_number', 'product_type', 'phone_number', 'service_status', 'token_used', 'created_at']
    list_filter = ['product_type', 'service_status', 'is_warranty', 'token_used']
    search_fields = ['customer_name', 'bill_number', 'phone_number', 'registration_code']
    readonly_fields = ['access_token', 'created_at', 'updated_at', 'token_used', 'token_used_at']
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('row_number', 'bill_number', 'customer_name', 'phone_number', 'address')
        }),
        ('اطلاعات محصول', {
            'fields': ('product_type', 'product_model', 'serial_number', 'operation_type')
        }),
        ('اطلاعات گارانتی', {
            'fields': ('is_warranty', 'has_warranty_card', 'warranty_card_number')
        }),
        ('اطلاعات پذیرش', {
            'fields': ('acceptance_date', 'registration_code', 'issuer_name', 'completion_date', 'service_status')
        }),
        ('اطلاعات سیستمی', {
            'fields': ('access_token', 'token_used', 'token_used_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields
        return self.readonly_fields


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ['customer', 'product_type', 'product_model', 'status', 'contact_called', 'request_date']
    list_filter = ['product_type', 'status', 'contact_called']
    search_fields = ['customer__customer_name', 'customer__bill_number', 'customer__phone_number', 'product_model']
    readonly_fields = ['request_date', 'called_at']
    
    fieldsets = (
        ('اطلاعات مشتری', {
            'fields': ('customer',)
        }),
        ('اطلاعات درخواست', {
            'fields': ('product_type', 'product_model', 'problem_description')
        }),
        ('وضعیت و پیگیری', {
            'fields': ('status', 'admin_notes', 'contact_called', 'called_at', 'request_date')
        }),
    )
    
    actions = ['mark_as_called', 'mark_as_pending', 'mark_as_completed']
    
    @admin.action(description='علامت‌گذاری به عنوان تماس گرفته شد')
    def mark_as_called(self, request, queryset):
        for obj in queryset:
            obj.mark_as_called()
        self.message_user(request, f"{queryset.count()} درخواست به عنوان 'تماس گرفته شد' علامت‌گذاری شد.")
    
    @admin.action(description='علامت‌گذاری به عنوان در انتظار بررسی')
    def mark_as_pending(self, request, queryset):
        queryset.update(status='pending')
        self.message_user(request, f"{queryset.count()} درخواست به عنوان 'در انتظار بررسی' علامت‌گذاری شد.")
    
    @admin.action(description='علامت‌گذاری به عنوان انجام شده')
    def mark_as_completed(self, request, queryset):
        queryset.update(status='completed')
        self.message_user(request, f"{queryset.count()} درخواست به عنوان 'انجام شده' علامت‌گذاری شد.")
