from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from email_intelligence.openenv_env import OpenEnvEmailEnvironment
from email_intelligence.openenv_models import (
    Action,
    EnvironmentMetadata,
    EnvironmentState,
    Observation,
    SchemaResponse,
    StepResult,
)
from email_intelligence.service import EmailDecisionPlatform


app = FastAPI(
    title="Synaptrix MailOS OpenEnv",
    version="0.1.0",
    description="Submission-ready OpenEnv runtime and UI for AI-powered email decision intelligence.",
)

runtime_env = OpenEnvEmailEnvironment()
ui_platform = EmailDecisionPlatform()
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metadata", response_model=EnvironmentMetadata)
def metadata() -> EnvironmentMetadata:
    return runtime_env.metadata()


@app.get("/schema", response_model=SchemaResponse)
def schema() -> SchemaResponse:
    return runtime_env.schema()


@app.get("/tasks")
def tasks() -> dict[str, Any]:
    return {"tasks": [task.model_dump() for task in runtime_env.list_tasks()]}


@app.post("/reset", response_model=Observation)
def reset(
    task_id: str | None = Query(default=None),
    difficulty: str | None = Query(default=None),
) -> Observation:
    return runtime_env.reset(task_id=task_id, difficulty=difficulty)


@app.post("/step", response_model=StepResult)
def step(action: Action) -> StepResult:
    return runtime_env.step(action)


@app.get("/state", response_model=EnvironmentState)
def state() -> EnvironmentState:
    return runtime_env.state()


@app.get("/api/state")
def ui_state() -> dict[str, Any]:
    return ui_platform.get_snapshot()


@app.post("/api/reset")
def ui_reset(payload: dict[str, Any] | None = Body(default=None)) -> dict[str, Any]:
    return ui_platform.reset_email(payload)


@app.post("/api/analyze")
def ui_analyze() -> dict[str, Any]:
    return ui_platform.analyze()


@app.post("/api/step")
def ui_step(payload: dict[str, Any] | None = Body(default=None)) -> dict[str, Any]:
    payload = payload or {}
    return ui_platform.apply_action(
        action=payload.get("action"),
        use_recommended=bool(payload.get("use_recommended")),
    )


@app.post("/api/open-email")
def ui_open_email(payload: dict[str, Any] | None = Body(default=None)) -> dict[str, Any]:
    payload = payload or {}
    return ui_platform.open_email(str(payload.get("email_id") or ""))


@app.post("/api/send-reply")
def ui_send_reply() -> dict[str, Any]:
    return ui_platform.send_reply()


@app.get("/")
def root() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/index.html")
def index_html() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/{page_name}.html")
def html_pages(page_name: str) -> FileResponse:
    path = STATIC_DIR / f"{page_name}.html"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Page not found")
    return FileResponse(path)


app.mount("/", StaticFiles(directory=STATIC_DIR, html=False), name="static")
