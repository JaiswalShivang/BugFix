import os
import yaml
from services.switch.room import SwitchRoom

def test_template_fidelity():
    template_path = "configs/switch/bugproof.template.yaml"
    assert os.path.exists(template_path)
    with open(template_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    assert config["room"]["name"] == "bugproof"
    instructions = config["room"]["instructions"]
    assert "@bug-reproducer" in instructions
    assert "@code-fixer" in instructions
    assert "qa-commander" in instructions
    assert "PROOF BEFORE FIX" in instructions

    agents = [a["name"] for a in config.get("agents", [])]
    assert "bug-reproducer" in agents
    assert "code-fixer" in agents

    aliases = {al["alias"]: al["target"] for al in config.get("aliases", [])}
    assert aliases.get("repro") == "bug-reproducer"
    assert aliases.get("fixer") == "code-fixer"

    roles = {r["name"]: r for r in config.get("roles", [])}
    assert "qa-commander" in roles
    assert roles["qa-commander"].get("approval_gate") is True
    assert "reproducer" in roles
    assert "fixer" in roles

def test_switch_judge_inspection_commands():
    room = SwitchRoom()

    agents_out = room.execute_command("!list-agents")
    assert "@bug-reproducer" in agents_out
    assert "@code-fixer" in agents_out
    assert "playwright-worker" in agents_out
    assert "worktree-worker" in agents_out

    status_out = room.execute_command("!agents-status")
    assert "@bug-reproducer" in status_out
    assert "@code-fixer" in status_out
    assert "ONLINE" in status_out

    aliases_out = room.execute_command("!list-aliases")
    assert "@repro -> @bug-reproducer" in aliases_out
    assert "@fixer -> @code-fixer" in aliases_out

    roles_out = room.execute_command("!roles")
    assert "qa-commander" in roles_out
    assert "reproducer" in roles_out
    assert "fixer" in roles_out
    assert "[APPROVAL GATE]" in roles_out

    docs_out = room.execute_command("!list-documents")
    assert "verification-policy.md" in docs_out

    refs_out = room.execute_command("!list-references")
    assert "demo-app-url" in refs_out
    assert "worktree-root" in refs_out
