from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import select
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from db import get_db
from user.schemas import RefreshTokenRequest
from user.models import User, BlackList
from user.schemas import UserCreate, Token, ChangeProfileSchema, UserResponse, PasswordChangeSchema, LogoutSchema
from user.permissions import is_authenticated
from user.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)

router = APIRouter()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    
    result = await db.execute(
        select(User).where(
            (User.username == user_in.username) | (User.email == user_in.email)
        )
    )
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu username yoki email allaqachon mavjud",
        )

    new_user = User(
        username=user_in.username,
        email=user_in.email,
        password=hash_password(user_in.password),
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return {"msg": 'User created', 
            'username':new_user.username}
    


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username yoki parol noto'g'ri",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Foydalanuvchi faol emas"
        )

    token_payload = {"sub": str(user.id)}
    access_token = create_access_token(token_payload)
    refresh_token = create_refresh_token(token_payload)

    return  Token(access_token=access_token, refresh_token=refresh_token)
    


@router.post("/refresh", response_model=Token)
async def refresh_access_token(data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(str(data.refresh_token))

    result = await db.execute(select(BlackList).where(BlackList.refresh == data.refresh_token))
    token = result.scalar_one_or_none()

    if token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token yaroqsiz yoki muddati o'tgan",
        )

    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token yaroqsiz yoki muddati o'tgan",
        )

    user_id = payload.get("sub")
    token_payload = {"sub": str(user_id)}
    new_access_token = create_access_token(token_payload)
    new_refresh_token = create_refresh_token(token_payload)

    return Token(access_token=new_access_token, refresh_token=new_refresh_token)

async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Tizimga kirish tasdiqlanmadi",
    )

    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception

    return user


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch('/update-profile', response_model=UserResponse, status_code=200)
async def update_profile(new_data : ChangeProfileSchema, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    
    data = new_data.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(current_user, key, value)

    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.patch('/change-password', status_code=200)
async def change_password(new_data : PasswordChangeSchema, current_user : User = Depends(get_current_user), db : AsyncSession = Depends(get_db)):
    if not verify_password(new_data.old_password, current_user.password):
        raise HTTPException(detail="Eski parol xato", status_code=400)
    
    if verify_password(new_data.new_password, current_user.password):
        raise HTTPException(detail="Yangi parol eskisidan farq qilishi kerak", status_code=400)

    if new_data.new_password != new_data.confirm_password:
        raise HTTPException(detail="Parollar mos emas", status_code=400)
    
    current_user.password = hash_password(new_data.new_password)

    await db.commit()
    await db.refresh(current_user)
    return {
        "msg":"Parol uzgartirildi"
    }


@router.post('/logout')
async def logout(data: LogoutSchema, db: AsyncSession = Depends(get_db), _: None = Depends(is_authenticated)):
    payload = decode_token(data.refresh)

    type = payload.get('type')
    if type is None or type != 'refresh':
        raise HTTPException(detail='Refresh is not valid', status_code=status.HTTP_400_BAD_REQUEST)

    refresh_token = await db.execute(select(BlackList).where(BlackList.refresh == data.refresh))
    token = refresh_token.scalar_one_or_none()

    if token:
        raise HTTPException(detail='Refresh is not valid', status_code=status.HTTP_400_BAD_REQUEST)

    refresh = BlackList(refresh=data.refresh, exp_time=datetime.fromtimestamp(payload.get('exp')))

    db.add(refresh)

    await db.commit()
    await db.refresh(refresh)

    return {
        'msg': 'Logout',
        'status': status.HTTP_200_OK
    }