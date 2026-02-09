# [Feature: News Management] [Story: NM-ADMIN-001] [Ticket: NM-ADMIN-001-DB-T01]
"""
Create news table and enums

Revision ID: 002_create_news
Revises: 001_create_users
Create Date: 2026-02-09

Creates:
- news_status enum (DRAFT, PUBLISHED, ARCHIVED)
- news_scope enum (GENERAL, INTERNAL)
- news table with all columns and indexes
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_create_news'
down_revision = '001_create_users'
branch_labels = None
depends_on = None

# Define enums at module level with create_type=False to prevent auto-creation
news_status_enum = postgresql.ENUM('DRAFT', 'PUBLISHED', 'ARCHIVED', name='news_status', create_type=False)
news_scope_enum = postgresql.ENUM('GENERAL', 'INTERNAL', name='news_scope', create_type=False)


def upgrade() -> None:
    # Create enums first using raw SQL (most reliable approach)
    op.execute("CREATE TYPE news_status AS ENUM ('DRAFT', 'PUBLISHED', 'ARCHIVED')")
    op.execute("CREATE TYPE news_scope AS ENUM ('GENERAL', 'INTERNAL')")
    
    # Create news table using the pre-defined enums with create_type=False
    op.create_table(
        'news',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('summary', sa.String(500), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('status', news_status_enum, nullable=False, server_default='DRAFT'),
        sa.Column('scope', news_scope_enum, nullable=False, server_default='GENERAL'),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('cover_url', sa.String(2048), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
    )
    
    # Create indexes for common query patterns
    op.create_index('ix_news_status', 'news', ['status'])
    op.create_index('ix_news_scope', 'news', ['scope'])
    op.create_index('ix_news_is_deleted', 'news', ['is_deleted'])
    op.create_index('ix_news_published_at', 'news', ['published_at'])
    op.create_index('ix_news_author_id', 'news', ['author_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_news_author_id', table_name='news')
    op.drop_index('ix_news_published_at', table_name='news')
    op.drop_index('ix_news_is_deleted', table_name='news')
    op.drop_index('ix_news_scope', table_name='news')
    op.drop_index('ix_news_status', table_name='news')
    
    # Drop table
    op.drop_table('news')
    
    # Drop enums using raw SQL
    op.execute("DROP TYPE IF EXISTS news_scope")
    op.execute("DROP TYPE IF EXISTS news_status")
