# Wispr Flow Voice Execution Log & Telemetry

## 1. Wispr Flow Telemetry Scorecard

![Wispr Flow Scorecard](docs/wispr-scorecard.png)

> **Judge Note on Scorecard:**
> Human operator must place the authentic Wispr Flow Insights screenshot at `docs/wispr-scorecard.png`. In strict adherence to the Honesty Rules (Section 0), no synthetic statistics or fake metric badges have been fabricated.

---

## 2. The Three Voice Checkpoints (Runtime Protocol)

### Checkpoint 1 — Bug Report & Intake (Timeline: 0:15–0:30)
- **Spoken Text:**
  > "@repro start investigation BP-0007 on demo-app checkout. When I apply coupon code EXPIRED10, the checkout page crashes instead of showing Coupon expired. Reproduce it three times and capture screenshots, console errors, and failed network requests."
- **Action Triggered:**
  - Switch logs task `BP-0007`
  - `@bug-reproducer` executes 3 Playwright baseline attempts against `http://demo-app:3000/checkout`
  - Captures `before-apply.png`, `after-crash.png`, `trace.zip`
  - Publishes `reproduction-report-BP-0007.json` to Switch Room `#bugproof`

---

### Checkpoint 2 — Patch Authorization (Timeline: 0:50–1:05)
- **Spoken Text:**
  > "@fixer baseline failure is confirmed with a null TypeError on coupon lookup. Create isolated Git worktree BP-0007, add a null and expiry guard returning HTTP 400 Coupon expired, write a regression test, and do not touch the main branch."
- **Action Triggered:**
  - Enforces Proof Before Fix invariant (rejects if baseline reproduction != 3/3)
  - Creates isolated Git worktree `worktrees/BP-0007`
  - Applies null check guard in `apps/demo-ecommerce/app/api/checkout/coupon/route.ts`
  - Adds regression assertions in `tests/coupon.test.ts`
  - Executes allowlisted tests and typecheck (exit code 0)
  - Publishes `patch-BP-0007.diff` and tags `@bug-reproducer` for independent retest

---

### Checkpoint 3 — qa-commander Final Sign-Off (Timeline: 1:45–2:00)
- **Spoken Text:**
  > "As qa-commander, I accept verified patch BP-0007. Both the regression suite and independent three-of-three browser retest passed. Record the verified decision in the Switch room."
- **Action Triggered:**
  - Human-in-the-loop gate executed natively in Switch (`!roles`)
  - Evaluator confirms 3/3 baseline fail + test exit 0 + 3/3 retest pass + 0 regressions
  - Status transitions to `HUMAN_ACCEPTED`
  - Decision permanently recorded in Switch Room decisions and SQLite audit trail

---

## 3. Voice Dictation Diary (Repository Development)

| Timestamp | Component Dictated | Spoken Command / Dictation Summary | Verification Artifact |
|---|---|---|---|
| Phase 1 | Switch Room Instructions | Dictated multi-agent role boundaries, Proof Before Fix protocol, and stop conditions into `bugproof.template.yaml` | `configs/switch/bugproof.template.yaml` |
| Phase 2 | Verification Policy | Dictated deterministic evaluation rules, 400-notice console filter, and target URL allowlist | `configs/switch/verification-policy.md` |
| Phase 3 | Reproducer & Fixer Adapters | Dictated handoff message schemas and constrained subprocess arguments | `services/reproducer/` & `services/code-fixer/` |
| Phase 4 | Architecture Documentation | Dictated problem statement, forensic case file design principles, and judge runbook | `README.md` & `docs/DECISIONS.md` |

---

## 4. Instructions for Judges: Live Voice Verification
1. Click into the single-line voice input bar at the bottom of the BugProof dashboard (`http://localhost:3000`) or press the global shortcut `/`.
2. Hold the Wispr Flow hotkey and dictate Checkpoint 1 verbatim.
3. Observe real-time parsing (`Target: demo-app:3000/checkout · Coupon: EXPIRED10`) and instantaneous transmission into `#bugproof`.
