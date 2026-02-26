"""Authentication endpoints and logic."""

import logging
import os
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

import bcrypt
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from telegram_rutor_bot.config import settings
from telegram_rutor_bot.db import get_async_db
from telegram_rutor_bot.db.models import User
from telegram_rutor_bot.schemas import UserResponse

# Configuration
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 3000

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/auth/login')
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl='/api/auth/login', auto_error=False)

router = APIRouter(prefix='/api/auth', tags=['auth'])
log = logging.getLogger(__name__)

# Temporary storage for TFA codes (In-memory)
tfa_codes: dict[str, str] = {}


class Token(BaseModel):
    """Token response model."""

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token payload data."""

    username: str | None = None


class TfaRequest(BaseModel):
    """2FA verification request."""

    username: str
    code: str


def verify_password(plain_password: str, hashed_password: str | None) -> bool:
    """Verify a password against a hash."""
    if not hashed_password:
        return False
    try:
        # bcrypt.checkpw requires bytes
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        # Fallback for legacy plain text passwords if any remain (optional, but safe to keep logic simple)
        return plain_password == hashed_password


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create JWT token."""
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta if expires_delta else timedelta(minutes=15))
    to_encode.update({'exp': expire})
    return str(jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM))


async def verify_token_and_get_user(token: str, session: AsyncSession) -> User:
    """Verify token and retrieve user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    try:
        log.info('Verifying token: %s...', token[:10])
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        username: str | None = payload.get('sub')
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError as e:
        log.error('JWT Error: %s', e)
        raise credentials_exception from e

    result = await session.execute(select(User).where(User.username == token_data.username))
    user = result.scalars().first()

    if user is None:
        log.error('User %s not found', token_data.username)
        raise credentials_exception
    return user


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], session: AsyncSession = Depends(get_async_db)
) -> User:
    """Get current authenticated user."""
    return await verify_token_and_get_user(token, session)


async def get_current_admin_if_configured(
    token: Annotated[str | None, Depends(oauth2_scheme_optional)], session: AsyncSession = Depends(get_async_db)
) -> User | None:
    """Get current admin if configured."""
    # Only enforce if configured
    if not settings.is_configured:
        return None

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Not authenticated',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    user = await verify_token_and_get_user(token, session)
    if not user.is_authorized or not user.is_admin:
        raise HTTPException(status_code=403, detail='Forbidden')
    return user


def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """Get current active user."""
    if not current_user.is_authorized:
        raise HTTPException(status_code=400, detail='Inactive user')
    return current_user


def get_current_admin_user(current_user: Annotated[User, Depends(get_current_active_user)]) -> User:
    """Get current admin user."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail='Not enough permissions')
    return current_user


async def send_telegram_code(chat_id: int, code: str) -> None:
    """Send TFA code to Telegram."""
    async with httpx.AsyncClient() as client:
        url = f'https://api.telegram.org/bot{settings.telegram_token}/sendMessage'
        await client.post(url, json={'chat_id': chat_id, 'text': f'Your authentication code is: {code}'})


@router.post('/login')
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session: AsyncSession = Depends(get_async_db)
) -> dict[str, Any]:
    """Login endpoint."""
    # Try to find by username
    result = await session.execute(select(User).where(User.username == form_data.username))
    user = result.scalars().first()

    # If not found, trying mapping provided username to chat_id if possible?
    # For now, stick to strict username.

    if not user:
        raise HTTPException(status_code=400, detail='Incorrect username or password')

    if not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=400, detail='Incorrect username or password')

    if not user.is_authorized:
        raise HTTPException(status_code=400, detail='User not authorized')

    if not user.is_admin:
        raise HTTPException(status_code=403, detail='Only admins can login')

    # If using legacy password, maybe upgrade it here?
    # Skipping for simplicity, but good practice would be:
    # if user.password == form_data.password:
    #     user.password = get_password_hash(form_data.password)
    #     await session.commit()

    if user.is_tfa_enabled:
        if not user.username:
            log.error('User with TFA enabled has no username')
            raise HTTPException(status_code=500, detail='Internal Auth Error')

        code = secrets.token_hex(3).upper()
        tfa_codes[user.username] = code
        log.info('TESTING MFA CODE for %s: %s', user.username, code)
        try:
            await send_telegram_code(user.chat_id, code)
        except Exception as e:  # pylint: disable=broad-exception-caught
            log.error('Failed to send TFA code: %s', e)

        return {'tfa_required': True, 'username': user.username}

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={'sub': user.username}, expires_delta=access_token_expires)
    return {'access_token': access_token, 'token_type': 'bearer'}


@router.post('/verify-tfa', response_model=Token)
async def verify_tfa(request: TfaRequest, session: AsyncSession = Depends(get_async_db)) -> dict[str, str]:
    """Verify TFA code."""
    expected_code = tfa_codes.get(request.username)
    if not expected_code:
        raise HTTPException(status_code=400, detail='Code expired or invalid request')

    if expected_code != request.code.upper():
        raise HTTPException(status_code=400, detail='Invalid code')

    del tfa_codes[request.username]

    result = await session.execute(select(User).where(User.username == request.username))
    user = result.scalars().first()

    if not user or not user.is_authorized:
        raise HTTPException(status_code=400, detail='User invalid')

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={'sub': user.username}, expires_delta=access_token_expires)
    return {'access_token': access_token, 'token_type': 'bearer'}


if os.environ.get('DEBUG', 'false').lower() == 'true':

    @router.get('/debug-tfa/{username}', include_in_schema=False)
    async def get_debug_tfa_code(username: str) -> dict[str, str]:
        """Debug endpoint to get the current TFA code for a user."""
        code = tfa_codes.get(username)
        if not code:
            raise HTTPException(status_code=404, detail='No code found for user')
        return {'code': code}


@router.get('/me', response_model=UserResponse)
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """Get current user."""
    return current_user
