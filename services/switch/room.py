import os
import json
import yaml
import importlib
from typing import Dict, Any, List, Optional

class SwitchRoom:
    def __init__(self, template_path: str = "configs/switch/bugproof.template.yaml", artifacts_root: str = "artifacts"):
        self.template_path = template_path
        self.artifacts_root = artifacts_root
        self.config = self._load_template()
        
        repro_mod = importlib.import_module("services.reproducer.switch_adapter")
        self.reproducer = repro_mod.BugReproducerAdapter(artifacts_root=self.artifacts_root)
        
        fixer_mod = importlib.import_module("services.code-fixer.switch_adapter")
        self.fixer = fixer_mod.CodeFixerAdapter(artifacts_root=self.artifacts_root)
        
        self.messages: List[Dict[str, Any]] = []

    def _load_template(self) -> Dict[str, Any]:
        if os.path.exists(self.template_path):
            with open(self.template_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        return {
            "room": {"name": "bugproof", "description": "Evidence-based AI debugging room"},
            "roles": [],
            "agents": [],
            "aliases": [],
            "references": [],
            "documents": [],
        }

    def _load_json(self, path: str) -> Dict[str, Any]:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def execute_command(self, command: str) -> str:
        cmd = command.strip().lower()
        if cmd == "!list-agents":
            agents = self.config.get("agents", [])
            lines = ["Registered agents in #bugproof:"]
            for a in agents:
                lines.append(f"  - @{a['name']} (runtime: {a['runtime']})")
            return "\n".join(lines)

        elif cmd == "!agents-status":
            repro_status = self.reproducer.get_status()
            fixer_status = self.fixer.get_status()
            lines = [
                "Agent live status:",
                f"  - @{repro_status['name']} ({repro_status['status']} - {repro_status['runtime']})",
                f"  - @{fixer_status['name']} ({fixer_status['status']} - {fixer_status['runtime']})",
            ]
            return "\n".join(lines)

        elif cmd == "!list-aliases":
            aliases = self.config.get("aliases", [])
            lines = ["Configured voice and text aliases:"]
            for al in aliases:
                lines.append(f"  - @{al['alias']} -> @{al['target']}")
            return "\n".join(lines)

        elif cmd == "!roles":
            roles = self.config.get("roles", [])
            lines = ["Configured room roles:"]
            for r in roles:
                assigned = ", ".join(r.get("assigned_to", []))
                gate = " [APPROVAL GATE]" if r.get("approval_gate") else ""
                lines.append(f"  - {r['name']}: {r['description']} (assigned: {assigned}){gate}")
            return "\n".join(lines)

        elif cmd in ("!list-documents", "!documents"):
            docs = self.config.get("documents", [])
            lines = ["Attached room documents:"]
            for d in docs:
                lines.append(f"  - {d['name']} (path: {d.get('path', 'n/a')})")
            inv_repro = os.path.join(self.artifacts_root, "BP-0007", "reproduction-report-BP-0007.json")
            if os.path.exists(inv_repro):
                lines.append("  - reproduction-report-BP-0007.json (stage: BASELINE_REPRODUCTION)")
            inv_patch = os.path.join(self.artifacts_root, "BP-0007", "patch-summary-BP-0007.md")
            if os.path.exists(inv_patch):
                lines.append("  - patch-summary-BP-0007.md (stage: WORKTREE_PATCH)")
            return "\n".join(lines)

        elif cmd in ("!list-references", "!references"):
            refs = self.config.get("references", [])
            lines = ["Attached room references:"]
            for rf in refs:
                lines.append(f"  - {rf['name']}: {rf['value']}")
            return "\n".join(lines)

        else:
            return f"Unknown room command: {command}. Available: !list-agents, !agents-status, !list-aliases, !roles, !list-documents, !list-references"

    async def post_message(
        self,
        sender: str,
        text: str,
        investigation_id: str = "BP-0007",
        is_voice: bool = False,
    ) -> List[Dict[str, Any]]:
        msg_id = f"sw-msg-{len(self.messages) + 1:04d}"
        event = {
            "id": msg_id,
            "sender": sender,
            "text": text,
            "is_voice": is_voice,
            "investigation_id": investigation_id,
        }
        self.messages.append(event)
        responses = [event]

        if text.startswith("!"):
            reply_text = self.execute_command(text)
            reply = {
                "id": f"sw-msg-{len(self.messages) + 1:04d}",
                "sender": "system",
                "text": reply_text,
                "is_voice": False,
                "investigation_id": investigation_id,
            }
            self.messages.append(reply)
            responses.append(reply)
            return responses

        text_lower = text.lower()
        is_cp1 = any(k in text_lower for k in ["@repro", "@bug-reproducer", "reproduce", "start investigation", "investigate", "baseline"])
        is_cp2 = any(k in text_lower for k in ["@fixer", "@code-fixer", "patch", "worktree", "fix", "repair"])
        is_cp3 = any(k in text_lower for k in ["qa-commander", "approve", "accept", "sign-off", "sign off", "reject"])

        if is_cp1 and not is_cp2 and not is_cp3:
            repro_res = await self.reproducer.handle_message(text, investigation_id)
            reply = {
                "id": f"sw-msg-{len(self.messages) + 1:04d}",
                "sender": "@bug-reproducer",
                "text": repro_res["message"],
                "report": repro_res.get("report"),
                "is_voice": False,
                "investigation_id": investigation_id,
            }
            self.messages.append(reply)
            responses.append(reply)

        elif is_cp2:
            fixer_res = self.fixer.handle_message(text, investigation_id)
            fixer_reply = {
                "id": f"sw-msg-{len(self.messages) + 1:04d}",
                "sender": "@code-fixer",
                "text": fixer_res["message"],
                "patch_summary": fixer_res.get("patch_summary"),
                "is_voice": False,
                "investigation_id": investigation_id,
            }
            self.messages.append(fixer_reply)
            responses.append(fixer_reply)

            if fixer_res.get("type") == "PATCH_HANDOFF" and fixer_res.get("patch_summary", {}).get("status") == "PATCH_READY":
                from services.worktree_switch import WorktreeSwitcher
                switcher = WorktreeSwitcher()
                switcher.switch_to_worktree(investigation_id)

                from services.reproducer.runner import run_retest_scenario
                target_url = "http://localhost:3001/checkout"
                retest_res = await run_retest_scenario(investigation_id, target_url, self.artifacts_root)

                from services.api.verification.evaluator import evaluate_verification
                base_report = self._load_json(os.path.join(self.artifacts_root, investigation_id, f"reproduction-report-{investigation_id}.json"))
                verdict, reasons = evaluate_verification(base_report, fixer_res["patch_summary"], retest_res)

                retest_reply = {
                    "id": f"sw-msg-{len(self.messages) + 1:04d}",
                    "sender": "@bug-reproducer",
                    "text": (
                        f"@bug-reproducer completed independent 3x browser retest on reloaded worktree. "
                        f"Passes: {retest_res['passes_observed']}/3. Deterministic Evaluator verdict: {verdict.value}. "
                        f"Awaiting qa-commander human sign-off."
                    ),
                    "report": retest_res,
                    "evaluated_verdict": verdict.value,
                    "evaluator_reasons": reasons,
                    "is_voice": False,
                    "investigation_id": investigation_id,
                }
                self.messages.append(retest_reply)
                responses.append(retest_reply)

        elif is_cp3:
            verif_path = os.path.join(self.artifacts_root, investigation_id, f"verification-report-{investigation_id}.json")
            if not os.path.exists(verif_path):
                verif_path = os.path.join(self.artifacts_root, investigation_id, "retest", f"verification-report-{investigation_id}.json")
            is_verified = os.path.exists(verif_path)

            if is_verified:
                reply = {
                    "id": f"sw-msg-{len(self.messages) + 1:04d}",
                    "sender": "qa-commander",
                    "text": f"qa-commander accepted verified patch {investigation_id}. Human gate approved and recorded.",
                    "decision": "HUMAN_ACCEPTED",
                    "is_voice": is_voice,
                    "investigation_id": investigation_id,
                }
            else:
                reply = {
                    "id": f"sw-msg-{len(self.messages) + 1:04d}",
                    "sender": "system",
                    "text": f"Cannot approve patch {investigation_id}: No completed verification report found.",
                    "decision": "REJECTED",
                    "is_voice": False,
                    "investigation_id": investigation_id,
                }
            self.messages.append(reply)
            responses.append(reply)

        return responses
