# [Feature: News Management] [Story: NM-ADMIN-001] [Ticket: NM-ADMIN-001-DB-T01]
"""
News SQLAlchemy Model

Represents a news article in the system with support for:
- Draft/Published/Archived status lifecycle
- General/Internal scope for RBAC filtering
- Soft delete for audit trail preservation
"""

import enum
import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.infrastructure.db.base import Base


class NewsStatus(str, enum.Enum):
    """News article status lifecycle.
    
    - DRAFT: Article is being written, not visible to users
    - PUBLISHED: Article is live and visible per scope rules
    - ARCHIVED: Article is hidden but preserved for history
    """
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class NewsScope(str, enum.Enum):
    """News article visibility scope.
    
    - GENERAL: Visible to all users including anonymous visitors
    - INTERNAL: Only visible to authenticated members (RBAC enforced)
    """
    GENERAL = "GENERAL"
    INTERNAL = "INTERNAL"


class News(Base):
    """News article model.
    
    Supports the full news management lifecycle with:
    - Rich content (title, summary, HTML body)
    - Status transitions (draft -> published -> archived)
    - Scope-based access control
    - Author tracking via FK to users
    - Soft delete for audit preservation
    """
    
    __tablename__ = "news"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    summary = Column(String(500), nullable=True)
    content = Column(Text, nullable=True)
    status = Column(
        Enum(NewsStatus, name="news_status", create_type=False), 
        nullable=False, 
        default=NewsStatus.DRAFT
    )
    scope = Column(
        Enum(NewsScope, name="news_scope", create_type=False), 
        nullable=False, 
        default=NewsScope.GENERAL
    )
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    cover_url = Column(String(2048), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False, nullable=False)

    # Relationships
    author = relationship("User", back_populates="news_articles")
    
    def __repr__(self) -> str:
        return f"<News(id={self.id}, title='{self.title[:30]}...', status={self.status})>"
