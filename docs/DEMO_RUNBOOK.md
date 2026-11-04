# BugProof Demonstration Runbook

## Clean-Room Split Screen Setup (0:00–0:15)
- **Left Panel:** Switch Room `#bugproof` terminal window or interactive prompt.
- **Top Right Panel:** Target store `demo-ecommerce` at `http://localhost:3001/checkout`.
- **Bottom Right Panel:** BugProof Forensic Dashboard at `http://localhost:3000`.

### Step 1: Judge Verification Check
Execute the 5 clean-room verification commands:
```bash
python -m services.switch.cli "!list-agents"
python -m services.switch.cli "!agents-status"
python -m services.switch.cli "!list-aliases"
python -m services.switch.cli "!roles"
python -m services.switch.cli "!list-documents"
python -m services.switch.cli "!list-references"
```
*Verification Proved:* Both isolated containers are online, roles and permissions are active, and policy documents are loaded.

---

## Checkpoint 1: Wispr Voice Bug Report (0:15–0:35)
Hold the Wispr Flow hotkey (or focus the voice field with `/`) and speak:
> "@repro start investigation BP-0007 on demo-app checkout. When I apply coupon code EXPIRED10, the checkout page crashes instead of showing Coupon expired. Reproduce it three times and capture screenshots, console errors, and failed network requests."

*Observable Outcome:*
- `@bug-reproducer` executes 3 Playwright attempts.
- Observes HTTP 500 TypeError crash 3/3 times.
- Registers before-apply.png, after-crash.png, and trace.zip.
- Status in `#bugproof` and dashboard updates to `REPRODUCED`.

---

## Checkpoint 2: Worktree Patch Authorization (0:50–1:20)
Hold the Wispr Flow hotkey and speak:
> "@fixer baseline failure is confirmed with a null TypeError on coupon lookup. Create isolated Git worktree BP-0007, add a null and expiry guard returning HTTP 400 Coupon expired, write a regression test, and do not touch the main branch."

*Observable Outcome:*
- `@code-fixer` creates `worktrees/BP-0007` off `main`.
- Applies the null check guard.
- Runs allowlisted tests and tsc typecheck (exit code 0).
- Generates Git diff `artifacts/BP-0007/patch-BP-0007.diff`.
- Demo app reloads from the patched worktree.
- `@bug-reproducer` runs 3 independent retests + auxiliary checks (`SAVE20`).
- Dashboard exhibits update to `VERIFIED`.

---

## Checkpoint 3: qa-commander Human Sign-Off (1:45–2:00)
Hold the Wispr Flow hotkey and speak:
> "As qa-commander, I accept verified patch BP-0007. Both the regression suite and independent three-of-three browser retest passed. Record the verified decision in the Switch room."

*Observable Outcome:*
- Human gate signs off.
- Dashboard stamp marks `APPROVED FOR MERGE`.
- State transitions to `HUMAN_ACCEPTED`.

---

## Rapid Reset Command
To restore the repository and demo store to pristine unpatched state in under 15 seconds:
```bash
make demo-reset
```

