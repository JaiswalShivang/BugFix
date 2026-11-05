import pytest
import asyncio
import importlib
from services.reproducer.runner import run_reproduction_scenario, run_retest_scenario
from services.worktree_switch import WorktreeSwitcher
from services.api.verification.evaluator import evaluate_verification
from packages.contracts.models import InvestigationStatus

repro_adapter_mod = importlib.import_module("services.reproducer.switch_adapter")
fixer_adapter_mod = importlib.import_module("services.code-fixer.switch_adapter")

@pytest.mark.asyncio
async def test_full_investigation_pipeline():
    inv_id = "BP-0007"
    target_url = "http://localhost:3001/checkout"
    
    switcher = WorktreeSwitcher()
    switcher.switch_to_main()

    repro_res = await run_reproduction_scenario(inv_id, target_url, "EXPIRED10")
    assert repro_res["status"] == "REPRODUCED"
    assert repro_res["failures_observed"] == 3

    fixer_adapter = fixer_adapter_mod.CodeFixerAdapter()
    patch_res = fixer_adapter.handle_message("@fixer patch null coupon crash", inv_id)
    assert patch_res["type"] == "PATCH_HANDOFF"
    assert patch_res["patch_summary"]["status"] == "PATCH_READY"
    assert patch_res["patch_summary"]["test_exit_code"] == 0

    switcher.switch_to_worktree(inv_id)

    retest_res = await run_retest_scenario(inv_id, target_url)
    assert retest_res["status"] == "COMPLETED"
    assert retest_res["passes_observed"] == 3

    final_status, reasons = evaluate_verification(
        repro_res,
        patch_res["patch_summary"],
        retest_res,
    )
    assert final_status == InvestigationStatus.VERIFIED
    assert len(reasons) == 5

    switcher.switch_to_main()

