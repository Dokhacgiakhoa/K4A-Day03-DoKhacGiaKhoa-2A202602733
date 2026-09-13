# 📊 BÁO CÁO THU HOẠCH NGHIỆM THU BÀI LAB 3 (BƯỚC 3 — SUBMISSION ARTIFACT)

> **Họ và Tên Học viên:** Đỗ Khắc Gia Khoa
> **Mã Sinh Viên / Mã Học viên:** 2A202602733
> **Chủ đề Lựa chọn:** Gợi ý 1.1 — Trợ lý Học vụ & Tra cứu Lịch thi VinUni (Lĩnh vực Giáo dục & Đào tạo)

---

## 1. BẢNG CHẤM ĐIỂM AGENTIC FIT SCORING MATRIX (ĐÁNH GIÁ CHỦ ĐỀ)

| Tiêu chí Đánh giá | Mức độ (1 - 5) | Giải trình chi tiết lý do chọn điểm |
| :--- | :---: | :--- |
| **1. Multi-step Reasoning** | 4 / 5 | Bài toán có chuỗi suy luận nối tiếp: ví dụ TC04 yêu cầu Agent tra cứu cố vấn học tập của sinh viên **trước**, rồi dùng chính thông tin đó để đặt lịch hẹn. Nhiều tình huống cần ≥ 2 bước suy luận. |
| **2. Tool Interaction** | 5 / 5 | Bắt buộc kết nối MCP Server để gọi 2 công cụ thực tế (`academic_query`, `schedule_appointment`). Không thể trả lời chính xác GPA/email/booking nếu không gọi Tool → phụ thuộc Tool rất cao. |
| **3. Dynamic Decision** | 4 / 5 | Bước tiếp theo phụ thuộc kết quả Observation: nếu Tool trả về `NOT_FOUND` (TC05) Agent phải đổi hướng phản hồi lịch sự thay vì bịa dữ liệu; nếu `SUCCESS` thì tổng hợp câu trả lời. |
| **4. Long Horizon Goal** | 3 / 5 | Mục tiêu duy trì trong phạm vi một phiên hội thoại (tra cứu → đặt lịch). Chưa yêu cầu ghi nhớ dài hạn xuyên nhiều phiên (đó là đặc trưng của Agent Cấp 4). |
| **TỔNG ĐIỂM AGENTIC FIT** | **16 / 20** | *Tổng điểm 16/20 > 12/20 → Bài toán RẤT PHÙ HỢP triển khai Agentic System (ReAct Agent).* |

---

## 2. TRÍCH XUẤT KẾT QUẢ WATERFALL TRACE LOG (SAU KHI CHẠY TEST SUITE TRÊN API THẬT)

> ✅ **Nghiệm thu trên LLM thật:** Đã cấu hình `GEMINI_API_KEY` trong `.env`, Provider = `GeminiProvider`, Model = `gemini-flash-latest`. Lệnh chạy: `python src/app.py --all`.

Đoạn trích tiêu biểu từ `docs/trace_waterfall.json` — thể hiện đầy đủ chuỗi **Action (Tool Execution) → Observation → Final Answer** do Gemini quyết định gọi Tool qua MCP Server:

```json
[
  {
    "step": 1,
    "query": "Hãy tra cứu thông tin học vụ của sinh viên SV2026001.",
    "action_type": "TOOL_EXECUTION",
    "tool_name": "academic_query",
    "arguments": {
      "student_id": "SV2026001"
    },
    "observation": {
      "status": "SUCCESS",
      "student_id": "SV2026001",
      "data": {
        "full_name": "Nguyễn Văn An",
        "class": "AI-K4",
        "gpa": 3.85,
        "email": "an.nv@vinuni.edu.vn",
        "status": "Đang học",
        "advisor": "PGS.TS Nguyễn Văn A"
      }
    },
    "latency_ms": 2245.3
  },
  {
    "step": 2,
    "query": "Hãy tra cứu thông tin học vụ của sinh viên SV2026001.",
    "action_type": "FINAL_ANSWER",
    "thought": "Tổng hợp kết quả từ MCP Server thành công.",
    "output": "Kết quả tra cứu cho sinh viên SV2026001 (Nguyễn Văn An): Lớp AI-K4, GPA: 3.85, Email: an.nv@vinuni.edu.vn, Trạng thái: Đang học, Cố vấn: PGS.TS Nguyễn Văn A.",
    "latency_ms": 10.0
  }
]
```

**Kiểm chứng chống ảo giác (Anti-Hallucination) qua TC05:** Với mã `SV9999999` không tồn tại, Gemini gọi đúng `academic_query(student_id="SV9999999")`, MCP Server trả `status: "NOT_FOUND"`, và Agent phản hồi trung thực *"Không tìm thấy dữ liệu sinh viên có mã 'SV9999999'"* — **không bịa** thông tin. Đây là bằng chứng Agent chạy trên dữ liệu Tool thật, không phải Mock (Mock luôn trả về SV2026001).

---

## 3. TỔNG KẾT KẾT QUẢ NGHIỆM THU & NỘP BÀI

- [x] Đã điền API Key thật trong `.env` và xác nhận Agent chạy mượt mà trên LLM API thật (Gemini `gemini-3.6-flash`).
- **Tổng số Test Cases đã chạy thành công:** 5 / 5 test cases.
- **Số lượt gọi Tool qua MCP Server chính xác:** 4 lượt (TC02: `academic_query`, TC03: `schedule_appointment`, TC04: `schedule_appointment`, TC05: `academic_query`). Riêng TC01 Agent trả lời trực tiếp không cần Tool — đúng kỳ vọng.
- **Kết quả đẩy Repo nộp bài:** [ ] Đã Commit và Push mã nguồn thành công lên GitHub cá nhân.

### 📋 Bảng kết quả Test Suite

| Test | Loại | Độ phức tạp | Kết quả | Tool được gọi |
| :---: | :--- | :---: | :---: | :--- |
| TC01 | direct_query | Low | ✅ PASS | (trả lời trực tiếp) |
| TC02 | single_tool_query | Medium | ✅ PASS | `academic_query` |
| TC03 | appointment_booking | Medium | ✅ PASS | `schedule_appointment` |
| TC04 | multi_step_reasoning | High | ✅ PASS | `schedule_appointment` |
| TC05 | edge_case_handling | Medium | ✅ PASS | `academic_query` (→ NOT_FOUND) |

---

## 4. 🎁 PHẦN MỞ RỘNG — AGENT NÂNG CAO + WEB REACT + DEPLOY (BONUS)

Ngoài yêu cầu core (CLI + trace log 2 tool), đồ án nâng cấp agent "làm được nhiều hơn" và bổ sung giao diện React trực quan:

**Năng lực Agent nâng cao:**
- **6 Tools qua MCP:** `academic_query`, `schedule_appointment`, `get_current_datetime` (thời gian thực), `get_exam_schedule` (lịch thi), `register_course` (đăng ký môn), `search_guidebook` (tra cứu Sổ tay chương trình 'AI in Action' từ kho tri thức thật).
- **ReAct ĐA BƯỚC thật sự:** Agent gọi nhiều Tool nối tiếp trong một câu hỏi. Ví dụ đã kiểm chứng: *"Tra cứu cố vấn của SV2026001 rồi đặt lịch với đúng cố vấn đó vào 09:30 ngày 20/09/2026"* → Agent gọi `academic_query` → dùng kết quả (cố vấn PGS.TS Nguyễn Văn A) → gọi tiếp `schedule_appointment`. Kỹ thuật: nạp lại Observation cho LLM qua `provider.run_agent`, bảo toàn `thought_signature` của Gemini.
- **Trí nhớ hội thoại:** frontend gửi kèm lịch sử các lượt trước để Agent hiểu ngữ cảnh câu hỏi nối tiếp.

**Kiến trúc Web:**
- **Backend:** FastAPI (`web/backend.py`) — tái sử dụng 100% lớp MCP Server, Tool Router, LLM Provider của core; API `POST /api/chat` (nhận `query` + `history`, chạy ReAct đa bước, trả JSON các bước) và `GET /api/info`.
- **Frontend:** **React (Vite + Tailwind + framer-motion + lucide-react)** tại `web/frontend/`, build ra `web/static_react/`. **Bố cục 2 cột:** trái = khung hội thoại; phải = luồng suy luận trực quan (mỗi bước Thought/Action/Observation/Final là card màu riêng, có animation, latency, JSON tô màu). Header hiển thị Provider/Model/MCP + badge LIVE/MOCK.
- **CLI nâng cấp:** `src/app.py` dùng `rich` (Panel/Table/spinner) + bảng tổng kết Test Suite.
- **Deploy:** `render.yaml` (Blueprint) — bản React đã build được commit nên Render chỉ chạy Python; `GEMINI_API_KEY` đặt trong Environment (secret), không commit.

Lệnh chạy Web UI local:
```bash
python web/backend.py   # http://localhost:8000
```

**Nguồn dữ liệu Sổ tay:** kho FAQ thật của chương trình VinUni AI in Action (học phí & trợ cấp 8 triệu/tháng, lịch học 9h–13h, yêu cầu tiếng Anh, thực tập 6 tuần, cấu trúc thi ĐGNL 90 phút, cơ hội việc làm).

---

> ✅ **HOÀN TẤT NỘP BÀI:** Sao chép đường link GitHub Repository cá nhân của bạn và dán vào ô nộp bài trên hệ thống LMS VLearn để hoàn tất Bài Lab 3!
