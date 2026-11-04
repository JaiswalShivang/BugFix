import pytest
from services.api.verification.evaluator import evaluate_verification
from packages.contracts.models import InvestigationStatus

def test_evaluator_all_pass():
    base = {"attempts_run": 3, "failures_observed": 3}
    patch = {"test_exit_code": 0, "typecheck_exit_code": 0}
    retest = {
        "attempts_run": 3,
        "passes_observed": 3,
        "regression_checks": [{"name": "SAVE20", "passed": True}],
    }
    status, reasons = evaluate_verification(base, patch, retest)
    assert status == InvestigationStatus.VERIFIED
    assert len(reasons) == 5

def test_evaluator_baseline_flaky():
    base = {"attempts_run": 3, "failures_observed": 2}
    patch = {"test_exit_code": 0, "typecheck_exit_code": 0}
    retest = {
        "attempts_run": 3,
        "passes_observed": 3,
        "regression_checks": [{"name": "SAVE20", "passed": True}],
    }
    status, reasons = evaluate_verification(base, patch, retest)
    assert status == InvestigationStatus.NOT_VERIFIED

def test_evaluator_test_failure():
    base = {"attempts_run": 3, "failures_observed": 3}
    patch = {"test_exit_code": 1, "typecheck_exit_code": 0}
    retest = {
        "attempts_run": 3,
        "passes_observed": 3,
        "regression_checks": [{"name": "SAVE20", "passed": True}],
    }
    status, reasons = evaluate_verification(base, patch, retest)
    assert status == InvestigationStatus.NOT_VERIFIED

def test_evaluator_retest_failure():
    base = {"attempts_run": 3, "failures_observed": 3}
    patch = {"test_exit_code": 0, "typecheck_exit_code": 0}
    retest = {
        "attempts_run": 3,
        "passes_observed": 2,
        "regression_checks": [{"name": "SAVE20", "passed": True}],
    }
    status, reasons = evaluate_verification(base, patch, retest)
    assert status == InvestigationStatus.NOT_VERIFIED

def test_evaluator_regression_failed():
    base = {"attempts_run": 3, "failures_observed": 3}
    patch = {"test_exit_code": 0, "typecheck_exit_code": 0}
    retest = {
        "attempts_run": 3,
        "passes_observed": 3,
        "regression_checks": [{"name": "SAVE20", "passed": False}],
    }
    status, reasons = evaluate_verification(base, patch, retest)
    assert status == InvestigationStatus.NOT_VERIFIED

