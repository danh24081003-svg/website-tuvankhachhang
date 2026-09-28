import json
import logging
import os
import time
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import BASE_DIR, get_settings
from app.database import get_db
from app.models import ChatAttachment, ChatMessage, ConsultationState, Conversation, Customer, Lead
from app.schemas import ChatAttachmentOut, ChatMessageOut, ChatRequest, ChatResponse
from app.services.ai_service import AIService, AIServiceError
from app.services.auth_service import is_admin_logged_in
from app.services.knowledge_service import KnowledgeService, get_knowledge_service
from app.services.service_consultation_flows import (
    SERVICE_SPECS,
    extract_attributes,
    extract_location,
    extract_name,
    extract_phone,
    normalize_slug,
)
from app.services.storage_service import optimize_chat_image


router = APIRouter(prefix="/api/chat", tags=["chat"])
_request_log: dict[str, deque[float]] = defaultdict(deque)
logger = logging.getLogger("uvicorn.error")
SAFE_AI_MESSAGE = "Trợ lý đang tạm thời gián đoạn. Anh/chị vui lòng thử lại sau hoặc liên hệ 0901 040 484."
if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
    CHAT_UPLOAD_DIR = Path("/tmp/storage/chat_uploads")
else:
    CHAT_UPLOAD_DIR = BASE_DIR / "storage" / "chat_uploads"

try:
    CHAT_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    CHAT_UPLOAD_DIR = Path("/tmp/storage/chat_uploads")
    CHAT_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _client_key(request: Request, session_id: str) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    ip = forwarded.split(",")[0].strip() or (request.client.host if request.client else "unknown")
    return f"{ip}:{session_id}"


def _rate_limit(request: Request, session_id: str) -> None:
    settings = get_settings()
    now = time.monotonic()
    key = _client_key(request, session_id)
    bucket = _request_log[key]
    while bucket and now - bucket[0] > 60:
        bucket.popleft()
    if len(bucket) >= settings.chat_rate_limit_per_minute:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Anh/chị gửi hơi nhanh ạ. Vui lòng thử lại sau ít phút.",
        )
    bucket.append(now)


def _infer_service_from_text(text: str) -> str | None:
    lowered = text.lower()
    if any(k in lowered for k in ["chuyển nhà", "vận chuyển", "di dời", "xe tải", "chuyển đồ", "dọn trọ"]):
        return "van-chuyen-di-doi"
    if any(k in lowered for k in ["vệ sinh", "dọn dẹp công nghiệp", "chà sàn", "lau kính", "sau xây dựng"]):
        return "ve-sinh-cong-nghiep"
    if any(k in lowered for k in ["sửa chữa", "điện nước", "sơn tường", "chống thấm", "thạch cao"]):
        return "trang-tri-sua-chua"
    if any(k in lowered for k in ["lao động", "công nhân", "bốc xếp", "phụ kho", "nhân lực"]):
        return "cung-cap-quan-ly-lao-dong"
    if any(k in lowered for k in ["giúp việc", "theo giờ", "nấu ăn", "dọn nhà theo giờ"]):
        return "giup-viec"
    if any(k in lowered for k in ["cây cảnh", "cắt tỉa", "sân vườn", "cây xanh", "bón phân"]):
        return "cham-soc-cay-canh"
    if any(k in lowered for k in ["diệt côn trùng", "muỗi", "mối", "chuột", "gián", "kiến"]):
        return "diet-con-trung"
    return None


def _error_response(status_code: int, code: str, message: str, retryable: bool = False) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"success": False, "error": code, "retryable": retryable, "message": message},
    )


def _conversation_title_from_message(message: str) -> str:
    cleaned = " ".join(message.strip().split())
    if not cleaned:
        return "Cuộc trò chuyện mới"
    return cleaned[:77] + "..." if len(cleaned) > 80 else cleaned


def _payload_client_id(payload: dict | None = None, request: Request | None = None) -> str:
    payload = payload or {}
    value = str(payload.get("client_id") or "").strip()
    if not value and request:
        value = str(request.headers.get("x-chat-client-id") or "").strip()
    if len(value) < 8 or len(value) > 80:
        raise HTTPException(status_code=400, detail="Client không hợp lệ")
    return value


def _owned_conversation(db: Session, conversation_id: int, client_id: str) -> Conversation:
    conversation = db.scalars(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.client_id == client_id,
            Conversation.deleted_at.is_(None),
        )
    ).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Không tìm thấy cuộc trò chuyện")
    return conversation


def _ensure_conversation(db: Session, session_id: str, service_slug: str | None = None, client_id: str | None = None) -> Conversation:
    conversation = db.scalars(
        select(Conversation).where(Conversation.session_id == session_id)
    ).first()
    if conversation and conversation.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Cuộc trò chuyện đã bị xóa")
    if not conversation:
        conversation = Conversation(session_id=session_id, client_id=client_id, status="ACTIVE", service_slug=service_slug)
        db.add(conversation)
        db.flush()
    elif conversation.status != "ACTIVE":
        conversation.status = "ACTIVE"
        conversation.ended_at = None
    if client_id and not conversation.client_id:
        conversation.client_id = client_id
    if client_id and conversation.client_id and conversation.client_id != client_id:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập cuộc trò chuyện")
    if service_slug and not conversation.service_slug:
        conversation.service_slug = service_slug
    return conversation


def _format_message_out(message: ChatMessage) -> ChatMessageOut:
    attachment_list: list[ChatAttachmentOut] = []
    if message.attachments:
        try:
            parsed = json.loads(message.attachments)
            if isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict):
                        attachment_list.append(
                            ChatAttachmentOut(
                                id=item.get("id", 0),
                                url=item.get("url") or f"/api/chat/attachments/{item.get('id', 0)}",
                                filename=item.get("filename", "image.webp"),
                                file_size=item.get("file_size", 0),
                                width=item.get("width"),
                                height=item.get("height"),
                            )
                        )
        except Exception:
            pass
    return ChatMessageOut(
        id=message.id,
        session_id=message.session_id,
        client_message_id=message.client_message_id,
        role=message.role,
        message=message.message,
        status=message.status,
        attachments=attachment_list,
        created_at=message.created_at,
    )


@router.post("/upload")
async def upload_chat_images(
    request: Request,
    files: list[UploadFile] = File(...),
    session_id: str = Form(...),
    client_id: str | None = Form(None),
    db: Session = Depends(get_db),
):
    _rate_limit(request, session_id)
    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="Không có tập tin nào được tải lên.")
    if len(files) > 4:
        raise HTTPException(status_code=400, detail="Chỉ được tải lên tối đa 4 hình ảnh mỗi lần.")

    c_id = client_id or str(request.headers.get("x-chat-client-id") or "").strip() or None
    created_attachments: list[ChatAttachment] = []

    for file in files:
        content = await file.read()
        if len(content) == 0:
            continue
        if len(content) > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Hình ảnh '{file.filename or ''}' vượt quá dung lượng cho phép 5MB.",
            )

        optimized_bytes, ext, w, h = optimize_chat_image(content)

        filename = f"{uuid4().hex}.{ext}"
        target_path = CHAT_UPLOAD_DIR / filename
        target_path.write_bytes(optimized_bytes)

        att = ChatAttachment(
            session_id=session_id,
            client_id=c_id,
            filename=file.filename or filename,
            storage_path=str(target_path),
            mime_type=f"image/{ext}",
            file_size=len(optimized_bytes),
            width=w,
            height=h,
        )
        db.add(att)
        db.flush()
        created_attachments.append(att)

    db.commit()
    for att in created_attachments:
        db.refresh(att)

    return [
        {
            "id": att.id,
            "url": f"/api/chat/attachments/{att.id}",
            "filename": att.filename,
            "file_size": att.file_size,
            "width": att.width,
            "height": att.height,
            "created_at": att.created_at.isoformat() if att.created_at else None,
        }
        for att in created_attachments
    ]


@router.get("/attachments/{attachment_id}")
def get_chat_attachment(
    attachment_id: int,
    request: Request,
    session_id: str | None = None,
    client_id: str | None = None,
    db: Session = Depends(get_db),
):
    att = db.get(ChatAttachment, attachment_id)
    if not att:
        raise HTTPException(status_code=404, detail="Hình ảnh không tồn tại.")

    # Ownership check: session_id or client_id or logged-in admin
    header_client_id = str(request.headers.get("x-chat-client-id") or "").strip() or None
    effective_client_id = client_id or header_client_id
    is_owner = (
        (session_id and session_id == att.session_id)
        or (effective_client_id and att.client_id and effective_client_id == att.client_id)
        or is_admin_logged_in(request, db)
    )
    if not is_owner:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập hình ảnh này.")

    path = Path(att.storage_path)
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="File ảnh không tìm thấy trên hệ thống lưu trữ.")

    return FileResponse(path=path, media_type=att.mime_type or "image/webp")


@router.post("", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    request: Request,
    db: Session = Depends(get_db),
    knowledge: KnowledgeService = Depends(get_knowledge_service),
):
    _rate_limit(request, payload.session_id)
    payload.validate_message_or_attachments()
    conversation = _ensure_conversation(db, payload.session_id, payload.service_slug, payload.client_id)

    # 1. Retrieve or initialize ConsultationState
    state = db.scalars(
        select(ConsultationState).where(ConsultationState.session_id == payload.session_id)
    ).first()
    if not state:
        state = ConsultationState(session_id=payload.session_id, status="collecting")
        db.add(state)
        db.flush()

    # Determine service slug
    inferred_slug = _infer_service_from_text(payload.message)
    slug = inferred_slug or normalize_slug(payload.service_slug) or state.service_slug
    if slug:
        state.service_slug = slug
        conversation.service_slug = slug

    service_name = (
        (SERVICE_SPECS.get(inferred_slug, {}).get("name") if inferred_slug else None)
        or payload.service_name
        or (SERVICE_SPECS.get(slug, {}).get("name") if slug else None)
        or "Tư vấn tổng quát"
    )

    # 2. Extract structured info from message
    reqs = json.loads(state.requirements) if state.requirements else {}

    phone = extract_phone(payload.message)
    if phone:
        state.phone = phone
        reqs["phone"] = phone

    name = extract_name(payload.message)
    if name:
        state.customer_name = name
        reqs["customer_name"] = name

    location = extract_location(payload.message)
    if location:
        state.location = location
        reqs["location"] = location

    if slug:
        reqs = extract_attributes(slug, payload.message, reqs)

    # Retrieve attachment records for this session
    attachment_records: list[ChatAttachment] = []
    if payload.attachment_ids:
        attachment_records = db.scalars(
            select(ChatAttachment).where(
                ChatAttachment.id.in_(payload.attachment_ids),
                ChatAttachment.session_id == payload.session_id,
            )
        ).all()
        if attachment_records:
            reqs["has_customer_photos"] = f"Đã gửi {len(attachment_records)} hình ảnh hiện trạng"

    state.requirements = json.dumps(reqs, ensure_ascii=False)
    db.commit()

    # 3. Save user message once. Retry uses the same client_message_id to avoid duplicate DB history.
    user_message = None
    if payload.client_message_id:
        user_message = db.scalars(
            select(ChatMessage).where(
                ChatMessage.session_id == payload.session_id,
                ChatMessage.client_message_id == payload.client_message_id,
                ChatMessage.role == "user",
            )
        ).first()

    attachments_payload_json = None
    if attachment_records:
        attachments_payload_json = json.dumps([
            {
                "id": a.id,
                "url": f"/api/chat/attachments/{a.id}",
                "filename": a.filename,
                "file_size": a.file_size,
                "width": a.width,
                "height": a.height,
            }
            for a in attachment_records
        ], ensure_ascii=False)

    effective_user_text = payload.message.strip()
    if not effective_user_text and attachment_records:
        effective_user_text = "[Hình ảnh đính kèm]"

    if not user_message:
        user_message = ChatMessage(
            session_id=payload.session_id,
            client_message_id=payload.client_message_id,
            role="user",
            message=effective_user_text,
            attachments=attachments_payload_json,
            status="SUCCESS",
        )
        db.add(user_message)
        if conversation.title == "Cuộc trò chuyện mới":
            conversation.title = _conversation_title_from_message(payload.message or "Gửi ảnh tư vấn")
        db.commit()
        db.refresh(user_message)

    # Associate attachments with conversation and message
    for att in attachment_records:
        att.conversation_id = conversation.id
        att.message_id = user_message.id
    db.commit()

    # 4. Check if lead should be created / updated
    lowered = payload.message.lower().strip()
    is_handoff = any(k in lowered for k in ["gặp nhân viên", "gap nhan vien", "nhân viên", "nhan vien", "hotline", "gọi lại", "goi lai"])
    is_confirm = any(k in lowered for k in ["đúng rồi", "dung roi", "chính xác", "chinh xac", "ok em", "đồng ý", "dong y"])

    lead_obj = None
    has_phone = bool(state.phone)
    has_enough_info = has_phone and (len(reqs) >= 1 or bool(slug) or is_handoff or is_confirm or bool(attachment_records))

    if has_enough_info:
        existing_lead = db.scalars(
            select(Lead).where(Lead.session_id == payload.session_id)
        ).first()

        summary_parts = [f"Nhu cầu: {service_name}"]
        for k, v in reqs.items():
            if k not in {"phone", "customer_name"}:
                summary_parts.append(f"{k}: {v}")
        lead_summary = "; ".join(summary_parts)

        customer = db.scalars(select(Customer).where(Customer.phone == state.phone)).first()
        cust_name = state.customer_name or (customer.name if customer else "Khách hàng AI Chat")
        if not customer:
            customer = Customer(name=cust_name, phone=state.phone, address=state.location)
            db.add(customer)
            db.flush()
        else:
            if state.customer_name:
                customer.name = state.customer_name
            if state.location and not customer.address:
                customer.address = state.location
            db.flush()

        if existing_lead:
            existing_lead.service = service_name
            existing_lead.message = lead_summary
            if state.location:
                existing_lead.location = state.location
            existing_lead.requirements = state.requirements
            lead_obj = existing_lead
        else:
            new_lead = Lead(
                customer_id=customer.id,
                service=service_name,
                message=lead_summary,
                status="new",
                source="AI_CHAT",
                session_id=payload.session_id,
                location=state.location,
                requirements=state.requirements,
            )
            db.add(new_lead)
            db.flush()
            lead_obj = new_lead

        state.lead_id = lead_obj.id
        conversation.lead_id = lead_obj.id
        for att in attachment_records:
            att.lead_id = lead_obj.id
        if is_confirm:
            state.status = "completed"
        db.commit()

    # 5. Load image bytes for Gemini Multimodal
    image_bytes_list: list[bytes] = []
    for att in attachment_records:
        path = Path(att.storage_path)
        if path.exists() and path.is_file() and path.stat().st_size > 0:
            image_bytes_list.append(path.read_bytes())

    # Generate reply
    history = db.scalars(
        select(ChatMessage)
        .where(ChatMessage.session_id == payload.session_id)
        .order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc())
    ).all()

    ai_service = AIService(knowledge)
    try:
        reply, quick_actions = await ai_service.generate_reply(
            user_message=payload.message,
            history=history,
            service_slug=slug,
            service_name=service_name,
            current_state=reqs,
            has_phone=has_phone,
            image_bytes_list=image_bytes_list if image_bytes_list else None,
        )
    except AIServiceError as err:
        db.rollback()
        return _error_response(503, err.code, err.safe_message, retryable=err.retryable)
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database error during chat request")
        return _error_response(500, "DATABASE_ERROR", "Hệ thống đang tạm thời gián đoạn. Anh/chị vui lòng thử lại sau.")

    # 6. Save assistant message
    assistant_message = ChatMessage(session_id=payload.session_id, role="assistant", message=reply, status="SUCCESS")
    db.add(assistant_message)
    db.commit()

    return ChatResponse(
        reply=reply,
        quick_actions=quick_actions,
        lead_created=bool(lead_obj),
        lead_id=lead_obj.id if lead_obj else None,
        conversation_id=conversation.id,
        service_context={"slug": slug, "name": service_name} if slug else None,
        attachments=[
            ChatAttachmentOut(
                id=a.id,
                url=f"/api/chat/attachments/{a.id}",
                filename=a.filename,
                file_size=a.file_size,
                width=a.width,
                height=a.height,
            )
            for a in attachment_records
        ],
    )


@router.post("/conversations")
def create_conversation(payload: dict | None = None, request: Request = None, db: Session = Depends(get_db)):
    payload = payload or {}
    client_id = _payload_client_id(payload, request)
    old_session_id = str(payload.get("session_id") or "").strip()
    service_slug = normalize_slug(payload.get("service_slug")) if payload.get("service_slug") else None

    try:
        if old_session_id:
            old_conversation = db.scalars(
                select(Conversation).where(Conversation.session_id == old_session_id)
            ).first()
            if old_conversation and old_conversation.client_id and old_conversation.client_id != client_id:
                raise HTTPException(status_code=403, detail="Không có quyền truy cập cuộc trò chuyện")
            if old_conversation and not old_conversation.client_id:
                old_conversation.client_id = client_id
            if old_conversation and old_conversation.status == "ACTIVE":
                old_conversation.status = "ENDED"
                old_conversation.ended_at = datetime.utcnow()

            old_state = db.scalars(
                select(ConsultationState).where(ConsultationState.session_id == old_session_id)
            ).first()
            if old_state and old_state.status != "completed":
                old_state.status = "ended"

        new_session_id = f"chat-{uuid4()}"
        conversation = Conversation(
            session_id=new_session_id,
            client_id=client_id,
            title="Cuộc trò chuyện mới",
            status="ACTIVE",
            service_slug=service_slug,
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Could not create new chat conversation")
        return _error_response(500, "CONVERSATION_CREATE_FAILED", "Chưa thể bắt đầu cuộc trò chuyện mới. Vui lòng thử lại.")

    return {
        "conversation_id": conversation.id,
        "session_id": conversation.session_id,
        "title": conversation.title,
        "status": conversation.status,
    }


@router.get("/conversations")
def list_conversations(client_id: str, db: Session = Depends(get_db)):
    if len(client_id) < 8 or len(client_id) > 80:
        raise HTTPException(status_code=400, detail="Client không hợp lệ")
    rows = db.execute(
        select(
            Conversation,
            func.count(ChatMessage.id).label("message_count"),
            func.max(ChatMessage.created_at).label("last_message_at"),
        )
        .join(ChatMessage, ChatMessage.session_id == Conversation.session_id, isouter=True)
        .where(Conversation.client_id == client_id, Conversation.deleted_at.is_(None))
        .group_by(Conversation.id)
        .order_by(func.coalesce(func.max(ChatMessage.created_at), Conversation.updated_at).desc())
    ).all()
    return [
        {
            "conversation_id": conversation.id,
            "session_id": conversation.session_id,
            "title": conversation.title,
            "status": conversation.status,
            "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
            "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None,
            "last_message_at": last_message_at.isoformat() if last_message_at else None,
            "message_count": message_count,
        }
        for conversation, message_count, last_message_at in rows
    ]


@router.get("/conversations/{conversation_id}/messages", response_model=list[ChatMessageOut])
def get_conversation_messages(conversation_id: int, client_id: str, db: Session = Depends(get_db)):
    conversation = _owned_conversation(db, conversation_id, client_id)
    messages = db.scalars(
        select(ChatMessage)
        .where(ChatMessage.session_id == conversation.session_id)
        .order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc())
    ).all()
    return [_format_message_out(m) for m in messages]


@router.patch("/conversations/{conversation_id}")
def rename_conversation(conversation_id: int, payload: dict | None = None, request: Request = None, db: Session = Depends(get_db)):
    payload = payload or {}
    client_id = _payload_client_id(payload, request)
    title = str(payload.get("title") or "").strip()
    if not title:
        raise HTTPException(status_code=422, detail="Tên cuộc trò chuyện không được rỗng")
    if len(title) > 80:
        raise HTTPException(status_code=422, detail="Tên cuộc trò chuyện tối đa 80 ký tự")
    conversation = _owned_conversation(db, conversation_id, client_id)
    conversation.title = title
    conversation.updated_at = datetime.utcnow()
    db.commit()
    return {"success": True, "conversation_id": conversation.id, "session_id": conversation.session_id, "title": conversation.title}


@router.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: int, payload: dict | None = None, request: Request = None, db: Session = Depends(get_db)):
    payload = payload or {}
    client_id = _payload_client_id(payload, request)
    active_session_id = str(payload.get("active_session_id") or "").strip()
    service_slug = normalize_slug(payload.get("service_slug")) if payload.get("service_slug") else None
    conversation = _owned_conversation(db, conversation_id, client_id)

    try:
        now = datetime.utcnow()
        conversation.deleted_at = now
        conversation.status = "ENDED"
        conversation.ended_at = conversation.ended_at or now

        old_state = db.scalars(
            select(ConsultationState).where(ConsultationState.session_id == conversation.session_id)
        ).first()
        if old_state and old_state.status != "completed":
            old_state.status = "ended"

        replacement = None
        if active_session_id and active_session_id == conversation.session_id:
            replacement = Conversation(
                session_id=f"chat-{uuid4()}",
                client_id=client_id,
                title="Cuộc trò chuyện mới",
                status="ACTIVE",
                service_slug=service_slug,
            )
            db.add(replacement)

        db.commit()
        if replacement:
            db.refresh(replacement)
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Could not delete chat conversation")
        return _error_response(500, "CONVERSATION_DELETE_FAILED", "Chưa thể xóa cuộc trò chuyện. Vui lòng thử lại.")

    response = {"success": True, "deleted_conversation_id": conversation.id}
    if replacement:
        response.update(
            {
                "conversation_id": replacement.id,
                "session_id": replacement.session_id,
                "title": replacement.title,
                "status": replacement.status,
            }
        )
    return response


@router.get("/{session_id}/messages", response_model=list[ChatMessageOut])
def get_messages(session_id: str, db: Session = Depends(get_db)):
    if len(session_id) < 8 or len(session_id) > 80:
        raise HTTPException(status_code=400, detail="Session không hợp lệ")
    messages = db.scalars(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc())
    ).all()
    return [_format_message_out(m) for m in messages]


@router.get("/status")
async def chat_ai_status(knowledge: KnowledgeService = Depends(get_knowledge_service)):
    """
    Returns AI status without exposing any sensitive credentials or secrets.
    """
    service = AIService(knowledge)
    return await service.check_status()
