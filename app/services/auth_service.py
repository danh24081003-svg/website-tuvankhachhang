import hashlib
import hmac
import secrets
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import AdminSession, AdminUser, SiteUser, UserSession


SESSION_COOKIE = "oshin_admin_session"
CSRF_COOKIE = "oshin_admin_csrf"
CSRF_HEADER = "x-csrf-token"
USER_SESSION_COOKIE = "oshin_user_session"


def _bcrypt():
    try:
        import bcrypt
    except ModuleNotFoundError as exc:
        raise RuntimeError("bcrypt is required. Install dependencies from requirements.txt.") from exc
    return bcrypt


def hash_password(password: str) -> str:
    bcrypt = _bcrypt()
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    bcrypt = _bcrypt()
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_admin_session(db: Session, user: AdminUser, response: Response) -> None:
    settings = get_settings()
    token = secrets.token_urlsafe(48)
    csrf_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(minutes=settings.admin_session_minutes)
    db.add(AdminSession(user_id=user.id, token_hash=hash_token(token), csrf_token=csrf_token, expires_at=expires_at))
    user.last_login = datetime.utcnow()
    db.commit()

    secure = settings.environment.lower() == "production"
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=settings.admin_session_minutes * 60,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        CSRF_COOKIE,
        csrf_token,
        max_age=settings.admin_session_minutes * 60,
        httponly=False,
        secure=secure,
        samesite="lax",
        path="/",
    )


def create_user_session(db: Session, user: SiteUser, response: Response) -> None:
    settings = get_settings()
    token = secrets.token_urlsafe(48)
    expires_at = datetime.utcnow() + timedelta(days=30)
    db.add(UserSession(user_id=user.id, token_hash=hash_token(token), expires_at=expires_at))
    user.last_login = datetime.utcnow()
    db.commit()

    secure = settings.environment.lower() == "production"
    response.set_cookie(
        USER_SESSION_COOKIE,
        token,
        max_age=30 * 24 * 60 * 60,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
    )


def clear_admin_session(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/")
    response.delete_cookie(CSRF_COOKIE, path="/")


def clear_user_session(response: Response) -> None:
    response.delete_cookie(USER_SESSION_COOKIE, path="/")


def _session_from_request(request: Request, db: Session) -> AdminSession:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Chưa đăng nhập")
    session = db.scalars(select(AdminSession).where(AdminSession.token_hash == hash_token(token))).first()
    if not session or session.expires_at <= datetime.utcnow() or not session.user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Phiên đăng nhập không hợp lệ")
    return session


def require_admin(request: Request, db: Session = Depends(get_db)) -> AdminUser:
    session = _session_from_request(request, db)
    return session.user


def require_admin_with_csrf(request: Request, db: Session = Depends(get_db)) -> AdminUser:
    session = _session_from_request(request, db)
    header_token = request.headers.get(CSRF_HEADER, "")
    cookie_token = request.cookies.get(CSRF_COOKIE, "")
    if not header_token or not cookie_token or not hmac.compare_digest(header_token, session.csrf_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token không hợp lệ")
    if not hmac.compare_digest(cookie_token, session.csrf_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token không hợp lệ")
    return session.user


def is_admin_logged_in(request: Request, db: Session) -> bool:
    try:
        token = request.cookies.get(SESSION_COOKIE)
        if not token:
            return False
        session = db.scalars(select(AdminSession).where(AdminSession.token_hash == hash_token(token))).first()
        if not session or session.expires_at <= datetime.utcnow() or not session.user.is_active:
            return False
        return True
    except Exception:
        return False


def get_current_user(request: Request, db: Session = Depends(get_db)) -> SiteUser | None:
    token = request.cookies.get(USER_SESSION_COOKIE)
    if not token:
        return None
    session = db.scalars(select(UserSession).where(UserSession.token_hash == hash_token(token))).first()
    if not session or session.expires_at <= datetime.utcnow() or not session.user.is_active:
        return None
    return session.user

