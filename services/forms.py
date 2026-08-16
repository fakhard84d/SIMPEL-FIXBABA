from django import forms
from .models import ServiceRequest


class ServiceRequestForm(forms.ModelForm):
    """فرم ثبت درخواست خدمات"""
    
    class Meta:
        model = ServiceRequest
        fields = ['product_type', 'product_model', 'problem_description']
        widgets = {
            'product_type': forms.Select(attrs={
                'class': 'form-select form-select-lg',
                'dir': 'rtl'
            }),
            'product_model': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'مثلاً: GI-135 NP',
                'dir': 'ltr'
            }),
            'problem_description': forms.Textarea(attrs={
                'class': 'form-control form-control-lg',
                'rows': 5,
                'placeholder': 'لطفاً مشکل دستگاه خود را با جزئیات توضیح دهید...',
                'dir': 'rtl'
            }),
        }
        labels = {
            'product_type': 'نوع محصول',
            'product_model': 'مدل محصول',
            'problem_description': 'شرح مشکل',
        }
