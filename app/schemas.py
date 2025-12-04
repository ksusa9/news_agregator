# app/schemas.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# Токен
class TokenData(BaseModel):
    user_id: Optional[int] = None
    role: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


#Пользователь
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str = Field(min_length=6, max_length=100)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str
    created_at: datetime

    class Config:
        orm_mode = True


#Источник
class SourceBase(BaseModel):
    name: str
    url: str
    description: Optional[str] = None

class SourceCreate(SourceBase):
    pass


class SourceUpdate(SourceBase):
    name: Optional[str] = Field(None, max_length=255)
    url: Optional[str] = Field(None, max_length=1024)
    description: Optional[str] = Field(None, max_length=1000)


class SourceResponse(SourceBase):
    id: int
    url: str
    author_id: int
    created_at: datetime

    class Config:
        orm_mode = True

class SourceDetailResponse(SourceResponse):
    articles: List['ArticleResponse'] = []

    class Config:
        orm_mode = True

#Статья
class ArticleBase(BaseModel):
    title: str
    summary: Optional[str] = None
    content: str


class ArticleCreate(ArticleBase):
    source_id: int


class ArticleUpdate(ArticleBase):
    title: Optional[str] = Field(None, max_length=1024)
    summary: Optional[str] = Field(None, max_length=5000)
    content: Optional[str] = None
    author_name: Optional[str] = None


class ArticleResponse(ArticleBase):
    id: int
    source_id: int
    author_id: int
    created_at: datetime

    class Config:
        orm_mode = True

