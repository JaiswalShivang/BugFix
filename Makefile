.PHONY: up down switch-up test e2e reset-demo demo-reset

up:
	docker compose up -d

down:
	docker compose down

switch-up:
	python -m services.switch.cli "!list-agents"
	python -m services.switch.cli "!agents-status"

test:
	python -m pytest tests/api -v
	pnpm --filter demo-ecommerce test
	pnpm --filter demo-ecommerce exec tsc --noEmit
	pnpm --filter dashboard exec tsc --noEmit

e2e:
	python -m pytest tests/end_to_end -v

reset-demo: demo-reset

demo-reset:
	python -c "from services.worktree_switch import WorktreeSwitcher; WorktreeSwitcher().switch_to_main()"
	git checkout -- apps/demo-ecommerce/app/api/checkout/coupon/route.ts
	python -c "import subprocess, shutil; subprocess.run(['git', 'worktree', 'remove', '--force', 'worktrees/BP-0007'], capture_output=True); subprocess.run(['git', 'worktree', 'prune'], capture_output=True); subprocess.run(['git', 'branch', '-D', 'bugproof/BP-0007'], capture_output=True); [shutil.rmtree(p, ignore_errors=True) for p in ['worktrees/BP-0007', 'artifacts/BP-0007']]"
