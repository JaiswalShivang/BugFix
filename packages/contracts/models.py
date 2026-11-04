from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class InvestigationStatus(str, Enum):
    CREATED = "CREATED"
    REPRODUCING = "REPRODUCING"
    REPRODUCED = "REPRODUCED"
    NOT_REPRODUCED = "NOT_REPRODUCED"
    INCONCLUSIVE = "INCONCLUSIVE"
    ENVIRONMENT_UNAVAILABLE = "ENVIRONMENT_UNAVAILABLE"
    PATCHING = "PATCHING"
    PATCH_READY = "PATCH_READY"
    PATCH_FAILED = "PATCH_FAILED"
    NEEDS_HUMAN_REVIEW = "NEEDS_HUMAN_REVIEW"
    RETESTING = "RETESTING"
    VERIFIED = "VERIFIED"
    NOT_VERIFIED = "NOT_VERIFIED"
    HUMAN_ACCEPTED = "HUMAN_ACCEPTED"
    HUMAN_REJECTED = "HUMAN_REJECTED"


class FailedRequest(BaseModel):
    url: str
    method: str
    status: int


class AttemptResult(BaseModel):
    attempt: int
    validation_visible: bool
    crash_visible: bool
    console_errors: List[str] = Field(default_factory=list)
    http_errors: List[Dict[str, Any]] = Field(default_factory=list)
    passed: bool


class ReproductionReport(BaseModel):
    investigation_id: str
    stage: str
    agent: str = "@bug-reproducer"
    target_url: str
    scenario: str
    attempts_run: int
    failures_observed: int
    expected_behavior: str
    observed_behavior: str
    console_errors: List[str] = Field(default_factory=list)
    failed_requests: List[FailedRequest] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)
    status: str
    next_handoff: Optional[str] = "@code-fixer"


class PatchSummary(BaseModel):
    investigation_id: str
    worktree_path: str
    branch_name: str
    commit_sha: Optional[str] = None
    files_changed: List[str] = Field(default_factory=list)
    diff_ref: str
    test_exit_code: int
    typecheck_exit_code: int
    root_cause: str
    patch_description: str
    status: str
    next_handoff: Optional[str] = "@bug-reproducer"


class RegressionCheck(BaseModel):
    name: str
    passed: bool
    details: Optional[str] = None


class VerificationReport(BaseModel):
    investigation_id: str
    stage: str = "INDEPENDENT_RETEST"
    agent: str = "@bug-reproducer"
    attempts_run: int
    passes_observed: int
    failures_observed: int
    regression_checks: List[RegressionCheck] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)
    status: str
    reasons: List[str] = Field(default_factory=list)


class Decision(BaseModel):
    investigation_id: str
    actor_role: str = "qa-commander"
    decision: str
    switch_message_id: Optional[str] = None
    is_voice: bool = False
    notes: Optional[str] = None


class InvestigationState(BaseModel):
    id: str
    status: InvestigationStatus
    target_url: str
    scenario: str
    coupon_code: Optional[str] = None
    worktree: Optional[str] = None
    baseline_report: Optional[ReproductionReport] = None
    patch_summary: Optional[PatchSummary] = None
    verification_report: Optional[VerificationReport] = None
    decision: Optional[Decision] = None
    history: List[Dict[str, Any]] = Field(default_factory=list)
