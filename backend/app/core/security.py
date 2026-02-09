# [Feature: News Management] [Story: NM-ADMIN-001] [Ticket: NM-ADMIN-001-BE-T01]
"""
Security Dependencies

Authentication and authorization dependencies for FastAPI endpoints.
Stub implementation until User Management feature is complete.
"""

from dataclasses import dataclass
from uuid import UUID, uuid4

from fastapi import Depends, HTTPException, status


@dataclass
class CurrentUser:
    """Stub user representation for auth dependencies."""
    id: UUID
    email: str
    is_active: bool = True
    is_superuser: bool = False


# Stub admin user for development/testing
# TODO: Replace with real auth when User Management is implemented
_STUB_ADMIN = CurrentUser(
    id=uuid4(),
    email="admin@example.com",
    is_active=True,
    is_superuser=True,
)


def get_current_user() -> CurrentUser:
    """Get the current authenticated user.
    
    STUB: Returns a mock admin user for development.
    Replace with real JWT/OAuth2 implementation.
    """
    return _STUB_ADMIN


def require_admin(
    current_user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """Require that the current user is an administrator.
    
    Raises:
        HTTPException: 403 Forbidden if user is not admin
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
