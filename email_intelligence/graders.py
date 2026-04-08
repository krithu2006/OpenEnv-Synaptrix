from __future__ import annotations

from typing import Any

from email_intelligence.tasks import BenchmarkTask


PRIORITY_LEVELS = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}
RISK_LEVELS = {"Low": 0, "Medium": 1, "High": 2}


def _clean(value: str | None) -> str:
    return (value or "").strip().lower()


def _exact_score(actual: str | None, expected: str, weight: float) -> float:
    return weight if _clean(actual) == _clean(expected) else 0.0


def _ordered_score(actual: str | None, expected: str, weight: float, mapping: dict[str, int]) -> float:
    if not actual:
        return 0.0
    actual_key = actual.strip().title()
    expected_key = expected.strip().title()
    if actual_key not in mapping or expected_key not in mapping:
        return 0.0
    delta = abs(mapping[actual_key] - mapping[expected_key])
    if delta == 0:
        return weight
    if delta == 1:
        return round(weight * 0.5, 4)
    return 0.0


def grade_triage(task: BenchmarkTask, action: dict[str, Any]) -> dict[str, Any]:
    components = {
        "category": round(_exact_score(action.get("predicted_category"), task.expected_category, 0.20), 4),
        "priority": round(_ordered_score(action.get("predicted_priority"), task.expected_priority, 0.15, PRIORITY_LEVELS), 4),
        "risk_level": round(_ordered_score(action.get("predicted_risk_level"), task.expected_risk_level, 0.10, RISK_LEVELS), 4),
    }
    feedback = [
        f"Category target: {task.expected_category}",
        f"Priority target: {task.expected_priority}",
        f"Risk target: {task.expected_risk_level}",
    ]
    return {
        "score": round(sum(components.values()), 4),
        "components": components,
        "feedback": feedback,
        "rubric": {"category": 0.20, "priority": 0.15, "risk_level": 0.10},
    }


def grade_routing(task: BenchmarkTask, action: dict[str, Any]) -> dict[str, Any]:
    components = {
        "selected_action": round(_exact_score(action.get("selected_action"), task.expected_action, 0.25), 4),
        "inbox_lane": round(_exact_score(action.get("inbox_lane"), task.expected_lane, 0.10), 4),
        "destination_folder": round(_exact_score(action.get("destination_folder"), task.expected_folder, 0.05), 4),
        "applied_label": round(_exact_score(action.get("applied_label"), task.expected_label, 0.05), 4),
    }
    feedback = [
        f"Action target: {task.expected_action}",
        f"Lane target: {task.expected_lane}",
        f"Folder target: {task.expected_folder}",
        f"Label target: {task.expected_label}",
    ]
    return {
        "score": round(sum(components.values()), 4),
        "components": components,
        "feedback": feedback,
        "rubric": {
            "selected_action": 0.25,
            "inbox_lane": 0.10,
            "destination_folder": 0.05,
            "applied_label": 0.05,
        },
    }


def grade_response(task: BenchmarkTask, action: dict[str, Any]) -> dict[str, Any]:
    send_reply = bool(action.get("send_reply"))
    summary = _clean(action.get("response_summary"))

    components = {
        "send_reply": 0.0,
        "response_summary": 0.0,
    }

    if task.response_required:
        components["send_reply"] = 0.05 if send_reply else 0.0
        keyword_hits = sum(1 for keyword in task.response_keywords if keyword in summary)
        components["response_summary"] = round(min(0.05, keyword_hits * 0.0125), 4)
    else:
        if not send_reply:
            components["send_reply"] = 0.05
        if any(keyword in summary for keyword in task.response_keywords):
            components["response_summary"] = 0.05

    feedback = [
        f"Reply required: {'yes' if task.response_required else 'no'}",
        f"Helpful keywords: {', '.join(task.response_keywords)}",
    ]
    return {
        "score": round(sum(components.values()), 4),
        "components": components,
        "feedback": feedback,
        "rubric": {"send_reply": 0.05, "response_summary": 0.05},
    }
