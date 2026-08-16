"""
Custom Authentication Backends for FixBaba
"""

from django.contrib.auth.backends import ModelBackend
from apps.customers.models import CustomerDevice


class DeviceSessionBackend(ModelBackend):
    """
    Authenticate users via device credential from secure HttpOnly cookie.
    This is used for returning customers who have already authenticated.
    """
    
    def authenticate(self, request, device_credential=None, **kwargs):
        if device_credential is None:
            return None
        
        customer = CustomerDevice.validate_credential(device_credential)
        return customer
    
    def get_user(self, user_id):
        from apps.customers.models import Customer
        try:
            return Customer.objects.get(pk=user_id)
        except Customer.DoesNotExist:
            return None
