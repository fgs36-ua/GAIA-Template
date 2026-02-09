# [Feature: News Management] [Story: NM-ADMIN-001] [Ticket: NM-ADMIN-001-BE-T01]
"""
News Domain Entity

Framework-agnostic representation of a news article.
Supports the full news management lifecycle with status and scope.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class NewsStatus(str, Enum):
    """News article status lifecycle.
    
    - DRAFT: Article is being written, not visible to users
    - PUBLISHED: Article is live and visible per scope rules
    - ARCHIVED: Article is hidden but preserved for history
    """
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class NewsScope(str, Enum):
    """News article visibility scope.
    
    - GENERAL: Visible to all users including anonymous visitors
    - INTERNAL: Only visible to authenticated members (RBAC enforced)
    """
    GENERAL = "GENERAL"
    INTERNAL = "INTERNAL"


@dataclass
class News:
    """News domain entity.
    
    Framework-agnostic representation with all business attributes.
    Used by use cases and passed to/from repositories.
    """
    title: str
    author_id: UUID
    id: UUID = field(default_factory=uuid4)
    summary: Optional[str] = None
    content: Optional[str] = None
    status: NewsStatus = NewsStatus.DRAFT
    scope: NewsScope = NewsScope.GENERAL
    cover_url: Optional[str] = None
    published_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    is_deleted: bool = False
