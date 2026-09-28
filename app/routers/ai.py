from fastapi import APIRouter, Depends
from app.services.ai_service import AIService
from app.services.knowledge_service import KnowledgeService, get_knowledge_service

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.get("/status")
async def ai_status(knowledge: KnowledgeService = Depends(get_knowledge_service)):
    """
    Returns AI status without exposing any sensitive credentials or secrets.
    """
    service = AIService(knowledge)
    return await service.check_status()
