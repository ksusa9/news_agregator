from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import Annotated, List

from app.schemas import SourceCreate, SourceUpdate, SourceResponse, ArticleResponse
from app.database import get_db
from app.models import Source, User, Article
from app.auth.dependencies import get_current_user, require_role

router = APIRouter(tags=["Sources"])

AdminUser = Annotated[User, Depends(require_role("admin"))]
LoggedInUser = Annotated[User, Depends(get_current_user)]
DB_Session = Annotated[AsyncSession, Depends(get_db)]


@router.post(
    "/", 
    response_model=SourceResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый источник новостей",
    description="Создание доступно только авторизованым пользователям"
)
async def create_source(
    source_in: SourceCreate, 
    db: DB_Session,
    current_user: LoggedInUser
):
    stmt = select(Source).where(Source.url == str(source_in.url))
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Источник с таким URL уже существует."
        )

    new_source = Source(
        **source_in.model_dump(exclude_unset=True),
        author_id=current_user.id
    )
    
    db.add(new_source)
    await db.commit()
    await db.refresh(new_source)
    
    return new_source


@router.get(
    "/", 
    response_model=List[SourceResponse],
    summary="Получить список всех источников новостей",
    description="Список источников доступен всем пользователям"
)
async def read_sources(
    db: DB_Session,
):
    stmt = select(Source)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get(
    "/{source_id}", 
    response_model=SourceResponse,
    summary="Получить источник по ID",
    description="Получение информации о источнике доступно всем пользователям"
)
async def read_source(
    source_id: int, 
    db: DB_Session,
):
    stmt = select(Source).where(Source.id == source_id)
    result = await db.execute(stmt)
    source = result.scalar_one_or_none()
    
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Источник не найден")
        
    return source


@router.get(
    "/{source_id}/articles",
    response_model=List[ArticleResponse],
    summary="Получить все статьи конкретного источника",
    description="Получить список статей, связанных с указанным ID источника,доступен всем пользователям."
)
async def get_articles_by_source(
    source_id: int,
    db: DB_Session,
):
    source_stmt = select(Source).where(Source.id == source_id)
    source = await db.execute(source_stmt)
    if source.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Источник с ID {source_id} не найден"
        )
        
    stmt = (
        select(Article).where(Article.source_id == source_id)
    )
    result = await db.execute(stmt)
    
    return result.scalars().all()


@router.patch(
    "/{source_id}", 
    response_model=SourceResponse,
    summary="Изменить существующий источник",
    description="Изменение доступно пользователю, который создал статью"
)
async def update_source(
    source_id: int, 
    source_in: SourceUpdate, 
    db: DB_Session,
    current_user: LoggedInUser
):
    stmt = select(Source).where(Source.id == source_id)
    result = await db.execute(stmt)
    source = result.scalar_one_or_none()

    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Источник не найден")

    is_admin = current_user.role == "admin"
    is_author = source.author_id == current_user.id
    
    if not is_admin and not is_author:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Недостаточно прав. Только Администратор или Автор могут обновить источник."
        )

    update_data = source_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(source, key, value)
        
    await db.commit()
    await db.refresh(source)
    
    return source


@router.delete(
    "/{source_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить источник",
    description="Удаление доступно пользователю, который создал статью"
)
async def delete_source(
    source_id: int, 
    db: DB_Session,
    current_user: LoggedInUser
):
    stmt_find = (
        select(Source)
        .where(Source.id == source_id)
    )
    result_find = await db.execute(stmt_find)
    source_to_delete = result_find.scalar_one_or_none() 

    if source_to_delete is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Источник не найден")

    is_admin = current_user.role == "admin"
    is_author = source_to_delete.author_id == current_user.id
    
    if not is_admin and not is_author:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Недостаточно прав. Только администратор или автор могут удалить источник."
        )

    await db.delete(source_to_delete)
    await db.commit()
    
    return