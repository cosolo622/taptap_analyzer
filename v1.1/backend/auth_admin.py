# -*- coding: utf-8 -*-
import os
import uuid
import secrets
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
_admin_sessions = {}
_admin_session_ttl = timedelta(hours=12)


def extract_admin_token(authorization: Optional[str], x_admin_token: Optional[str]) -> Optional[str]:
    if x_admin_token:
        return x_admin_token.strip()
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    return None


def verify_admin(authorization: Optional[str], x_admin_token: Optional[str]) -> str:
    token = extract_admin_token(authorization, x_admin_token)
    if not token:
        raise HTTPException(status_code=401, detail="请先登录管理员账号")
    expires_at = _admin_sessions.get(token)
    if not expires_at or expires_at < datetime.now():
        _admin_sessions.pop(token, None)
        raise HTTPException(status_code=401, detail="管理员登录已过期，请重新登录")
    return token


def admin_login(password: str):
    if not secrets.compare_digest(password, ADMIN_PASSWORD):
        raise HTTPException(status_code=401, detail="管理员密码错误")
    token = uuid.uuid4().hex
    expires_at = datetime.now() + _admin_session_ttl
    _admin_sessions[token] = expires_at
    return token, expires_at


def admin_logout(authorization: Optional[str], x_admin_token: Optional[str]):
    token = extract_admin_token(authorization, x_admin_token)
    if token:
        _admin_sessions.pop(token, None)
