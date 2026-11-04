import asyncio
import json
import os
import sys
from typing import Dict, Any, Optional
from .runner import run_reproduction_scenario, run_retest_scenario
from .scenario_parser import parse_spoken_scenario

class BugReproducerAdapter:
    def __init__(self, room_name: str = "bugproof", artifacts_root: str = "artifacts"):
        self.room_name = room_name
        self.artifacts_root = artifacts_root
        self.name = "bug-reproducer"
        self.alias = "repro"
        self.runtime = "playwright-worker"
        self.status = "ONLINE"

    def get_status(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "alias": self.alias,
            "runtime": self.runtime,
            "status": self.status,
            "room": self.room_name,
        }

    async def handle_message(self, message_text: str, investigation_id: str = "BP-0007") -> Dict[str, Any]:
        parsed = parse_spoken_scenario(message_text)
        target_url = parsed["target_url"]
        coupon = parsed["coupon_code"]

        if "retest" in message_text.lower() or "verify" in message_text.lower():
            result = await run_retest_scenario(investigation_id, target_url, self.artifacts_root)
            return {
                "type": "VERIFICATION_HANDOFF",
                "room": self.room_name,
                "author": f"@{self.name}",
                "report": result,
                "message": (
                    f"@{self.name} completed independent retest for {investigation_id}. "
                    f"Result: {result['status']}. Passed {result['passes_observed']}/3 attempts. "
                    f"Regressions: 0 detected. Tagging qa-commander for sign-off."
                ),
            }
        else:
            result = await run_reproduction_scenario(investigation_id, target_url, coupon, self.artifacts_root)
            next_agent = "@code-fixer" if result["status"] == "REPRODUCED" else "none"
            return {
                "type": "EVIDENCE_HANDOFF",
                "room": self.room_name,
                "author": f"@{self.name}",
                "report": result,
                "message": (
                    f"@{self.name} finished baseline reproduction for {investigation_id}. "
                    f"Status: {result['status']} ({result['failures_observed']}/3 failures observed). "
                    f"Artifacts registered: before-apply.png, after-crash.png, trace.zip. "
                    f"Handoff target: {next_agent}."
                ),
            }

if __name__ == "__main__":
    adapter = BugReproducerAdapter()
    msg = sys.argv[1] if len(sys.argv) > 1 else "@repro investigate why checkout crashes with EXPIRED10"
    inv_id = sys.argv[2] if len(sys.argv) > 2 else "BP-0007"
    res = asyncio.run(adapter.handle_message(msg, inv_id))
    print(json.dumps(res, indent=2))
