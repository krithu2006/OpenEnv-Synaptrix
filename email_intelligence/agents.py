from __future__ import annotations

import re
from collections import Counter

from email_intelligence.models import (
    ClassificationResult,
    DecisionResult,
    EmailAnalysis,
    EmailMessage,
    InboxAutomationResult,
    ProductivityTask,
    RiskAnalysisResult,
)


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z']+", text.lower())


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


class ClassificationAgent:
    work_keywords = {
        "approval",
        "budget",
        "client",
        "contract",
        "credentials",
        "deadline",
        "draft",
        "finance",
        "investor",
        "launch",
        "legal",
        "meeting",
        "metrics",
        "mitigation",
        "project",
        "report",
        "review",
        "schedule",
        "security",
        "shipment",
        "team",
        "update",
        "workspace",
    }
    personal_keywords = {
        "birthday",
        "cafe",
        "call",
        "dad",
        "dinner",
        "doctor",
        "family",
        "friend",
        "friday",
        "mom",
        "photos",
        "place",
        "reunion",
        "trip",
        "weekend",
    }
    spam_keywords = {
        "act",
        "bonus",
        "claim",
        "click",
        "congratulations",
        "exclusive",
        "free",
        "limited",
        "lottery",
        "offer",
        "payment",
        "pricing",
        "reward",
        "sale",
        "selected",
        "unlock",
        "vip",
        "wallet",
        "winnings",
    }

    def analyze(self, email: EmailMessage) -> ClassificationResult:
        tokens = _tokenize(f"{email.subject} {email.body}")
        counts = Counter(tokens)

        work_score = sum(counts[token] * 1.2 for token in self.work_keywords if token in counts)
        personal_score = sum(counts[token] * 1.1 for token in self.personal_keywords if token in counts)
        spam_score = sum(counts[token] * 1.5 for token in self.spam_keywords if token in counts)

        sender = email.sender.lower()
        if any(marker in sender for marker in ("promo", "winner", "noreply", "offer", "deal")):
            spam_score += 2.5
        if any(marker in sender for marker in ("family", "friends", "mom", "dad")):
            personal_score += 1.8
        if any(marker in sender for marker in ("ops", "security", "client", "team", "legal")):
            work_score += 1.8

        scores = {"Work": work_score, "Personal": personal_score, "Spam": spam_score}
        category = max(scores, key=scores.get)

        ordered_scores = sorted(scores.values(), reverse=True)
        top_score = ordered_scores[0]
        second_score = ordered_scores[1] if len(ordered_scores) > 1 else 0.0
        confidence = _clamp(0.58 + ((top_score - second_score) / max(top_score + 1, 1)) * 0.35, 0.55, 0.97)

        rationale = {
            "Work": "Detected operational, deadline, or business coordination language.",
            "Personal": "Detected relationship-oriented and informal personal communication cues.",
            "Spam": "Detected promotional or manipulative language with suspicious call-to-action patterns.",
        }[category]

        return ClassificationResult(
            category=category,
            confidence=round(confidence, 2),
            rationale=rationale,
            category_scores={name: round(score, 2) for name, score in scores.items()},
        )


class RiskAnalysisAgent:
    urgency_weights = {
        "asap": 26,
        "before": 18,
        "deadline": 26,
        "detected": 16,
        "eod": 28,
        "expires": 20,
        "immediately": 30,
        "impact": 18,
        "incident": 32,
        "launch": 22,
        "now": 16,
        "today": 18,
        "tomorrow": 10,
        "unusual": 18,
        "urgent": 32,
    }
    importance_weights = {
        "approval": 26,
        "client": 18,
        "contract": 26,
        "credentials": 28,
        "doctor": 18,
        "finance": 22,
        "investor": 22,
        "legal": 22,
        "meeting": 14,
        "metrics": 12,
        "mitigation": 18,
        "report": 16,
        "review": 14,
        "security": 30,
        "shipment": 18,
    }
    spam_markers = {
        "act": 14,
        "bonus": 18,
        "claim": 25,
        "click": 24,
        "congratulations": 18,
        "exclusive": 15,
        "free": 18,
        "limited": 18,
        "offer": 20,
        "payment": 16,
        "reward": 24,
        "selected": 20,
        "unlock": 16,
        "vip": 15,
        "wallet": 16,
        "winnings": 24,
    }

    def analyze(self, email: EmailMessage, classification: ClassificationResult) -> RiskAnalysisResult:
        tokens = _tokenize(f"{email.subject} {email.body}")
        counts = Counter(tokens)
        subject_lower = email.subject.lower()
        body_lower = email.body.lower()

        urgency_score = sum(
            counts[token] * weight for token, weight in self.urgency_weights.items() if token in counts
        )
        importance_score = sum(
            counts[token] * weight for token, weight in self.importance_weights.items() if token in counts
        )
        spam_risk_score = sum(
            counts[token] * weight for token, weight in self.spam_markers.items() if token in counts
        )

        if "?" in email.subject or "?" in email.body:
            importance_score += 8
        if any(marker in body_lower for marker in ("click", "verify", "submit payment", "claim")):
            spam_risk_score += 20
        if any(marker in subject_lower for marker in ("security", "approval", "delay", "detected")):
            urgency_score += 12
            importance_score += 10
        if classification.category == "Work":
            importance_score += 12
        if classification.category == "Personal":
            importance_score += 8
        if classification.category == "Spam":
            spam_risk_score += 18

        urgency_score = max(0, min(100, urgency_score))
        importance_score = max(0, min(100, importance_score))
        spam_risk_score = max(0, min(100, spam_risk_score))

        if urgency_score >= 80 or (urgency_score >= 60 and importance_score >= 60):
            priority = "Critical"
        elif urgency_score >= 55 or importance_score >= 68:
            priority = "High"
        elif urgency_score >= 30 or importance_score >= 35:
            priority = "Medium"
        else:
            priority = "Low"

        if priority == "Critical" or spam_risk_score >= 75 or (
            classification.category == "Spam" and spam_risk_score >= 50
        ):
            risk_level = "High"
        elif urgency_score >= 65 or spam_risk_score >= 45:
            risk_level = "Medium"
        else:
            risk_level = "Low"

        tone = "Neutral"
        if classification.category == "Spam":
            tone = "Manipulative"
        elif urgency_score >= 65:
            tone = "Urgent"
        elif any(marker in body_lower for marker in ("hi", "hey", "favorite", "photos", "dinner")):
            tone = "Friendly"
        elif classification.category == "Work":
            tone = "Professional"

        rationale_parts = [
            f"Priority set to {priority} from importance {importance_score} and urgency {urgency_score}.",
            f"Spam risk scored {spam_risk_score} based on promotional and sender cues.",
            f"Tone inferred as {tone.lower()} from wording patterns.",
        ]

        threat_indicators: list[str] = []
        if any(marker in body_lower for marker in ("click", "verify", "submit payment", "claim")):
            threat_indicators.append("Suspicious call-to-action detected")
        if any(marker in subject_lower for marker in ("detected", "unusual", "urgent", "expires")):
            threat_indicators.append("High-pressure or security language detected")
        if classification.category == "Spam" or spam_risk_score >= 60:
            threat_indicators.append("Potential spam/phishing pattern")
        if not threat_indicators:
            threat_indicators.append("No major threat indicators")

        return RiskAnalysisResult(
            priority=priority,
            tone=tone,
            risk_level=risk_level,
            importance_score=importance_score,
            urgency_score=urgency_score,
            spam_risk_score=spam_risk_score,
            threat_indicators=threat_indicators,
            rationale=" ".join(rationale_parts),
        )


class DecisionAgent:
    def _response_window(self, action: str, risk: RiskAnalysisResult) -> str:
        if action == "Urgent Action":
            return "Respond within 15 minutes"
        if action == "Respond" and risk.priority in {"High", "Critical"}:
            return "Respond within 1 hour"
        if action == "Respond":
            return "Respond today"
        return "No response required"

    def analyze(
        self,
        email: EmailMessage,
        classification: ClassificationResult,
        risk: RiskAnalysisResult,
    ) -> DecisionResult:
        body_lower = email.body.lower()

        if classification.category == "Spam" or risk.spam_risk_score >= 70:
            action = "Ignore"
            rationale = "High spam likelihood or promotional manipulation indicates no response is needed."
        elif risk.priority == "Critical" or risk.urgency_score >= 75:
            action = "Urgent Action"
            rationale = "Critical timing or high operational impact requires immediate attention."
        elif any(marker in body_lower for marker in ("please", "let me know", "can you", "reply")):
            action = "Respond"
            rationale = "The email contains a direct request and should receive a reply."
        elif classification.category == "Personal":
            action = "Respond"
            rationale = "Personal coordination email likely benefits from acknowledgment."
        elif risk.importance_score >= 45:
            action = "Respond"
            rationale = "Meaningful business context suggests a normal response is appropriate."
        else:
            action = "Ignore"
            rationale = "Low-impact content does not justify a response at this time."

        confidence = 55
        confidence += int(classification.confidence * 15)
        confidence += int(risk.importance_score * 0.18)
        confidence += int(risk.urgency_score * 0.12)
        confidence -= int(risk.spam_risk_score * 0.08)
        confidence_score = max(45, min(98, confidence))

        if action == "Ignore":
            reply_suggestion = "No reply suggested. Archive, monitor, or mark as spam based on your policy."
            draft_subject = f"Re: {email.subject}"
            draft_body = "No reply draft generated because the email does not require a response."
        elif action == "Urgent Action":
            reply_suggestion = (
                "Acknowledge immediately, summarize the risk, confirm next action, and give a concrete timeline."
            )
            draft_subject = f"Re: {email.subject} - Action underway"
            draft_body = (
                f"Hi,\n\nI have reviewed your email regarding \"{email.subject}\" and I am treating it as urgent. "
                "I am taking action now and will share the next update shortly.\n\nBest regards,"
            )
        elif classification.category == "Work":
            reply_suggestion = (
                "Thanks for the update. I have reviewed the request and will take action shortly. "
                "I will share the next steps and timing in my follow-up."
            )
            draft_subject = f"Re: {email.subject}"
            draft_body = (
                f"Hi,\n\nThank you for the update on \"{email.subject}\". I have reviewed the request and "
                "will follow up with the next steps shortly.\n\nBest regards,"
            )
        else:
            reply_suggestion = (
                "Thanks for reaching out. I saw your message and will get back to you with a clear answer soon."
            )
            draft_subject = f"Re: {email.subject}"
            draft_body = (
                "Hi,\n\nThanks for reaching out. I saw your message and wanted to let you know I will respond "
                "with more detail soon.\n\nBest,"
            )

        return DecisionResult(
            action=action,
            response_needed=action in {"Respond", "Urgent Action"},
            confidence_score=confidence_score,
            response_window=self._response_window(action, risk),
            reply_suggestion=reply_suggestion,
            draft_subject=draft_subject,
            draft_body=draft_body,
            rationale=rationale,
        )

    def override_decision(
        self,
        email: EmailMessage,
        classification: ClassificationResult,
        risk: RiskAnalysisResult,
        chosen_action: str,
    ) -> DecisionResult:
        if chosen_action == "Ignore":
            reply_suggestion = "Operator chose to ignore this email. Monitor or archive it without replying."
            draft_subject = f"Re: {email.subject}"
            draft_body = "No reply draft generated because the operator selected Ignore."
            rationale = "Manual override applied by the user to ignore this message."
        elif chosen_action == "Urgent Action":
            reply_suggestion = "Operator escalated this email for urgent handling and immediate acknowledgment."
            draft_subject = f"Re: {email.subject} - Escalated"
            draft_body = (
                f"Hi,\n\nI have escalated \"{email.subject}\" for urgent handling and I am acting on it now. "
                "I will send the next update shortly.\n\nBest regards,"
            )
            rationale = "Manual override applied by the user to escalate this message as urgent."
        else:
            reply_suggestion = "Operator marked this email for reply and follow-up."
            draft_subject = f"Re: {email.subject}"
            draft_body = (
                f"Hi,\n\nI reviewed \"{email.subject}\" and I am following up now. "
                "I will share the requested update shortly.\n\nBest regards,"
            )
            rationale = "Manual override applied by the user to send a reply."

        return DecisionResult(
            action=chosen_action,
            response_needed=chosen_action in {"Respond", "Urgent Action"},
            confidence_score=96,
            response_window=self._response_window(chosen_action, risk),
            reply_suggestion=reply_suggestion,
            draft_subject=draft_subject,
            draft_body=draft_body,
            rationale=rationale,
        )


class InboxAutomationAgent:
    task_patterns = [
        (re.compile(r"\bmeeting at (\d{1,2}(?::\d{2})?\s?(?:am|pm))\b", re.IGNORECASE), "Attend meeting", "Today"),
        (re.compile(r"\bbefore (\d{1,2}(?::\d{2})?\s?(?:am|pm))\b", re.IGNORECASE), "Complete requested action", "Before deadline"),
        (re.compile(r"\btomorrow\b", re.IGNORECASE), "Prepare follow-up for tomorrow", "Tomorrow"),
        (re.compile(r"\btoday\b", re.IGNORECASE), "Handle today's request", "Today"),
    ]

    def analyze(
        self,
        email: EmailMessage,
        classification: ClassificationResult,
        risk: RiskAnalysisResult,
        decision: DecisionResult,
    ) -> InboxAutomationResult:
        if classification.category == "Spam" or risk.spam_risk_score >= 70:
            inbox_lane = "Others"
            applied_label = "Spam Risk"
            destination_folder = "Spam"
            highlight = "Spam candidate quarantined"
            auto_actions = ["Auto-apply label", "Move to Spam folder"]
        elif decision.action == "Urgent Action" or risk.priority == "Critical":
            inbox_lane = "Urgent"
            applied_label = "Urgent Action"
            destination_folder = "Priority Inbox"
            highlight = "Urgent email highlighted"
            auto_actions = ["Auto-apply label", "Highlight urgent", "Pin to top"]
        elif decision.action == "Respond" or risk.priority == "High":
            inbox_lane = "Important"
            applied_label = "Needs Reply"
            destination_folder = "Inbox"
            highlight = "Response recommended"
            auto_actions = ["Auto-apply label", "Add to Important tab"]
        else:
            inbox_lane = "Others"
            applied_label = "Monitor"
            destination_folder = "Archive Queue"
            highlight = "Low-priority email organized"
            auto_actions = ["Auto-apply label", "Queue for later review"]

        notifications: list[str] = []
        if destination_folder == "Spam":
            notifications.append("Suspicious email moved to Spam")
        if inbox_lane == "Urgent":
            notifications.append("Urgent email detected")
        if decision.response_needed:
            notifications.append("Action required")

        tasks = self._extract_tasks(email, decision, classification)
        if tasks:
            notifications.append("Task generated from email")

        rationale = (
            f"Placed in {inbox_lane} lane, labeled '{applied_label}', and routed to {destination_folder} "
            f"based on decision {decision.action}, priority {risk.priority}, and spam risk {risk.spam_risk_score}."
        )

        return InboxAutomationResult(
            inbox_lane=inbox_lane,
            applied_label=applied_label,
            destination_folder=destination_folder,
            highlight=highlight,
            auto_actions=auto_actions,
            notifications=notifications,
            tasks=tasks,
            rationale=rationale,
        )

    def analyze_for_action(
        self,
        email: EmailMessage,
        classification: ClassificationResult,
        risk: RiskAnalysisResult,
        action: str,
        decision: DecisionResult,
    ) -> InboxAutomationResult:
        if action == "Urgent Action":
            inbox_lane = "Urgent"
            applied_label = "Urgent Action"
            destination_folder = "Priority Inbox"
            highlight = "Urgent email highlighted by manual override"
            auto_actions = ["Manual override", "Highlight urgent", "Pin to top"]
        elif action == "Respond":
            inbox_lane = "Important"
            applied_label = "Needs Reply"
            destination_folder = "Inbox"
            highlight = "Response recommended by manual override"
            auto_actions = ["Manual override", "Add to Important tab"]
        else:
            inbox_lane = "Others"
            if classification.category == "Spam" or risk.spam_risk_score >= 70:
                applied_label = "Spam Risk"
                destination_folder = "Spam"
                highlight = "Spam candidate quarantined by manual override"
                auto_actions = ["Manual override", "Move to Spam folder"]
            else:
                applied_label = "Monitor"
                destination_folder = "Archive Queue"
                highlight = "Low-priority email organized by manual override"
                auto_actions = ["Manual override", "Queue for later review"]

        notifications: list[str] = []
        if destination_folder == "Spam":
            notifications.append("Suspicious email moved to Spam")
        if inbox_lane == "Urgent":
            notifications.append("Urgent email detected")
        if decision.response_needed:
            notifications.append("Action required")

        tasks = self._extract_tasks(email, decision, classification)
        if tasks:
            notifications.append("Task generated from email")

        rationale = (
            f"Manual override routed the email to {destination_folder} with label '{applied_label}' "
            f"and inbox lane {inbox_lane}."
        )

        return InboxAutomationResult(
            inbox_lane=inbox_lane,
            applied_label=applied_label,
            destination_folder=destination_folder,
            highlight=highlight,
            auto_actions=auto_actions,
            notifications=notifications,
            tasks=tasks,
            rationale=rationale,
        )

    def _extract_tasks(
        self,
        email: EmailMessage,
        decision: DecisionResult,
        classification: ClassificationResult,
    ) -> list[ProductivityTask]:
        combined = f"{email.subject} {email.body}"
        tasks: list[ProductivityTask] = []

        for pattern, title, due_hint in self.task_patterns:
            if pattern.search(combined):
                tasks.append(
                    ProductivityTask(
                        title=title,
                        due_hint=due_hint,
                        status="Open",
                        source_email_id=email.email_id,
                        rationale=f"Generated from time-sensitive wording in '{email.subject}'.",
                    )
                )
                break

        if not tasks and decision.response_needed and classification.category != "Spam":
            tasks.append(
                ProductivityTask(
                    title=f"Reply to: {email.subject[:42]}",
                    due_hint="Soon",
                    status="Open",
                    source_email_id=email.email_id,
                    rationale="Generated because the decision layer marked the email as requiring a response.",
                )
            )

        return tasks


class MultiAgentPipeline:
    def __init__(self) -> None:
        self.classifier = ClassificationAgent()
        self.risk_agent = RiskAnalysisAgent()
        self.decision_agent = DecisionAgent()
        self.automation_agent = InboxAutomationAgent()

    def analyze(self, email: EmailMessage) -> EmailAnalysis:
        classification = self.classifier.analyze(email)
        risk = self.risk_agent.analyze(email, classification)
        decision = self.decision_agent.analyze(email, classification, risk)
        automation = self.automation_agent.analyze(email, classification, risk, decision)
        return EmailAnalysis(
            email=email,
            classification=classification,
            risk=risk,
            decision=decision,
            automation=automation,
        )
