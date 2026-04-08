from __future__ import annotations

import json
from collections import Counter
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from email_intelligence.data import load_sample_emails
from email_intelligence.env import EmailDecisionEnv
from email_intelligence.models import DashboardSnapshot, EmailMessage, EpisodeResult


class EmailDecisionPlatform:
    def __init__(self) -> None:
        self.samples = load_sample_emails()
        self.email_index = {email.email_id: email for email in self.samples}
        self.env = EmailDecisionEnv(self.samples)
        self.history: list[EpisodeResult] = []
        self.sent_replies: list[dict[str, Any]] = []
        self.custom_counter = 1
        self.last_event = "System ready."
        self.env.reset()

    def get_snapshot(self) -> dict[str, Any]:
        snapshot = DashboardSnapshot(
            current_email=self._current_email_payload(),
            current_analysis=self.env.current_analysis.as_dict() if self.env.current_analysis else None,
            history=[record.as_dict() for record in reversed(self.history)],
            analytics=self._analytics(),
        )
        return snapshot.as_dict()

    def reset_email(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        custom_email = None
        if payload and any(payload.get(field) for field in ("sender", "subject", "body")):
            custom_email = EmailMessage(
                email_id=f"custom-{self.custom_counter:03d}",
                sender=str(payload.get("sender") or "custom.sender@example.com"),
                subject=str(payload.get("subject") or "Untitled custom email"),
                body=str(payload.get("body") or "No body provided."),
                received_at="Custom submission",
                source="custom",
            )
            self.email_index[custom_email.email_id] = custom_email
            self.custom_counter += 1

        self.env.reset(custom_email)
        self.last_event = "Loaded a new email into the workspace."
        return self.get_snapshot()

    def analyze(self) -> dict[str, Any]:
        analysis = self.env.analyze_current()
        analysis.email.gmail_label = analysis.automation.applied_label
        analysis.email.mailbox_folder = analysis.automation.destination_folder
        self.last_event = f"Analyzed email and routed it to {analysis.automation.destination_folder}."
        return {"analysis": analysis.as_dict(), "snapshot": self.get_snapshot()}

    def apply_action(self, action: str | None = None, use_recommended: bool = False) -> dict[str, Any]:
        chosen_action = None if use_recommended else action
        result = self.env.step(chosen_action)
        self.history.append(result)
        self.last_event = (
            f"Applied {result.chosen_action}. Gmail automation updated to "
            f"{result.applied_label} in {result.mailbox_folder}."
        )
        return {
            "result": result.as_dict(),
            "snapshot": self.get_snapshot(),
        }

    def send_reply(self) -> dict[str, Any]:
        analysis = self.env.current_analysis or self.env.analyze_current()
        if not analysis.decision.response_needed:
            return {
                "sent": False,
                "message": "The current email does not require a reply.",
                "snapshot": self.get_snapshot(),
            }

        reply = {
            "email_id": analysis.email.email_id,
            "recipient": analysis.email.sender,
            "subject": analysis.decision.draft_subject,
            "body": analysis.decision.draft_body,
            "status": "Sent (Simulated)",
        }
        self.sent_replies.append(reply)
        self.last_event = f"Sent simulated reply to {analysis.email.sender}."
        return {
            "sent": True,
            "reply": reply,
            "message": "Auto-reply sent in simulation mode.",
            "snapshot": self.get_snapshot(),
        }

    def open_email(self, email_id: str) -> dict[str, Any]:
        record = next((item for item in reversed(self.history) if item.email.email_id == email_id), None)
        if record:
            self.env.current_email = record.email
            self.env.current_analysis = record.analysis
            self.env.last_result = record
            self.last_event = f"Opened {record.email.subject} from processed history."
            return self.get_snapshot()

        email = self.email_index.get(email_id)
        if not email:
            return self.get_snapshot()

        self.env.reset(email)
        self.env.analyze_current()
        self.last_event = f"Opened {email.subject} in the detail pane."
        return self.get_snapshot()

    def _analytics(self) -> dict[str, Any]:
        total_processed = len(self.history)
        category_counter = Counter()
        risk_counter = Counter()
        action_counter = Counter()
        lane_counter = Counter()
        folder_counter = Counter()
        reward_trend: list[dict[str, Any]] = []
        open_tasks: list[dict[str, Any]] = []
        notifications: list[str] = []

        for record in self.history:
            category_counter[record.analysis.classification.category] += 1
            risk_counter[record.analysis.risk.risk_level] += 1
            action_counter[record.chosen_action] += 1
            lane_counter[record.analysis.automation.inbox_lane] += 1
            folder_counter[record.mailbox_folder] += 1
            open_tasks.extend(task.as_dict() for task in record.analysis.automation.tasks)
            notifications.extend(record.analysis.automation.notifications)

        for index, record in enumerate(self.history[-8:], start=max(total_processed - 7, 1)):
            reward_trend.append({"label": f"E{index}", "reward": record.reward_score})

        success_rate = round(
            (sum(1 for record in self.history if record.success) / total_processed) * 100, 1
        ) if total_processed else 0.0
        average_reward = round(
            sum(record.reward_score for record in self.history) / total_processed, 2
        ) if total_processed else 0.0
        urgent_count = lane_counter.get("Urgent", 0)
        spam_count = category_counter.get("Spam", 0)

        current_analysis = self.env.current_analysis
        smart_inbox = {"Urgent": [], "Important": [], "Others": []}
        for record in reversed(self.history):
            smart_inbox[record.analysis.automation.inbox_lane].append(self._mail_item(record))
        if current_analysis:
            already_recorded = bool(
                self.env.last_result and self.env.last_result.email.email_id == current_analysis.email.email_id
            )
            if not already_recorded:
                smart_inbox[current_analysis.automation.inbox_lane].insert(0, self._mail_item(current_analysis))
                open_tasks = [task.as_dict() for task in current_analysis.automation.tasks] + open_tasks
                notifications = current_analysis.automation.notifications + notifications

        return {
            "total_processed": total_processed,
            "success_rate": success_rate,
            "average_reward": average_reward,
            "emails_handled_today": total_processed,
            "urgent_rate": round((urgent_count / total_processed) * 100, 1) if total_processed else 0.0,
            "spam_rate": round((spam_count / total_processed) * 100, 1) if total_processed else 0.0,
            "auto_replies_sent": len(self.sent_replies),
            "tasks_created": len(open_tasks),
            "category_distribution": dict(category_counter),
            "risk_distribution": dict(risk_counter),
            "action_distribution": dict(action_counter),
            "lane_distribution": dict(lane_counter),
            "folder_distribution": dict(folder_counter),
            "reward_trend": reward_trend,
            "smart_inbox": smart_inbox,
            "tasks": open_tasks[:8],
            "notifications": notifications[-5:][::-1],
            "recent_replies": list(reversed(self.sent_replies[-5:])),
            "last_event": self.last_event,
        }

    def _current_email_payload(self) -> dict[str, Any] | None:
        if not self.env.current_email:
            return None

        payload = self.env.current_email.as_dict()
        if self.env.current_analysis:
            payload["gmail_label"] = self.env.current_analysis.automation.applied_label
            payload["mailbox_folder"] = self.env.current_analysis.automation.destination_folder
        return payload

    def _mail_item(self, source: EpisodeResult | Any) -> dict[str, Any]:
        if isinstance(source, EpisodeResult):
            email = source.email
            analysis = source.analysis
            processed = True
        else:
            email = source.email
            analysis = source
            processed = False

        return {
            "email_id": email.email_id,
            "sender": email.sender,
            "subject": email.subject,
            "preview": f"{email.body[:108]}..." if len(email.body) > 108 else email.body,
            "received_at": email.received_at,
            "lane": analysis.automation.inbox_lane,
            "label": analysis.automation.applied_label,
            "folder": analysis.automation.destination_folder,
            "priority": analysis.risk.priority,
            "action": analysis.decision.action,
            "processed": processed,
        }


class EmailRequestHandler(BaseHTTPRequestHandler):
    platform = EmailDecisionPlatform()
    static_dir = Path(__file__).resolve().parent.parent / "static"

    def do_GET(self) -> None:
        route = self.path.split("?", 1)[0]
        if route in {"/", "/index.html"}:
            self._serve_file("index.html", "text/html; charset=utf-8")
            return
        if route == "/api/state":
            self._send_json(self.platform.get_snapshot())
            return
        static_path = self.static_dir / route.lstrip("/")
        if static_path.exists() and static_path.is_file():
            content_type = {
                ".html": "text/html; charset=utf-8",
                ".css": "text/css; charset=utf-8",
                ".js": "application/javascript; charset=utf-8",
            }.get(static_path.suffix, "application/octet-stream")
            self._serve_file(static_path.name, content_type)
            return
        self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        route = self.path.split("?", 1)[0]
        if route == "/api/reset":
            payload = self._read_json()
            self._send_json(self.platform.reset_email(payload))
            return
        if route == "/api/analyze":
            self._send_json(self.platform.analyze())
            return
        if route == "/api/step":
            payload = self._read_json() or {}
            action = payload.get("action")
            use_recommended = bool(payload.get("use_recommended"))
            self._send_json(self.platform.apply_action(action=action, use_recommended=use_recommended))
            return
        if route == "/api/open-email":
            payload = self._read_json() or {}
            self._send_json(self.platform.open_email(str(payload.get("email_id") or "")))
            return
        if route == "/api/send-reply":
            self._send_json(self.platform.send_reply())
            return
        self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)

    def log_message(self, format: str, *args: object) -> None:
        return

    def _read_json(self) -> dict[str, Any] | None:
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length == 0:
            return None
        raw = self.rfile.read(content_length).decode("utf-8")
        return json.loads(raw)

    def _serve_file(self, filename: str, content_type: str) -> None:
        path = self.static_dir / filename
        if not path.exists():
            self._send_json({"error": "Missing static file"}, status=HTTPStatus.NOT_FOUND)
            return
        data = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()
        self.wfile.write(data)


def run_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), EmailRequestHandler)
    print(f"Email Decision Intelligence server running at http://{host}:{port}")
    server.serve_forever()
