from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import Annotated, List

from app.schemas import ArticleCreate, ArticleUpdate, ArticleResponse
from app.database import get_db
from app.models import Article, Source, User
from app.auth.dependencies import get_current_user, require_role

router = APIRouter(tags=["Articles"])

# Зависимости
AdminUser = Annotated[User, Depends(require_role("admin"))]
LoggedInUser = Annotated[User, Depends(get_current_user)] 
DB_Session = Annotated[AsyncSession, Depends(get_db)]



@router.post(
    "/", 
    response_model=ArticleResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Создать новую статью",
    description="Создание статьи доступно всем авторизованным пользователям."
)
async def create_article(
    article_in: ArticleCreate, 
    db: DB_Session,
    current_user: LoggedInUser
):
    source_stmt = select(Source).where(Source.id == article_in.source_id)
    source_exists = await db.execute(source_stmt)
    if not source_exists.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Источник с ID {article_in.source_id} не найден."
        )

    new_article = Article(
        **article_in.model_dump(exclude_unset=True),
        author_id=current_user.id
    )
    
    db.add(new_article)
    await db.commit()
    await db.refresh(new_article)
    
    return new_article



@router.get(
    "/", 
    response_model=List[ArticleResponse],
    summary="Получить список всех статей",
    description="Список статей доступен всем пользователям."
)
async def read_articles(
    db: DB_Session,
):
    stmt = select(Article)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get(
    "/{article_id}", 
    response_model=ArticleResponse,
    summary="Получить статью по ID",
    description="Получение информации о статье. Доступно всем пользователям"
)
async def read_article(
    article_id: int, 
    db: DB_Session,
):
    stmt = select(Article).where(Article.id == article_id)
    result = await db.execute(stmt)
    article = result.scalar_one_or_none()
    
    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Статья не найдена")
        
    return article


@router.patch(
    "/{article_id}", 
    response_model=ArticleResponse,
    summary="Изменить статью",
    description="Изменение доступно пользователю, который создал статью."
    )
async def update_article(
    article_id: int, 
    article_in: ArticleUpdate, 
    db: DB_Session,
    current_user: LoggedInUser
):
    stmt = select(Article).where(Article.id == article_id)
    result = await db.execute(stmt)
    article = result.scalar_one_or_none()

    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Статья не найдена")

    is_admin = current_user.role == "admin"
    is_author = article.author_id == current_user.id
    
    if not is_admin and not is_author:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Недостаточно прав. Только Администратор или Автор могут обновить статью."
        )

    update_data = article_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(article, key, value)
        
    await db.commit()
    await db.refresh(article)
    
    return article


@router.delete(
    "/{article_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить статью",
    description="Удаление доступно пользователю, который создал статью."
)
async def delete_article(
    article_id: int, 
    db: DB_Session,
    current_user: LoggedInUser
):
    stmt = select(Article).where(Article.id == article_id)
    result = await db.execute(stmt)
    article = result.scalar_one_or_none()
    
    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Статья не найдена")
    
    is_admin = current_user.role == "admin"
    is_author = article.author_id == current_user.id
    
    if not is_admin and not is_author:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Недостаточно прав."
        )

    delete_stmt = delete(Article).where(Article.id == article_id)
    await db.execute(delete_stmt)
    await db.commit()
    
    return