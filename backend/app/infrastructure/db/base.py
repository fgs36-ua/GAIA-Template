# [Feature: Infrastructure] [Story: Backend Setup] [Ticket: NM-ADMIN-001-DB-T01]
"""
SQLAlchemy Declarative Base

All models inherit from this base class.
"""

from sqlalchemy.orm import declarative_base

Base = declarative_base()
