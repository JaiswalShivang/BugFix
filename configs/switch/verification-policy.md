# BugProof Verification Policy & Protocol (Proof Before Fix)

## 1. Deterministic Pass Criteria
A bug fix is declared VERIFIED only when all of the following deterministic checks pass:
1. Baseline Failure: `@bug-reproducer` reproduces the reported failure 3 consecutive times (3/3) before any code is modified.
2. Regression Suite: `@code-fixer` adds regression test assertions for the failing scenario and runs tests inside the isolated worktree.
3. Build and Type Safety: Allowlisted test runner and `tsc --noEmit` return exit code 0.
4. Independent Browser Retest: `@bug-reproducer` independently executes the identical 3-attempt browser test against the reloaded worktree with 3/3 successes.
5. Zero Regression Invariant: Auxiliary checks (`SAVE20` 20% discount and empty promo submission) pass without error.
6. Human Gate: `qa-commander` reviews before/after evidence and Git diff, dictating authorization via Wispr Flow.

## 2. Console Error Filtering Rule
HTTP 400 Bad Request responses are the expected contract for invalid or expired coupons. Chromium automatically logs a resource status notice for 400 responses: `Failed to load resource: the server responded with a status of 400`.
- This notice is considered normal validation behavior and is filtered out of the failure counter.
- Uncaught exceptions, `TypeError`, and 5xx responses (`Internal Server Error`) are strictly treated as fatal failures.

## 3. Security & SSRF Target Allowlist
The Playwright reproducer is restricted to authorized local sandbox targets:
- `http://demo-app:3000` (internal Docker DNS)
- `http://localhost:3001` (host development port)
- `http://127.0.0.1:3001`

Requests to cloud instance metadata (`169.254.169.254`), non-allowlisted private IP subnets, or arbitrary external domains are rejected immediately with `ENVIRONMENT_UNAVAILABLE`.

## 4. Minimal Patch Constraint
Coding agents operating in `worktrees/{investigation_id}` are strictly constrained:
- Edits must be minimal and localized strictly to the fault handler (`app/api/checkout/coupon/route.ts`).
- Agents must not modify unrelated checkout code, pricing calculators, or UI components.
- The `SAVE20` coupon path and cart calculation must remain completely intact.

## 5. State Machine & Stop Conditions
- Illegal transitions (e.g. `PATCHING` without prior `REPRODUCED`, or `HUMAN_ACCEPTED` without `VERIFIED`) are rejected by the state engine.
- If fewer than 3/3 baseline failures occur, or if tests fail, execution stops immediately and reports `INCONCLUSIVE` or `PATCH_FAILED`.
