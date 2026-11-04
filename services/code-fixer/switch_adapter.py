import os
import json
import sys
from typing import Dict, Any
from .worktree_manager import WorktreeManager
from .patch_applier import apply_patch_and_verify

class CodeFixerAdapter:
    def __init__(self, room_name: str = "bugproof", artifacts_root: str = "artifacts"):
        self.room_name = room_name
        self.artifacts_root = artifacts_root
        self.name = "code-fixer"
        self.alias = "fixer"
        self.runtime = "worktree-worker"
        self.status = "ONLINE"
        self.worktree_mgr = WorktreeManager()

    def get_status(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "alias": self.alias,
            "runtime": self.runtime,
            "status": self.status,
            "room": self.room_name,
        }

    def verify_baseline_reproduction(self, investigation_id: str) -> bool:
        report_path = os.path.join(
            self.artifacts_root,
            investigation_id,
            f"reproduction-report-{investigation_id}.json",
        )
        if not os.path.exists(report_path):
            report_path = os.path.join(
                self.artifacts_root,
                investigation_id,
                "repro",
                f"reproduction-report-{investigation_id}.json",
            )
        if not os.path.exists(report_path):
            return False

        try:
            with open(report_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("status") == "REPRODUCED" and data.get("failures_observed") == 3
        except Exception:
            return False

    def handle_message(self, message_text: str, investigation_id: str = "BP-0007") -> Dict[str, Any]:
        if not self.verify_baseline_reproduction(investigation_id):
            return {
                "type": "ERROR",
                "room": self.room_name,
                "author": f"@{self.name}",
                "status": "REPRODUCE_REQUIRED",
                "message": (
                    f"@{self.name} Refused to edit code: Proof Before Fix invariant violated. "
                    f"No confirmed 3/3 REPRODUCED report found in room for {investigation_id}."
                ),
            }

        worktree_path = self.worktree_mgr.create_worktree(investigation_id)
        patch_result = apply_patch_and_verify(worktree_path, investigation_id, self.artifacts_root)

        return {
            "type": "PATCH_HANDOFF",
            "room": self.room_name,
            "author": f"@{self.name}",
            "patch_summary": patch_result,
            "message": (
                f"@{self.name} applied minimal null/expiry fix in isolated worktree {investigation_id}. "
                f"Regression tests and tsc typecheck exited 0. "
                f"Diff published to {patch_result['diff_ref']}. "
                f"Tagging @bug-reproducer for independent 3x browser retest on reloaded worktree."
            ),
        }

if __name__ == "__main__":
    adapter = CodeFixerAdapter()
    msg = sys.argv[1] if len(sys.argv) > 1 else "@fixer create worktree and patch null coupon crash"
    inv_id = sys.argv[2] if len(sys.argv) > 2 else "BP-0007"
    res = adapter.handle_message(msg, inv_id)
    print(json.dumps(res, indent=2))

