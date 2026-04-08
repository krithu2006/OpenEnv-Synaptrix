from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class EmailMessage:
    email_id: str
    sender: str
    subject: str
    body: str
    received_at: str
    source: str = "sample"
    expected_category: str | None = None
    expected_action: str | None = None
    gmail_label: str = "Unprocessed"
    mailbox_folder: str = "Inbox"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ClassificationResult:
    category: str
    confidence: float
    rationale: str
    category_scores: dict[str, float]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class RiskAnalysisResult:
    priority: str
    tone: str
    risk_level: str
    importance_score: int
    urgency_score: int
    spam_risk_score: int
    threat_indicators: list[str]
    rationale: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class DecisionResult:
    action: str
    response_needed: bool
    confidence_score: int
    response_window: str
    reply_suggestion: str
    draft_subject: str
    draft_body: str
    rationale: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ProductivityTask:
    title: str
    due_hint: str
    status: str
    source_email_id: str
    rationale: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class InboxAutomationResult:
    inbox_lane: str
    applied_label: str
    destination_folder: str
    highlight: str
    auto_actions: list[str]
    notifications: list[str]
    tasks: list[ProductivityTask]
    rationale: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "inbox_lane": self.inbox_lane,
            "applied_label": self.applied_label,
            "destination_folder": self.destination_folder,
            "highlight": self.highlight,
            "auto_actions": self.auto_actions,
            "notifications": self.notifications,
            "tasks": [task.as_dict() for task in self.tasks],
            "rationale": self.rationale,
        }


@dataclass(slots=True)
class EmailAnalysis:
    email: EmailMessage
    classification: ClassificationResult
    risk: RiskAnalysisResult
    decision: DecisionResult
    automation: InboxAutomationResult

    def as_dict(self) -> dict[str, Any]:
        return {
            "email": self.email.as_dict(),
            "classification": self.classification.as_dict(),
            "risk": self.risk.as_dict(),
            "decision": self.decision.as_dict(),
            "automation": self.automation.as_dict(),
        }


@dataclass(slots=True)
class EpisodeResult:
    email: EmailMessage
    analysis: EmailAnalysis
    chosen_action: str
    reward_score: float
    expected_action: str
    success: bool
    notes: str
    reply_sent: bool
    mailbox_folder: str
    applied_label: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "email": self.email.as_dict(),
            "analysis": self.analysis.as_dict(),
            "chosen_action": self.chosen_action,
            "reward_score": self.reward_score,
            "expected_action": self.expected_action,
            "success": self.success,
            "notes": self.notes,
            "reply_sent": self.reply_sent,
            "mailbox_folder": self.mailbox_folder,
            "applied_label": self.applied_label,
        }


@dataclass(slots=True)
class DashboardSnapshot:
    current_email: dict[str, Any] | None
    current_analysis: dict[str, Any] | None
    history: list[dict[str, Any]] = field(default_factory=list)
    analytics: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
