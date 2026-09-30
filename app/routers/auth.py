import json
import secrets
from datetime import datetime
from urllib.parse import urlencode

import requests
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import BASE_DIR, get_settings
from app.database import get_db
from app.models import AdminUser, SiteUser, UserSession
from app.services.auth_service import (
    USER_SESSION_COOKIE,
    clear_user_session,
    create_admin_session,
    create_user_session,
    get_current_user,
    hash_password,
    hash_token,
)


router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
GOOGLE_STATE_COOKIE = "oshin_google_oauth_state"
GOOGLE_NEXT_COOKIE = "oshin_google_oauth_next"


def _redirect_uri(request: Request) -> str:
    settings = get_settings()
    if settings.google_redirect_uri:
        return settings.google_redirect_uri
    base_url = settings.app_url.rstrip("/") if settings.app_url else str(request.base_url).rstrip("/")
    return f"{base_url}/auth/google/callback"


def _google_configured() -> bool:
    settings = get_settings()
    return bool(settings.google_client_id and settings.google_client_secret)


def user_out(user: SiteUser) -> dict:
    try:
        permissions = json.loads(user.permissions or "[]")
    except json.JSONDecodeError:
        permissions = []
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "avatar_url": user.avatar_url or "",
        "role": user.role,
        "permissions": permissions if isinstance(permissions, list) else [],
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        "last_login": user.last_login.isoformat() if user.last_login else None,
    }


@router.get("/login", response_class=HTMLResponse)
def user_login_page(request: Request, user: SiteUser | None = Depends(get_current_user)):
    if user:
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse(request, "user_login.html", {"google_configured": _google_configured()})


@router.get("/auth/google/start")
def google_start(request: Request, next: str = ""):
    settings = get_settings()
    if not _google_configured():
        raise HTTPException(status_code=503, detail="Google login chưa được cấu hình.")

    state = secrets.token_urlsafe(32)
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": _redirect_uri(request),
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    }
    response = RedirectResponse(f"{GOOGLE_AUTH_URL}?{urlencode(params)}", status_code=302)
    secure = settings.environment.lower() == "production"
    response.set_cookie(
        GOOGLE_STATE_COOKIE,
        state,
        max_age=10 * 60,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
    )
    if next == "admin":
        response.set_cookie(
            GOOGLE_NEXT_COOKIE,
            "admin",
            max_age=10 * 60,
            httponly=True,
            secure=secure,
            samesite="lax",
            path="/",
        )
    else:
        response.delete_cookie(GOOGLE_NEXT_COOKIE, path="/")
    return response


@router.get("/auth/google/callback")
def google_callback(request: Request, response: Response, code: str = "", state: str = "", db: Session = Depends(get_db)):
    settings = get_settings()
    expected_state = request.cookies.get(GOOGLE_STATE_COOKIE, "")
    if not code or not state or not expected_state or not secrets.compare_digest(state, expected_state):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phiên đăng nhập Google không hợp lệ.")
    if not _google_configured():
        raise HTTPException(status_code=503, detail="Google login chưa được cấu hình.")

    try:
        token_response = requests.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": _redirect_uri(request),
                "grant_type": "authorization_code",
            },
            timeout=15,
        )
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail="Máy chủ local chưa kết nối được Google OAuth. Vui lòng kiểm tra quyền network/firewall rồi thử lại.") from exc
    if not token_response.ok:
        raise HTTPException(status_code=502, detail="Không thể xác thực với Google.")
    token_data = token_response.json()
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=502, detail="Google không trả về access token.")

    try:
        userinfo_response = requests.get(GOOGLE_USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"}, timeout=15)
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail="Máy chủ local chưa lấy được thông tin tài khoản Google. Vui lòng kiểm tra quyền network/firewall rồi thử lại.") from exc
    if not userinfo_response.ok:
        raise HTTPException(status_code=502, detail="Không thể lấy thông tin tài khoản Google.")
    profile = userinfo_response.json()
    email = str(profile.get("email") or "").strip().lower()
    google_sub = str(profile.get("sub") or "").strip()
    if not email or not google_sub:
        raise HTTPException(status_code=400, detail="Tài khoản Google không có email hợp lệ.")

    user = db.scalars(select(SiteUser).where((SiteUser.google_sub == google_sub) | (SiteUser.email == email))).first()
    if not user:
        user = SiteUser(
            email=email,
            google_sub=google_sub,
            name=str(profile.get("name") or email).strip(),
            avatar_url=str(profile.get("picture") or "").strip() or None,
            role="customer",
            permissions="[]",
            is_active=True,
        )
        db.add(user)
    else:
        user.google_sub = user.google_sub or google_sub
        user.name = str(profile.get("name") or user.name or email).strip()
        user.avatar_url = str(profile.get("picture") or user.avatar_url or "").strip() or None
        user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tài khoản đã bị khóa.")

    admin_required = request.cookies.get(GOOGLE_NEXT_COOKIE) == "admin"
    is_admin_user = user.role == "admin"
    if admin_required and not is_admin_user:
        redirect = RedirectResponse("/admin/login?error=not_admin", status_code=302)
        redirect.delete_cookie(GOOGLE_STATE_COOKIE, path="/")
        redirect.delete_cookie(GOOGLE_NEXT_COOKIE, path="/")
        return redirect

    redirect_target = "/admin?login=success" if is_admin_user else "/?login=success"
    redirect = RedirectResponse(redirect_target, status_code=302)
    redirect.delete_cookie(GOOGLE_STATE_COOKIE, path="/")
    redirect.delete_cookie(GOOGLE_NEXT_COOKIE, path="/")
    create_user_session(db, user, redirect)
    if is_admin_user:
        admin_user = db.scalars(select(AdminUser).where(AdminUser.email == user.email)).first()
        if not admin_user:
            admin_user = AdminUser(
                email=user.email,
                password_hash=hash_password(secrets.token_urlsafe(48)),
                is_active=True,
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
        elif not admin_user.is_active:
            admin_user.is_active = True
            db.commit()
            db.refresh(admin_user)
        create_admin_session(db, admin_user, redirect)
    return redirect


@router.get("/api/auth/me")
def auth_me(user: SiteUser | None = Depends(get_current_user)):
    return {"authenticated": bool(user), "user": user_out(user) if user else None}


@router.post("/api/auth/logout")
def auth_logout(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(USER_SESSION_COOKIE)
    if token:
        session = db.scalars(select(UserSession).where(UserSession.token_hash == hash_token(token))).first()
        if session:
            db.delete(session)
            db.commit()
    clear_user_session(response)
    return {"ok": True}
