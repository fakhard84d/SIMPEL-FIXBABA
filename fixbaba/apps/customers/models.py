"""
Customer models for FixBaba platform.
Handles customer data, magic links, device sessions, and audit logging.
"""

import secrets
import hashlib
from datetime import timedelta
from django.db import models, transaction
from django.utils import timezone
from django.conf import settings


def normalize_phone_number(phone: str) -> str:
    """Normalize phone number to canonical format: 09xxxxxxxxx"""
    if not phone:
        return phone
    
    # Remove spaces, dashes, etc.
    phone = ''.join(c for c in phone if c.isdigit())
    
    # Handle different formats
    if phone.startswith('989') and len(phone) == 13:
        phone = '0' + phone[2:]
    elif phone.startswith('+989') and len(phone) == 14:
        phone = '0' + phone[3:]
    elif phone.startswith('9') and len(phone) == 11:
        phone = '0' + phone
    
    return phone


class Customer(models.Model):
    """Customer model - represents a user of the service"""
    
    customer_id = models.CharField(max_length=50, unique=True, db_index=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=11, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'customers'
        indexes = [
            models.Index(fields=['phone']),
            models.Index(fields=['customer_id']),
            models.Index(fields=['is_active', 'created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.phone})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_masked_phone(self):
        """Return masked phone number for display"""
        if len(self.phone) >= 4:
            return self.phone[:4] + '***' + self.phone[-4:]
        return self.phone


class MagicLink(models.Model):
    """
    Magic Link for passwordless authentication.
    Token is stored as hash, never in plain text.
    """
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('EXPIRED', 'Expired'),
        ('REVOKED', 'Revoked'),
        ('EXHAUSTED', 'Exhausted'),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='magic_links')
    token_hash = models.CharField(max_length=64, unique=True, db_index=True)
    max_activations = models.PositiveSmallIntegerField(default=settings.MAGIC_LINK_MAX_ACTIVATIONS)
    successful_activations = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    
    class Meta:
        db_table = 'magic_links'
        indexes = [
            models.Index(fields=['token_hash']),
            models.Index(fields=['status', 'expires_at']),
            models.Index(fields=['customer', 'status']),
        ]
    
    def __str__(self):
        return f"MagicLink for {self.customer} - {self.status}"
    
    @classmethod
    def generate_token(cls) -> str:
        """Generate cryptographically secure token"""
        return secrets.token_urlsafe(32)
    
    @classmethod
    def hash_token(cls, token: str) -> str:
        """Hash token with server pepper"""
        pepper = settings.SERVER_PEPPER.encode('utf-8')
        token_bytes = token.encode('utf-8')
        return hashlib.sha256(token_bytes + pepper).hexdigest()
    
    @classmethod
    def create_for_customer(cls, customer: Customer, expiration_minutes: int = None) -> tuple[str, 'MagicLink']:
        """
        Create a new magic link for a customer.
        Returns (raw_token, magic_link_instance)
        """
        if expiration_minutes is None:
            expiration_minutes = settings.MAGIC_LINK_EXPIRATION_MINUTES
        
        raw_token = cls.generate_token()
        token_hash = cls.hash_token(raw_token)
        expires_at = timezone.now() + timedelta(minutes=expiration_minutes)
        
        magic_link = cls.objects.create(
            customer=customer,
            token_hash=token_hash,
            expires_at=expires_at,
            max_activations=settings.MAGIC_LINK_MAX_ACTIVATIONS,
        )
        
        return raw_token, magic_link
    
    @classmethod
    def validate_and_activate(cls, token: str, device_credential: str = None) -> dict:
        """
        Validate token and handle activation with race condition protection.
        Returns dict with 'success', 'customer', 'device', 'error' keys.
        """
        token_hash = cls.hash_token(token)
        now = timezone.now()
        
        with transaction.atomic():
            try:
                magic_link = cls.objects.select_for_update().get(token_hash=token_hash)
            except cls.DoesNotExist:
                return {'success': False, 'error': 'invalid_token'}
            
            # Check revocation
            if magic_link.revoked_at:
                return {'success': False, 'error': 'revoked'}
            
            # Check expiration
            if magic_link.expires_at < now:
                magic_link.status = 'EXPIRED'
                magic_link.save(update_fields=['status'])
                return {'success': False, 'error': 'expired'}
            
            # Check if already exhausted
            if magic_link.status == 'EXHAUSTED':
                return {'success': False, 'error': 'exhausted'}
            
            # Check if device already has a session
            if device_credential:
                existing_device = CustomerDevice.objects.filter(
                    customer=magic_link.customer,
                    is_active=True,
                    revoked_at__isnull=True
                ).filter(
                    models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=now)
                ).first()
                
                if existing_device:
                    # Existing device - don't consume quota
                    magic_link.last_used_at = now
                    magic_link.save(update_fields=['last_used_at'])
                    return {
                        'success': True,
                        'customer': magic_link.customer,
                        'device': existing_device,
                        'is_existing_device': True
                    }
            
            # New device - check quota
            if magic_link.successful_activations >= magic_link.max_activations:
                magic_link.status = 'EXHAUSTED'
                magic_link.save(update_fields=['status'])
                return {'success': False, 'error': 'exhausted'}
            
            # Activate new device
            magic_link.successful_activations += 1
            magic_link.last_used_at = now
            
            if magic_link.successful_activations >= magic_link.max_activations:
                magic_link.status = 'EXHAUSTED'
            
            magic_link.save(update_fields=['successful_activations', 'last_used_at', 'status'])
            
            # Create device session
            device = CustomerDevice.create_for_customer(magic_link.customer, device_credential)
        
        return {
            'success': True,
            'customer': magic_link.customer,
            'device': device,
            'is_existing_device': False,
            'activations_remaining': magic_link.max_activations - magic_link.successful_activations
        }
    
    def revoke(self):
        """Revoke this magic link"""
        self.revoked_at = timezone.now()
        self.status = 'REVOKED'
        self.save(update_fields=['revoked_at', 'status'])


class CustomerDevice(models.Model):
    """
    Device session for returning users.
    Uses hashed credential stored in secure HttpOnly cookie.
    """
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='devices')
    credential_hash = models.CharField(max_length=64, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    user_agent_hash = models.CharField(max_length=64, blank=True)
    ip_hash = models.CharField(max_length=64, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'customer_devices'
        indexes = [
            models.Index(fields=['credential_hash']),
            models.Index(fields=['customer', 'is_active']),
            models.Index(fields=['expires_at', 'revoked_at']),
        ]
    
    def __str__(self):
        return f"Device for {self.customer} (created: {self.created_at.date()})"
    
    @classmethod
    def generate_credential(cls) -> str:
        """Generate cryptographically secure device credential"""
        return secrets.token_urlsafe(32)
    
    @classmethod
    def hash_credential(cls, credential: str) -> str:
        """Hash device credential"""
        pepper = settings.SERVER_PEPPER.encode('utf-8')
        credential_bytes = credential.encode('utf-8')
        return hashlib.sha256(credential_bytes + pepper).hexdigest()
    
    @classmethod
    def create_for_customer(cls, customer: Customer, credential: str = None) -> 'CustomerDevice':
        """Create a new device session"""
        if not credential:
            credential = cls.generate_credential()
        
        credential_hash = cls.hash_credential(credential)
        expires_at = timezone.now() + timedelta(days=settings.DEVICE_SESSION_DAYS)
        
        return cls.objects.create(
            customer=customer,
            credential_hash=credential_hash,
            expires_at=expires_at,
        )
    
    @classmethod
    def validate_credential(cls, credential: str, customer: Customer = None) -> Customer:
        """
        Validate device credential and return customer if valid.
        Does NOT consume magic link quota.
        """
        credential_hash = cls.hash_credential(credential)
        now = timezone.now()
        
        try:
            device = cls.objects.select_related('customer').get(
                credential_hash=credential_hash,
                is_active=True,
                revoked_at__isnull=True,
            )
            
            # Check expiration
            if device.expires_at and device.expires_at < now:
                return None
            
            # Update last seen
            device.last_seen_at = now
            device.save(update_fields=['last_seen_at'])
            
            return device.customer
            
        except cls.DoesNotExist:
            return None
    
    def revoke(self):
        """Revoke this device session"""
        self.revoked_at = timezone.now()
        self.is_active = False
        self.save(update_fields=['revoked_at', 'is_active'])


class AuditLog(models.Model):
    """
    Audit log for security and compliance.
    Never store sensitive data like tokens or credentials.
    """
    
    ACTION_CHOICES = [
        ('MAGIC_LINK_CREATED', 'Magic Link Created'),
        ('MAGIC_LINK_USED', 'Magic Link Used'),
        ('LOGIN_SUCCESS', 'Login Success'),
        ('LOGIN_FAILED', 'Login Failed'),
        ('DEVICE_CREATED', 'Device Created'),
        ('DEVICE_REVOKED', 'Device Revoked'),
        ('REQUEST_CREATED', 'Request Created'),
        ('REQUEST_UPDATED', 'Request Updated'),
        ('IMAGE_UPLOADED', 'Image Uploaded'),
        ('LINK_REVOKED', 'Link Revoked'),
        ('ADMIN_ACTION', 'Admin Action'),
        ('SMS_SENT', 'SMS Sent'),
        ('SMS_FAILED', 'SMS Failed'),
    ]
    
    action = models.CharField(max_length=50, choices=ACTION_CHOICES, db_index=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'audit_logs'
        indexes = [
            models.Index(fields=['action', 'created_at']),
            models.Index(fields=['customer', 'created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.action} - {self.created_at}"
    
    @classmethod
    def log(cls, action: str, customer: Customer = None, request=None, **metadata):
        """Create an audit log entry"""
        ip_address = None
        user_agent = None
        
        if request:
            ip_address = cls._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        
        # Sanitize metadata - remove sensitive fields
        safe_metadata = {}
        for key, value in metadata.items():
            if key.lower() not in ['token', 'credential', 'password', 'secret', 'key']:
                safe_metadata[key] = value
        
        return cls.objects.create(
            action=action,
            customer=customer,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=safe_metadata,
        )
    
    @staticmethod
    def _get_client_ip(request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
