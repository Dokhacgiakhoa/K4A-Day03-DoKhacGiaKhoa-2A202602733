"""
🔌 MULTI-PROVIDER LLM ADAPTER (Google Gemini, OpenAI & Offline Mock)
Hỗ trợ Native Tool Calling và chuyển đổi linh hoạt qua biến môi trường LLM_PROVIDER.
"""

import os
import re
import sys
import json
import time
from typing import Dict, Any, List
from dotenv import load_dotenv

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

class BaseLLMProvider:
    """Interface cơ sở cho các LLM Provider hỗ trợ Native Tool Calling"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        raise NotImplementedError

    def next_action(self, turns: List[Dict[str, Any]], tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        """
        [ReAct ĐA BƯỚC] Nhận toàn bộ 'turns' (lịch sử hội thoại + các Tool Call/Observation
        đã thực hiện) và quyết định HÀNH ĐỘNG TIẾP THEO của Agent.

        turns: danh sách các lượt, mỗi lượt là dict với "role" thuộc:
          - "user"            : {"role":"user", "text": ...}            (câu hỏi người dùng / trí nhớ hội thoại)
          - "assistant"       : {"role":"assistant", "text": ...}       (câu trả lời trước đó — trí nhớ)
          - "model_tool_call" : {"role":"model_tool_call", "name":..., "args": {...}}
          - "tool"            : {"role":"tool", "name":..., "result": {...}}   (Observation từ MCP)

        Trả về: {"type": "text", "content":..., "thought":...}
             hoặc {"type": "tool_call", "tool_name":..., "arguments": {...}, "thought":...}
        """
        raise NotImplementedError

    # -------------------------------------------------------------------------
    # VÒNG LẶP REACT ĐA BƯỚC (dùng chung) — Mock & OpenAI dùng bản này qua next_action.
    # Gemini override để bảo toàn thought_signature.
    # -------------------------------------------------------------------------
    @staticmethod
    def _seed_turns(user_query: str, history):
        turns = []
        for h in (history or []):
            role = "user" if h.get("role") == "user" else "assistant"
            txt = h.get("text") or h.get("content") or ""
            if txt:
                turns.append({"role": role, "text": txt})
        turns.append({"role": "user", "text": user_query})
        return turns

    @staticmethod
    def _fallback_from_turns(turns) -> str:
        for t in reversed(turns):
            if t.get("role") == "tool":
                res = t.get("result", {})
                if isinstance(res, dict):
                    return res.get("message") or json.dumps(res, ensure_ascii=False)
                return str(res)
        return "Xin lỗi, tôi chưa thể hoàn tất yêu cầu trong số bước cho phép."

    def run_agent(self, user_query, history, tools_schema, system_prompt, execute_tool, max_steps=5) -> Dict[str, Any]:
        """
        Chạy trọn vòng lặp ReAct đa bước.
          execute_tool(tool_name, arguments) -> dict Observation (thường là mcp_server.call_tool(...).result)
        Trả về: {steps, trace_logs, final_answer, tools_called}
        """
        steps, trace_logs, tools_called = [], [], []
        turns = self._seed_turns(user_query, history)
        final_answer = ""
        step = 0
        while step < max_steps:
            step += 1
            t0 = time.time()
            action = self.next_action(turns, tools_schema, system_prompt)
            latency_ms = round((time.time() - t0) * 1000, 2)
            thought = action.get("thought", "Đang suy luận...")
            steps.append({"kind": "thought", "step": step, "text": thought, "latency_ms": latency_ms})

            if action.get("type") == "text":
                final_answer = action.get("content", "")
                steps.append({"kind": "final", "step": step, "text": final_answer})
                trace_logs.append({"step": step, "query": user_query, "action_type": "FINAL_ANSWER",
                                   "thought": thought, "output": final_answer, "latency_ms": latency_ms})
                break

            tool_name = action.get("tool_name")
            arguments = action.get("arguments", {}) or {}
            tools_called.append(tool_name)
            obs = execute_tool(tool_name, arguments)
            steps.append({"kind": "action", "step": step, "tool_name": tool_name, "arguments": arguments})
            steps.append({"kind": "observation", "step": step, "data": obs})
            trace_logs.append({"step": step, "query": user_query, "action_type": "TOOL_EXECUTION",
                               "tool_name": tool_name, "arguments": arguments, "observation": obs, "latency_ms": latency_ms})
            turns.append({"role": "model_tool_call", "name": tool_name, "args": arguments})
            turns.append({"role": "tool", "name": tool_name, "result": obs})
        else:
            final_answer = self._fallback_from_turns(turns)
            steps.append({"kind": "final", "step": step + 1, "text": final_answer})
            trace_logs.append({"step": step + 1, "query": user_query, "action_type": "FINAL_ANSWER",
                               "thought": "Đạt số bước tối đa, tổng hợp từ Observation cuối.", "output": final_answer, "latency_ms": 10.0})

        return {"steps": steps, "trace_logs": trace_logs, "final_answer": final_answer, "tools_called": tools_called}


class MockOfflineProvider(BaseLLMProvider):
    """Offline Mock Provider dùng để chạy thử mà không tốn API Key"""
    def __init__(self):
        self.model_name = "Offline-Mock-Model-2026"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        return f"[Mock Chatbot Response]: Xin chào! Tôi đã nhận được câu hỏi '{prompt}'. (Chế độ Chatbot không có Tool tra cứu dữ liệu thời gian thực)."

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        prompt_lower = prompt.lower()
        
        # Mô phỏng nhận diện intent gọi Tool
        if "sv2026001" in prompt_lower and "đặt lịch" in prompt_lower:
            return {
                "type": "tool_call",
                "tool_name": "schedule_appointment",
                "arguments": {"student_id": "SV2026001", "datetime_str": "14:00 15/09/2026", "advisor_name": "PGS.TS Nguyễn Văn A"},
                "thought": "Người dùng yêu cầu đặt lịch hẹn tư vấn cho sinh viên SV2026001. Tôi sẽ gọi tool schedule_appointment."
            }
        elif "sv2026001" in prompt_lower or "tra cứu" in prompt_lower:
            return {
                "type": "tool_call",
                "tool_name": "academic_query",
                "arguments": {"student_id": "SV2026001"},
                "thought": "Người dùng muốn tra cứu thông tin học vụ của sinh viên SV2026001. Tôi sẽ gọi tool academic_query."
            }
        else:
            return {
                "type": "text",
                "content": f"[Mock Agent Response]: Xin chào! Quy chế học vụ VinUni yêu cầu sinh viên tích lũy tối thiểu 120 tín chỉ và duy trì GPA trên 2.0 để tốt nghiệp.",
                "thought": "Câu hỏi chung về quy chế học vụ, trả lời trực tiếp không cần gọi Tool."
            }

    def next_action(self, turns: List[Dict[str, Any]], tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        """Mô phỏng ReAct đa bước offline: nếu đã có Observation cho câu hỏi hiện tại thì tổng hợp
        câu trả lời; nếu chưa thì chọn Tool phù hợp dựa trên từ khóa."""
        # Xác định câu hỏi hiện tại (lượt user gần nhất)
        last_user_idx = -1
        for i, t in enumerate(turns):
            if t.get("role") == "user":
                last_user_idx = i
        query = turns[last_user_idx]["text"] if last_user_idx >= 0 else ""
        ql = query.lower()

        # Đã có Observation kể từ câu hỏi hiện tại chưa?
        recent = turns[last_user_idx:] if last_user_idx >= 0 else turns
        tool_results = [t for t in recent if t.get("role") == "tool"]
        if tool_results:
            last_res = tool_results[-1].get("result", {})
            msg = last_res.get("message") if isinstance(last_res, dict) else str(last_res)
            if not msg and isinstance(last_res, dict) and "data" in last_res:
                d = last_res["data"]
                msg = (f"Sinh viên {last_res.get('student_id','')} ({d.get('full_name','')}): "
                       f"Lớp {d.get('class','')}, GPA {d.get('gpa','')}, Cố vấn {d.get('advisor','')}.")
            return {
                "type": "text",
                "content": msg or "Đã hoàn tất xử lý yêu cầu.",
                "thought": "Đã nhận Observation từ MCP Server, tổng hợp câu trả lời cuối cùng."
            }

        # Chưa có Observation -> chọn Tool
        sv_match = re.search(r"sv\s*\d+", ql)
        sv_id = sv_match.group(0).replace(" ", "").upper() if sv_match else "SV2026001"

        if "lịch thi" in ql or "thi" in ql and "đgnl" not in ql:
            return {"type": "tool_call", "tool_name": "get_exam_schedule",
                    "arguments": {"student_id": sv_id},
                    "thought": f"Người dùng hỏi lịch thi của {sv_id}. Gọi get_exam_schedule."}
        if "đặt lịch" in ql:
            return {"type": "tool_call", "tool_name": "schedule_appointment",
                    "arguments": {"student_id": sv_id, "datetime_str": "14:00 15/09/2026", "advisor_name": "PGS.TS Nguyễn Văn A"},
                    "thought": f"Người dùng muốn đặt lịch hẹn cho {sv_id}. Gọi schedule_appointment."}
        if "đăng ký" in ql and ("môn" in ql or "course" in ql):
            code_match = re.search(r"[a-z]{2,4}\s*\d{3}", ql)
            code = code_match.group(0).replace(" ", "").upper() if code_match else "CS201"
            return {"type": "tool_call", "tool_name": "register_course",
                    "arguments": {"student_id": sv_id, "course_code": code},
                    "thought": f"Người dùng muốn đăng ký môn {code} cho {sv_id}. Gọi register_course."}
        if any(k in ql for k in ["hôm nay", "ngày mấy", "bao nhiêu", "mấy giờ", "bây giờ", "ngày bao"]):
            return {"type": "tool_call", "tool_name": "get_current_datetime", "arguments": {},
                    "thought": "Người dùng hỏi thời gian hiện tại. Gọi get_current_datetime."}
        if any(k in ql for k in ["học phí", "trợ cấp", "phụ cấp", "tiếng anh", "thực tập", "đgnl", "việc làm", "lương", "chương trình", "học bổng"]):
            return {"type": "tool_call", "tool_name": "search_guidebook",
                    "arguments": {"query": query},
                    "thought": "Câu hỏi thuộc kiến thức chương trình. Gọi search_guidebook."}
        if sv_match or "tra cứu" in ql:
            return {"type": "tool_call", "tool_name": "academic_query",
                    "arguments": {"student_id": sv_id},
                    "thought": f"Người dùng muốn tra cứu hồ sơ {sv_id}. Gọi academic_query."}
        return {"type": "text",
                "content": "[Mock Agent] Quy chế học vụ VinUni yêu cầu tối thiểu 120 tín chỉ và GPA trên 2.0 để tốt nghiệp.",
                "thought": "Câu hỏi chung, trả lời trực tiếp không cần Tool."}


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider (Native Tool Calling với Google GenAI SDK)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gemini-2.5-flash"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return "[Gemini Error]: Chưa cấu hình GEMINI_API_KEY trong file .env! Đang sử dụng chế độ Mock."
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = client.models.generate_content(model=self.model_name, contents=contents)
            return response.text
        except Exception as e:
            return f"[Gemini Exception]: {str(e)}"

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            print("ℹ️ [Gemini Provider]: Chưa tìm thấy GEMINI_API_KEY hợp lệ. Tự động chuyển sang Mock Offline.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)
        
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            
            # Chuẩn hóa function declarations cho Gemini SDK
            function_declarations = []
            for tool in tools_schema:
                # Bỏ qua các tool schema chưa được định nghĩa hoàn chỉnh
                if not tool.get("name") or not tool.get("parameters"):
                    continue
                function_declarations.append({
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("parameters", {})
                })

            config = types.GenerateContentConfig(
                system_instruction=system_prompt if system_prompt else None,
                tools=[{"function_declarations": function_declarations}] if function_declarations else None,
                temperature=0.2
            )

            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )

            # Kiểm tra xem Gemini có trả về Tool Call không
            if response.function_calls:
                call = response.function_calls[0]
                args = dict(call.args) if hasattr(call, 'args') and call.args else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.name,
                    "arguments": args,
                    "thought": f"Gemini quyết định gọi công cụ '{call.name}' với tham số: {json.dumps(args, ensure_ascii=False)}"
                }
            else:
                return {
                    "type": "text",
                    "content": response.text or "",
                    "thought": "Gemini phản hồi trực tiếp bằng văn bản (không cần gọi công cụ)."
                }

        except Exception as e:
            print(f"⚠️ [Gemini API Warning]: Không thể kết nối live API ({str(e)}). Tự động fallback về Mock.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)

    def next_action(self, turns: List[Dict[str, Any]], tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        """ReAct đa bước với Gemini Native Function Calling (multi-turn): dựng lại toàn bộ
        lịch sử hội thoại + function_call/function_response rồi hỏi Gemini hành động kế tiếp."""
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            print("ℹ️ [Gemini Provider]: Chưa có GEMINI_API_KEY hợp lệ. Chuyển sang Mock Offline.")
            return MockOfflineProvider().next_action(turns, tools_schema, system_prompt)
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)

            function_declarations = []
            for tool in tools_schema:
                if not tool.get("name") or not tool.get("parameters"):
                    continue
                function_declarations.append({
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("parameters", {})
                })

            # Dựng contents đa lượt từ turns
            contents = []
            for t in turns:
                role = t.get("role")
                if role == "user":
                    contents.append(types.Content(role="user", parts=[types.Part(text=t["text"])]))
                elif role == "assistant":
                    contents.append(types.Content(role="model", parts=[types.Part(text=t["text"])]))
                elif role == "model_tool_call":
                    contents.append(types.Content(role="model", parts=[
                        types.Part(function_call=types.FunctionCall(name=t["name"], args=t.get("args", {}) or {}))
                    ]))
                elif role == "tool":
                    resp = t.get("result", {})
                    if not isinstance(resp, dict):
                        resp = {"result": resp}
                    contents.append(types.Content(role="user", parts=[
                        types.Part.from_function_response(name=t["name"], response=resp)
                    ]))

            config = types.GenerateContentConfig(
                system_instruction=system_prompt if system_prompt else None,
                tools=[{"function_declarations": function_declarations}] if function_declarations else None,
                temperature=0.2
            )

            response = client.models.generate_content(
                model=self.model_name, contents=contents, config=config
            )

            if response.function_calls:
                call = response.function_calls[0]
                args = dict(call.args) if hasattr(call, "args") and call.args else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.name,
                    "arguments": args,
                    "thought": f"Gemini quyết định gọi công cụ '{call.name}' với tham số: {json.dumps(args, ensure_ascii=False)}"
                }
            return {
                "type": "text",
                "content": response.text or "",
                "thought": "Gemini tổng hợp thông tin và phản hồi bằng văn bản."
            }
        except Exception as e:
            print(f"⚠️ [Gemini API Warning]: Không thể kết nối live API ({str(e)}). Tự động fallback về Mock.")
            return MockOfflineProvider().next_action(turns, tools_schema, system_prompt)

    def run_agent(self, user_query, history, tools_schema, system_prompt, execute_tool, max_steps=5) -> Dict[str, Any]:
        """Vòng lặp ReAct đa bước cho Gemini — giữ nguyên Content model gốc để bảo toàn
        thought_signature (bắt buộc với Gemini 3.x khi gửi lại function call trong lịch sử)."""
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return MockOfflineProvider().run_agent(user_query, history, tools_schema, system_prompt, execute_tool, max_steps)
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            function_declarations = [
                {"name": t["name"], "description": t.get("description", ""), "parameters": t.get("parameters", {})}
                for t in tools_schema if t.get("name") and t.get("parameters")
            ]
            config = types.GenerateContentConfig(
                system_instruction=system_prompt if system_prompt else None,
                tools=[{"function_declarations": function_declarations}] if function_declarations else None,
                temperature=0.2
            )

            # Dựng contents ban đầu: trí nhớ hội thoại + câu hỏi hiện tại
            contents = []
            for h in (history or []):
                role = "user" if h.get("role") == "user" else "model"
                txt = h.get("text") or h.get("content") or ""
                if txt:
                    contents.append(types.Content(role=role, parts=[types.Part(text=txt)]))
            contents.append(types.Content(role="user", parts=[types.Part(text=user_query)]))

            steps, trace_logs, tools_called = [], [], []
            final_answer = ""
            step = 0
            while step < max_steps:
                step += 1
                t0 = time.time()
                response = client.models.generate_content(model=self.model_name, contents=contents, config=config)
                latency_ms = round((time.time() - t0) * 1000, 2)

                if response.function_calls:
                    fc = response.function_calls[0]
                    args = dict(fc.args) if getattr(fc, "args", None) else {}
                    thought = f"Gemini quyết định gọi công cụ '{fc.name}' với tham số: {json.dumps(args, ensure_ascii=False)}"
                    steps.append({"kind": "thought", "step": step, "text": thought, "latency_ms": latency_ms})

                    obs = execute_tool(fc.name, args)
                    tools_called.append(fc.name)
                    steps.append({"kind": "action", "step": step, "tool_name": fc.name, "arguments": args})
                    steps.append({"kind": "observation", "step": step, "data": obs})
                    trace_logs.append({"step": step, "query": user_query, "action_type": "TOOL_EXECUTION",
                                       "tool_name": fc.name, "arguments": args, "observation": obs, "latency_ms": latency_ms})

                    # Bảo toàn Content model gốc (kèm thought_signature) rồi nạp function_response
                    contents.append(response.candidates[0].content)
                    resp_payload = obs if isinstance(obs, dict) else {"result": obs}
                    contents.append(types.Content(role="user", parts=[
                        types.Part.from_function_response(name=fc.name, response=resp_payload)
                    ]))
                    continue

                # Final Answer
                final_answer = response.text or ""
                steps.append({"kind": "thought", "step": step, "text": "Gemini tổng hợp thông tin và đưa ra câu trả lời.", "latency_ms": latency_ms})
                steps.append({"kind": "final", "step": step, "text": final_answer})
                trace_logs.append({"step": step, "query": user_query, "action_type": "FINAL_ANSWER",
                                   "thought": "Tổng hợp kết quả thành công.", "output": final_answer, "latency_ms": latency_ms})
                return {"steps": steps, "trace_logs": trace_logs, "final_answer": final_answer, "tools_called": tools_called}

            # Chạm giới hạn bước
            final_answer = self._fallback_from_turns(
                [{"role": "tool", "result": s["data"]} for s in steps if s.get("kind") == "observation"]
            )
            steps.append({"kind": "final", "step": step + 1, "text": final_answer})
            trace_logs.append({"step": step + 1, "query": user_query, "action_type": "FINAL_ANSWER",
                               "thought": "Đạt số bước tối đa.", "output": final_answer, "latency_ms": 10.0})
            return {"steps": steps, "trace_logs": trace_logs, "final_answer": final_answer, "tools_called": tools_called}

        except Exception as e:
            print(f"⚠️ [Gemini API Warning]: run_agent lỗi ({str(e)}). Fallback về Mock.")
            return MockOfflineProvider().run_agent(user_query, history, tools_schema, system_prompt, execute_tool, max_steps)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider (Native Tool Calling với OpenAI SDK)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return "[OpenAI Error]: Chưa cấu hình OPENAI_API_KEY trong file .env! Đang sử dụng chế độ Mock."
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            response = client.chat.completions.create(model=self.model_name, messages=messages)
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"[OpenAI Exception]: {str(e)}"

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            print("ℹ️ [OpenAI Provider]: Chưa tìm thấy OPENAI_API_KEY hợp lệ. Tự động chuyển sang Mock Offline.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)

            tools = []
            for tool in tools_schema:
                if not tool.get("name"):
                    continue
                tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("parameters", {})
                    }
                })

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None
            )

            msg = response.choices[0].message
            if msg.tool_calls:
                call = msg.tool_calls[0]
                args = json.loads(call.function.arguments) if call.function.arguments else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.function.name,
                    "arguments": args,
                    "thought": f"OpenAI quyết định gọi công cụ '{call.function.name}' với tham số: {json.dumps(args, ensure_ascii=False)}"
                }
            else:
                return {
                    "type": "text",
                    "content": msg.content or "",
                    "thought": "OpenAI phản hồi trực tiếp bằng văn bản (không cần gọi công cụ)."
                }
        except Exception as e:
            print(f"⚠️ [OpenAI API Warning]: Không thể kết nối live API ({str(e)}). Tự động fallback về Mock.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)

    def next_action(self, turns: List[Dict[str, Any]], tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        """ReAct đa bước với OpenAI Native Tool Calling (multi-turn)."""
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            print("ℹ️ [OpenAI Provider]: Chưa có OPENAI_API_KEY hợp lệ. Chuyển sang Mock Offline.")
            return MockOfflineProvider().next_action(turns, tools_schema, system_prompt)
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)

            tools = []
            for tool in tools_schema:
                if not tool.get("name"):
                    continue
                tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("parameters", {})
                    }
                })

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            for t in turns:
                role = t.get("role")
                if role == "user":
                    messages.append({"role": "user", "content": t["text"]})
                elif role == "assistant":
                    messages.append({"role": "assistant", "content": t["text"]})
                elif role == "model_tool_call":
                    call_id = f"call_{t['name']}"
                    messages.append({
                        "role": "assistant",
                        "tool_calls": [{
                            "id": call_id, "type": "function",
                            "function": {"name": t["name"], "arguments": json.dumps(t.get("args", {}), ensure_ascii=False)}
                        }]
                    })
                elif role == "tool":
                    messages.append({
                        "role": "tool",
                        "tool_call_id": f"call_{t['name']}",
                        "content": json.dumps(t.get("result", {}), ensure_ascii=False)
                    })

            response = client.chat.completions.create(
                model=self.model_name, messages=messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None
            )
            msg = response.choices[0].message
            if msg.tool_calls:
                call = msg.tool_calls[0]
                args = json.loads(call.function.arguments) if call.function.arguments else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.function.name,
                    "arguments": args,
                    "thought": f"OpenAI quyết định gọi công cụ '{call.function.name}' với tham số: {json.dumps(args, ensure_ascii=False)}"
                }
            return {
                "type": "text",
                "content": msg.content or "",
                "thought": "OpenAI tổng hợp thông tin và phản hồi bằng văn bản."
            }
        except Exception as e:
            print(f"⚠️ [OpenAI API Warning]: Không thể kết nối live API ({str(e)}). Tự động fallback về Mock.")
            return MockOfflineProvider().next_action(turns, tools_schema, system_prompt)


def get_llm_provider() -> BaseLLMProvider:
    """Factory function khởi tạo Provider theo LLM_PROVIDER env variable"""
    provider_type = os.getenv("LLM_PROVIDER", "gemini").lower()
    
    if provider_type == "gemini":
        key = os.getenv("GEMINI_API_KEY")
        if key and key != "your_gemini_api_key_here":
            return GeminiProvider()
        else:
            return MockOfflineProvider()
    elif provider_type == "openai":
        key = os.getenv("OPENAI_API_KEY")
        if key and key != "your_openai_api_key_here":
            return OpenAIProvider()
        else:
            return MockOfflineProvider()
    elif provider_type == "mock":
        return MockOfflineProvider()
    else:
        return MockOfflineProvider()
