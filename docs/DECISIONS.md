# Architecture and Implementation Decisions

## Decision 1: Evidence-First Invariant
No source code modification is permitted before an independent browser agent reproduces the reported failure 3/3 times. No fix is declared verified until the browser agent re-runs the exact scenario 3/3 times post-patch.

## Decision 2: Switch Room as Load-Bearing Bus
The Switch room is the primary communication and coordination layer. The dashboard and API mirror Switch messages, artifacts, and diffs via SSE and webhooks.

## Decision 3: Deterministic Verification
Evaluation is computed by a pure state evaluator based strictly on Playwright exit status, HTTP error logs, console logs, and unit test exit codes. Language model prose is never used as a verdict.

## Decision 4: Worktree Isolation
Code fixing is isolated in dedicated Git worktrees under `worktrees/` to leave `main` untouched until approved by `qa-commander`.

## Decision 5: Console Error Filtering
HTTP 400 responses from invalid coupon validations log standard resource response notices in Chromium. The reproducer filters expected 400 resource status logs while treating unhandled exceptions, TypeErrors, and 5xx errors as failures.
