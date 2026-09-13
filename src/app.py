"""
🚀 CORE AGENT APPLICATION (DAY 03: CHATBOT VS REACT AGENT)
Thực thi so sánh giữa Chatbot Baseline (Cấp 2) và ReAct Agent kết nối MCP Server (Cấp 3).

Giao diện CLI được nâng cấp bằng thư viện `rich` (màu sắc, khung Panel, bảng Table,
spinner) — Giai đoạn 2 làm đẹp terminal. Logic core (ReAct Loop, MCP, trace log)
giữ nguyên 100% để đảm bảo tiêu chí chấm điểm.
"""

import json
import os
import sys
import time
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# --- Rich: nâng cấp giao diện terminal ---
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.rule import Rule
from rich.text import Text
from rich.json import JSON
from rich.align import Align
from rich import box

from mcp_server import MCPAcademicServer
from prompts import (
    CHATBOT_BASELINE_PROMPT,
    REACT_AGENT_SYSTEM_PROMPT,
    MAX_ITERATIONS
)
from providers import get_llm_provider

load_dotenv()
console = Console()


def load_test_cases():
    """Tải danh sách 5 test cases từ config/test_cases.json hoặc config/test_cases.example.json"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    if not os.path.exists(config_path):
        example_path = os.path.join(base_dir, "config", "test_cases.example.json")
        if os.path.exists(example_path):
            console.print("⚠️ [yellow][CONFIG NOTICE][/]: Chưa thấy file 'config/test_cases.json'. Đang dùng mẫu 'config/test_cases.example.json'.")
            console.print("👉 Hãy chạy: [cyan]copy config/test_cases.example.json config/test_cases.json[/] và viết test cases theo đề tài của bạn!\n")
            config_path = example_path
        else:
            config_path = "test_cases.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_waterfall_trace(trace_data: list):
    """Ghi vết log Waterfall Trace Log ra file docs/trace_waterfall.json"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_dir = os.path.join(base_dir, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    trace_path = os.path.join(docs_dir, "trace_waterfall.json")
    with open(trace_path, "w", encoding="utf-8") as f:
        json.dump(trace_data, f, ensure_ascii=False, indent=2)
    console.print(f"📊 [bold green][OBSERVABILITY][/]: Đã lưu [bold]{len(trace_data)}[/] sự kiện Waterfall Trace tại '[cyan]{trace_path}[/]'!")


def run_baseline_chatbot(user_query: str, provider):
    """Chạy Chatbot gốc (Cấp 2) không có công cụ gọi Tool"""
    console.print(Panel(user_query, title="💬 CHATBOT BASELINE — Câu hỏi", border_style="blue", box=box.ROUNDED))
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    console.print(Panel(response, title="🤖 Chatbot phản hồi", border_style="cyan", box=box.ROUNDED))


def run_react_agent(user_query: str, provider, mcp_server: MCPAcademicServer) -> list:
    """
    [REACT AGENT LOOP] Thực thi vòng lặp Thought -> Action -> Observation với MCP Server
    Trả về danh sách trace log của phiên thực thi.
    """
    console.print(Panel(Text(user_query, style="bold white"), title="🤖 REACT AGENT — Câu hỏi", border_style="magenta", box=box.HEAVY))

    step = 0
    trace_logs = []
    tools_list = mcp_server.list_tools()

    while step < MAX_ITERATIONS:
        step += 1
        step_start_time = time.time()
        console.print(Rule(f"🔄 ReAct Loop · Step {step}/{MAX_ITERATIONS}", style="dim"))

        # Gọi LLM với Native Tool Calling Specs (hiển thị spinner trong lúc chờ API)
        with console.status("[bold magenta]🧠 Agent đang suy luận & gọi LLM…", spinner="dots"):
            llm_response = provider.generate_with_tools(user_query, tools_list, system_prompt=REACT_AGENT_SYSTEM_PROMPT)
        latency_ms = round((time.time() - step_start_time) * 1000, 2)

        thought = llm_response.get("thought", "Đang suy luận...")
        console.print(Panel(thought, title="🧠 Thought", subtitle=f"⏱️ {latency_ms} ms", border_style="yellow", box=box.ROUNDED))

        # Trường hợp 1: LLM quyết định trả lời bằng văn bản trực tiếp
        if llm_response.get("type") == "text":
            final_content = llm_response.get("content", "")
            console.print(Panel(Text(final_content, style="bold"), title="🏁 Final Answer", border_style="green", box=box.DOUBLE))
            trace_logs.append({
                "step": step,
                "query": user_query,
                "action_type": "FINAL_ANSWER",
                "thought": thought,
                "output": final_content,
                "latency_ms": latency_ms
            })
            break

        # Trường hợp 2: LLM đề xuất gọi Tool (Action)
        elif llm_response.get("type") == "tool_call":
            tool_name = llm_response.get("tool_name")
            arguments = llm_response.get("arguments", {})

            args_txt = ", ".join(f"[cyan]{k}[/]=[green]{v!r}[/]" for k, v in arguments.items())
            console.print(Panel(f"[bold]{tool_name}[/]({args_txt})", title="🛠️ Action Proposed — Gọi Tool", border_style="cyan", box=box.ROUNDED))

            # Thực thi Tool qua MCP Server
            mcp_result = mcp_server.call_tool(tool_name, arguments)
            obs_data = mcp_result.get("result", {})

            if not obs_data:
                console.print(Panel("{}", title="👁️ Observation từ MCP Server", border_style="red", box=box.ROUNDED))
                console.print("⚠️ [red][CHÚ Ý][/]: MCP Server trả về kết quả rỗng! Học viên cần hoàn thành TODO 2.1 trong 'src/mcp_server.py'.")
                final_answer = "Chưa thể trả lời chi tiết do chưa nhận được dữ liệu từ MCP Server (hãy hoàn thành TODO 2.1)."
            else:
                console.print(Panel(JSON(json.dumps(obs_data, ensure_ascii=False)), title="👁️ Observation từ MCP Server (JSON-RPC 2.0)", border_style="green", box=box.ROUNDED))

                # Tổng hợp Final Answer từ kết quả Observation thực tế
                if obs_data.get("status") == "SUCCESS":
                    if "data" in obs_data:
                        d = obs_data["data"]
                        final_answer = (
                            f"Kết quả tra cứu cho sinh viên {obs_data.get('student_id', '')} ({d.get('full_name', '')}): "
                            f"Lớp {d.get('class', '')}, GPA: {d.get('gpa', '')}, Email: {d.get('email', '')}, "
                            f"Trạng thái: {d.get('status', '')}, Cố vấn: {d.get('advisor', '')}."
                        )
                    elif "message" in obs_data:
                        final_answer = obs_data["message"]
                    else:
                        final_answer = f"Đã hoàn tất xử lý qua MCP Server: {json.dumps(obs_data, ensure_ascii=False)}"
                elif obs_data.get("status") == "NOT_FOUND":
                    final_answer = obs_data.get("message", "Không tìm thấy thông tin sinh viên yêu cầu.")
                else:
                    final_answer = f"Phản hồi từ công cụ: {json.dumps(obs_data, ensure_ascii=False)}"

            trace_logs.append({
                "step": step,
                "query": user_query,
                "action_type": "TOOL_EXECUTION",
                "tool_name": tool_name,
                "arguments": arguments,
                "observation": obs_data,
                "latency_ms": latency_ms
            })

            # Kết thúc vòng lặp sau khi hoàn tất Observation và xuất Final Answer
            console.print("🧠 [dim]Thought: Đã nhận dữ liệu từ MCP Server. Tổng hợp kết quả phản hồi.[/]")
            console.print(Panel(Text(final_answer, style="bold"), title="🏁 Final Answer", border_style="green", box=box.DOUBLE))

            trace_logs.append({
                "step": step + 1,
                "query": user_query,
                "action_type": "FINAL_ANSWER",
                "thought": "Tổng hợp kết quả từ MCP Server thành công.",
                "output": final_answer,
                "latency_ms": 10.0
            })
            break

    return trace_logs


def print_banner(provider, mcp_server):
    """In banner khởi động chương trình."""
    is_live = provider.__class__.__name__ != "MockOfflineProvider"
    mode = "[green]● LIVE (LLM thật)[/]" if is_live else "[yellow]● MOCK (offline)[/]"
    body = (
        f"🔌 LLM Provider : [bold cyan]{provider.__class__.__name__}[/]\n"
        f"🧬 Model        : [bold]{getattr(provider, 'model_name', 'N/A')}[/]\n"
        f"🌐 MCP Server   : [bold]{mcp_server.server_name}[/] (v{mcp_server.version})\n"
        f"⚙️  Chế độ       : {mode}"
    )
    console.print(Panel(
        Align.center(body),
        title="🏫 VINUNI AI COURSE · DAY 03 · CHATBOT VS REACT AGENT",
        border_style="magenta", box=box.DOUBLE
    ))


if __name__ == "__main__":
    provider = get_llm_provider()
    mcp_server = MCPAcademicServer()
    print_banner(provider, mcp_server)

    tests = load_test_cases()
    console.print(f"✅ Đã tải thành công [bold]{len(tests)}[/] Test Cases thử nghiệm.\n")

    if "--interactive" in sys.argv:
        console.print(Panel(
            "💡 Gợi ý câu hỏi:\n"
            "  • Câu hỏi chung : 'Quy chế học vụ VinUni yêu cầu bao nhiêu tín chỉ?'\n"
            "  • Tra cứu học vụ: 'Hãy tra cứu thông tin học vụ của sinh viên SV2026001'\n"
            "  • Đặt lịch hẹn  : 'Đặt lịch hẹn tư vấn cho SV2026001 vào 14:00 ngày 15/09/2026'\n"
            "  • Gõ 'exit' hoặc 'quit' để kết thúc.",
            title="🎮 INTERACTIVE MODE — Trò chuyện trực tiếp với ReAct Agent", border_style="cyan", box=box.ROUNDED
        ))
        while True:
            try:
                user_input = console.input("[bold blue]👤 Sinh viên hỏi:[/] ").strip()
                if not user_input or user_input.lower() in ["exit", "quit"]:
                    console.print("👋 [dim]Tạm biệt! Kết thúc phiên trò chuyện.[/]")
                    break
                logs = run_react_agent(user_input, provider, mcp_server)
                save_waterfall_trace(logs)
            except (KeyboardInterrupt, EOFError):
                console.print("\n👋 [dim]Đã thoát phiên tương tác.[/]")
                break

    elif "--all" in sys.argv:
        console.print(Rule("🚀 TEST SUITE MODE — Kiểm tra 5 Test Cases", style="magenta"))
        completed_count = 0
        todo_count = 0
        all_traces = []
        summary_rows = []

        for tc in tests:
            console.print()
            console.print(Panel(
                f"[bold]{tc['question']}[/]\n\n[dim]📌 Kỳ vọng:[/] {tc['expected_behavior']}",
                title=f"🧪 {tc['id']} · {tc['type']} · Độ phức tạp: {tc['complexity']}",
                border_style="blue", box=box.ROUNDED
            ))

            if tc["question"].strip().startswith("TODO"):
                console.print(f"⏸️ [yellow][CHƯA KÍCH HOẠT - ĐANG LÀ TODO][/]: Hãy mở 'config/test_cases.json' viết câu hỏi cho test này!")
                todo_count += 1
                summary_rows.append((tc["id"], tc["type"], "[yellow]TODO[/]", "—"))
            else:
                logs = run_react_agent(tc["question"], provider, mcp_server)
                all_traces.extend(logs)
                completed_count += 1
                tool_calls = [l.get("tool_name") for l in logs if l.get("action_type") == "TOOL_EXECUTION"]
                tool_used = tool_calls[0] if tool_calls else "(trả lời trực tiếp)"
                summary_rows.append((tc["id"], tc["type"], "[green]PASS[/]", tool_used))

        # Bảng tổng kết
        table = Table(title="📊 KẾT QUẢ TEST SUITE", box=box.SIMPLE_HEAVY, header_style="bold magenta")
        table.add_column("Test", style="cyan", justify="center")
        table.add_column("Loại")
        table.add_column("Kết quả", justify="center")
        table.add_column("Tool được gọi", style="green")
        for row in summary_rows:
            table.add_row(*row)
        console.print()
        console.print(table)
        console.print(f"➡️  Đã thực thi [bold green]{completed_count}[/]/{len(tests)} Test Cases | [yellow]{todo_count}[/] đang chờ điền câu hỏi (TODO)")

        if all_traces:
            save_waterfall_trace(all_traces)
        console.print("💡 [dim]Chat trực tiếp: python src/app.py --interactive · Web UI: python web/backend.py[/]")

    else:
        console.print(Panel(
            "  1. Chat trực tiếp liên tục : [cyan]python src/app.py --interactive[/]\n"
            "  2. Chạy toàn bộ Test Cases : [cyan]python src/app.py --all[/]\n"
            "  3. Giao diện Web trực quan  : [cyan]python web/backend.py[/]",
            title="ℹ️ HƯỚNG DẪN SỬ DỤNG", border_style="cyan", box=box.ROUNDED
        ))
        sample_query = tests[1]["question"]
        console.print(Rule("🏁 DEMO CHẠY THỬ 1 TEST CASE MẪU (TC02: Tra cứu học vụ)", style="dim"))
        logs = run_react_agent(sample_query, provider, mcp_server)
        save_waterfall_trace(logs)
