# BugProof v2.0 — Evidence-Based AI Debugging & Independent Verification Platform

> **Track:** WeMakeDevs "Flip the Switch" Hackathon & "Code with Wispr" Track  
> **Repository:** [https://github.com/JaiswalShivang/BugFix.git](https://github.com/JaiswalShivang/BugFix.git)  
> **Core Thesis:** *Proof Before Fix.* When an AI coding assistant says "I fixed your bug," how do you know it is telling the truth? Single-agent assistants hallucinate plausible-looking patches that fail at runtime. BugProof enforces deterministic, multi-agent browser reproduction: no code is edited until a browser reproduces the bug 3/3 times, and no fix is declared verified until an independent browser agent reruns the scenario 3/3 times post-patch.

---

## 1. System Architecture: The Two-Agent Isolation Boundary

Every debugging task flows strictly through the Switch Room `#bugproof`. Two mutually isolated agent containers perform the investigation without shared mounts or shared authority:

```
                      HUMAN DEVELOPER (Role: qa-commander)
            Speaks via Wispr Flow (Checkpoint 1, 2, 3 or / Hotkey)
                                  │
                                  ▼
                     SWITCH ROOM (#bugproof)
          Room Instructions · Roles (!roles) · Documents · References
                                  │
               ┌──────────────────┴──────────────────┐
               │ 1. Reproduce & Retest               │ 2. Evidence Handoff
               ▼                                     ▼
   AGENT 1: @bug-reproducer             AGENT 2: @code-fixer
   (alias: @repro)                      (alias: @fixer)
   Runtime: Playwright Container        Runtime: Worktree Worker (Groq AI)
   Isolation: ZERO source repo access   Isolation: ZERO browser access
   Access: http://demo-app:3000         Access: /worktrees/{investigation_id}
               │                                     │
               │ HTTP / DOM Interaction              │ Git Worktree Edits
               ▼                                     ▼
   TARGET DEMO STORE ◄─────────────────── ISOLATED GIT WORKTREE
   (demo-ecommerce :3001)                (worktrees/BP-0007)
```

### Why Switch Is 100% Load-Bearing: Isolation Table

| Isolation Boundary | `@bug-reproducer` Container | `@code-fixer` Container |
|---|---|---|
| **Primary Mission** | Black-box browser reproduction & independent retest | White-box code analysis, Groq LLM patch, regression test |
| **Filesystem Mounts** | `/artifacts` (writes reports, screenshots, traces) | `/worktrees/{id}`, `/artifacts` (writes patch diffs) |
| **Source Code Access** | **ZERO.** No `/apps` or `/repo` mount; cannot view files | Mounted strictly to disposable worktree `/worktrees/{id}` |
| **Git Binary Access** | **ZERO.** `which git` exits with code 1 | Allowed: constrained allowlist (`git diff`, `git status`) |
| **Browser / Chromium** | Headless Chromium + Playwright runtime | **ZERO.** Chromium not installed; Playwright not installed |
| **Verdict Authority** | Gathers browser pass/fail exit data only | **ZERO.** Cannot declare its own code change `VERIFIED` |
| **Verification Gate** | Deterministic evaluator computes verdict from exit codes | Human `qa-commander` holds exclusive approval gate |

---

## 2. The 5 Mandatory Judge Verification Commands

Judges verify the clean-room environment configuration by executing the 5 Switch inspection commands:

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

### Expected Output Table

| Command | Expected Clean-Room Output |
|---|---|
| `!list-agents` | `@bug-reproducer (runtime: playwright-worker)`, `@code-fixer (runtime: worktree-worker)` |
| `!agents-status` | `@bug-reproducer (ONLINE - playwright-worker)`, `@code-fixer (ONLINE - worktree-worker)` |
| `!list-aliases` | `@repro -> @bug-reproducer`, `@fixer -> @code-fixer` |
| `!roles` | `qa-commander (assigned: human) [APPROVAL GATE]`, `reproducer (assigned: bug-reproducer)`, `fixer (assigned: code-fixer)` |
| `!list-documents` | `verification-policy.md`, `reproduction-report-BP-0007.json`, `patch-summary-BP-0007.md` |
| `!list-references` | `demo-app-url: http://demo-app:3000`, `worktree-root: /worktrees`, `rubric: configs/switch/verification-policy.md` |

---

## 3. The 3 Wispr Flow Voice Checkpoints

The operator controls the full debugging lifecycle hands-free via Wispr Flow voice dictation. Pressing `/` in the dashboard focuses the voice command bar:

1. **Checkpoint 1 — Bug Report & Baseline Reproduction (0:15–0:30):**
   > *"@repro start investigation BP-0007 on demo-app checkout. When I apply coupon code EXPIRED10, the checkout page crashes instead of showing Coupon expired. Reproduce it three times and capture screenshots, console errors, and failed network requests."*
   - Launches Chromium in `@bug-reproducer`; runs 3 attempts against `/checkout`; verifies 3/3 HTTP 500 TypeError crashes; pauses at `REPRODUCED`.

2. **Checkpoint 2 — Worktree Patch Directive & Retest (0:50–1:05):**
   > *"@fixer baseline failure is confirmed with a null TypeError on coupon lookup. Create isolated Git worktree BP-0007, add a null and expiry guard returning HTTP 400 Coupon expired, write a regression test, and do not touch the main branch."*
   - `@code-fixer` creates `worktrees/BP-0007`; Groq AI Agent (`openai/gpt-oss-120b`) patches `route.ts` and adds assertions to `coupon.test.ts`; `npm test` and `tsc` pass; demo-app hot-reloads; `@bug-reproducer` reruns 3/3 browser retest; evaluator computes `VERIFIED`.

3. **Checkpoint 3 — Human Gate Sign-Off (1:35–1:45):**
   > *"As qa-commander, I accept verified patch BP-0007. Both the regression suite and independent three-of-three browser retest passed. Record the verified decision in the Switch room."*
   - Enforces `qa-commander` gate; checks `VERIFIED` state; records `HUMAN_ACCEPTED` in Switch room.

See [`WISPR_VOICE_LOG.md`](WISPR_VOICE_LOG.md) for full verbatim prompts, and [`docs/wispr-scorecard.png`](docs/wispr-scorecard.png) for the scorecard artifact.

---

## 4. 10-Minute Clean-Room Setup & Verification Guide

### Step 1: Clone & Configure Environment

```bash
git clone https://github.com/JaiswalShivang/BugFix.git
cd BugFix

# Configure credentials
cp .env.example .env
```

Ensure `.env` contains:
```env
SWITCH_API_KEY=<your_switch_api_key>
SWITCH_ROOM_NAME=bugproof
SWITCH_ROOM_URL=https://api.switch.dev/v1
GROQ_API_KEY=<your_groq_api_key>
GROQ_MODEL=openai/gpt-oss-120b
```

### Step 2: Build & Start All 5 Docker Containers

```bash
docker compose up --build -d
docker compose ps
```

All 5 services (`api`, `bug-reproducer`, `code-fixer`, `dashboard`, `demo-app`) will show `healthy`.

### Step 3: Run Full Unit & Isolation Test Suite

```bash
make test
```
- 16/16 Python unit tests pass (command runner allowlist, SSRF allowlist, container isolation, state machine, evaluator).
- TypeScript regression tests pass 3/3.
- `tsc --noEmit` on demo-ecommerce and dashboard pass with 0 errors.

### Step 4: Run End-to-End Pipeline Test

```bash
make e2e
```
- Executes full Playwright reproduction, Groq LLM patch, hot-reload, and independent browser retest.

### Step 5: Run the Timed 3-Checkpoint Pipeline

```bash
python scripts/timed_3checkpoint_run.py
```
- Completes the entire 3-checkpoint journey in **~70 seconds** (target goal: < 110 seconds).

---

## 5. System Verification Matrix

| Check | Target / Invariant | Result |
|---|---|---|
| **Container Isolation** | `@bug-reproducer` has no source code; `@code-fixer` has no browser | **PASS** (automated test) |
| **Proof Before Fix** | Baseline failure observed 3 of 3 consecutive browser attempts | **PASS** (3/3 reproduced) |
| **Code Repair Engine** | Groq AI Agent (`openai/gpt-oss-120b`) generates guarded route + tests | **PASS** (exit code 0) |
| **Regression Suite** | Auxiliary coupons (`SAVE20`, empty code) verified without regressions | **PASS** (3/3 pass) |
| **Independent Retest** | Post-patch browser retest reproduces 0 errors across 3 attempts | **PASS** (3/3 pass) |
| **Deterministic Verdict** | State evaluator strictly computes `VERIFIED` from exit codes | **PASS** (`VERIFIED`) |
| **Human Gate** | Only `qa-commander` voice/role can record `HUMAN_ACCEPTED` | **PASS** (enforced) |
| **A11y & Performance** | Keyboard navigation `/` + `prefers-reduced-motion` compliance | **PASS** (verified) |
