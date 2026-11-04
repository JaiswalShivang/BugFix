import pytest
import importlib
import subprocess

wm_mod = importlib.import_module("services.code-fixer.worktree_manager")
WorktreeManager = wm_mod.WorktreeManager

def test_path_traversal_prevention():
    mgr = WorktreeManager()
    with pytest.raises(ValueError):
        mgr.validate_investigation_id("../../../etc/passwd")

def test_main_branch_clean():
    res = subprocess.run(["git", "diff", "--name-only"], capture_output=True, text=True)
    modified_files = [line.strip() for line in res.stdout.splitlines() if line.strip()]
    assert "apps/demo-ecommerce/app/api/checkout/coupon/route.ts" not in modified_files
