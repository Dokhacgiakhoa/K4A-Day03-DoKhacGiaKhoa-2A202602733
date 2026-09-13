"""
🌐 WEB BACKEND (FastAPI) — GIAI ĐOẠN 2: AGENT NÂNG CAO
Bọc ReAct Agent thành Web Service với giao diện 2 cột trực quan.

Nâng cấp so với bản Core:
  • ReAct ĐA BƯỚC thật sự: Agent gọi nhiều Tool nối tiếp trong 1 câu hỏi
    (nạp lại Observation cho LLM qua provider.next_action) — Thought/Action/Observation lặp
    cho tới khi LLM đưa Final Answer hoặc chạm MAX_ITERATIONS.
  • TRÍ NHỚ hội thoại: frontend gửi kèm lịch sử các lượt trước để Agent hiểu ngữ cảnh.
  • 6 Tools: academic_query, schedule_appointment, get_current_datetime,
    get_exam_schedule, register_course, search_guidebook.

Tái sử dụng MCP Server (src/mcp_server.py), Tool Router (src/tools.py),
LLM Provider (src/providers.py) của phần Core.
"""

import os
import sys
import time
import json

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

# Cho phép import các module trong thư mục src/ (tái sử dụng code Core)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE_DIR, "src")
sys.path.append(SRC_DIR)

from mcp_server import MCPAcademicServer          # noqa: E402
from providers import get_llm_provider            # noqa: E402
from prompts import REACT_AGENT_SYSTEM_PROMPT, MAX_ITERATIONS  # noqa: E402

load_dotenv()

# Agent dùng chung cho mọi request
provider = get_llm_provider()
mcp_server = MCPAcademicServer()


def _mcp_execute(tool_name: str, arguments: dict) -> dict:
    """Callback thực thi Tool qua MCP Server, trả về phần 'result' (Observation)."""
    return mcp_server.call_tool(tool_name, arguments).get("result", {})


def execute_react_query(user_query: str, history: list | None = None) -> dict:
    """
    Vòng lặp ReAct ĐA BƯỚC + TRÍ NHỚ hội thoại (ủy quyền cho provider.run_agent).
    Trả về: { steps, trace_logs, final_answer, tool_used, tools_called }
    """
    result = provider.run_agent(
        user_query=user_query,
        history=history or [],
        tools_schema=mcp_server.list_tools(),
        system_prompt=REACT_AGENT_SYSTEM_PROMPT,
        execute_tool=_mcp_execute,
        max_steps=MAX_ITERATIONS,
    )
    tools_called = result.get("tools_called", [])
    result["tool_used"] = tools_called[0] if tools_called else None
    return result


# ==============================================================================
# FASTAPI APP
# ==============================================================================
app = FastAPI(title="VinUni ReAct Agent — Web UI", version="2.0.0")
WEB_DIR = os.path.dirname(os.path.abspath(__file__))
REACT_DIR = os.path.join(WEB_DIR, "static_react")        # bản React (Vite build)
LEGACY_DIR = os.path.join(WEB_DIR, "static")             # bản HTML/JS thuần (fallback)
USE_REACT = os.path.isdir(REACT_DIR) and os.path.exists(os.path.join(REACT_DIR, "index.html"))
FRONTEND_DIR = REACT_DIR if USE_REACT else LEGACY_DIR


class HistoryTurn(BaseModel):
    role: str
    text: str


class ChatRequest(BaseModel):
    query: str
    history: list[HistoryTurn] | None = None


@app.get("/api/info")
def get_info():
    return {
        "provider": provider.__class__.__name__,
        "model": getattr(provider, "model_name", "N/A"),
        "mcp_server": mcp_server.server_name,
        "mcp_version": mcp_server.version,
        "tools": [
            {"name": t["name"], "description": t.get("description", "")}
            for t in mcp_server.list_tools()
        ],
        "max_iterations": MAX_ITERATIONS,
        "live_mode": provider.__class__.__name__ != "MockOfflineProvider",
    }


@app.post("/api/chat")
def chat(req: ChatRequest):
    query = (req.query or "").strip()
    if not query:
        return {"error": "Câu hỏi trống."}
    history = [{"role": h.role, "text": h.text} for h in (req.history or [])]
    return execute_react_query(query, history)


@app.get("/")
def index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


# Serve tài nguyên tĩnh (js/css). Bản React đặt assets ở /assets; giữ /static cho bản cũ.
if USE_REACT:
    app.mount("/assets", StaticFiles(directory=os.path.join(REACT_DIR, "assets")), name="assets")
if os.path.isdir(LEGACY_DIR):
    app.mount("/static", StaticFiles(directory=LEGACY_DIR), name="static")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    print(f"🌐 Khởi động Web UI tại http://localhost:{port}")
    uvicorn.run("backend:app", host="0.0.0.0", port=port, reload=True)
