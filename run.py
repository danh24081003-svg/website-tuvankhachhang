import uvicorn
from app.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    print(f"==================================================")
    print(f"OSHIN THOI DAI SERVICE PLATFORM")
    print(f"Server starting on http://{settings.host}:{settings.port}")
    print(f"Admin Dashboard: http://{settings.host}:{settings.port}/admin")
    print(f"Services Index:  http://{settings.host}:{settings.port}/dich-vu")
    print(f"==================================================")
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
