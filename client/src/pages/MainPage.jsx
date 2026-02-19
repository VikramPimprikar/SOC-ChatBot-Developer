import { auth } from "../firebase";
import { useEffect, useMemo, useRef, useState } from "react";

const BASE_URL = "https://ragassistant.online";
const QUERY_ENDPOINT = `${BASE_URL}/chat`;


function nowTime() {
  const d = new Date();
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function ChatBubble({ role, text, time }) {
  const isUser = role === "user";

  return (
    <div
      className={`w-full flex ${
        isUser ? "justify-end" : "justify-start"
      } group animate-fadeIn`}
    >
      <div
        className={[
          "max-w-[85%] rounded-2xl px-5 py-3.5 border backdrop-blur-sm transition-all duration-200",
          isUser
            ? "bg-blue-600/90 border-blue-500/50 text-white shadow-lg"
            : "bg-slate-800/60 border-slate-700/50 text-slate-100 shadow-lg",
        ].join(" ")}
      >
        <div className="text-[15px] leading-relaxed whitespace-pre-wrap">
          {text}
        </div>
        <div className={`mt-2 text-[11px] text-right flex items-center justify-end gap-1.5 ${
          isUser ? "text-blue-200" : "text-slate-400"
        }`}>
          <svg
            className="w-3 h-3"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          {time}
        </div>
      </div>
    </div>
  );
}

function SidebarCard({ title, children, icon }) {
  return (
    <div className="bg-slate-900/40 border border-slate-700/50 rounded-xl shadow-lg backdrop-blur-xl">
      <div className="px-5 py-4 border-b border-slate-700/50">
        <div className="flex items-center gap-2.5">
          {icon && <div className="text-blue-400">{icon}</div>}
          <div className="text-sm font-medium text-slate-100">
            {title}
          </div>
        </div>
      </div>
      <div className="p-5">
        {children}
      </div>
    </div>
  );
}

export default function MainPage({ user, onLogout }) {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text:
        "Welcome to the SOC Knowledge Assistant. I'm here to help you with security operations and incident response procedures.\n\nYou can ask me questions like:\n• How do we contain a phishing attack?\n• What are the remediation steps for ransomware?\n• Show me the incident response procedure for DDoS attacks",
      time: nowTime(),
    },
  ]);

  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const [retrievedChunks, setRetrievedChunks] = useState([]);
  const [latencyMs, setLatencyMs] = useState(null);

  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const canSend = useMemo(
    () => input.trim().length > 0 && !isLoading,
    [input, isLoading]
  );

  function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  async function pollForResult(requestId) {
    const url = `${BASE_URL}/result/${requestId}`;

    // Try for ~30 seconds max
    for (let i = 0; i < 30; i++) {
      const res = await fetch(url, { method: "GET" });

      if (res.ok) {
        const data = await res.json();
        if (data?.status === "success") return data;
      } else if (res.status === 404) {
        // Result not ready yet
      } else {
        const errText = await res.text();
        throw new Error(errText || `HTTP Error ${res.status}`);
      }

      await sleep(1000);
    }

    throw new Error("Timeout: result not ready after 30 seconds.");
  }

  async function handleSend() {
  const question = input.trim();
  if (!question) return;

  setInput("");
  setIsLoading(true);

  const userMsg = { role: "user", text: question, time: nowTime() };
  setMessages((prev) => [...prev, userMsg]);

  try {
    const start = performance.now();

    // 🔐 Get Firebase auth user directly
    const currentUser = auth.currentUser;

    if (!currentUser) {
      throw new Error("User not authenticated on frontend.");
    }

    // Force refresh token
    const idToken = await currentUser.getIdToken(true);

    console.log("ID TOKEN EXISTS:", !!idToken);

    const res = await fetch(QUERY_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${idToken}`,
      },
      body: JSON.stringify({ text: question, top_k: 3 }),
    });

    if (!res.ok) {
      const errText = await res.text();
      throw new Error(errText || `HTTP Error ${res.status}`);
    }

    const data = await res.json();

    const end = performance.now();
    setLatencyMs(Math.round(end - start));

    const finalAnswer =
      data?.final_answer || "No answer returned by backend.";

    const contexts = Array.isArray(data?.contexts_used)
      ? data.contexts_used
      : [];

    const mappedContext = contexts.map((text, idx) => ({
      playbook: `Context ${idx + 1}`,
      section: text,
      score: 1.0,
    }));

    setRetrievedChunks(mappedContext);

    setMessages((prev) => [
      ...prev,
      { role: "assistant", text: finalAnswer, time: nowTime() },
    ]);
  } catch (err) {
    console.error("AUTH ERROR:", err);

    setRetrievedChunks([]);

    setMessages((prev) => [
      ...prev,
      {
        role: "assistant",
        text:
          "Authentication failed.\n\n" +
          `Error: ${err.message}`,
        time: nowTime(),
      },
    ]);
  } finally {
    setIsLoading(false);
  }
}


  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (canSend) handleSend();
    }
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white relative overflow-hidden">
      {/* Animated background effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-1/2 -left-1/4 w-full h-full bg-gradient-to-br from-blue-600/15 via-purple-600/10 to-transparent rounded-full blur-3xl animate-pulse"></div>
        <div
          className="absolute -bottom-1/2 -right-1/4 w-full h-full bg-gradient-to-tl from-purple-600/15 via-pink-600/10 to-transparent rounded-full blur-3xl animate-pulse"
          style={{ animationDelay: "2s" }}
        ></div>
        <div
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-3/4 h-3/4 bg-gradient-to-r from-cyan-600/8 via-blue-600/8 to-purple-600/8 rounded-full blur-3xl animate-pulse"
          style={{ animationDelay: "1s" }}
        ></div>
      </div>

      {/* Grid overlay */}
      <div className="fixed inset-0 bg-[linear-gradient(rgba(59,130,246,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(59,130,246,0.03)_1px,transparent_1px)] bg-[size:60px_60px] [mask-image:radial-gradient(ellipse_80%_80%_at_50%_50%,black,transparent)] pointer-events-none"></div>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fadeIn {
          animation: fadeIn 0.3s ease-out;
        }
      `}</style>

      <header className="sticky top-0 z-50 bg-slate-950/80 backdrop-blur-2xl border-b border-slate-800/50 shadow-2xl">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg">
                <svg
                  className="w-6 h-6 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                  />
                </svg>
              </div>

              <div>
                <h1 className="text-xl font-semibold text-white">
                  SOC Knowledge Assistant
                </h1>
                <p className="text-xs text-slate-400 mt-0.5 flex items-center gap-1.5">
                  <span className="inline-block w-1.5 h-1.5 rounded-full bg-blue-500"></span>
                  Powered by RAG Technology
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="hidden md:flex items-center gap-3 px-4 py-2 rounded-lg bg-slate-800/60 border border-slate-700/50">
                <div className="relative">
                  <div className="w-8 h-8 rounded-lg overflow-hidden border border-slate-600">
                    {user?.photoURL ? (
                      <img
                        src={user.photoURL}
                        alt="User"
                        className="w-full h-full object-cover"
                        referrerPolicy="no-referrer"
                      />
                    ) : (
                      <div className="w-full h-full bg-slate-700 flex items-center justify-center text-xs font-semibold text-slate-200">
                        {(user?.email?.[0] || "U").toUpperCase()}
                      </div>
                    )}
                  </div>
                  <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-green-500 border-2 border-slate-950"></div>
                </div>

                <div className="leading-tight">
                  <div className="text-sm font-semibold text-slate-100">
                    {user?.displayName || "User"}
                  </div>
                  <div className="text-xs text-slate-400 max-w-[160px] truncate">
                    {user?.email || "unknown"}
                  </div>
                </div>
              </div>

              <button
                onClick={onLogout}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white text-sm font-medium transition-all duration-200 flex items-center gap-2"
              >
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                  />
                </svg>
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="relative max-w-7xl mx-auto px-6 py-6 grid grid-cols-1 lg:grid-cols-[1fr_380px] gap-6">
        {/* Chat section */}
        <section className="relative">
          <div className="bg-slate-900/40 border border-slate-700/50 rounded-2xl overflow-hidden flex flex-col h-[calc(100vh-140px)] shadow-2xl backdrop-blur-xl">
            <div className="px-6 py-4 border-b border-slate-700/50 bg-slate-800/40">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                  <div className="text-sm font-medium text-slate-100">
                    Conversation
                  </div>
                </div>
                {latencyMs !== null && (
                  <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/60 border border-slate-700/50">
                    <svg
                      className="w-4 h-4 text-blue-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M13 10V3L4 14h7v7l9-11h-7z"
                      />
                    </svg>
                    <span className="text-sm font-semibold text-slate-200">
                      {latencyMs}ms
                    </span>
                  </div>
                )}
              </div>
            </div>

            <div className="flex-1 overflow-auto px-6 py-6 space-y-4">
              {messages.map((m, idx) => (
                <ChatBubble key={idx} role={m.role} text={m.text} time={m.time} />
              ))}
              {isLoading && (
                <div className="w-full flex justify-start animate-fadeIn">
                  <div className="max-w-[85%] rounded-2xl px-5 py-3.5 border bg-slate-800/60 border-slate-700/50 shadow-lg backdrop-blur-sm">
                    <div className="flex items-center gap-3">
                      <div className="flex gap-1">
                        <div
                          className="w-2 h-2 rounded-full bg-blue-500 animate-bounce"
                          style={{ animationDelay: "0ms" }}
                        ></div>
                        <div
                          className="w-2 h-2 rounded-full bg-blue-500 animate-bounce"
                          style={{ animationDelay: "150ms" }}
                        ></div>
                        <div
                          className="w-2 h-2 rounded-full bg-blue-500 animate-bounce"
                          style={{ animationDelay: "300ms" }}
                        ></div>
                      </div>
                      <span className="text-sm text-slate-300 font-normal">
                        Processing your request...
                      </span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            <div className="border-t border-slate-700/50 p-4 bg-slate-800/30">
              <div className="flex gap-3">
                <textarea
                  className="flex-1 resize-none rounded-xl bg-slate-900/60 border border-slate-700/60 px-4 py-3 text-sm outline-none focus:border-blue-500/60 focus:ring-2 focus:ring-blue-500/20 transition-all placeholder-slate-500 text-slate-100"
                  rows={2}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask about SOC procedures, incident response, or security playbooks..."
                />
                <button
                  onClick={handleSend}
                  disabled={!canSend}
                  className={[
                    "px-6 rounded-xl text-sm font-semibold transition-all duration-200 flex items-center gap-2",
                    canSend
                      ? "bg-blue-600 hover:bg-blue-700 text-white shadow-lg"
                      : "bg-slate-800 text-slate-500 cursor-not-allowed",
                  ].join(" ")}
                >
                  {isLoading ? (
                    <>
                      <svg
                        className="animate-spin h-4 w-4"
                        fill="none"
                        viewBox="0 0 24 24"
                      >
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"
                        ></circle>
                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                        ></path>
                      </svg>
                      Sending
                    </>
                  ) : (
                    <>
                      Send
                      <svg
                        className="w-4 h-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M14 5l7 7m0 0l-7 7m7-7H3"
                        />
                      </svg>
                    </>
                  )}
                </button>
              </div>

              <div className="mt-3 flex items-center gap-2 text-xs text-slate-500">
                <svg
                  className="w-3.5 h-3.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <span>
                  Press{" "}
                  <kbd className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-400 font-mono text-xs">
                    Enter
                  </kbd>{" "}
                  to send •{" "}
                  <kbd className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-400 font-mono text-xs">
                    Shift+Enter
                  </kbd>{" "}
                  for new line
                </span>
              </div>
            </div>
          </div>
        </section>

        {/* Sidebar */}
        <aside className="space-y-5">
          <SidebarCard
            title="Retrieved References"
            icon={
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
            }
          >
            {retrievedChunks.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <div className="w-14 h-14 rounded-xl bg-slate-800/60 flex items-center justify-center mb-3 border border-slate-700/50">
                  <svg
                    className="w-7 h-7 text-slate-500"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.5}
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                </div>
                <div className="text-sm text-slate-300 font-medium mb-1">
                  No references yet
                </div>
                <div className="text-xs text-slate-500 leading-relaxed">
                  Send a query to see relevant playbook references
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                {retrievedChunks.map((r, i) => (
                  <div
                    key={i}
                    className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/50 hover:border-blue-500/40 hover:shadow-lg transition-all duration-200"
                  >
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <div className="text-sm font-medium text-slate-200">
                        {r.playbook}
                      </div>
                      <div className="flex items-center gap-1 px-2 py-1 rounded-full bg-blue-500/20 border border-blue-500/30">
                        <svg
                          className="w-3 h-3 text-blue-400"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                        </svg>
                        <span className="text-xs font-semibold text-blue-300">
                          {r.score.toFixed(2)}
                        </span>
                      </div>
                    </div>
                    <div className="text-xs text-slate-400 leading-relaxed">
                      {r.section}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </SidebarCard>

          <SidebarCard
            title="System Status"
            icon={
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            }
          >
            <div className="space-y-3">
              {[
                { 
                  icon: "✓", 
                  text: "Backend Connected", 
                  color: "text-green-400", 
                  bg: "bg-green-500/10", 
                  border: "border-green-500/30" 
                },
                { 
                  icon: "✓", 
                  text: "RAG Pipeline Active", 
                  color: "text-blue-400", 
                  bg: "bg-blue-500/10", 
                  border: "border-blue-500/30" 
                },
                { 
                  icon: "✓", 
                  text: "System Operational", 
                  color: "text-purple-400", 
                  bg: "bg-purple-500/10", 
                  border: "border-purple-500/30" 
                },
              ].map((status, i) => (
                <div
                  key={i}
                  className={`flex items-center gap-2.5 p-3 rounded-lg ${status.bg} border ${status.border}`}
                >
                  <span className={`text-sm font-semibold ${status.color}`}>
                    {status.icon}
                  </span>
                  <span className="text-sm text-slate-300">
                    {status.text}
                  </span>
                </div>
              ))}
            </div>
          </SidebarCard>
        </aside>
      </main>
    </div>
  );
}
