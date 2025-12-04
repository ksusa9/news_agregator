from __future__ import annotations

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    DateTime,
    func,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("username", name="uq_users_username"),
        UniqueConstraint("email", name="uq_users_email"),
    )

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(150), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password = Column(String(256), nullable=False)
    role = Column(String(20), nullable=False, server_default="user")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    sources = relationship("Source", back_populates="author_user")
    articles = relationship("Article", back_populates="author_user")


class Source(Base):
    __tablename__ = "sources"
    __table_args__ = (UniqueConstraint("url", name="uq_sources_url"),)

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    url = Column(String(1024), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    articles = relationship("Article", back_populates="source", cascade="all, delete-orphan")
    author_user = relationship("User", back_populates="sources")


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(1024), nullable=False)
    summary = Column(Text)
    content = Column(Text, nullable=False)
    author_name = Column(String(255), nullable=True)

    source_id = Column(Integer, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    source = relationship("Source", back_populates="articles")
    author_user = relationship("User", back_populates="articles")
