from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _strip_text(value: str) -> str:
    return value.strip()


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=8, max_length=80)
    client_id: str | None = Field(default=None, min_length=8, max_length=80)
    client_message_id: str | None = Field(default=None, min_length=8, max_length=120)
    message: str = Field(default="", max_length=2000)
    attachment_ids: list[int] = Field(default_factory=list)
    current_page: str | None = None
    service_slug: str | None = None
    service_name: str | None = None

    _strip_message = field_validator("message")(_strip_text)

    def validate_message_or_attachments(self):
        if not self.message.strip() and not self.attachment_ids:
            raise ValueError("Vui lòng nhập tin nhắn hoặc gửi hình ảnh.")
        return self


class ChatAttachmentOut(BaseModel):
    id: int
    url: str
    filename: str
    file_size: int = 0
    width: int | None = None
    height: int | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ChatResponse(BaseModel):
    reply: str
    quick_actions: list[str] = Field(default_factory=list)
    lead_created: bool = False
    lead_id: int | None = None
    conversation_id: int | None = None
    service_context: dict | None = None
    attachments: list[ChatAttachmentOut] = Field(default_factory=list)


class ChatMessageOut(BaseModel):
    id: int
    session_id: str
    client_message_id: str | None = None
    role: str
    message: str
    status: str = "SUCCESS"
    attachments: list[ChatAttachmentOut] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LeadCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    phone: str = Field(min_length=8, max_length=30)
    service: str = Field(min_length=2, max_length=160)
    address: str = Field(min_length=2, max_length=255)
    message: str = Field(min_length=2, max_length=2000)

    _strip_name = field_validator("name")(_strip_text)
    _strip_phone = field_validator("phone")(_strip_text)
    _strip_service = field_validator("service")(_strip_text)
    _strip_address = field_validator("address")(_strip_text)
    _strip_message = field_validator("message")(_strip_text)

    @field_validator("phone")
    @classmethod
    def phone_must_be_reasonable(cls, value: str) -> str:
        allowed = set("0123456789+ .-()")
        if any(char not in allowed for char in value):
            raise ValueError("Số điện thoại không hợp lệ")
        return value


class LeadOut(BaseModel):
    id: int
    status: str
    message: str = "Dạ bên em đã tiếp nhận thông tin. Nhân viên tư vấn sẽ liên hệ với anh/chị sớm nhất ạ."

    model_config = ConfigDict(from_attributes=True)
