import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.config import BASE_DIR


DATA_DIR = BASE_DIR / "data"


class KnowledgeService:
    def __init__(self, data_dir: Path = DATA_DIR) -> None:
        self.data_dir = data_dir

    def _load_json(self, filename: str) -> Any:
        file_path = self.data_dir / filename
        with file_path.open("r", encoding="utf-8") as file:
            return json.load(file)

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
