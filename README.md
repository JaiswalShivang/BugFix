# BugProof v2.0 — Evidence-Based AI Debugging & Independent Verification Platform

> "When an AI coding agent says 'I fixed your bug,' how do you know it's telling the truth? With BugProof, you report a bug by voice inside a Switch Room using Wispr Flow. First, a black-box Playwright agent with zero access to our source code opens the live web app, reproduces the crash 3 out of 3 times, and posts visual and network evidence into Switch. Second, a white-box coding agent reads that evidence from the room and patches the real code inside an isolated Git worktree. Finally, the browser agent independently retests the hot-reloaded app 3 out of 3 times before I approve the diff via Switch's `!roles` gate. It's Proof Before Fix — powered by Switch and driven by voice."

---

## 1. System Architecture

```
HUMAN DEVELOPER (role: qa-commander)
  speaks via Wispr Flow at 3 checkpoints (Report, Patch, Sign-off)
        │ voice-to-text
        ▼
SWITCH ROOM (#bugproof) — LOAD-BEARING CORE
  - Room Instructions (Proof-Before-Fix & Stop Conditions)
  - Roles (!roles): qa-commander, bug-reproducer, code-fixer
  - Shared Documents (!list-documents): reproduction-report.json, patch-summary.md, verification-policy.md
  - Shared References (!list-references): demo-app URL, worktree path, rubric
        │ 1. Reproduce & 4. Retest      │ 2. Evidence Handoff       │ 3. State/Diff Telemetry
        ▼                               ▼                           ▼
AGENT 1 @bug-reproducer (@repro)   AGENT 2 @code-fixer (@fixer)    BUGPROOF DASHBOARD & ARTIFACT API
- Isolated Playwright container    - Isolated OpenCode container   (Next.js + FastAPI)
- Access: http://demo-app:3000     - Access: Git worktree BP-0007  - Visualises PNGs, traces, Git diff
- NO source repo mount             - NO browser verdict control    - Deterministic VERIFIED badge
        │ browser HTTP/UI               │ edits files
        ▼                               ▼
TARGET DEMO APP  ◄──────────────  ISOLATED GIT WORKTREE (worktrees/BP-0007)
(http://demo-app:3000)             hot-reloads into demo server; main untouched
```

---

## 2. The 5 Mandatory Judge Verification Commands

Run these live commands to verify clean-room environment configuration:

```bash
# 1. List registered agents in #bugproof
python -m services.switch.cli "!list-agents"

# 2. Inspect active runtime status from live worker processes
python -m services.switch.cli "!agents-status"

# 3. Verify voice and text aliases
python -m services.switch.cli "!list-aliases"

# 4. Enforce human-in-the-loop authority roles
python -m services.switch.cli "!roles"

# 5. Inspect shared room documents and references
python -m services.switch.cli "!list-documents"
python -m services.switch.cli "!list-references"
```

---

## 3. The 3 Wispr Flow Voice Checkpoints

### Checkpoint 1 (0:15) — Intake & Baseline Reproduction
> "@repro start investigation BP-0007 on demo-app checkout. When I apply coupon code EXPIRED10, the checkout page crashes instead of showing Coupon expired. Reproduce it three times and capture screenshots, console errors, and failed network requests."

### Checkpoint 2 (0:50) — Worktree Patch Directive
> "@fixer baseline failure is confirmed with a null TypeError on coupon lookup. Create isolated Git worktree BP-0007, add a null and expiry guard returning HTTP 400 Coupon expired, write a regression test, and do not touch the main branch."

### Checkpoint 3 (1:45) — Human Gate Sign-Off
> "As qa-commander, I accept verified patch BP-0007. Both the regression suite and independent three-of-three browser retest passed. Record the verified decision in the Switch room."

---

## 4. Quick Start & Execution

### Prerequisites
- Node.js 20+ & pnpm
- Python 3.12+
- Docker & Docker Compose (optional for containerized run)

### Running Locally

```bash
# 1. Install dependencies
pnpm install
pip install -r requirements.txt
python -m playwright install chromium

# 2. Start the Demo Store (Port 3001)
pnpm --filter demo-ecommerce dev

# 3. Start the FastAPI Artifact & State Sync API (Port 8000)
uvicorn services.api.main:app --port 8000

# 4. Start the Forensic Case File Dashboard (Port 3000)
pnpm --filter dashboard dev
```

### Running Tests

```bash
# Run unit and state-machine tests
python -m pytest tests/api -v

# Run demo-app regression test suite
pnpm --filter demo-ecommerce test
```

### Rapid Demo Reset (Under 15 Seconds)

```bash
make demo-reset
```

---

## 5. Security & Isolation Matrix

| Component | Capabilities & Mounts | Explicitly Forbidden |
|---|---|---|
| `bug-reproducer` | Headless Chromium + Playwright; network route to `http://demo-app:3000`; writes to `/artifacts/` | NO mount to source code; cannot read or edit `.ts` files; cannot run Git |
| `code-fixer` | Subprocess runner constrained to allowlisted commands (`npm test`, `tsc --noEmit`, `git diff`); mounted to `/worktrees/{id}` | NO Playwright or browser binary; cannot modify `main`; cannot declare `VERIFIED` |
| `demo-app` | Serves active worktree on internal port 3000 (host port 3001) | No access to Switch credentials or unrelated host directories |
| `dashboard` & `api` | Read-mostly telemetry mirror; SQLite append-only event log; SSE stream | Cannot execute arbitrary shell strings; cannot bypass Switch |
