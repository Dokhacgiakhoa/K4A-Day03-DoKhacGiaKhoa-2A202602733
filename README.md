# 🏫 BÀI LAB 3: CHATBOT VS REACT AGENT — TỪ LÝ THUYẾT ĐẾN THỰC THI (MCP ENHANCED)

> **Mã bài học:** `DAY03-REACT-AGENT`  
> **Hình thức thực hiện:** **CÁ NHÂN** *(Mỗi học viên tự làm và tự nộp 1 bài cá nhân)*  
> **Quy chuẩn nộp bài:** Học viên Fork Repo này về GitHub cá nhân và đổi tên theo đúng cú pháp:  
> 📌 **`K4-DAY03-HoVaTen-MSSV`** *(Ví dụ: `K4-DAY03-NguyenVanA-SV2026001`)*  

---

## ⚡ 1. QUICKSTART — CÀI ĐẶT MÔI TRƯỜNG & CHẠY THỬ (3 PHÚT)

> 🐍 **Yêu cầu môi trường Python:** **Python 3.10 – 3.12** *(Tránh Python 3.9 do thiếu type hinting hiện đại và Python 3.13 do nhiều thư viện AI chưa hỗ trợ pre-built wheel)*.

Thực hiện 3 bước lệnh Terminal thiết thực ngay khi clone repo về máy:

### Bước 1: Clone Repo & Tạo môi trường ảo
```bash
git clone https://github.com/<tai_khoan_cua_ban>/K4-DAY03-HoVaTen-MSSV.git
cd K4-DAY03-HoVaTen-MSSV

python -m venv .venv
# Trên Windows PowerShell:
.venv\Scripts\Activate.ps1
# Trên macOS / Linux / Bash / Zsh:
source .venv/bin/activate
```

### Bước 2: Cài đặt thư viện & Tạo file cấu hình môi trường
```bash
pip install -r requirements.txt
# Trên Windows CMD/PowerShell:
copy .env.example .env
copy config\test_cases.example.json config\test_cases.json
# Trên macOS / Linux:
cp .env.example .env
cp config/test_cases.example.json config/test_cases.json
```

### Bước 3: Chạy thử Baseline kiểm tra môi trường
```bash
python src/app.py --all
```

**Kỳ vọng Output màn hình:**
```text
✅ [MOCK OFFLINE MODE PASS]: Môi trường đã sẵn sàng! 
📊 [KẾT QUẢ TEST SUITE]: 2 Đã chạy (TC01, TC02 mẫu) | 3 Đang chờ viết câu hỏi (TODO)
```

> 🔑 **QUY ĐỊNH BẮT BUỘC VỀ API KEY VÀ NỘP BÀI (SUBMISSION REQUIREMENT):**  
> 
> 1. **Giai đoạn gõ code & debug (Miễn phí 0đ):** Hệ thống mặc định chạy `MockOfflineProvider` giúp bạn thực hành gõ code, kiểm thử logic ban đầu hoàn toàn miễn phí, không tốn token, không lo nghẽn mạng.  
> 2. **Giai đoạn NỘP BÀI CHÍNH THỨC (Bắt buộc dùng LLM thật):** Khi chạy nghiệm thu để lấy dữ liệu dán vào báo cáo [`docs/trace_eval.md`](docs/trace_eval.md) nộp bài, **học viên BẮT BUỘC phải mở file `.env` điền `GEMINI_API_KEY` (hoặc `OPENAI_API_KEY`)** để Agent giao tiếp với mô hình LLM thật.  
> 
> ⚠️ *Lưu ý:* Bài nộp chỉ chạy trên Mock Provider mà không kết nối LLM API thật sẽ bị trừ điểm phần nghiệm thu thực tế (Tiêu chí 2 & Tiêu chí 3 trong Rubric).

---

## 🎯 2. BỨC TRANH TỔNG THỂ & MỤC TIÊU DÀI HẠN (NORTH STAR GOAL)

Mục tiêu cốt lõi của Bài Lab này là giúp học viên tự tay phát triển một **Trợ lý Tác tử ReAct (ReAct Agent)** hoàn chỉnh.

Thay vì chỉ sinh văn bản hội thoại đơn thuần như Chatbot cơ bản, tác tử (Agent) của bạn sẽ có khả năng:
1. **Tự suy luận và chọn công cụ:** Chủ động kích hoạt vòng lặp ReAct (`Thought -> Action -> Observation`) qua giao thức **Model Context Protocol (MCP)** để truy vấn dữ liệu thực tế.
2. **Tổng hợp câu trả lời chính xác:** Sử dụng dữ liệu thực tế từ Tool trả về để trả lời sinh viên, tránh hiện tượng ảo giác (Hallucination).
3. **Trích xuất bằng chứng (Trace Log):** Ghi lại file vết `docs/trace_waterfall.json` chứng minh chuỗi suy luận từng bước của Agent.

> 🌐 **GIAO THỨC MODEL CONTEXT PROTOCOL (MCP):**  
> Mã nguồn [`src/mcp_server.py`](src/mcp_server.py) mô phỏng kiến trúc MCP Server chuẩn (giao tiếp Client-Server độc lập qua giao thức JSON-RPC 2.0). Agent Core ([`src/app.py`](src/app.py)) đóng vai trò MCP Client gửi yêu cầu thực thi Tool tới MCP Server.

---

## 🗺️ 3. LUỒNG THỰC HÀNH TINH GIẢN 3 BƯỚC (DOCUMENTATION FLOW)

Học viên làm bài lần lượt theo đúng luồng 3 bước tinh giản dưới đây:

| Bước | Tài liệu / Hành động | Nội dung thực hiện |
| :---: | :--- | :--- |
| **Bước 1** | 📄 **`README.md`** *(Hiện tại)* | Nắm quy chế, chạy Quickstart verify môi trường offline miễn phí. |
| **Bước 2** | 🎓 **`docs/CODELAB.md`** | **[TRỌNG TÂM]** Chọn bài toán (Tham khảo gợi ý tại [docs/DANH_SACH_DE_TAI.md](docs/DANH_SACH_DE_TAI.md)) ➔ Phân tích Agentic Fit ➔ Điền `GEMINI_API_KEY` ➔ Code từng task theo checklist. |
| **Bước 3** | 📊 **`docs/trace_eval.md`** | Chạy test suite với API thật, xuất trace log, hoàn thiện báo cáo thu hoạch duy nhất và push repo nộp bài. |

---

## ⏱️ 4. PHÂN BỔ THỜI GIAN (180 PHÚT LÀM BÀI)

* **Phần 1 (45 phút):** Agentic Fit & Tool Schemas (Đánh giá 4 tiêu chí Fit & Khai báo Tool Schema chuẩn JSON Schema)
* **Phần 2 (60 phút):** ReAct Loop & MCP Integration (Viết hàm MCP Server & Vòng lặp Thought -> Action -> Observation)
* **Phần 3 (45 phút):** Test Execution & Waterfall Log (Cắm API Key thật, chạy 5 Test Cases & Xuất file docs/trace_waterfall.json)
* **Phần 4 (30 phút):** Self-Audit & Push GitHub (Tự kiểm tra code, hoàn thiện báo cáo docs/trace_eval.md & push bài nộp lên GitHub cá nhân)

---

## 📂 5. CẤU TRÚC THƯ MỤC DỰ ÁN

```text
📁 K4-Day03-Lab-Chatbot-vs-ReAct-Agent-MCP/
├── 📄 README.md                 <-- ⚡ [BƯỚC 1] Quickstart setup & Cảnh báo quy định API Key
├── 📄 .env.example              <-- 🔑 File cấu hình API Key (Gemini, OpenAI, Anthropic, Mock)
├── 📄 requirements.txt          <-- 📦 Thư viện Python tương thích đa nền tảng
│
├── 📁 config/
│   ├── 📄 test_cases.example.json <-- 🟢 Mẫu Bộ 5 Test Cases (Copy thành test_cases.json)
│   └── 📄 test_cases.json         <-- 🟢 Bộ 5 Test Cases tùy biến theo đề tài của bạn
│
├── 📁 src/                      <-- 💻 MÃ NGUỒN PYTHON
│   ├── 📄 mcp_server.py         <-- 🌐 MCP Server quản lý Tool Registry & JSON-RPC Dispatcher
│   ├── 📄 tools.py              <-- 🛠️ Backend Tool Schemas JSON & Execution Layer
│   ├── 📄 prompts.py            <-- 🛡️ System Prompts cho Chatbot và ReAct Agent
│   ├── 📄 providers.py          <-- 🔌 Multi-Provider LLM Adapter (Gemini/OpenAI/Mock)
│   ├── 📄 app.py                <-- 🚀 MCP Client & Core Agent App ghép nối ReAct Loop & Trace Log
│   └── 📁 ai_levels/            <-- 📚 [REFERENCE ONLY] Code mẫu kiến trúc tham khảo (Không sửa/debug)
│       └── 📄 README.md         <-- ⚠️ Chú thích mã nguồn tham khảo
│
└── 📁 docs/                     <-- 📚 TÀI LIỆU HƯỚNG DẪN CHUẨN VLEARN CODELAB
    ├── 📄 DANH_SACH_DE_TAI.md    <-- 💡 Gợi ý chủ đề theo Lĩnh vực & Đề tài Mở
    ├── 📄 CODELAB.md            <-- 🎓 [BƯỚC 2 - TRỌNG TÂM] Hướng dẫn Codelab thực hành theo checklist
    └── 📄 trace_eval.md          <-- 📊 [BƯỚC 3] File Báo cáo Nộp bài duy nhất (Submission Report Artifact)
```

---

## 💯 6. THANG ĐIỂM ĐÁNH GIÁ (SCORING RUBRIC 100%)

| Tiêu chí | Trọng số | Mô tả chi tiết | Bằng chứng kiểm tra (Artifacts) |
| :--- | :---: | :--- | :--- |
| **1. Agentic Fit & Tool Specs** | **25%** | Phân tích đúng 4 tiêu chí Agentic Fit. Khai báo Tool Schema chuẩn JSON Schema. | Bảng Scoring Matrix (`docs/trace_eval.md`) + `config/test_cases.json`. |
| **2. ReAct Loop & MCP Integration** | **35%** | Vòng lặp ReAct chạy mượt mà qua Native Tool Calling & MCP Server **trên LLM API thật (Gemini/OpenAI)**. | Code trong `src/mcp_server.py` + `src/tools.py` + `src/app.py` + Log API thật. |
| **3. Waterfall Trace & Observation** | **25%** | File log `trace_waterfall.json` trích xuất đầy đủ chuỗi suy luận Thought $\rightarrow$ Action $\rightarrow$ Observation. | File log `docs/trace_waterfall.json` + `docs/trace_eval.md`. |
| **4. Git Repository & Submission** | **15%** | Cấu trúc Repo sạch sẽ, commit chuẩn chỉ và nộp đúng hạn trên LMS VLearn. | Link Repo GitHub cá nhân. |

---

## 🎁 7. PHẦN MỞ RỘNG CỦA HỌC VIÊN — AGENT NÂNG CAO + WEB REACT + DEPLOY (BONUS)

**Chủ đề đã chọn:** Gợi ý 1.1 — Trợ lý Học vụ VinUni (Lĩnh vực Giáo dục).

Ngoài phần core (CLI + trace log 2 tool), đồ án nâng cấp agent "làm được nhiều hơn" và bổ sung giao diện **React** trực quan để demo/phản biện. Chi tiết trong [`docs/trace_eval.md`](docs/trace_eval.md) mục 4.

### 🧠 Năng lực nâng cao của Agent
- **6 Tools qua MCP:** `academic_query`, `schedule_appointment`, `get_current_datetime` (thời gian thực), `get_exam_schedule` (lịch thi), `register_course` (đăng ký môn), `search_guidebook` (tra cứu Sổ tay chương trình từ kho tri thức thật).
- **ReAct ĐA BƯỚC thật sự:** Agent gọi nhiều Tool nối tiếp trong một câu hỏi (vd: tra cứu cố vấn → đặt lịch với đúng cố vấn đó), nạp lại Observation cho LLM qua `provider.next_action` / `run_agent`.
- **Trí nhớ hội thoại:** frontend gửi kèm lịch sử các lượt trước để Agent hiểu ngữ cảnh câu hỏi nối tiếp.

### Cấu trúc bổ sung
```text
📁 web/
├── 📄 backend.py          <-- 🌐 FastAPI: serve UI + API /api/chat (ReAct đa bước + trí nhớ)
├── 📁 frontend/           <-- ⚛️ Mã nguồn React (Vite + Tailwind + framer-motion + lucide)
│   └── 📁 src/            <-- App.jsx (giao diện 2 cột), main.jsx, index.css
└── 📁 static_react/       <-- 📦 Bản React đã build (Vite) — FastAPI serve, được commit để Render dùng
📄 render.yaml             <-- 🚀 Cấu hình deploy lên Render
```

### Chạy giao diện Web (local)
```bash
python web/backend.py
# Mở trình duyệt tại http://localhost:8000
```
Muốn sửa giao diện React rồi build lại:
```bash
cd web/frontend
npm install
npm run build      # xuất ra web/static_react/
```

### Deploy lên Render
1. Push repo (kèm thư mục `web/static_react/` đã build) lên GitHub.
2. Vào [dashboard.render.com](https://dashboard.render.com) → **New +** → **Blueprint** → chọn repo (Render tự đọc `render.yaml`, chỉ cần chạy Python).
3. Tab **Environment**: điền `GEMINI_API_KEY` (giá trị bí mật).
4. Deploy → Render cấp URL công khai `https://<ten>.onrender.com`.

> ✨ CLI cũng được nâng cấp bằng `rich` (khung màu, bảng tổng kết): `python src/app.py --all`.
> 🧬 Model dùng: `gemini-flash-latest` (đặt trong `.env` / Render Env).
