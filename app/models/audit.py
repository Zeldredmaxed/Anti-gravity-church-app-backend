"""Audit trail model (standalone reference, main model in user.py)."""

# The AuditLog model is defined in app/models/user.py alongside the User model.
# This file serves as a convenience import.

from app.models.user import AuditLog

__all__ = ["AuditLog"]
