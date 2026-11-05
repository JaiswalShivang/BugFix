import os
import shutil
import subprocess
from typing import Dict, Any, Optional

class WorktreeManager:
    def __init__(self, repo_root: str = "."):
        self.repo_root = os.path.abspath(repo_root)
        self.worktrees_root = os.path.abspath(os.path.join(self.repo_root, "worktrees"))
        os.makedirs(self.worktrees_root, exist_ok=True)

    def validate_investigation_id(self, investigation_id: str) -> str:
        if not investigation_id or ".." in investigation_id or "/" in investigation_id or "\\" in investigation_id:
            raise ValueError(f"Invalid investigation id: {investigation_id}")
        return investigation_id.strip()

    def get_worktree_path(self, investigation_id: str) -> str:
        inv_id = self.validate_investigation_id(investigation_id)
        path = os.path.abspath(os.path.join(self.worktrees_root, inv_id))
        if not path.startswith(self.worktrees_root):
            raise ValueError(f"Path traversal detected: {path}")
        return path

    def create_worktree(self, investigation_id: str) -> str:
        inv_id = self.validate_investigation_id(investigation_id)
        worktree_path = self.get_worktree_path(inv_id)
        branch_name = f"bugproof/{inv_id}"

        if os.path.exists(worktree_path):
            self.remove_worktree(inv_id)

        shutil.rmtree(worktree_path, ignore_errors=True)
        subprocess.run(
            ["git", "worktree", "prune"],
            cwd=self.repo_root,
            capture_output=True,
            shell=False,
        )
        subprocess.run(
            ["git", "branch", "-D", branch_name],
            cwd=self.repo_root,
            capture_output=True,
            shell=False,
        )

        res = subprocess.run(
            ["git", "worktree", "add", "-b", branch_name, worktree_path, "main"],
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            shell=False,
        )
        if res.returncode != 0:
            raise RuntimeError(f"Failed to create worktree: {res.stderr}")

        root_app_modules = os.path.join(self.repo_root, "apps", "demo-ecommerce", "node_modules")
        wt_app_modules = os.path.join(worktree_path, "apps", "demo-ecommerce", "node_modules")
        if os.path.exists(root_app_modules) and not os.path.exists(wt_app_modules):
            if os.name == "nt":
                subprocess.run(["cmd", "/c", "mklink", "/J", wt_app_modules, root_app_modules], capture_output=True, shell=False)
            else:
                os.symlink(root_app_modules, wt_app_modules)

        root_root_modules = os.path.join(self.repo_root, "node_modules")
        wt_root_modules = os.path.join(worktree_path, "node_modules")
        if os.path.exists(root_root_modules) and not os.path.exists(wt_root_modules):
            if os.name == "nt":
                subprocess.run(["cmd", "/c", "mklink", "/J", wt_root_modules, root_root_modules], capture_output=True, shell=False)
            else:
                os.symlink(root_root_modules, wt_root_modules)

        npmrc_src = os.path.join(self.repo_root, ".npmrc")
        npmrc_dst = os.path.join(worktree_path, ".npmrc")
        if os.path.exists(npmrc_src) and not os.path.exists(npmrc_dst):
            shutil.copy2(npmrc_src, npmrc_dst)

        return worktree_path

    def get_diff(self, investigation_id: str) -> str:
        worktree_path = self.get_worktree_path(investigation_id)
        if not os.path.exists(worktree_path):
            return ""
        res = subprocess.run(
            ["git", "diff"],
            cwd=worktree_path,
            capture_output=True,
            text=True,
            shell=False,
        )
        return res.stdout

    def remove_worktree(self, investigation_id: str) -> None:
        inv_id = self.validate_investigation_id(investigation_id)
        worktree_path = self.get_worktree_path(inv_id)
        subprocess.run(
            ["git", "worktree", "remove", "--force", worktree_path],
            cwd=self.repo_root,
            capture_output=True,
            shell=False,
        )
        subprocess.run(
            ["git", "worktree", "prune"],
            cwd=self.repo_root,
            capture_output=True,
            shell=False,
        )
        shutil.rmtree(worktree_path, ignore_errors=True)
        subprocess.run(
            ["git", "branch", "-D", f"bugproof/{inv_id}"],
            cwd=self.repo_root,
            capture_output=True,
            shell=False,
        )

