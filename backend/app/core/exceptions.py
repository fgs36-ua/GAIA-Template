# [Feature: News Management] [Story: NM-ADMIN-002] [Ticket: NM-ADMIN-002-BE-T01]
"""
Core Application Exceptions

Reusable exception classes for use cases and domain logic.
"""


class NotFoundException(Exception):
    """Raised when a requested resource is not found."""
    pass
