import json
import re
from typing import Any


SERVICE_SPECS = {
    "van-chuyen-di-doi": {
        "slug": "van-chuyen-di-doi",
        "name": "Vận chuyển, di dời",
        "greeting": "Dạ anh/chị đang xem dịch vụ Vận chuyển, di dời trọn gói của Oshin Thời Đại. Em có thể hỗ trợ anh/chị tìm hiểu chi tiết hoặc tiếp nhận thông tin để lên phương án xe và báo giá ạ.",
        "fields": {
            "origin": {"label": "Địa điểm đi (quận/huyện/địa chỉ)", "priority": 1},
            "destination": {"label": "Địa điểm đến", "priority": 2},
            "items": {"label": "Loại tài sản / đồ đạc cần chuyển", "priority": 3},
            "estimated_volume": {"label": "Khối lượng ước tính / loại xe", "priority": 4},
            "origin_floor": {"label": "Tầng tại điểm đi", "priority": 5},
            "destination_floor": {"label": "Tầng tại điểm đến", "priority": 6},
            "elevator": {"label": "Có thang máy hay không", "priority": 7},
            "preferred_date": {"label": "Thời gian dự kiến chuyển", "priority": 8},
            "customer_name": {"label": "Họ và tên", "priority": 9},
            "phone": {"label": "Số điện thoại", "priority": 10},
        },
    },
    "ve-sinh-cong-nghiep": {
        "slug": "ve-sinh-cong-nghiep",
        "name": "Vệ sinh công nghiệp",
        "greeting": "Dạ anh/chị đang xem dịch vụ Vệ sinh công nghiệp. Em có thể hỗ trợ anh/chị tìm hiểu dịch vụ hoặc tiếp nhận thông tin diện tích, hiện trạng để tư vấn phương án phù hợp ạ.",
        "fields": {
            "building_type": {"label": "Loại công trình (nhà ở, văn phòng, nhà xưởng, chung cư)", "priority": 1},
            "estimated_area": {"label": "Diện tích ước tính (m²)", "priority": 2},
            "current_condition": {"label": "Tình trạng hiện tại (sau xây dựng, định kỳ, nhiều bụi/sơn...)", "priority": 3},
            "cleaning_items": {"label": "Hạng mục cần vệ sinh (sàn, kính, sofa, thảm...)", "priority": 4},
            "location": {"label": "Khu vực / Địa chỉ công trình", "priority": 5},
            "preferred_date": {"label": "Thời gian mong muốn thực hiện", "priority": 6},
            "customer_name": {"label": "Họ và tên", "priority": 7},
            "phone": {"label": "Số điện thoại", "priority": 8},
        },
    },
    "trang-tri-sua-chua": {
        "slug": "trang-tri-sua-chua",
        "name": "Trang trí, sửa chữa",
        "greeting": "Dạ anh/chị đang xem dịch vụ Trang trí, sửa chữa. Em có thể hỗ trợ tư vấn các hạng mục điện nước, chống thấm, sơn sửa hoặc tiếp nhận thông tin khảo sát ạ.",
        "fields": {
            "building_type": {"label": "Loại công trình", "priority": 1},
            "repair_items": {"label": "Hạng mục cần sửa chữa / trang trí (điện, nước, sơn, chống thấm...)", "priority": 2},
            "current_condition": {"label": "Hiện trạng sự cố / nhu cầu cải tạo", "priority": 3},
            "location": {"label": "Khu vực / Địa chỉ", "priority": 4},
            "preferred_date": {"label": "Thời gian mong muốn thi công", "priority": 5},
            "customer_name": {"label": "Họ và tên", "priority": 6},
            "phone": {"label": "Số điện thoại", "priority": 7},
        },
    },
    "cung-cap-quan-ly-lao-dong": {
        "slug": "cung-cap-quan-ly-lao-dong",
        "name": "Cung cấp & quản lý nguồn lao động",
        "greeting": "Dạ anh/chị đang xem dịch vụ Cung cấp & quản lý nguồn lao động. Em có thể hỗ trợ quý doanh nghiệp về nhân lực bốc xếp, phụ kho, công nhân đóng gói theo ca hoặc thời vụ ạ.",
        "fields": {
            "labor_type": {"label": "Loại lao động cần (bốc xếp, đóng gói, phụ kho, công nhân)", "priority": 1},
            "quantity": {"label": "Số lượng lao động cần", "priority": 2},
            "job_description": {"label": "Mô tả công việc", "priority": 3},
            "location": {"label": "Địa điểm làm việc", "priority": 4},
            "work_schedule": {"label": "Thời gian / Ca làm việc", "priority": 5},
            "start_date": {"label": "Thời gian cần bắt đầu", "priority": 6},
            "contact_person": {"label": "Người liên hệ / Tên công ty", "priority": 7},
            "phone": {"label": "Số điện thoại liên hệ", "priority": 8},
        },
    },
    "giup-viec": {
        "slug": "giup-viec",
        "name": "Giúp việc theo giờ, định kỳ",
        "greeting": "Dạ anh/chị đang xem dịch vụ Giúp việc theo giờ & định kỳ. Em có thể hỗ trợ tư vấn khung giờ dọn dẹp, nấu ăn, chăm sóc gia đình phù hợp với nhu cầu của anh/chị ạ.",
        "fields": {
            "housing_type": {"label": "Loại hình nhà ở (nhà phố, chung cư, biệt thự)", "priority": 1},
            "tasks": {"label": "Công việc cần hỗ trợ (dọn dẹp, giặt ủi, nấu ăn, rửa chén)", "priority": 2},
            "frequency": {"label": "Tần suất (theo giờ, cố định theo tuần, định kỳ)", "priority": 3},
            "preferred_schedule": {"label": "Khung giờ mong muốn", "priority": 4},
            "location": {"label": "Khu vực / Quận huyện", "priority": 5},
            "customer_name": {"label": "Họ và tên", "priority": 6},
            "phone": {"label": "Số điện thoại", "priority": 7},
        },
    },
    "cham-soc-cay-canh": {
        "slug": "cham-soc-cay-canh",
        "name": "Chăm sóc cây cảnh",
        "greeting": "Dạ anh/chị đang xem dịch vụ Chăm sóc cây cảnh & mảng xanh. Em có thể hỗ trợ tư vấn cắt tỉa, bón phân, phòng trừ sâu bệnh hoặc bảo dưỡng định kỳ ạ.",
        "fields": {
            "area_type": {"label": "Loại khu vực (sân vườn, ban công, cây cảnh văn phòng)", "priority": 1},
            "tasks": {"label": "Công việc cần làm (cắt tỉa, bón phân, trị rệp, thay đất)", "priority": 2},
            "frequency": {"label": "Tần suất (làm một lần hay định kỳ hàng tuần/tháng)", "priority": 3},
            "location": {"label": "Khu vực / Địa chỉ", "priority": 4},
            "customer_name": {"label": "Họ và tên", "priority": 5},
            "phone": {"label": "Số điện thoại", "priority": 6},
        },
    },
    "diet-con-trung": {
        "slug": "diet-con-trung",
        "name": "Diệt côn trùng",
        "greeting": "Dạ anh/chị đang xem dịch vụ Diệt côn trùng & kiểm soát dịch hại. Em có thể hỗ trợ tư vấn xử lý mối, muỗi, gián, kiến, chuột an toàn, có bảo hành ạ.",
        "fields": {
            "pest_type": {"label": "Loại côn trùng cần xử lý (mối, muỗi, gián, kiến, chuột...)", "priority": 1},
            "building_type": {"label": "Loại công trình (nhà ở, nhà hàng, quán ăn, kho bãi)", "priority": 2},
            "estimated_area": {"label": "Diện tích / Phạm vi xử lý", "priority": 3},
            "location": {"label": "Khu vực / Địa chỉ", "priority": 4},
            "preferred_date": {"label": "Thời gian mong muốn xử lý", "priority": 5},
            "customer_name": {"label": "Họ và tên", "priority": 6},
            "phone": {"label": "Số điện thoại", "priority": 7},
        },
    },
}

# Aliases mapping
SLUG_ALIASES = {
    "cung-cap-quan-ly-nguon-lao-dong": "cung-cap-quan-ly-lao-dong",
    "giup-viec-theo-gio-dinh-ky": "giup-viec",
}


def normalize_slug(slug: str | None) -> str | None:
    if not slug:
        return None
    slug = slug.strip().lower()
    return SLUG_ALIASES.get(slug, slug)


def extract_phone(text: str) -> str | None:
    if not text:
        return None
    # Matches Vietnamese phone numbers: e.g. 0901 040 484, 0901040484, +84 901 040 484, 03x, 05x, 07x, 08x, 09x
    pattern = r"(?:\+84|0)(?:[\s.-]*\d){9,10}\b"
    matches = re.findall(pattern, text)
    if matches:
        # Clean up separators
        cleaned = re.sub(r"[\s.-]", "", matches[0])
        if cleaned.startswith("+84"):
            cleaned = "0" + cleaned[3:]
        if len(cleaned) == 10 and cleaned.startswith("0"):
            return cleaned
    return None


def extract_name(text: str) -> str | None:
    if not text:
        return None
    patterns = [
        r"(?:tôi tên là|tôi tên|em tên là|em tên|mình tên là|mình tên|anh tên là|anh tên|chị tên là|chị tên|tên tôi là)\s+([A-ZÀ-Ỹa-zà-ỹ\s]{2,30})",
        r"(?:gặp|cho)\s+([A-ZÀ-Ỹa-zà-ỹ\s]{2,20})\s+(?:nhé|nhe|nha|ạ)",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            name = m.group(1).strip()
            # Remove trailing words
            name = re.sub(r"\b(nhé|nhe|nha|ạ|nhá|nhe|dạ|ở|tại)\b.*$", "", name, flags=re.IGNORECASE).strip()
            if 2 <= len(name) <= 30 and not any(ch in name for ch in "0123456789@#$"):
                return name.title()
    return None


def extract_location(text: str) -> str | None:
    if not text:
        return None
    # Common locations in Mekong/Can Tho or keywords
    districts = [
        "Ninh Kiều", "Cái Răng", "Bình Thủy", "Ô Môn", "Thốt Nốt", "Phong Điền",
        "Thới Lai", "Cờ Đỏ", "Vĩnh Thạnh", "Cần Thơ", "Hậu Giang", "Vĩnh Long",
        "Sóc Trăng", "An Giang", "Đồng Tháp", "Kiên Giang", "Bạc Liêu", "Cà Mau"
    ]
    lowered = text.lower()
    for d in districts:
        if d.lower() in lowered:
            return d

    # Pattern "ở ...", "tại ...", "đường ..."
    m = re.search(r"(?:ở|tại|khu vực|đường)\s+([A-ZÀ-Ỹa-zà-ỹ0-9\s,\.\/]{3,40})", text, re.IGNORECASE)
    if m:
        loc = m.group(1).strip()
        loc = re.sub(r"\b(nhé|nha|ạ|vào|lúc|khoảng|ngày)\b.*$", "", loc, flags=re.IGNORECASE).strip()
        if len(loc) >= 3:
            return loc
    return None


def extract_attributes(slug: str, text: str, current_reqs: dict[str, Any]) -> dict[str, Any]:
    """Extract structured details specific to a service flow without overwriting existing data."""
    reqs = dict(current_reqs)
    lowered = text.lower()

    # Generic Area (m2)
    area_match = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:m2|m²|mét vuông|met vuong)", lowered)
    if area_match:
        area_val = f"{area_match.group(1)} m²"
        if slug in {"ve-sinh-cong-nghiep", "trang-tri-sua-chua", "diet-con-trung"}:
            reqs.setdefault("estimated_area", area_val)
        elif slug == "cham-soc-cay-canh":
            reqs.setdefault("area_size", area_val)

    # Date / Time
    date_match = re.search(r"(thứ\s*[2-7]|chủ nhật|ngày mai|mai|hôm nay|tuần sau|thứ bảy|thứ 7|\d{1,2}[\/-]\d{1,2})", lowered)
    if date_match:
        date_val = date_match.group(1).capitalize()
        reqs.setdefault("preferred_date", date_val)
        if slug == "giup-viec":
            reqs.setdefault("preferred_schedule", date_val)

    # Service specific
    if slug == "van-chuyen-di-doi":
        # Origin / Destination
        from_to = re.search(r"(?:từ|đi từ)\s+([^,.\n]+?)\s+(?:sang|đến|qua|về)\s+([^,.\n]+)", text, re.IGNORECASE)
        if from_to:
            reqs.setdefault("origin", from_to.group(1).strip())
            reqs.setdefault("destination", from_to.group(2).strip())
        # Volume
        vol_match = re.search(r"(\d+\s*xe\s*tải[^\.,\n]*|xe\s*tải[^\.,\n]*|phòng trọ|căn hộ|nhà nguyên căn)", lowered)
        if vol_match:
            reqs.setdefault("estimated_volume", vol_match.group(1).strip())
        # Elevator / Stairs
        if "thang máy" in lowered:
            reqs.setdefault("elevator", "Có thang máy")
        elif "thang bộ" in lowered:
            reqs.setdefault("elevator", "Đi thang bộ")

    elif slug == "ve-sinh-cong-nghiep":
        # Building type
        for bt in ["nhà xưởng", "văn phòng", "nhà phố", "chung cư", "biệt thự", "công trình"]:
            if bt in lowered:
                reqs.setdefault("building_type", bt.capitalize())
                break
        # Condition
        if "sau xây dựng" in lowered or "mới xây" in lowered:
            reqs.setdefault("current_condition", "Sau xây dựng")
        elif "định kỳ" in lowered:
            reqs.setdefault("current_condition", "Vệ sinh định kỳ")
        elif "lâu ngày" in lowered or "bẩn nhiều" in lowered:
            reqs.setdefault("current_condition", "Lâu ngày chưa vệ sinh")

    elif slug == "cung-cap-quan-ly-lao-dong":
        # Quantity
        qty_match = re.search(r"(\d+)\s*(?:người|lao động|nhân sự|công nhân)", lowered)
        if qty_match:
            reqs.setdefault("quantity", f"{qty_match.group(1)} người")
        for lt in ["bốc xếp", "phụ kho", "đóng gói", "phụ việc", "thời vụ"]:
            if lt in lowered:
                reqs.setdefault("labor_type", lt.capitalize())
                break

    elif slug == "giup-viec":
        if "theo giờ" in lowered:
            reqs.setdefault("frequency", "Theo giờ")
        elif "định kỳ" in lowered or "cố định" in lowered:
            reqs.setdefault("frequency", "Định kỳ")
        for task in ["nấu ăn", "dọn dẹp", "giặt giũ", "trông trẻ", "rửa chén"]:
            if task in lowered:
                existing_tasks = reqs.get("tasks", "")
                if task not in existing_tasks.lower():
                    reqs["tasks"] = f"{existing_tasks}, {task}".strip(", ")

    elif slug == "diet-con-trung":
        for pest in ["mối", "muỗi", "gián", "kiến", "chuột", "bọ chét"]:
            if pest in lowered:
                reqs.setdefault("pest_type", pest.capitalize())

    return reqs


def get_conversational_quick_actions(slug: str | None, message: str = "", state_reqs: dict[str, Any] | None = None) -> list[str]:
    """Provide natural, helpful quick replies without acting as a questionnaire."""
    lowered = (message or "").lower()
    if any(k in lowered for k in ["cảm ơn", "cam on", "thank"]):
        return ["Xem dịch vụ khác", "Hotline 0901 040 484"]
    if any(k in lowered for k in ["tham khảo", "tham khao", "hỏi thôi"]):
        return ["Vệ sinh công nghiệp", "Vận chuyển di dời", "Hotline 0901 040 484"]
    if any(k in lowered for k in ["giá", "gia", "báo giá", "chi phí", "bao nhiêu"]):
        return ["Khảo sát miễn phí", "Tư vấn thêm", "Hotline 0901 040 484"]
    if any(k in lowered for k in ["chủ nhật", "thứ 7", "lịch", "giờ"]):
        return ["Đặt lịch cuối tuần", "Tư vấn thêm"]
    if slug == "van-chuyen-di-doi":
        return ["Chuyển nhà", "Chuyển văn phòng", "Chuyển trọ"]
    if slug == "ve-sinh-cong-nghiep":
        return ["Vệ sinh tổng thể", "Hạng mục cụ thể", "Khảo sát tận nơi"]
    if slug == "giup-viec":
        return ["Theo giờ", "Định kỳ tuần", "Có nấu ăn"]
    if slug == "cham-soc-cay-canh":
        return ["Cắt tỉa", "Bón phân", "Trị sâu bệnh"]
    if slug == "diet-con-trung":
        return ["Diệt mối", "Phun muỗi", "Diệt gián/chuột"]
    return ["Vệ sinh nhà", "Chuyển nhà", "Giúp việc theo giờ", "Dịch vụ khác"]


def get_next_question(slug: str, state_reqs: dict[str, Any], has_phone: bool) -> tuple[str | None, list[str]]:
    """Legacy helper: return natural quick actions without forcing a rigid questionnaire."""
    return (None, get_conversational_quick_actions(slug, "", state_reqs))


def build_confirmation_summary(slug: str, state_reqs: dict[str, Any], phone: str) -> str:
    spec = SERVICE_SPECS.get(slug, {})
    service_name = spec.get("name", "Dịch vụ")
    location = state_reqs.get("location") or state_reqs.get("origin") or state_reqs.get("destination") or "Chưa rõ"
    
    # Requirement summary
    req_parts = []
    for k, v in state_reqs.items():
        if k not in {"customer_name", "location", "phone"} and v:
            label = spec.get("fields", {}).get(k, {}).get("label", k)
            req_parts.append(f"{label}: {v}")
    req_text = "; ".join(req_parts) if req_parts else "Tư vấn dịch vụ"
    time_text = state_reqs.get("preferred_date") or state_reqs.get("preferred_schedule") or "Sớm nhất có thể"

    return (
        f"Em xin xác nhận lại thông tin của anh/chị ạ:\n"
        f"• Dịch vụ: {service_name}\n"
        f"• Khu vực: {location}\n"
        f"• Nhu cầu: {req_text}\n"
        f"• Thời gian: {time_text}\n"
        f"• Số điện thoại: {phone}\n\n"
        f"Thông tin trên đã chuẩn xác chưa ạ?"
    )
