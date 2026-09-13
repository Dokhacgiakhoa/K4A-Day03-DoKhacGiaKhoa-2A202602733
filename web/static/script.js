// =============================================================================
// VinUni ReAct Agent — Frontend (bố cục 2 cột)
// CỘT TRÁI (#chat)  : hội thoại — câu hỏi người dùng + câu trả lời cuối.
// CỘT PHẢI (#reason): luồng suy luận — Thought -> Action -> Observation -> Final.
// =============================================================================

const chat = document.getElementById("chat");
const reason = document.getElementById("reason");
const reasonQ = document.getElementById("reason-q");
const input = document.getElementById("input");
const sendBtn = document.getElementById("send");

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// TRÍ NHỚ hội thoại: lưu các lượt để gửi kèm mỗi câu hỏi (Agent hiểu ngữ cảnh)
let history = [];

function el(tag, cls, html) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (html !== undefined) e.innerHTML = html;
  return e;
}
function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}
function highlightJson(obj) {
  return escapeHtml(JSON.stringify(obj, null, 2))
    .replace(/&quot;(\w+)&quot;:/g, '<span class="k">&quot;$1&quot;</span>:')
    .replace(/: &quot;([^&]*)&quot;/g, ': <span class="s">&quot;$1&quot;</span>')
    .replace(/: (\d+\.?\d*)/g, ': <span class="n">$1</span>')
    .replace(/: (true|false|null)/g, ': <span class="b">$1</span>');
}
const scrollChat = () => (chat.scrollTop = chat.scrollHeight);
const scrollReason = () => (reason.scrollTop = reason.scrollHeight);

// ---------- Card cho CỘT PHẢI (luồng suy luận) ----------
function cardThought(step, text, latency) {
  return el("div", "card thought",
    `<span class="ico">🧠</span>
     <div class="lbl"><span>Thought · Step ${step}</span>${latency != null ? `<span class="lat">${latency} ms</span>` : ""}</div>
     <div class="body">${escapeHtml(text)}</div>`);
}
function cardAction(toolName, args) {
  const pills = Object.entries(args || {})
    .map(([k, v]) => `<span class="arg-pill">${escapeHtml(k)}: ${escapeHtml(v)}</span>`).join("");
  return el("div", "card action",
    `<span class="ico">🛠️</span>
     <div class="lbl"><span>Action · Gọi Tool qua MCP</span></div>
     <div class="body"><b>${escapeHtml(toolName)}</b>(${pills || "—"})</div>`);
}
function cardObservation(data) {
  const status = data && data.status ? data.status : "—";
  return el("div", "card observation",
    `<span class="ico">👁️</span>
     <div class="lbl"><span>Observation · JSON-RPC 2.0</span><span class="lat">${escapeHtml(status)}</span></div>
     <div class="code">${highlightJson(data)}</div>`);
}
function cardFinal(text) {
  return el("div", "card final",
    `<span class="ico">🏁</span>
     <div class="lbl"><span>Final Answer</span></div>
     <div class="body">${escapeHtml(text)}</div>`);
}

// ---------- Gửi câu hỏi ----------
async function sendQuery(query) {
  if (!query.trim()) return;

  // Dọn màn hình chào ở cả 2 cột
  const w = chat.querySelector(".welcome"); if (w) w.remove();
  reason.innerHTML = "";
  reasonQ.hidden = false;
  reasonQ.innerHTML = `Đang suy luận cho câu hỏi: <b>${escapeHtml(query)}</b>`;

  // CỘT TRÁI: bong bóng người dùng + bong bóng "đang trả lời"
  const userMsg = el("div", "user-msg");
  userMsg.appendChild(el("div", "user-bubble", escapeHtml(query)));
  chat.appendChild(userMsg);

  const agentMsg = el("div", "agent-msg");
  agentMsg.appendChild(el("div", "agent-avatar", "🤖"));
  const bubble = el("div", "agent-bubble thinking");
  bubble.innerHTML = `<div class="typing"><i></i><i></i><i></i></div>`;
  agentMsg.appendChild(bubble);
  chat.appendChild(agentMsg);
  scrollChat();

  input.value = "";
  input.disabled = true; sendBtn.disabled = true;

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, history }),
    });
    const data = await res.json();

    if (data.error) {
      bubble.classList.remove("thinking");
      bubble.textContent = "⚠️ " + data.error;
    } else {
      let finalText = data.final_answer || "";
      // Stream các bước sang CỘT PHẢI (có thể nhiều Action/Observation nếu đa bước)
      for (const s of data.steps) {
        let card = null;
        if (s.kind === "thought") card = cardThought(s.step, s.text, s.latency_ms);
        else if (s.kind === "action") card = cardAction(s.tool_name, s.arguments);
        else if (s.kind === "observation") card = cardObservation(s.data);
        else if (s.kind === "final") { card = cardFinal(s.text); finalText = s.text; }
        if (card) { reason.appendChild(card); scrollReason(); await sleep(240); }
      }
      // CỘT TRÁI: thay bong bóng "đang trả lời" bằng câu trả lời cuối
      bubble.classList.remove("thinking");
      bubble.textContent = finalText;

      // Nhãn cột phải: liệt kê (các) tool đã gọi
      const called = data.tools_called && data.tools_called.length
        ? " · đã gọi: " + data.tools_called.map((t) => `<b>${escapeHtml(t)}</b>`).join(" → ")
        : " · trả lời trực tiếp";
      reasonQ.innerHTML = `Câu hỏi: <b>${escapeHtml(query)}</b>${called}`;

      // Cập nhật TRÍ NHỚ hội thoại
      history.push({ role: "user", text: query });
      history.push({ role: "assistant", text: finalText });
      if (history.length > 12) history = history.slice(-12); // giữ 6 lượt gần nhất
    }
  } catch (err) {
    bubble.classList.remove("thinking");
    bubble.textContent = "⚠️ Lỗi kết nối server: " + err.message;
  } finally {
    input.disabled = false; sendBtn.disabled = false; input.focus();
    scrollChat();
  }
}

// ---------- Events ----------
sendBtn.addEventListener("click", () => sendQuery(input.value));
input.addEventListener("keydown", (e) => { if (e.key === "Enter") sendQuery(input.value); });
document.addEventListener("click", (e) => {
  if (e.target.classList.contains("example")) sendQuery(e.target.dataset.q);
});

// ---------- Load system info ----------
async function loadInfo() {
  try {
    const info = await (await fetch("/api/info")).json();
    document.getElementById("info-provider").textContent = info.provider;
    document.getElementById("info-model").textContent = info.model;
    document.getElementById("info-mcp").textContent = info.mcp_server;
    document.getElementById("info-max").textContent = info.max_iterations;

    const mode = document.getElementById("info-mode");
    if (info.live_mode) { mode.textContent = "LIVE"; mode.className = "badge live"; }
    else { mode.textContent = "MOCK"; mode.className = "badge mock"; }

    const toolsBox = document.getElementById("tools-list");
    if (toolsBox) {
      toolsBox.innerHTML = "";
      info.tools.forEach((t) => {
        toolsBox.appendChild(el("div", "tool",
          `<div class="tool-name">${escapeHtml(t.name)}()</div>
           <div class="tool-desc">${escapeHtml(t.description)}</div>`));
      });
    }
  } catch (e) { console.error("Không tải được /api/info", e); }
}
loadInfo();
