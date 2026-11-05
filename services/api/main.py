import os
import json
import asyncio
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

from packages.contracts.models import (
    InvestigationStatus,
    ReproductionReport,
    PatchSummary,
    VerificationReport,
    Decision,
)
from .db import Database
from .verification.evaluator import evaluate_verification
from services.switch.room import SwitchRoom
from services.worktree_switch import WorktreeSwitcher

app = FastAPI(title="BugProof API & Switch Sync Mirror")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("artifacts", exist_ok=True)
app.mount("/artifacts", StaticFiles(directory="artifacts"), name="artifacts")

db = Database()
room = SwitchRoom()
worktree_switcher = WorktreeSwitcher()

class CreateInvestigationRequest(BaseModel):
    investigation_id: str = "BP-0007"
    target_url: str = "http://localhost:3001/checkout"
    scenario: str = "Apply expired coupon code EXPIRED10 during checkout"
    coupon_code: str = "EXPIRED10"

class DecisionRequest(BaseModel):
    decision: str
    actor_role: str = "qa-commander"
    is_voice: bool = True
    notes: Optional[str] = None
    switch_message_id: Optional[str] = None

class VoiceMessageRequest(BaseModel):
    text: str
    is_voice: bool = True

class SwitchCommandRequest(BaseModel):
    command: str

class UnifiedCommandRequest(BaseModel):
    command: str
    investigation_id: str = "BP-0007"
    is_voice: bool = True

@app.get("/api/health")
def get_health():
    return {"status": "ok", "service": "bugproof-api", "room": "#bugproof"}

@app.get("/api/investigations")
def list_investigations():
    return db.list_investigations()

@app.post("/api/investigations")
async def create_investigation(req: CreateInvestigationRequest):
    inv = db.create_investigation(
        investigation_id=req.investigation_id,
        target_url=req.target_url,
        scenario=req.scenario,
        coupon_code=req.coupon_code,
    )
    await room.post_message(
        sender="system",
        text=f"Investigation {req.investigation_id} initialized for {req.target_url} (coupon: {req.coupon_code})",
        investigation_id=req.investigation_id,
    )
    return inv

@app.get("/api/investigations/{inv_id}")
def get_investigation_detail(inv_id: str):
    inv = db.get_investigation(inv_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return inv

@app.post("/api/investigations/{inv_id}/switch-webhook")
async def handle_switch_webhook(inv_id: str, payload: Dict[str, Any]):
    stage = payload.get("stage")
    status = payload.get("status")
    msg_id = payload.get("switch_message_id")

    if stage == "BASELINE_REPRODUCTION":
        db.update_baseline_report(inv_id, payload)
        if status == "REPRODUCED":
            db.update_status(inv_id, InvestigationStatus.REPRODUCED, "@bug-reproducer", payload, msg_id)
        elif status == "NOT_REPRODUCED":
            db.update_status(inv_id, InvestigationStatus.NOT_REPRODUCED, "@bug-reproducer", payload, msg_id)
        else:
            db.update_status(inv_id, InvestigationStatus.INCONCLUSIVE, "@bug-reproducer", payload, msg_id)

    elif stage == "WORKTREE_PATCH":
        db.update_patch_summary(inv_id, payload)
        if status == "PATCH_READY":
            worktree_switcher.switch_to_worktree(inv_id)
            db.update_status(inv_id, InvestigationStatus.PATCH_READY, "@code-fixer", payload, msg_id)
        else:
            db.update_status(inv_id, InvestigationStatus.PATCH_FAILED, "@code-fixer", payload, msg_id)

    elif stage == "INDEPENDENT_RETEST":
        db.update_verification_report(inv_id, payload)
        inv = db.get_investigation(inv_id)
        base = inv.get("baseline_report") or {}
        patch = inv.get("patch_summary") or {}
        evaluated_status, reasons = evaluate_verification(base, patch, payload)
        payload["evaluator_reasons"] = reasons
        db.update_status(inv_id, evaluated_status, "evaluator", payload, msg_id)

    return {"ok": True, "investigation_id": inv_id}

@app.post("/api/investigations/{inv_id}/start")
async def start_reproduction_endpoint(inv_id: str):
    inv = db.get_investigation(inv_id)
    if not inv:
        inv = db.create_investigation(inv_id, "http://localhost:3001/checkout", "Apply coupon EXPIRED10")
    db.update_status(inv_id, InvestigationStatus.REPRODUCING, "@bug-reproducer", {"stage": "BASELINE_REPRODUCTION"})
    responses = await room.post_message(
        sender="qa-commander",
        text=f"@repro start investigation {inv_id} on demo-app checkout with EXPIRED10",
        investigation_id=inv_id,
        is_voice=True,
    )
    for item in responses:
        if item.get("report") and item.get("report", {}).get("stage") == "BASELINE_REPRODUCTION":
            await handle_switch_webhook(inv_id, item["report"])
    return {
        "ok": True,
        "investigation_id": inv_id,
        "status": (db.get_investigation(inv_id) or {}).get("status"),
        "responses": responses,
    }

@app.post("/api/investigations/{inv_id}/patch")
async def start_patch_endpoint(inv_id: str):
    inv = db.get_investigation(inv_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    if inv.get("status") not in (InvestigationStatus.REPRODUCED.value, InvestigationStatus.PATCH_FAILED.value):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot patch: current status is {inv.get('status')}, requires REPRODUCED (Proof Before Fix invariant)",
        )
    db.update_status(inv_id, InvestigationStatus.PATCHING, "@code-fixer", {"stage": "WORKTREE_PATCH"})
    responses = await room.post_message(
        sender="qa-commander",
        text=f"@fixer patch null coupon crash in isolated worktree for {inv_id}",
        investigation_id=inv_id,
        is_voice=True,
    )
    for item in responses:
        if item.get("patch_summary"):
            summary = item["patch_summary"]
            summary["stage"] = "WORKTREE_PATCH"
            await handle_switch_webhook(inv_id, summary)
        elif item.get("report") and item.get("report", {}).get("stage") == "INDEPENDENT_RETEST":
            await handle_switch_webhook(inv_id, item["report"])
    return {
        "ok": True,
        "investigation_id": inv_id,
        "status": (db.get_investigation(inv_id) or {}).get("status"),
        "responses": responses,
    }

@app.get("/api/investigations/{inv_id}/artifacts")
def get_investigation_artifacts(inv_id: str):
    inv_dir = os.path.join("artifacts", inv_id)
    repro_dir = os.path.join(inv_dir, "repro")
    retest_dir = os.path.join(inv_dir, "retest")

    artifacts = {
        "investigation_id": inv_id,
        "before_apply": f"/artifacts/{inv_id}/repro/before-apply.png" if os.path.exists(os.path.join(repro_dir, "before-apply.png")) else None,
        "after_crash": f"/artifacts/{inv_id}/repro/after-crash.png" if os.path.exists(os.path.join(repro_dir, "after-crash.png")) else None,
        "trace": f"/artifacts/{inv_id}/repro/trace.zip" if os.path.exists(os.path.join(repro_dir, "trace.zip")) else None,
        "retest_after": f"/artifacts/{inv_id}/retest/attempt-1-after.png" if os.path.exists(os.path.join(retest_dir, "attempt-1-after.png")) else None,
        "diff": f"/artifacts/{inv_id}/patch-{inv_id}.diff" if os.path.exists(os.path.join(inv_dir, f"patch-{inv_id}.diff")) else None,
        "summary": f"/artifacts/{inv_id}/patch-summary-{inv_id}.md" if os.path.exists(os.path.join(inv_dir, f"patch-summary-{inv_id}.md")) else None,
    }
    return artifacts

@app.get("/api/investigations/{inv_id}/diff")
def get_investigation_diff(inv_id: str):
    diff_file = os.path.join("artifacts", inv_id, f"patch-{inv_id}.diff")
    if not os.path.exists(diff_file):
        import importlib
        wm_mod = importlib.import_module("services.code-fixer.worktree_manager")
        mgr = wm_mod.WorktreeManager()
        diff_text = mgr.get_diff(inv_id)
    else:
        with open(diff_file, "r", encoding="utf-8") as f:
            diff_text = f.read()

    return {
        "investigation_id": inv_id,
        "files_changed": [
            "apps/demo-ecommerce/app/api/checkout/coupon/route.ts",
            "apps/demo-ecommerce/tests/coupon.test.ts",
        ],
        "diff": diff_text,
    }

@app.post("/api/investigations/{inv_id}/decision")
def post_decision(inv_id: str, req: DecisionRequest):
    inv = db.get_investigation(inv_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    if inv.get("status") not in (InvestigationStatus.VERIFIED.value, InvestigationStatus.NEEDS_HUMAN_REVIEW.value):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot approve patch: current state is {inv.get('status')}, must be VERIFIED",
        )

    decision_data = req.dict()
    db.update_decision(inv_id, decision_data)

    target_status = (
        InvestigationStatus.HUMAN_ACCEPTED
        if req.decision.upper() in ("ACCEPT", "APPROVE", "HUMAN_ACCEPTED")
        else InvestigationStatus.HUMAN_REJECTED
    )

    db.update_status(
        inv_id,
        target_status,
        req.actor_role,
        decision_data,
        req.switch_message_id,
    )

    return {"ok": True, "status": target_status.value}

@app.post("/api/command")
async def handle_unified_command(req: UnifiedCommandRequest):
    cmd = req.command.strip()
    inv_id = req.investigation_id
    if cmd.startswith("!"):
        output = room.execute_command(cmd)
        return {"type": "COMMAND_OUTPUT", "command": cmd, "output": output}
    return await post_voice_input(inv_id, VoiceMessageRequest(text=cmd, is_voice=req.is_voice))

@app.post("/api/investigations/{inv_id}/voice")
async def post_voice_input(inv_id: str, req: VoiceMessageRequest):
    inv = db.get_investigation(inv_id)
    if not inv:
        db.create_investigation(inv_id, "http://localhost:3001/checkout", req.text)

    text = req.text.strip()
    responses = await room.post_message(
        sender="qa-commander",
        text=text,
        investigation_id=inv_id,
        is_voice=req.is_voice,
    )

    for item in responses:
        if item.get("report") and item.get("report", {}).get("stage") == "BASELINE_REPRODUCTION":
            await handle_switch_webhook(inv_id, item["report"])
        elif item.get("patch_summary"):
            summary = item["patch_summary"]
            summary["stage"] = "WORKTREE_PATCH"
            await handle_switch_webhook(inv_id, summary)
        elif item.get("report") and item.get("report", {}).get("stage") == "INDEPENDENT_RETEST":
            await handle_switch_webhook(inv_id, item["report"])

    text_lower = text.lower()
    if any(k in text_lower for k in ["approve", "accept", "sign-off", "sign off"]):
        latest = db.get_investigation(inv_id)
        if latest and latest.get("status") in (InvestigationStatus.VERIFIED.value, InvestigationStatus.NEEDS_HUMAN_REVIEW.value):
            post_decision(
                inv_id,
                DecisionRequest(
                    decision="ACCEPT",
                    actor_role="qa-commander",
                    is_voice=True,
                    switch_message_id=responses[0]["id"] if responses else "voice-gate",
                ),
            )

    return {
        "ok": True,
        "investigation_id": inv_id,
        "responses": responses,
        "current_status": (db.get_investigation(inv_id) or {}).get("status"),
    }

@app.post("/api/investigations/{inv_id}/switch-command")
def post_switch_command(inv_id: str, req: SwitchCommandRequest):
    output = room.execute_command(req.command)
    return {"command": req.command, "output": output}

@app.get("/api/investigations/{inv_id}/events")
async def stream_investigation_events(inv_id: str):
    async def event_generator():
        last_event_id = 0
        while True:
            inv = db.get_investigation(inv_id)
            if inv:
                events = inv.get("events", [])
                new_events = [e for e in events if e["id"] > last_event_id]
                for e in new_events:
                    last_event_id = e["id"]
                    yield f"event: update\ndata: {json.dumps(e)}\n\n"
            yield f"event: ping\ndata: {json.dumps({'time': asyncio.get_event_loop().time()})}\n\n"
            await asyncio.sleep(1.0)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
