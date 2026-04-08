from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


Difficulty = Literal["easy", "medium", "hard"]
Phase = Literal["triage", "routing", "response", "completed"]
Category = Literal["Work", "Personal", "Spam"]
Priority = Literal["Low", "Medium", "High", "Critical"]
RiskLevel = Literal["Low", "Medium", "High"]
DecisionAction = Literal["Ignore", "Respond", "Urgent Action"]
InboxLane = Literal["Urgent", "Important", "Others"]


class EmailEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email_id: str
    sender: str
    subject: str
    body: str
    received_at: str


class BenchmarkTaskCard(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: str
    difficulty: Difficulty
    title: str
    objective: str
    email_id: str


class Observation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    episode_id: str
    task_id: str
    difficulty: Difficulty
    phase: Phase
    step_number: int = Field(ge=1)
    max_steps: int = Field(default=3, ge=1)
    objective: str
    instructions: str
    email: EmailEnvelope
    available_actions: list[str]
    accumulated_reward: float = Field(default=0.0, ge=0.0, le=1.0)


class Action(BaseModel):
    model_config = ConfigDict(extra="forbid")

    predicted_category: Category | None = None
    predicted_priority: Priority | None = None
    predicted_risk_level: RiskLevel | None = None
    selected_action: DecisionAction | None = None
    applied_label: str | None = None
    destination_folder: str | None = None
    inbox_lane: InboxLane | None = None
    send_reply: bool | None = None
    response_summary: str | None = None
    reasoning: str | None = None


class Reward(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phase: Phase
    score: float = Field(ge=0.0, le=1.0)
    components: dict[str, float]
    feedback: list[str]
    rubric: dict[str, float]


class PhaseResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phase: Phase
    submitted_action: dict[str, Any]
    reward: Reward


class StepInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: str
    difficulty: Difficulty
    phase_completed: Phase
    remaining_steps: int = Field(ge=0)
    accumulated_reward: float = Field(ge=0.0, le=1.0)
    notes: str


class StepResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    observation: Observation
    reward: Reward
    done: bool
    info: StepInfo


class EnvironmentState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    episode_id: str | None = None
    task_id: str | None = None
    difficulty: Difficulty | None = None
    current_phase: Phase = "completed"
    step_number: int = 0
    max_steps: int = 3
    accumulated_reward: float = Field(default=0.0, ge=0.0, le=1.0)
    done: bool = False
    current_observation: Observation | None = None
    phase_history: list[PhaseResult] = Field(default_factory=list)
    available_tasks: list[BenchmarkTaskCard] = Field(default_factory=list)


class EnvironmentMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: str
    version: str
    task_count: int
    supported_difficulties: list[Difficulty]
    observation_model: dict[str, Any]
    action_model: dict[str, Any]
    reward_model: dict[str, Any]


class SchemaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    observation: dict[str, Any]
    action: dict[str, Any]
    reward: dict[str, Any]
    state: dict[str, Any]
