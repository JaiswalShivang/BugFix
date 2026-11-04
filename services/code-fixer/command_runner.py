import subprocess
import shutil
from typing import List, Dict, Any

ALLOWED_COMMAND_PREFIXES = [
    ["pnpm", "test"],
    ["pnpm", "--filter", "demo-ecommerce", "test"],
    ["pnpm", "--filter", "demo-ecommerce", "exec", "tsc", "--noEmit"],
    ["npm", "test"],
    ["npx", "tsc", "--noEmit"],
    ["git", "diff"],
    ["git", "status"],
    ["pytest"],
    ["node", "--test"],
]

def is_command_allowed(cmd: List[str]) -> bool:
    if not cmd:
        return False
    for allowed in ALLOWED_COMMAND_PREFIXES:
        if len(cmd) >= len(allowed) and cmd[:len(allowed)] == allowed:
            return True
    return False

def run_constrained_command(cmd: List[str], cwd: str, timeout: int = 60) -> Dict[str, Any]:
    if not is_command_allowed(cmd):
        raise ValueError(f"Command not allowlisted: {' '.join(cmd)}")

    resolved_bin = shutil.which(cmd[0]) or cmd[0]
    exec_cmd = [resolved_bin] + cmd[1:]

    try:
        proc = subprocess.run(
            exec_cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            shell=False,
            timeout=timeout,
        )
        return {
            "exit_code": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "command": " ".join(cmd),
        }
    except subprocess.TimeoutExpired:
        return {
            "exit_code": 124,
            "stdout": "",
            "stderr": f"Command timed out after {timeout} seconds",
            "command": " ".join(cmd),
        }
    except Exception as exc:
        return {
            "exit_code": 1,
            "stdout": "",
            "stderr": str(exc),
            "command": " ".join(cmd),
        }
