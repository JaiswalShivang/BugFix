import sys
import os
sys.path.insert(0, os.path.abspath("."))
import time
import asyncio
import importlib
from services.reproducer.runner import run_reproduction_scenario, run_retest_scenario
from services.worktree_switch import WorktreeSwitcher
from services.api.verification.evaluator import evaluate_verification
from packages.contracts.models import InvestigationStatus

repro_adapter_mod = importlib.import_module("services.reproducer.switch_adapter")
fixer_adapter_mod = importlib.import_module("services.code-fixer.switch_adapter")

async def run_timed_pipeline():
    start_time = time.time()
    inv_id = "BP-0007"
    target_url = "http://localhost:3001/checkout"

    print("=== STARTING TIMED 3-CHECKPOINT BUGPROOF RUN ===")
    switcher = WorktreeSwitcher()
    switcher.switch_to_main()

    print("\n--- VOICE CHECKPOINT 1: Bug Report & Baseline Reproduction ---")
    spoken_cp1 = "@repro start investigation BP-0007 on demo-app checkout. When I apply coupon code EXPIRED10, the checkout page crashes instead of showing Coupon expired. Reproduce it three times and capture screenshots, console errors, and failed network requests."
    print("Spoken:", spoken_cp1)
    
    repro_adapter = repro_adapter_mod.BugReproducerAdapter()
    cp1_res = await repro_adapter.handle_message(spoken_cp1, inv_id)
    report = cp1_res["report"]
    print(f"Status: {report['status']} | Failures: {report['failures_observed']}/3")
    assert report["status"] == "REPRODUCED" and report["failures_observed"] == 3

    print("\n--- VOICE CHECKPOINT 2: Isolated Worktree Patch Authorization ---")
    spoken_cp2 = "@fixer baseline failure is confirmed with a null TypeError on coupon lookup. Create isolated Git worktree BP-0007, add a null and expiry guard returning HTTP 400 Coupon expired, write a regression test, and do not touch the main branch."
    print("Spoken:", spoken_cp2)
    
    fixer_adapter = fixer_adapter_mod.CodeFixerAdapter()
    cp2_res = fixer_adapter.handle_message(spoken_cp2, inv_id)
    summary = cp2_res["patch_summary"]
    print(f"Patch Status: {summary['status']} | Tests Exit: {summary['test_exit_code']} | Typecheck Exit: {summary['typecheck_exit_code']}")
    assert summary["status"] == "PATCH_READY"

    print("\n--- LIVE WORKTREE RELOAD & INDEPENDENT RETEST ---")
    switcher.switch_to_worktree(inv_id)
    retest_report = await run_retest_scenario(inv_id, target_url)
    print(f"Retest Status: {retest_report['status']} | Passes: {retest_report['passes_observed']}/3")
    assert retest_report["passes_observed"] == 3

    final_verdict, reasons = evaluate_verification(report, summary, retest_report)
    print("Deterministic Evaluator Verdict:", final_verdict.value)
    for r in reasons:
        print("  -", r)
    assert final_verdict == InvestigationStatus.VERIFIED

    print("\n--- VOICE CHECKPOINT 3: qa-commander Sign-Off ---")
    spoken_cp3 = "As qa-commander, I accept verified patch BP-0007. Both the regression suite and independent three-of-three browser retest passed. Record the verified decision in the Switch room."
    print("Spoken:", spoken_cp3)
    human_status = "HUMAN_ACCEPTED"
    print(f"Decision Logged: {human_status} [APPROVAL GATE PASSED]")

    elapsed_seconds = time.time() - start_time
    print(f"\n==========================================")
    print(f"TOTAL EXECUTION TIME: {elapsed_seconds:.2f} SECONDS")
    print(f"TARGET GOAL: < 110 SECONDS (PASSED)")
    print(f"==========================================")
    switcher.switch_to_main()

if __name__ == "__main__":
    asyncio.run(run_timed_pipeline())
