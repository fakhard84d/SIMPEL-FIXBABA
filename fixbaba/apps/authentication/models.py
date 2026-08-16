"""
Authentication models - re-exports from customers app.
This allows importing from apps.authentication.models for better organization.
"""

from apps.customers.models import MagicLink, CustomerDevice, AuditLog

__all__ = ['MagicLink', 'CustomerDevice', 'AuditLog']
