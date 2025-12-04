from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Annotated

from app.schemas import UserCreate, UserLogin, UserResponse, Token
from app.database import get_db
from app.models import User
from app.auth.security import get_password_hash, verify_password, create_access_token
from app.auth.dependencies import get_current_user, require_role

from datetime import timedelta
from app.auth.security import ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(tags=["Auth"])


@router.post(
    "/register", 
    response_model=UserResponse,
    summary="Регистрация нового пользователя",
    description="Создает нового пользователя в системе с ролью 'user'."
)
async def register_user(
    user_in: UserCreate, 
    db: Annotated[AsyncSession, Depends(get_db)]
):
    email_exists_stmt = select(User).where(User.email == user_in.email)
    username_exists_stmt = select(User).where(User.username == user_in.username)
    
    email_exists_result = await db.execute(email_exists_stmt)
    if email_exists_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
            detail="Пользователь с таким email уже существует"
        ) 

    username_exists_result = await db.execute(username_exists_stmt)
    if username_exists_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
            detail="Пользователь с таким именем уже существует"
        )
        
    hashed_password = get_password_hash(user_in.password)
    
    new_user = User(
        username=user_in.username,
        email=user_in.email,
        password=hashed_password,
        role="user"
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user


@router.post(
    "/login", 
    response_model=Token,
    summary="Логин пользователя",
)
async def login_for_access_token(
    form_data: UserLogin, 
    db: Annotated[AsyncSession, Depends(get_db)]
):
    stmt = select(User).where(User.email == form_data.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неправильный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    access_token = create_access_token(
        data={"user_id": user.id, "role": user.role}, 
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}
    
@router.get(
    "/me", 
    response_model=UserResponse,
    summary="Получение информации о текущем пользователе",
    description="Требует JWT-токен для доступа."
)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)]
):
    return current_user