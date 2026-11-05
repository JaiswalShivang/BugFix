import os
import shutil
import subprocess
import time
import urllib.request

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

    def _sync_docker_container(self, src_file: str):
        try:
            subprocess.run(
                ["docker", "cp", src_file, "bugproof-demo-app:/app/apps/demo-ecommerce/app/api/checkout/coupon/route.ts"],
                capture_output=True,
                check=False,
            )
            subprocess.run(
                ["docker", "restart", "bugproof-demo-app"],
                capture_output=True,
                check=False,
            )
            for _ in range(30):
                try:
                    with urllib.request.urlopen("http://127.0.0.1:3001/checkout", timeout=2) as resp:
                        if resp.status == 200:
                            break
                except Exception:
                    time.sleep(0.5)
        except Exception:
            pass

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
        self._sync_docker_container(worktree_route)
        return True

    def switch_to_main(self) -> bool:
        if os.path.exists(self.main_backup_path):
            shutil.copyfile(self.main_backup_path, self.main_route_path)
            self._sync_docker_container(self.main_backup_path)
            return True
        return False
