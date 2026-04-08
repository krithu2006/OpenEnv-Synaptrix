from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib import request

from openai import OpenAI


BASE_URL = os.getenv("OPENENV_BASE_URL", "http://127.0.0.1:8000")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
OPENAI_SEED = int(os.getenv("OPENAI_SEED", "7"))
OUTPUT_PATH = Path("baseline_scores.json")
_LOCAL_CLIENT = None


@dataclass(slots=True)
class BaselineResult:
    task_id: str
    difficulty: str
    score: float
    driver: str


def _http_json(path: str, method: str = "GET", payload: dict[str, Any] | None = None) -> dict[str, Any]:
    url = f"{BASE_URL}{path}"
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError):
        return _local_json(path, method=method, payload=payload)


def _local_json(path: str, method: str = "GET", payload: dict[str, Any] | None = None) -> dict[str, Any]:
    global _LOCAL_CLIENT
    if _LOCAL_CLIENT is None:
        from fastapi.testclient import TestClient

        from email_intelligence.api import app

        _LOCAL_CLIENT = TestClient(app)

    if method == "POST":
        response = _LOCAL_CLIENT.post(path, json=payload)
    else:
        response = _LOCAL_CLIENT.get(path)
    response.raise_for_status()
    return response.json()


def _extract_json(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        return json.loads(stripped)
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("Model response did not contain JSON")
    return json.loads(stripped[start : end + 1])


def _reference_action(observation: dict[str, Any]) -> dict[str, Any]:
    task_id = observation["task_id"]
    phase = observation["phase"]
    reference = {
        "easy-spam-ignore": {
            "triage": {"predicted_category": "Spam", "predicted_priority": "Medium", "predicted_risk_level": "High"},
            "routing": {
                "selected_action": "Ignore",
                "applied_label": "Spam Risk",
                "destination_folder": "Spam",
                "inbox_lane": "Others",
            },
            "response": {"send_reply": False, "response_summary": "Spam detected, ignore with no reply."},
        },
        "medium-reply-scheduling": {
            "triage": {"predicted_category": "Personal", "predicted_priority": "Low", "predicted_risk_level": "Low"},
            "routing": {
                "selected_action": "Respond",
                "applied_label": "Needs Reply",
                "destination_folder": "Inbox",
                "inbox_lane": "Important",
            },
            "response": {"send_reply": True, "response_summary": "Reply about the doctor meeting tomorrow."},
        },
        "hard-security-escalation": {
            "triage": {"predicted_category": "Work", "predicted_priority": "Critical", "predicted_risk_level": "High"},
            "routing": {
                "selected_action": "Urgent Action",
                "applied_label": "Urgent Action",
                "destination_folder": "Priority Inbox",
                "inbox_lane": "Urgent",
            },
            "response": {"send_reply": True, "response_summary": "Urgent security action underway, credentials under review."},
        },
    }
    return reference[task_id][phase]


def _build_messages(observation: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are an evaluation baseline for an OpenEnv email triage environment. "
                "Return JSON only. Use only the fields relevant to the current phase."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "objective": observation["objective"],
                    "phase": observation["phase"],
                    "instructions": observation["instructions"],
                    "available_actions": observation["available_actions"],
                    "email": observation["email"],
                },
                indent=2,
            ),
        },
    ]


def _model_action(client: OpenAI | None, observation: dict[str, Any]) -> tuple[dict[str, Any], str]:
    if client is None:
        return _reference_action(observation), "reference-policy"

    request_payload = {
        "model": OPENAI_MODEL,
        "temperature": 0,
        "seed": OPENAI_SEED,
        "response_format": {"type": "json_object"},
        "messages": _build_messages(observation),
    }
    try:
        response = client.chat.completions.create(**request_payload)
    except TypeError:
        request_payload.pop("seed", None)
        response = client.chat.completions.create(**request_payload)
    content = response.choices[0].message.content or "{}"
    return _extract_json(content), f"openai:{OPENAI_MODEL}"


def run_task(client: OpenAI | None, task_id: str, difficulty: str) -> BaselineResult:
    observation = _http_json(f"/reset?task_id={task_id}", method="POST")
    driver = "reference-policy"
    final_score = 0.0

    while True:
        action, driver = _model_action(client, observation)
        result = _http_json("/step", method="POST", payload=action)
        final_score = result["info"]["accumulated_reward"]
        if result["done"]:
            return BaselineResult(task_id=task_id, difficulty=difficulty, score=final_score, driver=driver)
        observation = result["observation"]


def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key) if api_key else None
    tasks = _http_json("/tasks")["tasks"]
    results = [run_task(client, task["task_id"], task["difficulty"]) for task in tasks]

    average = round(sum(item.score for item in results) / max(len(results), 1), 4)
    payload = {
        "driver": results[0].driver if results else "reference-policy",
        "average_score": average,
        "tasks": [
            {
                "task_id": item.task_id,
                "difficulty": item.difficulty,
                "score": item.score,
                "driver": item.driver,
            }
            for item in results
        ],
    }
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(json.dumps(payload, indent=2))
    print(f"\nSaved baseline report to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
