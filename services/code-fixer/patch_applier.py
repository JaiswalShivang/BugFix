import os
from typing import Dict, Any
from .command_runner import run_constrained_command

PATCHED_ROUTE_CONTENT = """import { findCouponByCode } from "@/lib/coupons";

export async function POST(req: Request) {
  const { code } = await req.json();
  if (!code || typeof code !== "string" || !code.trim()) {
    return Response.json({ ok: false, message: "Please enter a coupon code" }, { status: 400 });
  }
  const coupon = await findCouponByCode(code.trim().toUpperCase());
  if (!coupon || coupon.expired) {
    return Response.json({ ok: false, message: "Coupon expired" }, { status: 400 });
  }
  return Response.json({ ok: true, discount: coupon.discount, message: "Coupon applied" }, { status: 200 });
}
"""

PATCHED_TEST_CONTENT = """import test from "node:test";
import assert from "node:assert/strict";
import { findCouponByCode } from "../lib/coupons";

test("findCouponByCode returns coupon for valid SAVE20", async () => {
  const coupon = await findCouponByCode("SAVE20");
  assert.ok(coupon);
  assert.equal(coupon.discount, 20);
  assert.equal(coupon.expired, false);
});

test("findCouponByCode returns null for EXPIRED10", async () => {
  const coupon = await findCouponByCode("EXPIRED10");
  assert.equal(coupon, null);
});

test("findCouponByCode returns null for empty or invalid code", async () => {
  assert.equal(await findCouponByCode(""), null);
  assert.equal(await findCouponByCode("NONEXISTENT"), null);
});
"""

def apply_patch_and_verify(
    worktree_path: str,
    investigation_id: str,
    artifacts_root: str = "artifacts",
) -> Dict[str, Any]:
    route_file = os.path.join(
        worktree_path,
        "apps",
        "demo-ecommerce",
        "app",
        "api",
        "checkout",
        "coupon",
        "route.ts",
    )
    test_file = os.path.join(
        worktree_path,
        "apps",
        "demo-ecommerce",
        "tests",
        "coupon.test.ts",
    )

    if not os.path.exists(os.path.dirname(route_file)):
        os.makedirs(os.path.dirname(route_file), exist_ok=True)
    if not os.path.exists(os.path.dirname(test_file)):
        os.makedirs(os.path.dirname(test_file), exist_ok=True)

    with open(route_file, "w", encoding="utf-8") as f:
        f.write(PATCHED_ROUTE_CONTENT)

    with open(test_file, "w", encoding="utf-8") as f:
        f.write(PATCHED_TEST_CONTENT)

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
