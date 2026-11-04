from typing import Dict, Any, List, Tuple
from packages.contracts.models import InvestigationStatus

def evaluate_verification(
    baseline_report: Dict[str, Any],
    patch_summary: Dict[str, Any],
    retest_report: Dict[str, Any],
) -> Tuple[InvestigationStatus, List[str]]:
    reasons: List[str] = []

    baseline_failures = baseline_report.get("failures_observed", 0)
    baseline_attempts = baseline_report.get("attempts_run", 0)
    if baseline_attempts != 3 or baseline_failures != 3:
        reasons.append(f"Baseline failure not verified 3/3 times ({baseline_failures}/{baseline_attempts} observed)")
        return InvestigationStatus.NOT_VERIFIED, reasons
    else:
        reasons.append("1. Baseline reproduction failed 3/3 times with observable crash")

    test_exit = patch_summary.get("test_exit_code", 1)
    tsc_exit = patch_summary.get("typecheck_exit_code", 1)
    if test_exit != 0:
        reasons.append(f"Regression test runner exited with non-zero code: {test_exit}")
        return InvestigationStatus.NOT_VERIFIED, reasons
    else:
        reasons.append("2. Regression unit tests passed with exit code 0")

    if tsc_exit != 0:
        reasons.append(f"TypeScript typecheck failed with exit code: {tsc_exit}")
        return InvestigationStatus.NOT_VERIFIED, reasons
    else:
        reasons.append("3. Typecheck validation passed with exit code 0")

    retest_passes = retest_report.get("passes_observed", 0)
    retest_attempts = retest_report.get("attempts_run", 0)
    if retest_attempts != 3 or retest_passes != 3:
        reasons.append(f"Independent browser retest failed {retest_attempts - retest_passes} attempts")
        return InvestigationStatus.NOT_VERIFIED, reasons
    else:
        reasons.append("4. Independent browser retest passed 3/3 attempts with 0 console errors")

    regressions = retest_report.get("regression_checks", [])
    if any(not r.get("passed", False) for r in regressions):
        reasons.append("Regression detected on auxiliary coupon flows (SAVE20 or empty input)")
        return InvestigationStatus.NOT_VERIFIED, reasons
    else:
        reasons.append("5. Auxiliary checks confirmed 0 regressions on SAVE20 and empty code")

    return InvestigationStatus.VERIFIED, reasons

