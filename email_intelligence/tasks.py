from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass

from email_intelligence.data import load_sample_emails
from email_intelligence.models import EmailMessage


@dataclass(frozen=True, slots=True)
class BenchmarkTask:
    task_id: str
    difficulty: str
    title: str
    objective: str
    email: EmailMessage
    expected_category: str
    expected_priority: str
    expected_risk_level: str
    expected_action: str
    expected_label: str
    expected_folder: str
    expected_lane: str
    response_required: bool
    response_keywords: tuple[str, ...]

    def fresh_email(self) -> EmailMessage:
        return deepcopy(self.email)


def load_benchmark_tasks() -> list[BenchmarkTask]:
    sample_index = {email.email_id: email for email in load_sample_emails()}

    return [
        BenchmarkTask(
            task_id="easy-spam-ignore",
            difficulty="easy",
            title="Filter an obvious spam email",
            objective=(
                "Identify a clearly malicious promotional email, avoid engaging with it, "
                "and route it safely into spam."
            ),
            email=sample_index["sample-002"],
            expected_category="Spam",
            expected_priority="Medium",
            expected_risk_level="High",
            expected_action="Ignore",
            expected_label="Spam Risk",
            expected_folder="Spam",
            expected_lane="Others",
            response_required=False,
            response_keywords=("spam", "ignore", "no reply"),
        ),
        BenchmarkTask(
            task_id="medium-reply-scheduling",
            difficulty="medium",
            title="Reply to a personal scheduling request",
            objective=(
                "Recognize a legitimate personal coordination email, keep it in the main inbox, "
                "and prepare a normal response."
            ),
            email=sample_index["sample-008"],
            expected_category="Personal",
            expected_priority="Low",
            expected_risk_level="Low",
            expected_action="Respond",
            expected_label="Needs Reply",
            expected_folder="Inbox",
            expected_lane="Important",
            response_required=True,
            response_keywords=("doctor", "meeting", "reply", "tomorrow"),
        ),
        BenchmarkTask(
            task_id="hard-security-escalation",
            difficulty="hard",
            title="Escalate a critical security incident",
            objective=(
                "Detect a high-risk operational email, escalate it immediately, and route it "
                "into the urgent workflow with a clear response plan."
            ),
            email=sample_index["sample-004"],
            expected_category="Work",
            expected_priority="Critical",
            expected_risk_level="High",
            expected_action="Urgent Action",
            expected_label="Urgent Action",
            expected_folder="Priority Inbox",
            expected_lane="Urgent",
            response_required=True,
            response_keywords=("urgent", "security", "credentials", "action"),
        ),
    ]
