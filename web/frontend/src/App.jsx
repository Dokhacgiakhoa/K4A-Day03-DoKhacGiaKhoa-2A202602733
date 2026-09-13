import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Brain, Wrench, Eye, Flag, Bot, Send, GraduationCap, Sparkles,
  Clock, Database, Search, CalendarDays, BookOpen, CheckCircle2, User, Zap,
} from "lucide-react";

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/* ---------- helpers ---------- */
function highlightJson(obj) {
  const esc = (s) =>
    String(s).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
  return esc(JSON.stringify(obj, null, 2))
    .replace(/&quot;/g, '"')
    .replace(/"(\w+)":/g, '<span class="tok-key">"$1"</span>:')
    .replace(/: "([^"]*)"/g, ': <span class="tok-str">"$1"</span>')
    .replace(/: (-?\d+\.?\d*)/g, ': <span class="tok-num">$1</span>')
    .replace(/: (true|false|null)/g, ': <span class="tok-bool">$1</span>');
}

const TOOL_ICONS = {
  academic_query: Database,
  schedule_appointment: CalendarDays,
  get_current_datetime: Clock,
  get_exam_schedule: CalendarDays,
  register_course: BookOpen,
  search_guidebook: Search,
};

/* ---------- Step card (cột phải) ---------- */
function StepCard({ step }) {
  const map = {
    thought: { icon: Brain, color: "#f59e0b", ring: "ring-amber-500/30", label: `Thought · Step ${step.step}` },
    action: { icon: Wrench, color: "#22d3ee", ring: "ring-cyan-500/30", label: "Action · Gọi Tool (MCP)" },
    observation: { icon: Eye, color: "#34d399", ring: "ring-emerald-500/30", label: "Observation · JSON-RPC 2.0" },
    final: { icon: Flag, color: "#a78bfa", ring: "ring-violet-500/30", label: "Final Answer" },
  };
  const cfg = map[step.kind] || map.thought;
  const Icon = cfg.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.28, ease: "easeOut" }}
      className={`relative rounded-2xl border border-white/10 bg-white/[0.03] p-4 pl-14 backdrop-blur-sm ${
        step.kind === "final" ? "bg-gradient-to-br from-violet-500/10 to-transparent" : ""
      }`}
      style={{ boxShadow: `inset 3px 0 0 ${cfg.color}` }}
    >
      <div
        className={`absolute left-3 top-4 grid h-7 w-7 place-items-center rounded-lg ring-1 ${cfg.ring}`}
        style={{ background: `${cfg.color}1f`, color: cfg.color }}
      >
        <Icon size={16} />
      </div>

      <div className="mb-1 flex items-center justify-between gap-2">
        <span className="text-[11px] font-bold uppercase tracking-wider" style={{ color: cfg.color }}>
          {cfg.label}
        </span>
        {step.latency_ms != null && (
          <span className="flex items-center gap-1 font-mono text-[10px] text-slate-400">
            <Zap size={10} /> {step.latency_ms} ms
          </span>
        )}
      </div>

      {step.kind === "action" ? (
        <div className="text-[13.5px]">
          <span className="font-mono font-semibold text-cyan-300">{step.tool_name}</span>
          <span className="text-slate-400">(</span>
          <div className="mt-1.5 flex flex-wrap gap-1.5">
            {Object.entries(step.arguments || {}).map(([k, v]) => (
              <span key={k} className="rounded-md border border-cyan-500/30 bg-cyan-500/10 px-2 py-0.5 font-mono text-[11px] text-cyan-200">
                {k}: {String(v)}
              </span>
            ))}
            {Object.keys(step.arguments || {}).length === 0 && <span className="text-slate-500">—</span>}
          </div>
          <span className="text-slate-400">)</span>
        </div>
      ) : step.kind === "observation" ? (
        <pre
          className="mt-1 overflow-x-auto rounded-xl border border-white/10 bg-[#060a14] p-3 font-mono text-[11.5px] leading-relaxed text-slate-300"
          dangerouslySetInnerHTML={{ __html: highlightJson(step.data) }}
        />
      ) : (
        <p className={`text-[13.5px] leading-relaxed text-slate-200 ${step.kind === "final" ? "font-medium" : ""}`}>
          {step.text}
        </p>
      )}
    </motion.div>
  );
}

/* ---------- Info chip (header) ---------- */
function Chip({ label, value, mono = true, accent }) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.04] px-3 py-1.5">
      <div className="text-[9px] font-semibold uppercase tracking-wider text-slate-400">{label}</div>
      <div className={`text-[12px] font-semibold ${mono ? "font-mono" : ""} ${accent || "text-slate-100"}`}>{value}</div>
    </div>
  );
}

/* ---------- App ---------- */
export default function App() {
  const [info, setInfo] = useState(null);
  const [messages, setMessages] = useState([]); // {role, text, thinking}
  const [steps, setSteps] = useState([]);
  const [reasonMeta, setReasonMeta] = useState(null); // {query, tools}
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [history, setHistory] = useState([]);

  const chatRef = useRef(null);
  const reasonRef = useRef(null);

  useEffect(() => {
    fetch("/api/info").then((r) => r.json()).then(setInfo).catch(() => {});
  }, []);
  useEffect(() => {
    if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight;
  }, [messages]);
  useEffect(() => {
    if (reasonRef.current) reasonRef.current.scrollTop = reasonRef.current.scrollHeight;
  }, [steps]);

  const examples = [
    { icon: Clock, label: "Hôm nay là ngày bao nhiêu?", q: "Hôm nay là ngày bao nhiêu?" },
    { icon: BookOpen, label: "Học phí & trợ cấp thế nào?", q: "Chương trình AI in Action trợ cấp hàng tháng bao nhiêu và điều kiện nhận là gì?" },
    { icon: CalendarDays, label: "Lịch thi của SV2026001", q: "Tra cứu lịch thi của sinh viên SV2026001." },
    { icon: Sparkles, label: "Đa bước: tra cứu → đặt lịch", q: "Tra cứu cố vấn học tập của sinh viên SV2026001, sau đó đặt lịch hẹn tư vấn với đúng cố vấn đó vào 09:30 ngày 20/09/2026." },
    { icon: Database, label: "Tra cứu học vụ SV2026001", q: "Hãy tra cứu thông tin học vụ của sinh viên SV2026001." },
  ];

  async function send(q) {
    const query = (q ?? input).trim();
    if (!query || busy) return;
    setBusy(true);
    setInput("");
    setSteps([]);
    setReasonMeta({ query, tools: null });

    setMessages((m) => [...m, { role: "user", text: query }, { role: "assistant", text: "", thinking: true }]);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, history }),
      });
      const data = await res.json();

      if (data.error) {
        setMessages((m) => replaceLastAssistant(m, "⚠️ " + data.error));
      } else {
        let finalText = data.final_answer || "";
        for (const s of data.steps) {
          setSteps((prev) => [...prev, s]);
          if (s.kind === "final") finalText = s.text;
          await sleep(230);
        }
        setMessages((m) => replaceLastAssistant(m, finalText));
        setReasonMeta({ query, tools: data.tools_called || [] });
        setHistory((h) => {
          const next = [...h, { role: "user", text: query }, { role: "assistant", text: finalText }];
          return next.slice(-12);
        });
      }
    } catch (e) {
      setMessages((m) => replaceLastAssistant(m, "⚠️ Lỗi kết nối server: " + e.message));
    } finally {
      setBusy(false);
    }
  }

  function replaceLastAssistant(m, text) {
    const copy = [...m];
    for (let i = copy.length - 1; i >= 0; i--) {
      if (copy[i].role === "assistant") {
        copy[i] = { role: "assistant", text, thinking: false };
        break;
      }
    }
    return copy;
  }

  const live = info?.live_mode;

  return (
    <div className="relative flex h-full flex-col">
      <div className="aurora" />

      {/* Header */}
      <header className="relative z-10 flex flex-wrap items-center justify-between gap-4 border-b border-white/10 bg-white/[0.02] px-6 py-3 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="grid h-11 w-11 place-items-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-500 shadow-lg shadow-indigo-500/30">
            <GraduationCap size={22} className="text-white" />
          </div>
          <div>
            <div className="text-[15px] font-extrabold tracking-tight">VinUni ReAct Agent</div>
            <div className="text-[11px] text-slate-400">Trợ lý Học vụ Thông minh · MCP Enhanced</div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {info && (
            <>
              <Chip label="LLM" value={info.provider} accent="text-indigo-300" />
              <Chip label="Model" value={info.model} accent="text-violet-300" />
              <Chip label="MCP" value={info.mcp_server} />
              <Chip label="Loops" value={info.max_iterations} />
              <div className="flex items-center gap-2 rounded-xl border px-3 py-2"
                   style={{ borderColor: live ? "#34d39955" : "#f59e0b55", background: live ? "#34d39914" : "#f59e0b14" }}>
                <span className={`h-2 w-2 rounded-full pulse-dot`} style={{ background: live ? "#34d399" : "#f59e0b" }} />
                <span className="text-[11px] font-bold" style={{ color: live ? "#34d399" : "#f59e0b" }}>
                  {live ? "LIVE · LLM thật" : "MOCK · offline"}
                </span>
              </div>
            </>
          )}
        </div>
      </header>

      {/* Workspace 2 cột */}
      <div className="relative z-10 grid min-h-0 flex-1 grid-cols-1 md:grid-cols-2">
        {/* Cột trái: Hội thoại */}
        <section className="flex min-h-0 flex-col border-r border-white/10">
          <div className="flex items-center gap-2 border-b border-white/10 px-6 py-3 text-[13px] font-bold">
            <Bot size={16} className="text-indigo-400" /> Hội thoại
          </div>

          <div ref={chatRef} className="flex-1 space-y-4 overflow-y-auto p-5">
            {messages.length === 0 && (
              <div className="mx-auto mt-6 max-w-md text-center text-slate-400">
                <div className="mx-auto mb-3 grid h-16 w-16 place-items-center rounded-2xl bg-gradient-to-br from-indigo-500/20 to-violet-500/20">
                  <Bot size={30} className="text-indigo-300" />
                </div>
                <h2 className="text-lg font-bold text-slate-100">Xin chào! Tôi là ReAct Agent Học vụ VinUni.</h2>
                <p className="mt-2 text-[13px] leading-relaxed">
                  Hỏi tôi về quy chế, tra cứu hồ sơ sinh viên, lịch thi, hoặc đặt lịch tư vấn.
                  Luồng suy luận của tôi hiện ở cột bên phải →
                </p>
                <div className="mt-5 space-y-2 text-left">
                  {examples.map((ex) => {
                    const Icon = ex.icon;
                    return (
                      <button key={ex.label} onClick={() => send(ex.q)}
                        className="flex w-full items-center gap-2.5 rounded-xl border border-white/10 bg-white/[0.03] px-3.5 py-2.5 text-[12.5px] text-slate-200 transition hover:border-indigo-500/50 hover:bg-indigo-500/10">
                        <Icon size={15} className="shrink-0 text-indigo-400" /> {ex.label}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            <AnimatePresence initial={false}>
              {messages.map((m, i) => (
                <motion.div key={i} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                  className={m.role === "user" ? "flex justify-end" : "flex gap-2.5"}>
                  {m.role === "assistant" && (
                    <div className="mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-gradient-to-br from-indigo-500/30 to-violet-500/30">
                      <Bot size={17} className="text-indigo-300" />
                    </div>
                  )}
                  <div className={
                    m.role === "user"
                      ? "max-w-[80%] rounded-2xl rounded-br-sm bg-gradient-to-br from-indigo-500 to-violet-500 px-4 py-2.5 text-[13.5px] leading-relaxed text-white shadow-lg shadow-indigo-500/20"
                      : "max-w-[88%] whitespace-pre-wrap rounded-2xl rounded-tl-sm border border-white/10 bg-white/[0.04] px-4 py-2.5 text-[13.5px] leading-relaxed text-slate-100"
                  }>
                    {m.thinking ? (
                      <span className="flex gap-1.5 py-1">
                        {[0, 1, 2].map((d) => (
                          <motion.span key={d} className="h-2 w-2 rounded-full bg-slate-400"
                            animate={{ y: [0, -5, 0], opacity: [0.4, 1, 0.4] }}
                            transition={{ duration: 1, repeat: Infinity, delay: d * 0.15 }} />
                        ))}
                      </span>
                    ) : (m.role === "user" ? <User size={14} className="mr-1.5 inline opacity-70" /> : null) }
                    {!m.thinking && m.text}
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>

          {/* Composer */}
          <div className="border-t border-white/10 bg-black/20 p-4">
            <div className="flex gap-2.5">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && send()}
                placeholder="Nhập câu hỏi… (vd: Tra cứu sinh viên SV2026001)"
                className="flex-1 rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 text-[13.5px] text-slate-100 outline-none transition placeholder:text-slate-500 focus:border-indigo-500/60 focus:ring-2 focus:ring-indigo-500/20"
              />
              <button onClick={() => send()} disabled={busy}
                className="flex items-center gap-1.5 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-500 px-5 text-[13.5px] font-semibold text-white transition hover:brightness-110 disabled:opacity-50">
                <Send size={15} /> Gửi
              </button>
            </div>
          </div>
        </section>

        {/* Cột phải: Luồng suy luận */}
        <section className="flex min-h-0 flex-col">
          <div className="flex items-center justify-between gap-2 border-b border-white/10 px-6 py-3">
            <div className="flex items-center gap-2 text-[13px] font-bold">
              <Brain size={16} className="text-amber-400" /> Luồng suy luận của Agent
            </div>
            <div className="flex gap-1.5">
              {[["Thought", "#f59e0b"], ["Action", "#22d3ee"], ["Observation", "#34d399"], ["Final", "#a78bfa"]].map(([l, c]) => (
                <span key={l} className="rounded-full border px-2 py-0.5 text-[9.5px] font-semibold"
                  style={{ color: c, borderColor: `${c}44` }}>{l}</span>
              ))}
            </div>
          </div>

          {reasonMeta && (
            <div className="border-b border-dashed border-white/10 bg-white/[0.02] px-6 py-2.5 text-[12px] text-slate-400">
              Câu hỏi: <b className="text-slate-200">{reasonMeta.query}</b>
              {reasonMeta.tools && reasonMeta.tools.length > 0 && (
                <span> · đã gọi: {reasonMeta.tools.map((t, i) => (
                  <span key={i}><b className="text-cyan-300 font-mono">{t}</b>{i < reasonMeta.tools.length - 1 ? " → " : ""}</span>
                ))}</span>
              )}
              {reasonMeta.tools && reasonMeta.tools.length === 0 && <span> · trả lời trực tiếp</span>}
            </div>
          )}

          <div ref={reasonRef} className="flex-1 space-y-3 overflow-y-auto p-5">
            {steps.length === 0 ? (
              <div className="mx-auto mt-6 max-w-sm text-center text-slate-400">
                <div className="mx-auto mb-3 grid h-14 w-14 place-items-center rounded-2xl bg-gradient-to-br from-amber-500/15 to-transparent">
                  <Search size={26} className="text-amber-300/80" />
                </div>
                <p className="text-[13px] leading-relaxed">
                  Gửi một câu hỏi để xem Agent suy luận từng bước<br />
                  <b className="text-slate-200">Thought → Action → Observation → Final Answer</b>.
                </p>
                {info?.tools && (
                  <div className="mt-5 space-y-2 text-left">
                    <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">{info.tools.length} Tools qua MCP</div>
                    {info.tools.map((t) => {
                      const Icon = TOOL_ICONS[t.name] || Wrench;
                      return (
                        <div key={t.name} className="rounded-xl border border-white/10 bg-white/[0.03] p-2.5">
                          <div className="flex items-center gap-2 font-mono text-[12px] font-semibold text-cyan-300">
                            <Icon size={13} /> {t.name}()
                          </div>
                          <div className="mt-1 text-[11px] leading-snug text-slate-400">{t.description}</div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            ) : (
              <AnimatePresence initial={false}>
                {steps.map((s, i) => <StepCard key={i} step={s} />)}
              </AnimatePresence>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
