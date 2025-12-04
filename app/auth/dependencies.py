from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.schemas import TokenData
from app.database import get_db
from app.models import User
from app.auth.security import SECRET_KEY, ALGORITHM 

security_scheme = HTTPBearer(auto_error=True)

async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security_scheme)], 
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    
    token = credentials.credentials
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Токен недействителен или отсутствует",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        user_role: str = payload.get("role")
        
        if user_id is None or user_role is None:
            raise credentials_exception
        
        token_data = TokenData(user_id=user_id, role=user_role)
    except JWTError:
        raise credentials_exception

    stmt = select(User).where(User.id == token_data.user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    return user

def require_role(role: str):
    def role_checker(current_user: Annotated[User, Depends(get_current_user)]):
        if current_user.role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Недостаточно прав. Требуется роль: {role}"
            )
        return current_user
    return role_checker