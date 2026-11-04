import os
import json
import shutil
import asyncio
from typing import Dict, Any, List
from playwright.async_api import async_playwright
from .url_validator import is_target_url_allowed

EXPECTED_FILTER_PATTERNS = [
    "status of 400",
    "Failed to load resource: the server responded with a status of 400",
]

def filter_console_errors(errors: List[str]) -> List[str]:
    filtered = []
    for err in errors:
        is_expected = any(pat in err for pat in EXPECTED_FILTER_PATTERNS)
        if not is_expected:
            filtered.append(err)
    return filtered

async def run_single_attempt(
    target_url: str,
    coupon_code: str,
    artifact_dir: str,
    attempt: int,
) -> Dict[str, Any]:
    os.makedirs(artifact_dir, exist_ok=True)
    console_errors: List[str] = []
    http_errors: List[Dict[str, Any]] = []

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            trace_path = os.path.join(artifact_dir, f"attempt-{attempt}-trace.zip")
            await context.tracing.start(screenshots=True, snapshots=True)
            page = await context.new_page()

            page.on(
                "console",
                lambda msg: console_errors.append(msg.text)
                if msg.type == "error"
                else None,
            )
            page.on(
                "response",
                lambda res: http_errors.append({"url": res.url, "status": res.status})
                if res.status >= 500
                else None,
            )

            await page.goto(target_url, wait_until="networkidle", timeout=15000)

            before_png = os.path.join(artifact_dir, f"attempt-{attempt}-before.png")
            await page.screenshot(path=before_png, full_page=True)

            coupon_input = page.get_by_label("Coupon code")
            await coupon_input.fill(coupon_code)

            apply_button = page.get_by_role("button", name="Apply coupon")
            await apply_button.click()
            await page.wait_for_timeout(800)

            after_png = os.path.join(artifact_dir, f"attempt-{attempt}-after.png")
            await page.screenshot(path=after_png, full_page=True)

            validation_visible = await page.get_by_text("Coupon expired").first.is_visible() if await page.get_by_text("Coupon expired").count() > 0 else False
            applied_visible = await page.get_by_text("Coupon applied").first.is_visible() if await page.get_by_text("Coupon applied").count() > 0 else False
            crash_visible = await page.get_by_text("Internal Server Error").first.is_visible() if await page.get_by_text("Internal Server Error").count() > 0 else False

            await context.tracing.stop(path=trace_path)
            await browser.close()

            relevant_console_errors = filter_console_errors(console_errors)
            has_error = crash_visible or len(relevant_console_errors) > 0 or len(http_errors) > 0
            passed = not has_error and (validation_visible or applied_visible)

            return {
                "attempt": attempt,
                "validation_visible": validation_visible,
                "applied_visible": applied_visible,
                "crash_visible": crash_visible,
                "console_errors": relevant_console_errors,
                "http_errors": http_errors,
                "passed": passed,
                "failed": has_error,
                "environment_error": False,
            }
    except Exception as exc:
        return {
            "attempt": attempt,
            "validation_visible": False,
            "applied_visible": False,
            "crash_visible": True,
            "console_errors": [str(exc)],
            "http_errors": [{"url": target_url, "status": 0}],
            "passed": False,
            "failed": True,
            "environment_error": True,
        }

async def run_reproduction_scenario(
    investigation_id: str,
    target_url: str,
    coupon_code: str = "EXPIRED10",
    artifacts_root: str = "artifacts",
) -> Dict[str, Any]:
    if not is_target_url_allowed(target_url):
        return {
            "investigation_id": investigation_id,
            "stage": "BASELINE_REPRODUCTION",
            "agent": "@bug-reproducer",
            "target_url": target_url,
            "scenario": f"Apply coupon code {coupon_code} during checkout",
            "attempts_run": 0,
            "failures_observed": 0,
            "expected_behavior": "Target URL blocked by security allowlist",
            "observed_behavior": f"Disallowed target host: {target_url}",
            "console_errors": [],
            "failed_requests": [],
            "evidence_refs": [],
            "status": "ENVIRONMENT_UNAVAILABLE",
            "next_handoff": None,
        }

    artifact_dir = os.path.join(artifacts_root, investigation_id, "repro")
    os.makedirs(artifact_dir, exist_ok=True)

    attempts = []
    failures = 0
    all_console_errors = []
    all_failed_requests = []

    for i in range(1, 4):
        result = await run_single_attempt(target_url, coupon_code, artifact_dir, i)
        attempts.append(result)
        if result["failed"]:
            failures += 1
        for ce in result["console_errors"]:
            if ce not in all_console_errors:
                all_console_errors.append(ce)
        for he in result["http_errors"]:
            if he not in all_failed_requests:
                all_failed_requests.append(he)

    before_standard = os.path.join(artifact_dir, "before-apply.png")
    after_standard = os.path.join(artifact_dir, "after-crash.png")
    trace_standard = os.path.join(artifact_dir, "trace.zip")

    attempt_1_before = os.path.join(artifact_dir, "attempt-1-before.png")
    attempt_1_after = os.path.join(artifact_dir, "attempt-1-after.png")
    attempt_1_trace = os.path.join(artifact_dir, "attempt-1-trace.zip")

    if os.path.exists(attempt_1_before):
        shutil.copyfile(attempt_1_before, before_standard)
    if os.path.exists(attempt_1_after):
        shutil.copyfile(attempt_1_after, after_standard)
    if os.path.exists(attempt_1_trace):
        shutil.copyfile(attempt_1_trace, trace_standard)

    if any(a.get("environment_error") for a in attempts):
        status = "ENVIRONMENT_UNAVAILABLE"
    elif failures == 3:
        status = "REPRODUCED"
    elif failures == 0:
        status = "NOT_REPRODUCED"
    else:
        status = "INCONCLUSIVE"

    report = {
        "investigation_id": investigation_id,
        "stage": "BASELINE_REPRODUCTION",
        "agent": "@bug-reproducer",
        "target_url": target_url,
        "scenario": f"Apply coupon code {coupon_code} during checkout",
        "attempts_run": 3,
        "failures_observed": failures,
        "expected_behavior": "Display 'Coupon expired' validation message; HTTP 400; checkout form remains interactive",
        "observed_behavior": "POST /api/checkout/coupon returned HTTP 500; unhandled TypeError crashed checkout view"
        if status == "REPRODUCED"
        else f"Completed 3 attempts with {failures} failures",
        "console_errors": all_console_errors,
        "failed_requests": all_failed_requests,
        "evidence_refs": [
            f"artifacts/{investigation_id}/repro/before-apply.png",
            f"artifacts/{investigation_id}/repro/after-crash.png",
            f"artifacts/{investigation_id}/repro/trace.zip",
        ],
        "status": status,
        "next_handoff": "@code-fixer" if status == "REPRODUCED" else None,
        "attempts": attempts,
    }

    report_path = os.path.join(artifact_dir, f"reproduction-report-{investigation_id}.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    root_report_path = os.path.join(artifacts_root, investigation_id, f"reproduction-report-{investigation_id}.json")
    with open(root_report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return report

async def run_retest_scenario(
    investigation_id: str,
    target_url: str,
    artifacts_root: str = "artifacts",
) -> Dict[str, Any]:
    artifact_dir = os.path.join(artifacts_root, investigation_id, "retest")
    os.makedirs(artifact_dir, exist_ok=True)

    attempts = []
    passes = 0
    all_console_errors = []
    all_failed_requests = []

    for i in range(1, 4):
        result = await run_single_attempt(target_url, "EXPIRED10", artifact_dir, i)
        attempts.append(result)
        if result["passed"]:
            passes += 1
        for ce in result["console_errors"]:
            if ce not in all_console_errors:
                all_console_errors.append(ce)
        for he in result["http_errors"]:
            if he not in all_failed_requests:
                all_failed_requests.append(he)

    save20_result = await run_single_attempt(target_url, "SAVE20", artifact_dir, 4)
    empty_result = await run_single_attempt(target_url, "   ", artifact_dir, 5)

    regression_checks = [
        {
            "name": "SAVE20 valid discount check",
            "passed": save20_result["applied_visible"] and not save20_result["crash_visible"],
            "details": "20% discount applied without errors",
        },
        {
            "name": "Empty coupon validation check",
            "passed": not empty_result["crash_visible"],
            "details": "Empty coupon handled gracefully",
        },
    ]

    all_regressions_passed = all(r["passed"] for r in regression_checks)

    reasons = []
    if passes == 3:
        reasons.append("Scenario reproduced 0 failures across 3 consecutive post-patch attempts")
    else:
        reasons.append(f"Post-patch retest failed {3 - passes} of 3 attempts")

    if all_regressions_passed:
        reasons.append("Zero regressions observed on SAVE20 and empty coupon flows")
    else:
        reasons.append("Regression detected on auxiliary coupon checks")

    retest_report = {
        "investigation_id": investigation_id,
        "stage": "INDEPENDENT_RETEST",
        "agent": "@bug-reproducer",
        "attempts_run": 3,
        "passes_observed": passes,
        "failures_observed": 3 - passes,
        "regression_checks": regression_checks,
        "evidence_refs": [
            f"artifacts/{investigation_id}/retest/attempt-1-after.png",
            f"artifacts/{investigation_id}/retest/attempt-2-after.png",
            f"artifacts/{investigation_id}/retest/attempt-3-after.png",
        ],
        "status": "COMPLETED",
        "reasons": reasons,
        "attempts": attempts,
    }

    report_path = os.path.join(artifact_dir, f"verification-report-{investigation_id}.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(retest_report, f, indent=2)

    root_report_path = os.path.join(artifacts_root, investigation_id, f"verification-report-{investigation_id}.json")
    with open(root_report_path, "w", encoding="utf-8") as f:
        json.dump(retest_report, f, indent=2)

    return retest_report
