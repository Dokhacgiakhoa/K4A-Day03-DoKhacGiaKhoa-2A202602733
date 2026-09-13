"""
🛠️ TOOL DEFINITIONS & EXECUTION BACKEND
Mã nguồn chứa danh sách Tool Schemas (JSON Schema) và Execution Layer phục vụ cho MCP Server.

Bản mở rộng (Giai đoạn 2): bổ sung thêm các công cụ giúp Agent "làm được nhiều hơn":
  - get_current_datetime : Thời gian thực (ngày/giờ hiện tại)
  - get_exam_schedule    : Tra cứu lịch thi của sinh viên
  - register_course      : Đăng ký môn học (công cụ hành động)
cùng với 2 công cụ gốc (academic_query, schedule_appointment).
"""

import json
from datetime import datetime
from typing import Dict, Any

try:
    from zoneinfo import ZoneInfo
    _TZ = ZoneInfo("Asia/Ho_Chi_Minh")
except Exception:  # pragma: no cover - fallback nếu hệ thống thiếu tzdata
    _TZ = None

# ==============================================================================
# 1. KHAI BÁO TOOL SCHEMAS CHUẨN NATIVE JSON SCHEMA (TASK 1.2)
# ==============================================================================

TOOLS_SCHEMA = [
    # Tool 1: Đã được định nghĩa mẫu sẵn cho Học viên tham khảo
    {
        "name": "academic_query",
        "description": "Tra cứu hồ sơ và thông tin học vụ của sinh viên VinUni bằng mã sinh viên.",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "Mã sinh viên cần tra cứu (ví dụ: 'SV2026001')"
                }
            },
            "required": ["student_id"]
        }
    },

    # Tool 2 (TASK 1.2): Đặt lịch hẹn tư vấn học vụ
    {
        "name": "schedule_appointment",
        "description": "Đặt lịch hẹn tư vấn học vụ với Cố vấn học tập VinUni.",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "Mã sinh viên cần đặt lịch hẹn (ví dụ: 'SV2026001')"
                },
                "datetime_str": {
                    "type": "string",
                    "description": "Thời gian hẹn tư vấn theo định dạng giờ và ngày (ví dụ: '14:00 15/09/2026')"
                },
                "advisor_name": {
                    "type": "string",
                    "description": "Tên cố vấn học tập phụ trách buổi tư vấn (ví dụ: 'PGS.TS Nguyễn Văn A')"
                }
            },
            "required": ["student_id", "datetime_str", "advisor_name"]
        }
    },

    # ---- TOOLS MỞ RỘNG (Giai đoạn 2) --------------------------------------
    # Tool 3: Thời gian thực
    {
        "name": "get_current_datetime",
        "description": "Trả về ngày, thứ và giờ ở thời điểm hiện tại (múi giờ Việt Nam). "
                       "Chỉ dùng khi người dùng hỏi đích danh về thời điểm hiện tại như 'hôm nay là ngày mấy', 'bây giờ mấy giờ', 'hôm nay thứ mấy'.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },

    # Tool 4: Tra cứu lịch thi
    {
        "name": "get_exam_schedule",
        "description": "Tra cứu lịch thi (môn học, ngày thi, phòng thi) của một sinh viên VinUni theo mã sinh viên.",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "Mã sinh viên cần tra cứu lịch thi (ví dụ: 'SV2026001')"
                }
            },
            "required": ["student_id"]
        }
    },

    # Tool 5: Đăng ký môn học (công cụ hành động)
    {
        "name": "register_course",
        "description": "Đăng ký một môn học mới cho sinh viên VinUni trong học kỳ hiện tại bằng mã môn học.",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "Mã sinh viên đăng ký môn (ví dụ: 'SV2026001')"
                },
                "course_code": {
                    "type": "string",
                    "description": "Mã môn học cần đăng ký (ví dụ: 'CS201', 'AI305')"
                }
            },
            "required": ["student_id", "course_code"]
        }
    },

    # Tool 6: Tra cứu sổ tay chương trình (RAG-lite trên kho tri thức thật)
    {
        "name": "search_guidebook",
        "description": "Tra cứu Sổ tay chương trình 'VinUni AI in Action'. DÙNG cho mọi câu hỏi kiến thức chung về chương trình: "
                       "học phí, TRỢ CẤP / PHỤ CẤP HÀNG THÁNG (8 triệu/tháng) và điều kiện nhận, lịch học, yêu cầu tiếng Anh, "
                       "thực tập, cấu trúc bài thi ĐGNL, cơ hội nghề nghiệp/mức lương, quy mô & triết lý đào tạo. "
                       "Đây là tool đúng cho câu hỏi về 'trợ cấp hàng tháng bao nhiêu'.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Nội dung/chủ đề cần tra cứu (ví dụ: 'trợ cấp hàng tháng', 'bài thi ĐGNL', 'yêu cầu tiếng Anh')"
                }
            },
            "required": ["query"]
        }
    }
]

# ==============================================================================
# 2. MÔ PHỎNG DỮ LIỆU & HÀM THỰC THI TOOL (EXECUTION LAYER)
# ==============================================================================

MOCK_DATABASE = {
    "SV2026001": {
        "full_name": "Nguyễn Văn An",
        "class": "AI-K4",
        "gpa": 3.85,
        "email": "an.nv@vinuni.edu.vn",
        "status": "Đang học",
        "advisor": "PGS.TS Nguyễn Văn A"
    },
    "SV2026002": {
        "full_name": "Trần Thị Bình",
        "class": "AI-K4",
        "gpa": 3.60,
        "email": "binh.tt@vinuni.edu.vn",
        "status": "Đang học",
        "advisor": "TS. Lê Thị B"
    },
    "SV2026003": {
        "full_name": "Phạm Minh Cường",
        "class": "CS-K4",
        "gpa": 3.20,
        "email": "cuong.pm@vinuni.edu.vn",
        "status": "Đang học",
        "advisor": "TS. Trần Văn C"
    },
    "SV2026004": {
        "full_name": "Lê Thu Dung",
        "class": "DS-K4",
        "gpa": 3.95,
        "email": "dung.lt@vinuni.edu.vn",
        "status": "Bảo lưu",
        "advisor": "PGS.TS Nguyễn Văn A"
    }
}

# Lịch thi mô phỏng theo từng sinh viên
EXAM_SCHEDULE = {
    "SV2026001": [
        {"course": "Nhập môn Trí tuệ Nhân tạo (AI101)", "date": "18/12/2026", "time": "08:00", "room": "B2-305"},
        {"course": "Giải tích 2 (MATH102)", "date": "22/12/2026", "time": "13:30", "room": "A1-201"}
    ],
    "SV2026002": [
        {"course": "Học máy (AI201)", "date": "19/12/2026", "time": "08:00", "room": "B2-410"},
        {"course": "Xác suất Thống kê (MATH205)", "date": "23/12/2026", "time": "10:00", "room": "A1-108"}
    ],
    "SV2026003": [
        {"course": "Cấu trúc Dữ liệu & Giải thuật (CS201)", "date": "20/12/2026", "time": "13:30", "room": "C3-102"}
    ]
}

# Môn học đang mở đăng ký (mô phỏng)
AVAILABLE_COURSES = {
    "CS201": "Cấu trúc Dữ liệu & Giải thuật",
    "AI305": "Học sâu Nâng cao (Advanced Deep Learning)",
    "DS210": "Trực quan hóa Dữ liệu",
    "MATH205": "Xác suất Thống kê"
}


def execute_academic_query(student_id: str) -> str:
    """Thực thi tra cứu học vụ theo mã sinh viên"""
    student = MOCK_DATABASE.get(student_id.strip().upper())
    if student:
        message = (
            f"Hồ sơ sinh viên **{student_id.strip().upper()}**:\n"
            f"- 👤 Họ tên: **{student['full_name']}**\n"
            f"- 🏫 Lớp: {student['class']}\n"
            f"- 📊 GPA: **{student['gpa']}**\n"
            f"- 📧 Email: {student['email']}\n"
            f"- 🧑‍🏫 Cố vấn: {student['advisor']}\n"
            f"- 🔖 Trạng thái: {student['status']}"
        )
        return json.dumps({
            "status": "SUCCESS",
            "student_id": student_id,
            "data": student,
            "message": message
        }, ensure_ascii=False)
    else:
        return json.dumps({
            "status": "NOT_FOUND",
            "message": f"Không tìm thấy dữ liệu sinh viên có mã '{student_id}'"
        }, ensure_ascii=False)


def execute_schedule_appointment(student_id: str, datetime_str: str, advisor_name: str = "PGS.TS Nguyễn Văn A") -> str:
    """Thực thi đặt lịch hẹn tư vấn học vụ"""
    return json.dumps({
        "status": "SUCCESS",
        "booking_id": f"BK-{student_id}-99",
        "student_id": student_id,
        "datetime": datetime_str,
        "advisor": advisor_name,
        "message": f"Đặt lịch thành công cho sinh viên {student_id} với {advisor_name} vào lúc {datetime_str}."
    }, ensure_ascii=False)


def execute_get_current_datetime() -> str:
    """Trả về ngày giờ hiện tại thực tế (múi giờ Việt Nam)."""
    now = datetime.now(_TZ) if _TZ else datetime.now()
    weekdays = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
    weekday = weekdays[now.weekday()]
    return json.dumps({
        "status": "SUCCESS",
        "iso": now.isoformat(),
        "date": now.strftime("%d/%m/%Y"),
        "time": now.strftime("%H:%M:%S"),
        "weekday": weekday,
        "timezone": "Asia/Ho_Chi_Minh",
        "message": f"Bây giờ là {now.strftime('%H:%M')} {weekday}, ngày {now.strftime('%d/%m/%Y')} (giờ Việt Nam)."
    }, ensure_ascii=False)


def execute_get_exam_schedule(student_id: str) -> str:
    """Tra cứu lịch thi của sinh viên."""
    sid = student_id.strip().upper()
    if sid not in MOCK_DATABASE:
        return json.dumps({
            "status": "NOT_FOUND",
            "message": f"Không tìm thấy sinh viên có mã '{student_id}'"
        }, ensure_ascii=False)
    exams = EXAM_SCHEDULE.get(sid, [])
    if not exams:
        return json.dumps({
            "status": "SUCCESS",
            "student_id": sid,
            "exams": [],
            "message": f"Sinh viên {sid} hiện chưa có lịch thi nào được công bố."
        }, ensure_ascii=False)
    lines = "\n".join(f"- 📝 **{e['course']}** — {e['date']} lúc {e['time']}, phòng {e['room']}" for e in exams)
    return json.dumps({
        "status": "SUCCESS",
        "student_id": sid,
        "exams": exams,
        "message": f"Lịch thi của sinh viên **{sid}**:\n{lines}"
    }, ensure_ascii=False)


def execute_register_course(student_id: str, course_code: str) -> str:
    """Đăng ký môn học cho sinh viên (công cụ hành động)."""
    sid = student_id.strip().upper()
    code = course_code.strip().upper()
    if sid not in MOCK_DATABASE:
        return json.dumps({
            "status": "NOT_FOUND",
            "message": f"Không tìm thấy sinh viên có mã '{student_id}'"
        }, ensure_ascii=False)
    if code not in AVAILABLE_COURSES:
        return json.dumps({
            "status": "INVALID_COURSE",
            "message": f"Mã môn '{course_code}' không có trong danh sách môn đang mở đăng ký: {', '.join(AVAILABLE_COURSES.keys())}."
        }, ensure_ascii=False)
    return json.dumps({
        "status": "SUCCESS",
        "registration_id": f"REG-{sid}-{code}",
        "student_id": sid,
        "course_code": code,
        "course_name": AVAILABLE_COURSES[code],
        "message": f"Đăng ký thành công môn {code} ({AVAILABLE_COURSES[code]}) cho sinh viên {sid}."
    }, ensure_ascii=False)


# Kho tri thức Sổ tay chương trình (trích từ FAQ thật của "VinUni AI in Action")
# content được viết sẵn dạng Markdown bullet + emoji để câu trả lời trình bày đẹp, đồng nhất.
GUIDEBOOK_KB = [
    {
        "keywords": ["tổng quan", "quy mô", "triết lý", "challenge", "cbl", "4 thật", "mục tiêu", "chương trình"],
        "title": "Tổng quan & Triết lý chương trình AI in Action",
        "content": ("- 🎯 **Mục tiêu:** đào tạo **10.000–20.000 nhân tài AI** trong 2 năm (hưởng ứng Nghị quyết 57-NQ/TW).\n"
                    "- 🧪 **Triết lý 4 Thật:** Bài toán thật · Dữ liệu thật · Chuyên gia thật · Cơ hội việc làm thật.\n"
                    "- 🚀 **Cách học:** Challenge-Based Learning với **~160 bài mô phỏng** và **200+ bài toán AI thực tế**.\n"
                    "- 📊 **Đánh giá:** năng lực toàn diện **mỗi 2 tuần/lần**.")
    },
    {
        "keywords": ["học phí", "trợ cấp", "phụ cấp", "8 triệu", "tài trợ", "sinh hoạt phí", "tiền", "miễn phí", "học bổng"],
        "title": "Học phí & Trợ cấp",
        "content": ("- 💰 **Miễn 100% học phí** trong suốt chương trình.\n"
                    "- 🏠 Trợ cấp sinh hoạt **8.000.000đ/tháng** trong **12 tuần** đào tạo.\n"
                    "- ✅ **Điều kiện:** chuyên cần **≥ 90%**, nộp bài/dự án đúng hạn và đạt đánh giá từ Mentor & Ban Đào tạo.")
    },
    {
        "keywords": ["lịch học", "giờ học", "buổi sáng", "mấy giờ", "ca sáng", "thời gian học"],
        "title": "Lịch học",
        "content": ("- ⏰ Ca sáng học từ **9h00** (khung AI20K Time **9h00–13h00**), trừ thông báo đặc biệt.\n"
                    "- 🪑 Nên có mặt **trước 10–15 phút** để chuẩn bị máy và điểm danh.")
    },
    {
        "keywords": ["tiếng anh", "english", "ngôn ngữ", "từ vựng"],
        "title": "Yêu cầu Tiếng Anh",
        "content": ("- 🗣️ **Không bắt buộc** giỏi tiếng Anh giao tiếp — slide và bài giảng bằng **tiếng Việt**.\n"
                    "- 📖 Cần **học từ vựng tiếng Anh chuyên ngành** AI/CNTT vì thuật ngữ xuất hiện nhiều.")
    },
    {
        "keywords": ["thực tập", "6 tuần", "doanh nghiệp", "internship", "full-time", "công ty"],
        "title": "Thực tập 6 tuần",
        "content": ("- 🏢 **6 tuần cuối khóa** thực tập **full-time** tại công ty công nghệ, tập đoàn đối tác hoặc viện nghiên cứu.\n"
                    "- 👨‍🏫 Tham gia **dự án thật** dưới sự giám sát của Mentor doanh nghiệp.")
    },
    {
        "keywords": ["đgnl", "bài thi", "đầu vào", "tuyển chọn", "đánh giá năng lực", "thi", "cấu trúc"],
        "title": "Bài thi Đánh giá Năng lực (ĐGNL)",
        "content": ("- 📋 **Tuyển chọn 2 vòng:** Vòng 1 xét hồ sơ online; Vòng 2 thi trực tiếp tại VinUni (Vinhomes Ocean Park, Hà Nội).\n"
                    "- ⏱️ **Bài thi 90 phút:** trắc nghiệm, đọc code ngắn và tự luận tình huống.\n"
                    "- 🧮 **Nhóm 1 — Toán / Định lượng**\n"
                    "- 💻 **Nhóm 2 — Lập trình & Dữ liệu** (Python, SQL)\n"
                    "- 🤖 **Nhóm 3 — Kiến thức & Tư duy Sản phẩm AI** (ML/LLM/RAG/Agent)\n"
                    "- ⚖️ **Nhóm 4 — Logic, Đạo đức & Hành vi**")
    },
    {
        "keywords": ["việc làm", "nghề nghiệp", "tuyển dụng", "lương", "vingroup", "cơ hội", "offer", "ra trường"],
        "title": "Cơ hội nghề nghiệp & Mức lương",
        "content": ("- 🎖️ **100%** học viên Khóa 1 đạt chuẩn năng lực VinUni (373/500) nhận **Offer từ Vingroup**.\n"
                    "- 💼 **95%** làm đúng chuyên môn: AI Engineer, Data Engineer, Software Dev, PM, BA.\n"
                    "- 💵 Lương khởi điểm tới **~50.000.000đ/tháng**.")
    }
]


def execute_search_guidebook(query: str) -> str:
    """Tra cứu Sổ tay chương trình theo từ khóa (RAG-lite)."""
    q = (query or "").strip().lower()
    if not q:
        return json.dumps({"status": "EMPTY_QUERY", "message": "Vui lòng cung cấp nội dung cần tra cứu."}, ensure_ascii=False)

    scored = []
    for entry in GUIDEBOOK_KB:
        score = sum(1 for kw in entry["keywords"] if kw in q)
        # cộng điểm nếu từ khóa xuất hiện trong tiêu đề
        if any(kw in q for kw in entry["title"].lower().split()):
            score += 1
        if score > 0:
            scored.append((score, entry))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = [e for _, e in scored[:2]]

    if not top:
        return json.dumps({
            "status": "NO_MATCH",
            "message": ("Không tìm thấy mục phù hợp trong Sổ tay. Các chủ đề có sẵn: học phí & trợ cấp, lịch học, "
                        "yêu cầu tiếng Anh, thực tập, bài thi ĐGNL, cơ hội nghề nghiệp, tổng quan chương trình.")
        }, ensure_ascii=False)

    results = [{"title": e["title"], "content": e["content"]} for e in top]
    # message = nội dung mục liên quan nhất (sạch, không nhãn ngoặc) để LLM diễn đạt lại
    message = results[0]["content"]
    return json.dumps({
        "status": "SUCCESS",
        "query": query,
        "topic": results[0]["title"],
        "results": results,
        "message": message
    }, ensure_ascii=False)


# Router gọi tool thực tế
TOOL_ROUTER = {
    "academic_query": execute_academic_query,
    "schedule_appointment": execute_schedule_appointment,
    "get_current_datetime": execute_get_current_datetime,
    "get_exam_schedule": execute_get_exam_schedule,
    "register_course": execute_register_course,
    "search_guidebook": execute_search_guidebook
}

def dispatch_tool_call(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Hàm trung chuyển thực thi tool"""
    if tool_name in TOOL_ROUTER:
        try:
            return TOOL_ROUTER[tool_name](**arguments)
        except Exception as e:
            return json.dumps({"status": "EXECUTION_ERROR", "error": str(e)}, ensure_ascii=False)
    return json.dumps({"status": "UNKNOWN_TOOL", "error": f"Tool '{tool_name}' không tồn tại!"}, ensure_ascii=False)
