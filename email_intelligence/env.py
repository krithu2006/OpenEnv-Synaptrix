from __future__ import annotations

from itertools import cycle

from email_intelligence.agents import MultiAgentPipeline
from email_intelligence.models import EmailAnalysis, EmailMessage, EpisodeResult


class EmailDecisionEnv:
    def __init__(self, emails: list[EmailMessage]) -> None:
        self._emails = emails
        self._email_cycle = cycle(self._emails)
        self.pipeline = MultiAgentPipeline()
        self.current_email: EmailMessage | None = None
        self.current_analysis: EmailAnalysis | None = None
        self.last_result: EpisodeResult | None = None

    def reset(self, email: EmailMessage | None = None) -> dict:
        self.current_email = email or next(self._email_cycle)
        self.current_analysis = None
        self.last_result = None
        return self.current_email.as_dict()

    def analyze_current(self) -> EmailAnalysis:
        if self.current_email is None:
            self.reset()
        assert self.current_email is not None
        self.current_analysis = self.pipeline.analyze(self.current_email)
        return self.current_analysis

    def step(self, action: str | None = None) -> EpisodeResult:
        analysis = self.current_analysis or self.analyze_current()
        chosen_action = action or analysis.decision.action
        if chosen_action != analysis.decision.action:
            analysis.decision = self.pipeline.decision_agent.override_decision(
                analysis.email,
                analysis.classification,
                analysis.risk,
                chosen_action,
            )
            analysis.automation = self.pipeline.automation_agent.analyze_for_action(
                analysis.email,
                analysis.classification,
                analysis.risk,
                chosen_action,
                analysis.decision,
            )
        expected_action = analysis.email.expected_action or analysis.decision.action
        reward = self._reward(analysis, chosen_action, expected_action)
        success = chosen_action == expected_action
        reply_sent = chosen_action in {"Respond", "Urgent Action"} and analysis.decision.response_needed

        analysis.email.gmail_label = analysis.automation.applied_label
        analysis.email.mailbox_folder = analysis.automation.destination_folder

        if success:
            notes = "Chosen action matches the expected handling pattern for this email."
        elif expected_action == "Urgent Action" and chosen_action == "Ignore":
            notes = "Critical message was ignored, causing the strongest negative reward."
        elif expected_action == "Ignore" and chosen_action != "Ignore":
            notes = "A suspicious or low-value email received unnecessary attention."
        else:
            notes = "Action partially aligns with the email intent but misses the ideal response level."

        result = EpisodeResult(
            email=analysis.email,
            analysis=analysis,
            chosen_action=chosen_action,
            reward_score=reward,
            expected_action=expected_action,
            success=success,
            notes=notes,
            reply_sent=reply_sent,
            mailbox_folder=analysis.automation.destination_folder,
            applied_label=analysis.automation.applied_label,
        )
        self.last_result = result
        return result

    def _reward(self, analysis: EmailAnalysis, action: str, expected_action: str) -> float:
        importance_bonus = analysis.risk.importance_score / 20
        urgency_bonus = analysis.risk.urgency_score / 25

        if action == expected_action:
            return round(min(10.0, 4.0 + importance_bonus + urgency_bonus), 2)
        if expected_action == "Urgent Action" and action == "Ignore":
            return -10.0
        if expected_action == "Urgent Action" and action == "Respond":
            return -4.5
        if expected_action == "Respond" and action == "Ignore":
            return -5.0
        if expected_action == "Ignore" and action in {"Respond", "Urgent Action"}:
            return -4.0 if analysis.classification.category == "Spam" else -2.5
        return -3.0
