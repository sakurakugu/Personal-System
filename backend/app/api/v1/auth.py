"""认证路由：登录、注册、刷新、登出。

此模块提供用户认证相关的接口，包括：
- 用户注册
- 用户登录（返回 access_token 和 refresh_token）
- Token 刷新
- 用户登出
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.redis import get_redis
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.api.deps import get_current_user
from app.models.models import SYSTEM_SETTING_REGISTER_ENABLED, SystemSetting, User
from app.schemas.schemas import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserRead,
)

# 创建路由器，前缀为 /auth，标签为 auth
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    用户注册。

    检查注册是否开放，验证用户名和邮箱是否已存在。

    Args:
        body: 注册请求数据（用户名、邮箱、密码等）
        db: 数据库会话

    Returns:
        UserRead: 创建的用户信息

    Raises:
        HTTPException: 403 - 注册已关闭
        HTTPException: 409 - 用户名或邮箱已被使用
    """
    # 检查注册是否关闭
    setting = await db.get(SystemSetting, SYSTEM_SETTING_REGISTER_ENABLED)
    if setting is not None and setting.bool_value is False:
        raise HTTPException(status_code=403, detail="注册已关闭")
    # 检查重复
    exists = await db.execute(
        select(User).where((User.username == body.username) | (User.email == body.email))
    )
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="用户名或邮箱已被使用")
    user = User(
        username=body.username,
        nickname=(body.nickname.strip() if body.nickname and body.nickname.strip() else body.username),
        email=body.email,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    用户登录。

    验证用户名和密码，返回 access_token 和 refresh_token。

    Args:
        body: 登录请求数据（用户名、密码）
        db: 数据库会话

    Returns:
        TokenResponse: 包含 access_token 和 refresh_token

    Raises:
        HTTPException: 401 - 用户名或密码错误
        HTTPException: 403 - 账号已被禁用
    """
    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已被禁用")
    access = create_access_token(str(user.id), extra={"role": user.role.value})
    refresh = create_refresh_token(str(user.id))
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest):
    """
    刷新访问令牌。

    使用 refresh_token 获取新的 access_token 和 refresh_token。
    旧的 refresh_token 会被加入黑名单，不可再次使用。

    Args:
        body: 刷新请求数据（refresh_token）

    Returns:
        TokenResponse: 新的 access_token 和 refresh_token

    Raises:
        HTTPException: 401 - 无效的刷新令牌
    """
    from jose import JWTError
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="无效的令牌类型")
        user_id = payload["sub"]
    except (JWTError, KeyError):
        raise HTTPException(status_code=401, detail="无效的刷新令牌")

    # 将旧刷新 token 加入黑名单
    redis = await get_redis()
    ttl = settings.JWT_REFRESH_EXPIRE_DAYS * 86400
    await redis.setex(f"bl:{body.refresh_token}", ttl, "1")

    access = create_access_token(user_id)
    new_refresh = create_refresh_token(user_id)
    return TokenResponse(access_token=access, refresh_token=new_refresh)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(user: User = Depends(get_current_user)):
    """
    用户登出。

    当前实现仅依赖客户端丢弃 token。
    实际生产环境中应将 access token 也加入黑名单。

    Args:
        user: 当前登录用户（依赖注入）

    Returns:
        None
    """
    # 实际场景中还应将访问 token 加入黑名单
    # 此处仅客户端丢弃 token
    return
