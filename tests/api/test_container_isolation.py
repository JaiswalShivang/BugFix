import pytest
import yaml
import subprocess
import shutil

def test_compose_isolation_definitions():
    with open("docker-compose.yml", "r", encoding="utf-8") as f:
        compose = yaml.safe_load(f)

    repro = compose["services"]["bug-reproducer"]
    repro_vols = repro.get("volumes", [])
    for v in repro_vols:
        assert "apps/demo-ecommerce" not in v
        assert "apps" not in v

    fixer = compose["services"]["code-fixer"]
    fixer_vols = fixer.get("volumes", [])
    for v in fixer_vols:
        assert "demo-app" not in v

def test_live_container_isolation():
    if not shutil.which("docker"):
        pytest.skip("Docker CLI not available")

    ps_res = subprocess.run(["docker", "ps", "-q", "-f", "name=bugproof-bug-reproducer"], capture_output=True, text=True)
    if not ps_res.stdout.strip():
        pytest.skip("Container bugproof-bug-reproducer not running")

    git_check = subprocess.run(
        ["docker", "exec", "bugproof-bug-reproducer", "which", "git"],
        capture_output=True,
        text=True,
    )
    assert git_check.returncode != 0

    src_check = subprocess.run(
        ["docker", "exec", "bugproof-bug-reproducer", "ls", "/app/apps/demo-ecommerce"],
        capture_output=True,
        text=True,
    )
    assert src_check.returncode != 0

    browser_check = subprocess.run(
        ["docker", "exec", "bugproof-code-fixer", "which", "chromium"],
        capture_output=True,
        text=True,
    )
    assert browser_check.returncode != 0
