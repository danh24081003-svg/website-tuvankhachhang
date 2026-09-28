import argparse
import getpass
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from sqlalchemy import select  # noqa: E402

from app.database import SessionLocal, init_db  # noqa: E402
from app.models import AdminUser  # noqa: E402
from app.services.auth_service import hash_password  # noqa: E402


def main() -> None:
    init_db()
    parser = argparse.ArgumentParser(description="Tạo hoặc cập nhật tài khoản quản trị website Oshin Thời Đại")
    parser.add_argument("--email", help="Email đăng nhập admin")
    parser.add_argument("--password", help="Mật khẩu admin")
    args = parser.parse_args()

    email = args.email or os.getenv("ADMIN_EMAIL")
    if not email:
        email = input("Email: ").strip().lower()
    else:
        email = email.strip().lower()

    if not email:
        raise SystemExit("Email không được để trống.")

    password = args.password or os.getenv("ADMIN_PASSWORD")
    if not password:
        if sys.stdin.isatty():
            password = getpass.getpass("Password: ")
            confirm = getpass.getpass("Confirm password: ")
        else:
            password = sys.stdin.readline().rstrip("\r\n")
            confirm = sys.stdin.readline().rstrip("\r\n")
        if password != confirm:
            raise SystemExit("Mật khẩu xác nhận không khớp.")
    if len(password) < 8:
        raise SystemExit("Mật khẩu nên có ít nhất 8 ký tự.")

    with SessionLocal() as db:
        existing = db.scalars(select(AdminUser).where(AdminUser.email == email)).first()
        if existing:
            existing.password_hash = hash_password(password)
            existing.is_active = True
            print(f"Đã cập nhật mật khẩu cho tài khoản admin: {email}")
        else:
            db.add(AdminUser(email=email, password_hash=hash_password(password), is_active=True))
            print(f"Đã tạo tài khoản admin thành công: {email}")
        db.commit()


if __name__ == "__main__":
    main()
