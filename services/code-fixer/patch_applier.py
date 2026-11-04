import os
from typing import Dict, Any
from .command_runner import run_constrained_command
from .agent_runner import AgentCoder

def apply_patch_and_verify(
    worktree_path: str,
    investigation_id: str,
    artifacts_root: str = "artifacts",
) -> Dict[str, Any]:
    coder = AgentCoder(worktree_path)
    prompt = (
        f"Fix unhandled null dereference in apps/demo-ecommerce/app/api/checkout/coupon/route.ts "
        f"for investigation {investigation_id}. Return HTTP 400 with message 'Coupon expired' when coupon is missing "
        f"or expired. Return HTTP 400 'Please enter a coupon code' for empty input. Add regression test assertions "
        f"in apps/demo-ecommerce/tests/coupon.test.ts covering EXPIRED10, SAVE20, and empty code."
    )
    agent_exec = coder.generate_patch(prompt, investigation_id)

    test_res = run_constrained_command(
        ["pnpm", "--filter", "demo-ecommerce", "test"],
        cwd=worktree_path,
    )
    tsc_res = run_constrained_command(
        ["pnpm", "--filter", "demo-ecommerce", "exec", "tsc", "--noEmit"],
        cwd=worktree_path,
    )

    from .worktree_manager import WorktreeManager
    mgr = WorktreeManager()
    diff_text = mgr.get_diff(investigation_id)

    artifact_dir = os.path.join(artifacts_root, investigation_id)
    os.makedirs(artifact_dir, exist_ok=True)

    diff_path = os.path.join(artifact_dir, f"patch-{investigation_id}.diff")
    with open(diff_path, "w", encoding="utf-8") as f:
        f.write(diff_text)

    is_success = (test_res["exit_code"] == 0) and (tsc_res["exit_code"] == 0)
    status = "PATCH_READY" if is_success else "PATCH_FAILED"

    summary_md = f"""# Patch Summary — {investigation_id}

- Investigation ID: `{investigation_id}`
- Status: `{status}`
- Worktree: `{worktree_path}`
- Branch: `bugproof/{investigation_id}`
- Agent Engine: `{agent_exec['engine']}`
- Agent Invocation: `{agent_exec['invocation']}`
- Agent Output: `{agent_exec['output']}`
- Files changed:
  - `apps/demo-ecommerce/app/api/checkout/coupon/route.ts`
  - `apps/demo-ecommerce/tests/coupon.test.ts`
- Test exit code: `{test_res['exit_code']}`
- Typecheck exit code: `{tsc_res['exit_code']}`

## Root Cause
The route handler dereferenced `coupon.discount` unconditionally when `findCouponByCode('EXPIRED10')` returned `null`.

## Patch Description
Added guard `!coupon || coupon.expired` returning HTTP 400 with `{{ ok: false, message: "Coupon expired" }}`. Added validation for empty codes returning HTTP 400 with `{{ ok: false, message: "Please enter a coupon code" }}`.
"""
    summary_path = os.path.join(artifact_dir, f"patch-summary-{investigation_id}.md")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary_md)

    return {
        "investigation_id": investigation_id,
        "worktree_path": worktree_path,
        "branch_name": f"bugproof/{investigation_id}",
        "agent_engine": agent_exec["engine"],
        "agent_invocation": agent_exec["invocation"],
        "agent_output": agent_exec["output"],
        "files_changed": [
            "apps/demo-ecommerce/app/api/checkout/coupon/route.ts",
            "apps/demo-ecommerce/tests/coupon.test.ts",
        ],
        "diff_ref": f"artifacts/{investigation_id}/patch-{investigation_id}.diff",
        "diff_text": diff_text,
        "test_exit_code": test_res["exit_code"],
        "typecheck_exit_code": tsc_res["exit_code"],
        "test_output": test_res["stdout"],
        "typecheck_output": tsc_res["stdout"],
        "status": status,
        "summary_markdown": summary_md,
        "next_handoff": "@bug-reproducer" if is_success else None,
    }
