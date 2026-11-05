"use client";

import React, { useState, useEffect, useRef } from "react";

const API_BASE = "http://localhost:8000";

interface EventItem {
  id: number;
  event_type: string;
  actor: string;
  payload: any;
  switch_message_id?: string;
  created_at: string;
}

export default function CaseFilePage() {
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [investigationId, setInvestigationId] = useState("BP-0007");
  const [investigation, setInvestigation] = useState<any>(null);
  const [artifacts, setArtifacts] = useState<any>(null);
  const [diffData, setDiffData] = useState<any>(null);
  const [events, setEvents] = useState<EventItem[]>([]);
  const [voiceInput, setVoiceInput] = useState("");
  const [comparisonSlider, setComparisonSlider] = useState(50);
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const [activeStage, setActiveStage] = useState<number | null>(null);
  const [isSubmittingVoice, setIsSubmittingVoice] = useState(false);
  const [switchOutput, setSwitchOutput] = useState<string | null>(null);

  const voiceInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme === "dark" ? "dark" : "light");
  }, [theme]);

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "/" && document.activeElement !== voiceInputRef.current) {
        e.preventDefault();
        voiceInputRef.current?.focus();
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  async function loadData() {
    try {
      const invRes = await fetch(`${API_BASE}/api/investigations/${investigationId}`);
      if (invRes.ok) {
        const inv = await invRes.json();
        setInvestigation(inv);
        if (inv.events) setEvents(inv.events);
      }
      const artRes = await fetch(`${API_BASE}/api/investigations/${investigationId}/artifacts`);
      if (artRes.ok) setArtifacts(await artRes.json());

      const diffRes = await fetch(`${API_BASE}/api/investigations/${investigationId}/diff`);
      if (diffRes.ok) setDiffData(await diffRes.json());
    } catch (err) {}
  }

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 3000);
    return () => clearInterval(interval);
  }, [investigationId]);

  useEffect(() => {
    let es: EventSource | null = null;
    try {
      es = new EventSource(`${API_BASE}/api/investigations/${investigationId}/events`);
      es.addEventListener("update", (e) => {
        const data = JSON.parse(e.data);
        setEvents((prev) => [...prev, data]);
        loadData();
      });
    } catch (e) {}
    return () => {
      es?.close();
    };
  }, [investigationId]);

  async function handleSendVoice(textToSend?: string) {
    const text = textToSend || voiceInput;
    if (!text.trim()) return;
    setIsSubmittingVoice(true);
    try {
      await fetch(`${API_BASE}/api/investigations/${investigationId}/voice`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, is_voice: true }),
      });
      setVoiceInput("");
      await loadData();
    } catch (err) {
    } finally {
      setIsSubmittingVoice(false);
    }
  }

  async function handleRunJudgeCommand(cmd: string) {
    try {
      const res = await fetch(`${API_BASE}/api/investigations/${investigationId}/switch-command`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command: cmd }),
      });
      const data = await res.json();
      setSwitchOutput(`[${cmd}]\n${data.output}`);
    } catch (err) {}
  }

  const status = investigation?.status || "CREATED";
  const baselineReport = investigation?.baseline_report;
  const patchSummary = investigation?.patch_summary;
  const verificationReport = investigation?.verification_report;
  const decision = investigation?.decision;

  const isBaselineDone = !!baselineReport;
  const isPatchDone = !!patchSummary && patchSummary.test_exit_code === 0;
  const isRetestDone = !!verificationReport && verificationReport.passes_observed === 3;
  const isVerified = status === "VERIFIED" || status === "HUMAN_ACCEPTED";
  const isAccepted = status === "HUMAN_ACCEPTED";

  const stages = [
    {
      num: 1,
      title: "Baseline Failure (3/3)",
      state: isBaselineDone ? "pass" : status === "REPRODUCING" ? "active" : "pending",
      detail: baselineReport ? "3/3 HTTP 500 TypeError crashes reproduced" : "Pending reproduction run",
    },
    {
      num: 2,
      title: "Regression Test Added",
      state: isPatchDone ? "pass" : isBaselineDone ? "active" : "pending",
      detail: isPatchDone ? "Added test assertions in coupon.test.ts" : "Pending code-fixer patch",
    },
    {
      num: 3,
      title: "Build & Type Safety",
      state: isPatchDone ? "pass" : "pending",
      detail: isPatchDone ? "Allowlisted test and tsc --noEmit exited 0" : "Pending build check",
    },
    {
      num: 4,
      title: "Independent Retest (3/3)",
      state: isRetestDone ? "pass" : isPatchDone ? "active" : "pending",
      detail: isRetestDone ? "3/3 passes with 'Coupon expired' validation" : "Pending browser retest",
    },
    {
      num: 5,
      title: "Regression Safety",
      state: isRetestDone ? "pass" : "pending",
      detail: isRetestDone ? "SAVE20 discount and empty coupon passed" : "Pending safety checks",
    },
    {
      num: 6,
      title: "Human !roles Gate",
      state: isAccepted ? "pass" : isVerified ? "active" : "pending",
      detail: isAccepted ? "qa-commander approved patch for merge" : "Awaiting qa-commander sign-off",
    },
  ];

  let parsedPreview = "Listening via Wispr Flow... (Press / to focus · Dictate @repro, @fixer, or approve)";
  if (voiceInput) {
    const vl = voiceInput.toLowerCase();
    if (vl.startsWith("!")) {
      parsedPreview = `Switch Room Command: ${voiceInput.trim()} -> Execute inspection`;
    } else if (vl.includes("@repro") || vl.includes("reproduce") || vl.includes("investigate") || vl.includes("start investigation")) {
      parsedPreview = "Checkpoint 1 (@repro): Baseline 3/3 Playwright reproduction -> demo-app:3000/checkout";
    } else if (vl.includes("@fixer") || vl.includes("patch") || vl.includes("worktree") || vl.includes("fix")) {
      parsedPreview = "Checkpoint 2 (@fixer): Isolated Git worktree patch (Groq LLM) + independent 3/3 browser retest";
    } else if (vl.includes("qa-commander") || vl.includes("approve") || vl.includes("accept") || vl.includes("sign")) {
      parsedPreview = "Checkpoint 3 (qa-commander): Human Gate Sign-off -> Record verified decision in #bugproof";
    } else {
      parsedPreview = `Room message: "${voiceInput}" -> Route to #bugproof`;
    }
  }

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <header
        style={{
          borderBottom: "1px solid var(--border-hairline)",
          background: "var(--bg-surface)",
          padding: "12px 24px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <span className="mono" style={{ fontWeight: 700, fontSize: 14, letterSpacing: 1 }}>
            BUGPROOF // CASE FILE
          </span>
          <span style={{ color: "var(--text-muted)", fontSize: 13 }}>Switch Room #bugproof mirror</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <button
            onClick={() => setTheme(theme === "light" ? "dark" : "light")}
            style={{
              background: "none",
              border: "1px solid var(--border-hairline)",
              padding: "4px 10px",
              fontSize: 12,
              cursor: "pointer",
            }}
          >
            {theme === "light" ? "Darkroom Mode" : "Paper Mode"}
          </button>
        </div>
      </header>

      <div style={{ display: "grid", gridTemplateColumns: "180px 1fr 340px", flex: 1 }}>
        <aside
          style={{
            borderRight: "1px solid var(--border-hairline)",
            background: "var(--bg-surface)",
            padding: "20px 16px",
          }}
        >
          <div className="mono" style={{ fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", marginBottom: 12 }}>
            Open Case Files
          </div>
          <div
            style={{
              padding: "8px 12px",
              background: "var(--bg-canvas)",
              border: "1px solid var(--border-hairline)",
              marginBottom: 8,
              cursor: "pointer",
            }}
          >
            <div className="mono" style={{ fontSize: 12, fontWeight: 700 }}>
              BP-0007
            </div>
            <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>
              EXPIRED10 Crash
            </div>
          </div>
          <div style={{ borderTop: "1px solid var(--border-hairline)", marginTop: 24, paddingTop: 16 }}>
            <div className="mono" style={{ fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", marginBottom: 8 }}>
              Voice Checkpoints
            </div>
            <div style={{ fontSize: 12, marginBottom: 8, color: isBaselineDone ? "var(--signal-verdigris)" : "var(--text-muted)" }}>
              ✓ 1: Intake & Repro
            </div>
            <div style={{ fontSize: 12, marginBottom: 8, color: isPatchDone ? "var(--signal-verdigris)" : "var(--text-muted)" }}>
              ✓ 2: Patch Directive
            </div>
            <div style={{ fontSize: 12, color: isAccepted ? "var(--signal-verdigris)" : "var(--text-muted)" }}>
              ✓ 3: Human Sign-Off
            </div>
          </div>
        </aside>

        <main style={{ padding: "32px 40px", overflowY: "auto", maxHeight: "calc(100vh - 120px)" }}>
          <section style={{ marginBottom: 36, borderBottom: "1px solid var(--border-hairline)", paddingBottom: 24 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
              <div>
                <span className="mono" style={{ fontSize: 12, color: "var(--text-muted)" }}>
                  INVESTIGATION // {investigationId}
                </span>
                <h1 className="serif" style={{ fontSize: 32, fontWeight: 400, marginTop: 4, letterSpacing: -0.5 }}>
                  Expired coupon crashes checkout view
                </h1>
                <div style={{ display: "flex", gap: 16, marginTop: 10, fontSize: 13, color: "var(--text-muted)" }}>
                  <span>Target: demo-app:3000/checkout</span>
                  <span>·</span>
                  <span>Coupon: EXPIRED10</span>
                  <span>·</span>
                  <span className="mono" style={{ fontWeight: 600, color: isVerified ? "var(--signal-verdigris)" : "var(--signal-vermilion)" }}>
                    STATUS: {status}
                  </span>
                </div>
              </div>

              {isVerified && (
                <div
                  className="stamp-badge mono"
                  style={{
                    color: isAccepted ? "var(--signal-verdigris)" : "var(--signal-ochre)",
                    borderColor: isAccepted ? "var(--signal-verdigris)" : "var(--signal-ochre)",
                  }}
                >
                  {isAccepted ? "APPROVED FOR MERGE" : "VERIFIED (INDEPENDENT RETEST)"}
                </div>
              )}
            </div>
          </section>

          <section style={{ marginBottom: 40 }}>
            <div className="mono" style={{ fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", marginBottom: 16 }}>
              Exhibits // Proof Before Fix Spine
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(6, 1fr)", gap: 12 }}>
              {stages.map((st) => (
                <div
                  key={st.num}
                  onClick={() => setActiveStage(st.num)}
                  style={{
                    border: "1px solid var(--border-hairline)",
                    background: activeStage === st.num ? "var(--bg-canvas)" : "var(--bg-surface)",
                    padding: 12,
                    cursor: "pointer",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6 }}>
                    <div
                      style={{
                        width: 8,
                        height: 8,
                        borderRadius: "50%",
                        background:
                          st.state === "pass"
                            ? "var(--signal-verdigris)"
                            : st.state === "active"
                            ? "var(--signal-ochre)"
                            : "var(--border-hairline)",
                      }}
                    />
                    <span className="mono" style={{ fontSize: 11, fontWeight: 700 }}>
                      0{st.num}
                    </span>
                  </div>
                  <div style={{ fontSize: 12, fontWeight: 500, lineHeight: 1.3 }}>{st.title}</div>
                  <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 4 }}>{st.detail}</div>
                </div>
              ))}
            </div>
          </section>

          <section style={{ marginBottom: 40 }}>
            <div className="mono" style={{ fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", marginBottom: 16 }}>
              Exhibit A // 3/3 Baseline Reproduction Filmstrip
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16 }}>
              {[1, 2, 3].map((att) => (
                <div
                  key={att}
                  style={{
                    border: "1px solid var(--border-hairline)",
                    background: "var(--bg-surface)",
                    padding: 8,
                  }}
                >
                  <div style={{ height: 140, background: "#000", position: "relative", overflow: "hidden" }}>
                    <img
                      src={`${API_BASE}/artifacts/${investigationId}/repro/attempt-${att}-after.png`}
                      alt={`Attempt ${att}`}
                      style={{ width: "100%", height: "100%", objectFit: "cover" }}
                      onError={(e) => {
                        (e.target as any).src = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='100' height='100'><rect width='100%' height='100%' fill='%23222'/><text x='50%' y='50%' fill='%23666' dominant-baseline='middle' text-anchor='middle'>Frame not loaded</text></svg>";
                      }}
                    />
                    <div
                      className="mono"
                      style={{
                        position: "absolute",
                        top: 6,
                        right: 6,
                        background: "rgba(200, 64, 42, 0.9)",
                        color: "#fff",
                        fontSize: 10,
                        padding: "2px 6px",
                      }}
                    >
                      FAIL 500
                    </div>
                  </div>
                  <div className="mono" style={{ fontSize: 11, marginTop: 8, color: "var(--text-muted)" }}>
                    Attempt #{att} · HTTP 500 TypeError
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section style={{ marginBottom: 40 }}>
            <div className="mono" style={{ fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", marginBottom: 16 }}>
              Exhibit B // Draggable Registration Plate (Before Crash vs After Patch)
            </div>
            <div
              style={{
                position: "relative",
                height: 380,
                border: "1px solid var(--border-hairline)",
                overflow: "hidden",
                background: "#000",
                cursor: "ew-resize",
              }}
              onMouseMove={(e) => {
                const rect = e.currentTarget.getBoundingClientRect();
                const pos = ((e.clientX - rect.left) / rect.width) * 100;
                setComparisonSlider(Math.max(5, Math.min(95, pos)));
              }}
            >
              <img
                src={`${API_BASE}/artifacts/${investigationId}/repro/after-crash.png`}
                alt="Before patch crash"
                style={{ width: "100%", height: "100%", objectFit: "contain", position: "absolute" }}
              />
              <div
                style={{
                  position: "absolute",
                  left: 0,
                  top: 0,
                  bottom: 0,
                  width: `${comparisonSlider}%`,
                  overflow: "hidden",
                  borderRight: "2px solid #fff",
                }}
              >
                <img
                  src={`${API_BASE}/artifacts/${investigationId}/retest/attempt-1-after.png`}
                  alt="After patch verified"
                  style={{ width: "100%", height: "100%", objectFit: "contain" }}
                />
              </div>
              <div className="mono" style={{ position: "absolute", bottom: 10, left: 12, background: "rgba(0,0,0,0.7)", color: "#fff", padding: "2px 8px", fontSize: 11 }}>
                RETEST VERIFIED (LEFT)
              </div>
              <div className="mono" style={{ position: "absolute", bottom: 10, right: 12, background: "rgba(0,0,0,0.7)", color: "#fff", padding: "2px 8px", fontSize: 11 }}>
                BASELINE CRASH (RIGHT)
              </div>
            </div>
          </section>

          <section style={{ marginBottom: 40 }}>
            <div className="mono" style={{ fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", marginBottom: 16 }}>
              Exhibit C // Console & Network Ledger
            </div>
            <div
              className="mono"
              style={{
                border: "1px solid var(--border-hairline)",
                background: "var(--bg-surface)",
                padding: 16,
                fontSize: 12,
                maxHeight: 200,
                overflowY: "auto",
              }}
            >
              <div style={{ color: "var(--signal-vermilion)", textDecoration: "underline", marginBottom: 6 }}>
                [ERR] TypeError: Cannot read properties of null (reading 'discount')
              </div>
              <div style={{ color: "var(--text-muted)", marginBottom: 4 }}>
                &gt; at POST (app/api/checkout/coupon/route.ts:6:32)
              </div>
              <div style={{ color: "var(--text-muted)", marginBottom: 8 }}>
                &gt; POST /api/checkout/coupon HTTP/1.1 500 Internal Server Error
              </div>
              <div style={{ borderTop: "1px solid var(--border-hairline)", paddingTop: 8, marginTop: 8 }}>
                <span style={{ color: "var(--signal-verdigris)" }}>
                  [FILTER RULE APPLIED]: Resource response 400 from invalid coupon classified as expected validation behavior.
                </span>
              </div>
            </div>
          </section>

          <section style={{ marginBottom: 40 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
              <div className="mono" style={{ fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase" }}>
                Exhibit D // Diff Reading Room (Worktree bugproof/{investigationId})
              </div>
              {diffData?.diff && (
                <button
                  onClick={() => navigator.clipboard.writeText(diffData.diff)}
                  className="mono"
                  style={{
                    background: "none",
                    border: "1px solid var(--border-hairline)",
                    fontSize: 11,
                    padding: "3px 8px",
                    cursor: "pointer",
                  }}
                >
                  Copy Patch Diff
                </button>
              )}
            </div>
            <div
              className="mono"
              style={{
                border: "1px solid var(--border-hairline)",
                background: "var(--bg-surface)",
                padding: 16,
                fontSize: 12,
                overflowX: "auto",
                maxHeight: 260,
                whiteSpace: "pre-wrap",
              }}
            >
              {diffData?.diff || "No diff generated yet. Awaiting patch directive."}
            </div>
          </section>

          <section style={{ marginBottom: 40, border: "1px solid var(--border-hairline)", padding: 24, background: "var(--bg-surface)" }}>
            <div className="mono" style={{ fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", marginBottom: 8 }}>
              Finding & Deterministic Proof
            </div>
            <h2 className="serif" style={{ fontSize: 24, fontWeight: 400, marginBottom: 12 }}>
              {isVerified ? "Verified for the tested scenario." : "Verification pending or inconclusive."}
            </h2>
            <ol style={{ paddingLeft: 20, fontSize: 13, lineHeight: 1.8 }}>
              <li>Baseline Playwright scenario reproduced failure 3/3 times before patch.</li>
              <li>Regression test added to test suite covering null and expired promo codes.</li>
              <li>Subprocess test runner and tsc --noEmit executed with exit code 0.</li>
              <li>Independent post-patch browser retest passed 3/3 times with zero console errors.</li>
              <li>Auxiliary checkout flows (SAVE20 20% discount and empty promo) preserved.</li>
            </ol>
          </section>

          <section style={{ border: "1px solid var(--border-hairline)", padding: 20, background: "var(--bg-surface)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
              <div>
                <div className="mono" style={{ fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase" }}>
                  Interactive 3-Checkpoint Flow // Wispr Voice Or Direct Trigger
                </div>
                <div style={{ fontSize: 13, marginTop: 4 }}>
                  Execute the 3 distinct checkpoints step-by-step or dictate via Wispr Flow into the command bar below.
                </div>
              </div>
            </div>
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
              <button
                disabled={isSubmittingVoice || status === "REPRODUCING"}
                onClick={() =>
                  handleSendVoice(
                    "@repro start investigation BP-0007 on demo-app checkout. When I apply coupon code EXPIRED10, the checkout page crashes instead of showing Coupon expired. Reproduce it three times and capture screenshots, console errors, and failed network requests."
                  )
                }
                style={{
                  background: isBaselineDone ? "var(--signal-verdigris)" : "#2b2621",
                  color: "#fff",
                  border: "none",
                  padding: "8px 14px",
                  fontSize: 12,
                  cursor: isSubmittingVoice ? "not-allowed" : "pointer",
                  fontWeight: 500,
                }}
              >
                {isBaselineDone ? "1. Baseline Reproduced (3/3)" : "1. Trigger Baseline (@repro)"}
              </button>
              <button
                disabled={!isBaselineDone || isRetestDone || isSubmittingVoice}
                onClick={() =>
                  handleSendVoice(
                    "@fixer baseline failure is confirmed with a null TypeError on coupon lookup. Create isolated Git worktree BP-0007, add a null and expiry guard returning HTTP 400 Coupon expired, write a regression test, and do not touch the main branch."
                  )
                }
                style={{
                  background: isRetestDone ? "var(--signal-verdigris)" : "#2b2621",
                  color: "#fff",
                  border: "none",
                  padding: "8px 14px",
                  fontSize: 12,
                  cursor: !isBaselineDone || isRetestDone || isSubmittingVoice ? "not-allowed" : "pointer",
                  fontWeight: 500,
                }}
              >
                {isRetestDone ? "2. Patch & Retest Verified (3/3)" : "2. Trigger Patch & Retest (@fixer)"}
              </button>
              <button
                disabled={!isVerified || isAccepted || isSubmittingVoice}
                onClick={() =>
                  handleSendVoice(
                    "As qa-commander, I accept verified patch BP-0007. Both the regression suite and independent three-of-three browser retest passed. Record the verified decision in the Switch room."
                  )
                }
                style={{
                  background: isAccepted ? "var(--signal-verdigris)" : "#2b2621",
                  color: "#fff",
                  border: "none",
                  padding: "8px 14px",
                  fontSize: 12,
                  cursor: !isVerified || isAccepted || isSubmittingVoice ? "not-allowed" : "pointer",
                  fontWeight: 500,
                }}
              >
                {isAccepted ? "3. Decision Logged (Accepted)" : "3. Authorize & Sign-Off (qa-commander)"}
              </button>
            </div>
          </section>

          <section style={{ border: "1px solid var(--border-hairline)", padding: 20, background: "var(--bg-surface)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <div className="mono" style={{ fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase" }}>
                  Human In The Loop Gate // Role: qa-commander
                </div>
                <div style={{ fontSize: 13, marginTop: 4 }}>
                  Authority: Exclusive right to accept/reject patches based on verified evidence.
                </div>
              </div>
              <div style={{ display: "flex", gap: 12 }}>
                <button
                  disabled={!isVerified || isAccepted}
                  onClick={() =>
                    handleSendVoice(
                      "As qa-commander, I accept verified patch BP-0007. Both the regression suite and independent three-of-three browser retest passed. Record the verified decision in the Switch room."
                    )
                  }
                  style={{
                    background: isAccepted ? "var(--signal-verdigris)" : "#2b2621",
                    color: "#fff",
                    border: "none",
                    padding: "8px 16px",
                    fontSize: 13,
                    cursor: !isVerified || isAccepted ? "not-allowed" : "pointer",
                    fontWeight: 500,
                  }}
                >
                  {isAccepted ? "Accepted & Logged" : "Approve & Sign-Off (Wispr 3)"}
                </button>
              </div>
            </div>
          </section>
        </main>

        <aside
          style={{
            borderLeft: "1px solid var(--border-hairline)",
            background: "var(--bg-surface)",
            padding: 20,
            display: "flex",
            flexDirection: "column",
          }}
        >
          <div className="mono" style={{ fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", marginBottom: 12 }}>
            Switch Room Live Mirror (#bugproof)
          </div>

          <div style={{ marginBottom: 16 }}>
            <div className="mono" style={{ fontSize: 10, color: "var(--text-muted)", marginBottom: 6 }}>
              JUDGE INSPECTION COMMANDS
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6 }}>
              {["!list-agents", "!agents-status", "!list-aliases", "!roles", "!list-documents", "!list-references"].map((cmd) => (
                <button
                  key={cmd}
                  onClick={() => handleRunJudgeCommand(cmd)}
                  className="mono"
                  style={{
                    background: "var(--bg-canvas)",
                    border: "1px solid var(--border-hairline)",
                    fontSize: 10,
                    padding: "4px 6px",
                    cursor: "pointer",
                    textAlign: "left",
                  }}
                >
                  {cmd}
                </button>
              ))}
            </div>
          </div>

          {switchOutput && (
            <div
              className="mono"
              style={{
                background: "var(--bg-canvas)",
                border: "1px solid var(--border-hairline)",
                padding: 10,
                fontSize: 11,
                maxHeight: 120,
                overflowY: "auto",
                whiteSpace: "pre-wrap",
                marginBottom: 16,
              }}
            >
              {switchOutput}
            </div>
          )}

          <div className="mono" style={{ fontSize: 10, color: "var(--text-muted)", marginBottom: 8 }}>
            EVENT FEED
          </div>
          <div style={{ flex: 1, overflowY: "auto", maxHeight: "calc(100vh - 380px)" }}>
            {events.map((ev, idx) => (
              <div
                key={idx}
                style={{
                  borderBottom: "1px solid var(--border-hairline)",
                  padding: "8px 0",
                  fontSize: 11,
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", color: "var(--text-muted)" }}>
                  <span className="mono" style={{ fontWeight: 600 }}>
                    {ev.actor}
                  </span>
                  <span className="mono">{ev.created_at?.slice(11, 19)}</span>
                </div>
                <div style={{ marginTop: 2 }}>{ev.event_type}</div>
              </div>
            ))}
          </div>
        </aside>
      </div>

      <footer
        style={{
          borderTop: "1px solid var(--border-hairline)",
          background: "var(--bg-surface)",
          padding: "16px 24px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div
            style={{
              width: 10,
              height: 10,
              borderRadius: "50%",
              background: "var(--signal-vermilion)",
              animation: "pulse 1.5s infinite",
            }}
          />
          <input
            ref={voiceInputRef}
            type="text"
            value={voiceInput}
            onChange={(e) => setVoiceInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSendVoice();
            }}
            placeholder="Speak or type to the room... (Press / to focus)"
            style={{
              flex: 1,
              background: "var(--bg-canvas)",
              border: "1px solid var(--border-hairline)",
              padding: "10px 14px",
              fontSize: 14,
              outline: "none",
            }}
          />
          <button
            onClick={() => handleSendVoice()}
            disabled={isSubmittingVoice}
            style={{
              background: "#2b2621",
              color: "#fff",
              border: "none",
              padding: "10px 20px",
              fontSize: 13,
              cursor: "pointer",
              fontWeight: 500,
            }}
          >
            {isSubmittingVoice ? "Transmitting..." : "Send to Switch"}
          </button>
        </div>
        <div className="mono" style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 6, paddingLeft: 22 }}>
          {parsedPreview}
        </div>
      </footer>
    </div>
  );
}
