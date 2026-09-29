import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.config import BASE_DIR


DATA_DIR = BASE_DIR / "data"
DEFAULT_KNOWLEDGE: dict[str, Any] = {
    "company.json": {
        "company_name": "Oshin Thoi Dai",
        "brand_name": "Oshin Thoi Dai",
        "hotline": "0901 040 484",
        "email": "",
        "address": "",
        "working_hours": "",
        "slogan": "",
    },
    "services.json": [],
    "pricing.json": [],
    "faq.json": [],
}


class KnowledgeService:
    def __init__(self, data_dir: Path = DATA_DIR) -> None:
        self.data_dir = data_dir

    def _load_json(self, filename: str) -> Any:
        try:
            file_path = self.data_dir / filename
            if file_path.exists() and file_path.is_file():
                with file_path.open("r", encoding="utf-8") as file:
                    return json.load(file)
        except Exception:
            pass
        default_value = DEFAULT_KNOWLEDGE.get(filename, [])
        if isinstance(default_value, dict):
            return dict(default_value)
        return list(default_value)

    def services(self) -> list[dict[str, Any]]:
        return self._load_json("services.json")

    def pricing(self) -> list[dict[str, Any]]:
        return self._load_json("pricing.json")

    def company(self) -> dict[str, Any]:
        return self._load_json("company.json")

    def faq(self) -> list[dict[str, Any]]:
        return self._load_json("faq.json")

    def all_context(self) -> dict[str, Any]:
        return {
            "company": self.company(),
            "services": self.services(),
            "pricing": self.pricing(),
            "faq": self.faq(),
        }


@lru_cache
def get_knowledge_service() -> KnowledgeService:
    return KnowledgeService()
