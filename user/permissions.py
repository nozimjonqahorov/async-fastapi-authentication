from fastapi import  Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from db import get_db
from user.models import User
from user.security import decode_token
from datetime import datetime

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")



async def is_authenticated(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):

    payload = decode_token(token)

    error = HTTPException(
        detail="UNAUTHORIZED",
        status_code=status.HTTP_401_UNAUTHORIZED
    )

    if payload is None:
        raise error

    if payload.get("type") != "access":
        raise error

    user_id = payload.get("sub")

    if user_id is None:
        raise error

    user = await db.get(User, int(user_id))

    if user is None:
        raise error

    exp = payload.get("exp")

    if exp is None:
        raise error

    if datetime.fromtimestamp(exp) < datetime.now():
        raise HTTPException(
            detail="Token muddati tugagan",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    return True


async def is_superuser(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):

    payload = decode_token(token)

    error = HTTPException(
        detail="UNAUTHORIZED",
        status_code=status.HTTP_401_UNAUTHORIZED
    )

    if payload is None:
        raise error

    if payload.get("type") != "access":
        raise error

    user_id = payload.get("sub")

    if user_id is None:
        raise error

    user = await db.get(User, int(user_id))

    if user is None:
        raise error

    exp = payload.get("exp")

    if exp is None:
        raise error

    if datetime.fromtimestamp(exp) < datetime.now():
        raise HTTPException(
            detail="Token muddati tugagan",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    if not user.is_superuser:
        raise HTTPException(
            detail="Bu amal uchun superuser huquqi kerak",
            status_code=status.HTTP_403_FORBIDDEN
        )

    return True