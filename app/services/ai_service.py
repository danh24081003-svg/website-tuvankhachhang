import json
import logging
import time
from typing import Any, Iterable

from anyio import to_thread
from google import genai
from google.genai import types

from app.config import get_settings
from app.models import ChatMessage
from app.services.knowledge_service import KnowledgeService
from app.services.service_consultation_flows import (
    SERVICE_SPECS,
    build_confirmation_summary,
    get_conversational_quick_actions,
    get_next_question,
)


SYSTEM_PROMPT = """
Bạn là trợ lý AI tư vấn khách hàng của CÔNG TY TNHH DỊCH VỤ OSHIN THỜI ĐẠI - ĐẤT PHƯƠNG NAM.
Thương hiệu: Oshin Thời Đại.
Hotline chính thức: 0901 040 484.
Trụ sở tại Cần Thơ, chuyên cung cấp 7 dịch vụ chính:
1. Vệ sinh công nghiệp & vệ sinh công trình sau xây dựng.
2. Vận chuyển di dời nhà ở, văn phòng, kho xưởng, phòng trọ trọn gói.
3. Cung ứng & quản lý lao động thời vụ / phổ thông, bốc xếp, phụ kho.
4. Chăm sóc, cắt tỉa cây cảnh & duy tu bảo dưỡng cảnh quan sân vườn.
5. Giúp việc nhà theo giờ, nấu ăn, dọn dẹp định kỳ cho gia đình.
6. Kiểm soát & phun xịt diệt côn trùng, mối mọt, muỗi, chuột khử khuẩn.
7. Trang trí nội thất & cải tạo, sửa chữa nhà trọn gói (sơn nước, điện nước, chống thấm).

==================================================
NGUYÊN TẮC CỐT LÕI: CONVERSATION FIRST (KHÁCH HÀNG LÀ TRỌNG TÂM)
==================================================
Bạn là một NHÂN VIÊN TƯ VẤN THẬT, giao tiếp tự nhiên, thấu hiểu và lắng nghe.
TUYỆT ĐỐI KHÔNG BIẾN CUỘC TRÒ CHUYỆN THÀNH FORM ĐIỀN THÔNG TIN HAY BÀI KHẢO SÁT (QUESTIONNAIRE).
Mục tiêu số 1 (Primary Goal): Hiểu rõ khách cần gì, trả lời trực tiếp câu hỏi của khách và tư vấn thật hữu ích.
Thu thập lead / Số điện thoại chỉ là MỤC TIÊU PHỤ (Secondary Goal).

CẤU TRÚC MỖI TIN NHẮN TRẢ LỜI:
1. Trả lời trực tiếp và rõ ràng câu hỏi hoặc ý kiến của khách trước.
2. Cung cấp góc nhìn hoặc thông tin hữu ích ngắn gọn.
3. (Tùy chọn) Tối đa 1 câu hỏi gợi mở tự nhiên tiếp theo.
TUYỆT ĐỐI KHÔNG hỏi 2-3 câu dồn dập. Tuyệt đối KHÔNG dùng danh sách câu hỏi gạch đầu dòng (1. Tên, 2. SĐT, 3. Địa chỉ...).

QUY TẮC BẮT BUỘC THEO TỪNG TÌNH HUỐNG:

1. CHÀO HỎI & SMALL TALK:
- Khách: "hello", "hi", "xin chào" -> Chào lại lịch sự, ấm áp và hỏi khách đang quan tâm dịch vụ nào. TUYỆT ĐỐI KHÔNG hỏi SĐT.
  Ví dụ: "Dạ em chào anh/chị 👋 Em là trợ lý tư vấn của Oshin Thời Đại. Anh/chị đang cần tìm hiểu dịch vụ nào ạ?"
- Khách: "cảm ơn", "thank you" -> Trả lời vui vẻ, lịch sự: "Dạ không có gì ạ 😊 Khi nào cần hỗ trợ thêm anh/chị cứ nhắn em nhé." TUYỆT ĐỐI KHÔNG xin SĐT sau lời cảm ơn.

2. KHÁCH HỎI THAM KHẢO ("tôi chỉ hỏi tham khảo", "chưa làm liền", "hỏi trước thôi"):
- Hoàn toàn thoải mái và ủng hộ khách: "Dạ được ạ 😊 Anh/chị cứ hỏi thoải mái, em sẽ hỗ trợ thông tin trước. Khi nào cần khảo sát hoặc báo giá cụ thể mình để lại thông tin sau cũng được ạ."
- TUYỆT ĐỐI KHÔNG tiếp tục gặng hỏi hay ép xin SĐT.

3. KHÁCH HỎI VỀ KHẢ NĂNG DỊCH VỤ ("Bên mình có vệ sinh nhà không?", "Có chuyển trọ không?"):
- Trả lời xác nhận rõ ràng trước, rồi mới gợi mở tự nhiên: "Dạ có ạ. Bên em có nhận vệ sinh nhà ở theo nhu cầu, từ vệ sinh tổng thể đến các hạng mục cụ thể. Anh/chị đang cần vệ sinh toàn bộ nhà hay một khu vực/hạng mục nhất định ạ?"
- KHÔNG lập tức đòi hỏi họ tên, SĐT, địa chỉ, diện tích hay thời gian.

4. KHÁCH CHIA SẺ THÔNG TIN CƠ BẢN (Ví dụ: "Nhà khoảng 100m2"):
- Ghi nhận thông tin, tư vấn phương án phù hợp, gợi ý chi tiết về công việc: "Dạ, với nhà khoảng 100m² bên em có thể tư vấn phương án phù hợp. Nếu tiện, anh/chị cho em biết nhà mình đang cần vệ sinh tổng thể hay chủ yếu là sàn, kính, bếp, nhà vệ sinh... ạ?"
- KHÔNG lập tức hỏi SĐT.

5. KHÁCH HỎI GIÁ ("Bao nhiêu tiền?", "Giá vệ sinh bao nhiêu?", "Báo giá cho tôi"):
- TUYỆT ĐỐI KHÔNG TỰ BỊA CON SỐ GIÁ (không tự đưa ra con số ước tính như 500k, 1 triệu, 20.000đ/m2...).
- Giải thích rõ ràng và khéo léo: "Dạ chi phí sẽ phụ thuộc vào hiện trạng và hạng mục cần làm nên em chưa muốn báo một mức không chính xác cho anh/chị. Với nhà [diện tích đã biết nếu có] như mình vừa trao đổi, nếu anh/chị cho em biết cần vệ sinh tổng thể hay những hạng mục nào thì em có thể tiếp nhận nhu cầu chi tiết hơn để bên em tư vấn/báo giá."

6. KHÁCH HỎI LỊCH LÀM VIỆC & CHỦ NHẬT ("Có làm chủ nhật không?", "Thứ 7 có làm không?"):
- Trả lời thẳng vào câu hỏi đó trước: "Dạ bên em có nhận lịch khảo sát và phục vụ vào cả Thứ 7 và Chủ nhật theo lịch hẹn trước của anh/chị ạ. Anh/chị đang dự kiến làm vào ngày nào để em hỗ trợ tư vấn nhé ạ?" (Nếu là câu hỏi về dịch vụ ngoài thẩm quyền thì thành thật nói chưa có thông tin chắc chắn để nhân viên kiểm tra).
- TUYỆT ĐỐI KHÔNG được bỏ qua câu hỏi để đòi địa chỉ hay SĐT.

7. NGUYÊN TẮC THU THẬP SỐ ĐIỆN THOẠI (SĐT):
- CHỈ đề nghị xin SĐT khi có tín hiệu: khách muốn báo giá cụ thể, muốn đặt dịch vụ, muốn khảo sát tận nơi, muốn nhân viên gọi lại, hoặc cuộc trao đổi đã làm rõ đủ nhu cầu và việc liên hệ là bước tiếp theo hợp lý.
- Phải dùng LỜI ĐỀ NGHỊ NHẸ NHÀNG, KHÔNG ÉP BUỘC: "Nếu anh/chị muốn, em có thể tiếp nhận số điện thoại để nhân viên bên em liên hệ tư vấn cụ thể và gửi báo giá chi tiết cho mình nhé ạ."
- Nếu khách chưa cho SĐT, VẪN TRÒ CHUYỆN VÀ TƯ VẤN BÌNH THƯỜNG.

8. ĐÃ CÓ THÔNG TIN THÌ TUYỆT ĐỐI KHÔNG HỎI LẠI:
- Xem kỹ phần "customer_information_already_collected" trong dữ liệu nội bộ.
- Nếu khách đã cung cấp thông tin (như: diện tích 100m2, ở Ninh Kiều, thứ 7 làm, SĐT 09xxxxxxxx), TUYỆT ĐỐI KHÔNG hỏi lại diện tích, khu vực, ngày giờ hay SĐT nữa! Hãy tóm tắt và xác nhận nhẹ nhàng.

9. GIỌNG ĐIỆU (TONE):
- Luôn xưng "em", gọi khách là "anh/chị", dùng từ ngữ tự nhiên "Dạ", "bên em", "dạ vâng".
- Thân thiện, chu đáo, giống nhân viên CSKH Việt Nam có tâm.
- Rất hạn chế emoji, không message nào cũng emoji.
- Không quá dài dòng, không dùng từ ngữ máy móc hay quá lễ nghi.
""".strip()


logger = logging.getLogger("uvicorn.error")
RETRYABLE_STATUS_CODES = [429, 500, 502, 503, 504]
TEMPORARY_AI_MESSAGE = "Trợ lý Oshin đang bận trong giây lát. Anh/chị vui lòng thử lại."
GENERAL_AI_MESSAGE = "Trợ lý đang tạm thời gián đoạn. Anh/chị vui lòng thử lại sau hoặc liên hệ 0901 040 484."


class AIServiceError(Exception):
    def __init__(self, code: str, safe_message: str, retryable: bool = False) -> None:
        super().__init__(safe_message)
        self.code = code
        self.safe_message = safe_message
        self.retryable = retryable


_cached_client = None
_cached_client_key = None


class AIService:
    def __init__(self, knowledge_service: KnowledgeService) -> None:
        global _cached_client, _cached_client_key
        self.settings = get_settings()
        self.knowledge_service = knowledge_service
        self.client = None
        self.active_provider: str = "consultation-flow"
        self.active_model: str = "rule-based-assistant"
        self.fallback_model = (self.settings.gemini_fallback_model or "").strip() or "gemini-flash-latest"
        
        http_options = types.HttpOptions(
            timeout=self.settings.gemini_timeout_ms,
            retry_options=types.HttpRetryOptions(
                attempts=2,
                initial_delay=0.5,
                max_delay=1.5,
                exp_base=2.0,
                jitter=0.2,
                http_status_codes=RETRYABLE_STATUS_CODES,
            ),
        )

        # 1. Priority: Direct Gemini API Key
        api_key = self.settings.gemini_api_key
        if api_key and api_key.strip():
            api_key_clean = api_key.strip()
            if _cached_client and _cached_client_key == api_key_clean:
                self.client = _cached_client
            else:
                try:
                    self.client = genai.Client(api_key=api_key_clean, http_options=http_options)
                    _cached_client = self.client
                    _cached_client_key = api_key_clean
                except Exception:
                    logger.exception("Gemini API key client initialization failed")
                    self.client = None
            if self.client:
                self.active_provider = "google-gemini"
                self.active_model = self.settings.gemini_model or "gemini-flash-lite-latest"

        # 2. Priority: Vertex AI (Google Cloud Project)
        if not self.client:
            project = self.settings.google_cloud_project
            has_project = bool(project and project != "your-project-id" and project.strip())
            if has_project:
                try:
                    self.client = genai.Client(
                        vertexai=True,
                        project=project.strip(),
                        location=self.settings.google_cloud_location,
                        http_options=http_options,
                    )
                    self.active_provider = "vertex-ai"
                    self.active_model = self.settings.vertex_model or "gemini-2.5-flash"
                except Exception:
                    logger.exception("Vertex AI client initialization failed")
                    self.client = None

    def get_status(self) -> dict[str, Any]:
        return {
            "provider": self.active_provider,
            "model": self.active_model,
            "configured": bool(self.client),
            "available": bool(self.client),
            "status": "ready" if self.client else "not_configured",
        }

    def _status_code(self, err: Exception) -> int | None:
        for attr in ("code", "status_code"):
            value = getattr(err, attr, None)
            if isinstance(value, int):
                return value
            if isinstance(value, str) and value.isdigit():
                return int(value)
        response = getattr(err, "response", None)
        value = getattr(response, "status_code", None)
        if isinstance(value, int):
            return value
        text = str(err)
        for code in [400, 401, 403, 404, 429, 500, 502, 503, 504]:
            if str(code) in text:
                return code
        return None

    def _classify_error(self, err: Exception) -> tuple[str, str, bool]:
        status_code = self._status_code(err)
        text = str(err).lower()
        if status_code in RETRYABLE_STATUS_CODES:
            return "AI_TEMPORARILY_UNAVAILABLE", TEMPORARY_AI_MESSAGE, True
        if "unavailable" in text or "high demand" in text or "resource_exhausted" in text:
            return "AI_TEMPORARILY_UNAVAILABLE", TEMPORARY_AI_MESSAGE, True
        if "deadline" in text or "timeout" in text or "timed out" in text:
            return "AI_TIMEOUT", TEMPORARY_AI_MESSAGE, True
        if "connecterror" in text or "socket" in text or "network" in text or "connection" in text:
            return "AI_PROVIDER_ERROR", GENERAL_AI_MESSAGE, True
        if status_code in {401, 403} or "credential" in text or "unauthorized" in text:
            return "AI_AUTH_ERROR", GENERAL_AI_MESSAGE, False
        if status_code == 400:
            return "INVALID_REQUEST", "Nội dung gửi chưa hợp lệ. Anh/chị vui lòng thử lại.", False
        return "AI_PROVIDER_ERROR", GENERAL_AI_MESSAGE, False

    def _build_contents(
        self,
        user_message: str,
        history: Iterable[ChatMessage],
        image_bytes_list: list[bytes] | None = None,
    ) -> list[types.Content]:
        contents: list[types.Content] = []
        for item in list(history)[-10:]:
            if item.role in {"user", "assistant"} and getattr(item, "status", "SUCCESS") == "SUCCESS":
                role = "model" if item.role == "assistant" else "user"
                msg_text = item.message or ""
                contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg_text)]))

        last_user_parts: list[types.Part] = []
        if image_bytes_list:
            for img_bytes in image_bytes_list:
                mime = "image/jpeg"
                if img_bytes.startswith(b"\x89PNG"):
                    mime = "image/png"
                elif img_bytes.startswith(b"RIFF") and b"WEBP" in img_bytes[:16]:
                    mime = "image/webp"
                last_user_parts.append(types.Part.from_bytes(data=img_bytes, mime_type=mime))

        text_content = user_message.strip() if user_message else ""
        if not text_content and image_bytes_list:
            text_content = "Tôi gửi hình ảnh này, nhờ bên mình xem hình ảnh và tư vấn giúp tôi nhé."

        if text_content:
            last_user_parts.append(types.Part.from_text(text=text_content))

        if not contents or contents[-1].role != "user":
            if last_user_parts:
                contents.append(types.Content(role="user", parts=last_user_parts))
        else:
            if last_user_parts:
                contents[-1] = types.Content(role="user", parts=last_user_parts)

        return contents

    def _generate_content_sync(self, model: str, contents: list[types.Content], config: types.GenerateContentConfig):
        return self.client.models.generate_content(model=model, contents=contents, config=config)

    async def check_status(self) -> dict[str, Any]:
        status = self.get_status()
        if not self.client:
            return status
        try:
            config = types.GenerateContentConfig(
                temperature=0,
                max_output_tokens=8,
            )
            await to_thread.run_sync(
                lambda: self.client.models.generate_content(
                    model=self.active_model,
                    contents=[types.Content(role="user", parts=[types.Part(text="ping")])],
                    config=config,
                )
            )
            status["available"] = True
            status["status"] = "ready"
        except Exception:
            logger.exception("AI status check failed")
            status["available"] = False
            status["status"] = "unavailable"
        return status

    def _knowledge_prompt(
        self,
        service_slug: str | None = None,
        service_name: str | None = None,
        current_state: dict[str, Any] | None = None,
    ) -> str:
        state_dict = current_state or {}
        context = {
            "company": self.knowledge_service.company(),
            "service_context": {
                "slug": service_slug,
                "name": service_name or (SERVICE_SPECS.get(service_slug, {}).get("name") if service_slug else None),
            },
            "customer_information_already_collected": state_dict,
        }
        return (
            f"Dữ liệu tư vấn nội bộ:\n{json.dumps(context, ensure_ascii=False, indent=2)}\n\n"
            "CHỈ DẪN QUAN TRỌNG VỀ BỘ NHỚ:\n"
            "- Các mục trong 'customer_information_already_collected' là thông tin khách ĐÃ cung cấp. TUYỆT ĐỐI KHÔNG HỎI LẠI những thông tin đã có này.\n"
            "- Đây chỉ là bộ nhớ ngầm để ghi nhận và tránh lặp lại. TUYỆT ĐỐI KHÔNG biến các thông tin còn thiếu thành bài kiểm tra hay checklist dồn dập. Hãy trò chuyện tự nhiên!"
        )

    def fallback_reply(
        self,
        message: str,
        service_slug: str | None = None,
        service_name: str | None = None,
        current_state: dict[str, Any] | None = None,
        has_phone: bool = False,
    ) -> tuple[str, list[str]]:
        state_reqs = current_state or {}
        lowered = message.lower().strip()
        quick = get_conversational_quick_actions(service_slug, message, state_reqs)

        # 1. Cảm ơn
        if any(kw in lowered for kw in ["cảm ơn", "cam on", "thank", "tks", "cmon"]):
            return (
                "Dạ không có gì ạ 😊 Khi nào cần hỗ trợ thêm anh/chị cứ nhắn em nhé.",
                ["Xem dịch vụ khác", "Hotline 0901 040 484"],
            )

        # 2. Tham khảo / Xem trước
        if any(kw in lowered for kw in ["tham khảo", "tham khao", "xem trước", "chưa làm liền", "chua lam lien", "hỏi thôi", "hoi thoi", "hỏi trước"]):
            return (
                "Dạ được ạ 😊 Anh/chị cứ hỏi thoải mái, em sẽ hỗ trợ thông tin trước. Khi nào cần khảo sát hoặc báo giá cụ thể mình để lại thông tin sau cũng được ạ.",
                ["Vệ sinh công nghiệp", "Vận chuyển di dời", "Dịch vụ khác"],
            )

        # 3. Chào hỏi
        if any(w in lowered.split() for w in ["hi", "hello", "halo", "alo"]) or lowered in ["chào", "xin chào", "xin chao", "chao em", "chào em"]:
            return (
                "Dạ em chào anh/chị 👋 Em là trợ lý tư vấn của Oshin Thời Đại. Anh/chị đang cần tìm hiểu dịch vụ nào ạ?",
                ["Vệ sinh nhà", "Chuyển nhà", "Giúp việc theo giờ", "Dịch vụ khác"],
            )

        # 4. Lịch làm việc / Chủ nhật / Thứ 7
        if any(kw in lowered for kw in ["chủ nhật", "chu nhat", "thứ 7", "thu 7", "thứ bảy", "cuối tuần", "cuoi tuan"]):
            return (
                "Dạ bên em có nhận lịch khảo sát và phục vụ vào cả Thứ 7 và Chủ nhật theo lịch hẹn trước của anh/chị ạ. Anh/chị đang dự kiến làm vào ngày nào để em hỗ trợ tư vấn phương án nhé ạ?",
                ["Thứ 7", "Chủ nhật", "Trong tuần"],
            )

        # 5. Giá cả / Chi phí
        if any(kw in lowered for kw in ["giá", "gia", "báo giá", "bao gia", "chi phí", "chi phi", "nhiêu tiền", "bao nhieu", "bao nhiu", "nhiêu"]):
            area = state_reqs.get("estimated_area") or state_reqs.get("area_size")
            if area:
                return (
                    f"Dạ chi phí sẽ phụ thuộc vào hiện trạng và hạng mục cần làm nên em chưa muốn báo một mức không chính xác cho anh/chị. Với nhà {area} như mình vừa trao đổi, nếu anh/chị cho em biết cần vệ sinh tổng thể hay những hạng mục nào thì em có thể tiếp nhận nhu cầu chi tiết hơn để bên em tư vấn/báo giá.",
                    ["Vệ sinh tổng thể", "Hạng mục cụ thể", "Khảo sát tận nơi"],
                )
            return (
                "Dạ chi phí sẽ phụ thuộc vào hiện trạng và hạng mục cần làm nên em chưa muốn báo một mức không chính xác cho anh/chị ạ. Anh/chị đang quan tâm đến hạng mục nào hoặc diện tích khoảng bao nhiêu m² để em hỗ trợ tư vấn phương án phù hợp nhé ạ?",
                ["Khảo sát miễn phí", "Tư vấn thêm", "Hotline 0901 040 484"],
            )

        # 6. Hỏi khả năng cung cấp dịch vụ vệ sinh
        if any(kw in lowered for kw in ["có vệ sinh", "co ve sinh", "vệ sinh nhà không", "ve sinh nha khong", "dọn dẹp nhà không", "don dep nha khong"]):
            return (
                "Dạ có ạ. Bên em có nhận vệ sinh nhà ở theo nhu cầu, từ vệ sinh tổng thể đến các hạng mục cụ thể. Anh/chị đang cần vệ sinh toàn bộ nhà hay một khu vực/hạng mục nhất định ạ?",
                ["Vệ sinh toàn bộ", "Hạng mục cụ thể", "Khảo sát tận nơi"],
            )

        # 7. Khách chia sẻ diện tích (ví dụ "100m2", "80m2")
        if any(kw in lowered for kw in ["m2", "m²", "mét vuông", "met vuong"]):
            area = state_reqs.get("estimated_area") or state_reqs.get("area_size") or "khoảng như mình chia sẻ"
            return (
                f"Dạ, với nhà khoảng {area} bên em có thể tư vấn phương án phù hợp. Nếu tiện, anh/chị cho em biết nhà mình đang cần vệ sinh tổng thể hay chủ yếu là sàn, kính, bếp, nhà vệ sinh... ạ?",
                ["Vệ sinh tổng thể", "Làm sàn & kính", "Khảo sát tận nơi"],
            )

        # 8. Yêu cầu đặt dịch vụ
        if any(kw in lowered for kw in ["tôi muốn đặt", "muốn đặt", "muon dat", "đặt lịch", "dat lich", "cần làm ngay"]):
            return (
                "Dạ vâng, em rất sẵn lòng hỗ trợ anh/chị lên lịch dịch vụ ạ. Để em sắp xếp đội ngũ phù hợp, anh/chị cho em biết nhà mình ở khu vực nào và dự kiến làm vào ngày nào được không ạ?",
                ["Ninh Kiều", "Cái Răng", "Cuối tuần này"],
            )

        # 9. Gặp nhân viên / Handoff
        if any(kw in lowered for kw in ["gặp nhân viên", "gap nhan vien", "nhân viên", "nhan vien", "hotline", "gọi lại", "goi lai"]):
            if has_phone:
                phone_num = state_reqs.get("phone", "của anh/chị")
                return (
                    f"Dạ em đã chuyển thông tin yêu cầu của anh/chị tới nhân viên tư vấn Oshin Thời Đại. Bên em sẽ liên hệ ngay qua số {phone_num} ạ. Nếu cần hỗ trợ khẩn cấp, anh/chị có thể gọi trực tiếp hotline 0901 040 484 để được phục vụ chu đáo nhất ạ!",
                    ["Hotline 0901 040 484", "Cần tư vấn thêm"],
                )
            return (
                "Nếu anh/chị cần trao đổi trực tiếp, bên em có thể hỗ trợ qua hotline 0901 040 484 hoặc nếu tiện anh/chị có thể để lại số điện thoại để nhân viên liên hệ tư vấn cụ thể cho mình nhé ạ.",
                ["Hotline 0901 040 484", "Để lại số điện thoại"],
            )

        # 10. Khách đã cung cấp đầy đủ thông tin (phone + requirements)
        if has_phone and len(state_reqs) >= 2:
            s_name = service_name or (SERVICE_SPECS.get(service_slug, {}).get("name") if service_slug else "dịch vụ")
            area_str = f", diện tích {state_reqs.get('estimated_area')}" if state_reqs.get("estimated_area") else ""
            loc_str = f" tại {state_reqs.get('location')}" if state_reqs.get("location") else ""
            date_str = f" vào {state_reqs.get('preferred_date')}" if state_reqs.get("preferred_date") else ""
            return (
                f"Dạ em đã ghi nhận thông tin của anh/chị cho {s_name}{area_str}{loc_str}{date_str} và số điện thoại {state_reqs.get('phone')}. Chuyên viên tư vấn Oshin Thời Đại sẽ liên hệ lại với anh/chị trong ít phút để trao đổi và hỗ trợ chu đáo nhất ạ!",
                ["Hotline 0901 040 484", "Dịch vụ khác"],
            )

        # 11. Theo ngữ cảnh dịch vụ
        if service_slug == "van-chuyen-di-doi":
            return (
                "Dạ Oshin Thời Đại chuyên nhận vận chuyển di dời trọn gói với xe tải và nhân công bốc xếp cẩn thận. Anh/chị cần em hỗ trợ tư vấn thêm thông tin nào về dịch vụ này ạ?",
                ["Chuyển nhà", "Chuyển văn phòng", "Chuyển trọ"],
            )
        if service_slug == "ve-sinh-cong-nghiep":
            return (
                "Dạ Oshin Thời Đại chuyên nhận vệ sinh nhà ở, căn hộ và công trình sau xây dựng. Anh/chị cần em tư vấn cụ thể phần nào ạ?",
                ["Vệ sinh toàn bộ", "Hạng mục cụ thể", "Khảo sát tận nơi"],
            )

        # Generic default
        return (
            "Dạ em đã nhận được thông tin từ anh/chị ạ. Anh/chị đang cần tìm hiểu thêm dịch vụ nào bên em để em hỗ trợ tư vấn chi tiết nhé ạ?",
            ["Vệ sinh công nghiệp", "Vận chuyển di dời", "Dịch vụ khác"],
        )

    async def generate_reply(
        self,
        user_message: str,
        history: Iterable[ChatMessage],
        service_slug: str | None = None,
        service_name: str | None = None,
        current_state: dict[str, Any] | None = None,
        has_phone: bool = False,
        image_bytes_list: list[bytes] | None = None,
    ) -> tuple[str, list[str]]:
        fallback_text, quick_actions = self.fallback_reply(
            user_message,
            service_slug=service_slug,
            service_name=service_name,
            current_state=current_state,
            has_phone=has_phone,
        )

        if not self.client:
            logger.error("AI chat request failed because no AI client is configured")
            raise AIServiceError(
                "AI_CONFIG_ERROR",
                "Trợ lý đang tạm thời gián đoạn. Anh/chị vui lòng thử lại sau hoặc liên hệ 0901 040 484.",
            )

        contents = self._build_contents(user_message, history, image_bytes_list=image_bytes_list)

        knowledge_text = self._knowledge_prompt(service_slug, service_name, current_state)
        config = types.GenerateContentConfig(
            system_instruction=f"{SYSTEM_PROMPT}\n\n{knowledge_text}",
            temperature=0.35,
            max_output_tokens=350,
        )

        started = time.monotonic()
        logger.info(
            "AI request started provider=%s model=%s history=%s",
            self.active_provider,
            self.active_model,
            len(contents),
        )
        models_to_try = [self.active_model]
        if self.fallback_model and self.fallback_model != self.active_model:
            models_to_try.append(self.fallback_model)

        last_error: Exception | None = None
        for model_index, model in enumerate(models_to_try):
            try:
                if model_index == 1:
                    logger.warning("Primary model unavailable, trying configured fallback.")
                response = await to_thread.run_sync(lambda: self._generate_content_sync(model, contents, config))
                latency_ms = int((time.monotonic() - started) * 1000)
                logger.info(
                    "AI request succeeded provider=%s model=%s latency_ms=%s",
                    self.active_provider,
                    model,
                    latency_ms,
                )
                reply = getattr(response, "text", None)
                if reply and reply.strip():
                    return reply.strip(), quick_actions
                logger.warning("AI provider returned an empty response model=%s", model)
                break
            except Exception as err:
                last_error = err
                code, safe_message, retryable = self._classify_error(err)
                latency_ms = int((time.monotonic() - started) * 1000)
                logger.warning(
                    "AI request failed provider=%s model=%s code=%s retryable=%s latency_ms=%s",
                    self.active_provider,
                    model,
                    code,
                    retryable,
                    latency_ms,
                )
                if model_index == 0 and len(models_to_try) > 1 and retryable:
                    continue
                logger.exception("Vertex AI chat request failed")
                raise AIServiceError(code, safe_message, retryable=retryable) from err

        if last_error is not None:
            code, safe_message, retryable = self._classify_error(last_error)
            raise AIServiceError(code, safe_message, retryable=retryable) from last_error

        logger.error("AI provider returned an empty response")
        raise AIServiceError("AI_PROVIDER_ERROR", GENERAL_AI_MESSAGE)

        try:
            response = await to_thread.run_sync(
                lambda: self.client.models.generate_content(
                    model=self.active_model,
                    contents=contents,
                    config=config,
                )
            )
            reply = getattr(response, "text", None)
            if reply and reply.strip():
                return reply.strip(), quick_actions
        except Exception as err:
            text = str(err).lower()
            if "deadline" in text or "timeout" in text or "timed out" in text:
                code = "AI_TIMEOUT"
            elif "connecterror" in text or "socket" in text or "network" in text or "connection" in text:
                code = "AI_PROVIDER_ERROR"
            elif "credential" in text or "unauthorized" in text or "403" in text or "401" in text:
                code = "AI_AUTH_ERROR"
            else:
                code = "AI_PROVIDER_ERROR"
            logger.exception("Vertex AI chat request failed")
            raise AIServiceError(
                code,
                "Trợ lý đang tạm thời gián đoạn. Anh/chị vui lòng thử lại sau hoặc liên hệ 0901 040 484.",
            ) from err

        logger.error("AI provider returned an empty response")
        raise AIServiceError(
            "AI_PROVIDER_ERROR",
            "Trợ lý đang tạm thời gián đoạn. Anh/chị vui lòng thử lại sau hoặc liên hệ 0901 040 484.",
        )
