import os
import shutil

class WorktreeSwitcher:
    def __init__(self, repo_root: str = "."):
        self.repo_root = os.path.abspath(repo_root)
        self.main_route_path = os.path.abspath(
            os.path.join(
                self.repo_root,
                "apps",
                "demo-ecommerce",
                "app",
                "api",
                "checkout",
                "coupon",
                "route.ts",
            )
        )
        self.main_backup_path = self.main_route_path + ".baseline"
        if not os.path.exists(self.main_backup_path) and os.path.exists(self.main_route_path):
            shutil.copyfile(self.main_route_path, self.main_backup_path)

    def switch_to_worktree(self, investigation_id: str) -> bool:
        worktree_route = os.path.abspath(
            os.path.join(
                self.repo_root,
                "worktrees",
                investigation_id,
                "apps",
                "demo-ecommerce",
                "app",
                "api",
                "checkout",
                "coupon",
                "route.ts",
            )
        )
        if not os.path.exists(worktree_route):
            raise FileNotFoundError(f"Patched route not found in worktree: {worktree_route}")

        shutil.copyfile(worktree_route, self.main_route_path)
        return True

    def switch_to_main(self) -> bool:
        if os.path.exists(self.main_backup_path):
            shutil.copyfile(self.main_backup_path, self.main_route_path)
            return True
        return False

