from __future__ import annotations

from uuid import uuid4

from email_intelligence.graders import grade_response, grade_routing, grade_triage
from email_intelligence.openenv_models import (
    Action,
    BenchmarkTaskCard,
    EmailEnvelope,
    EnvironmentMetadata,
    EnvironmentState,
    Observation,
    Phase,
    PhaseResult,
    Reward,
    SchemaResponse,
    StepInfo,
    StepResult,
)
from email_intelligence.tasks import BenchmarkTask, load_benchmark_tasks


PHASES: tuple[Phase, ...] = ("triage", "routing", "response")


class OpenEnvEmailEnvironment:
    def __init__(self) -> None:
        self.tasks = load_benchmark_tasks()
        self._task_cycle_index = 0
        self.current_task: BenchmarkTask | None = None
        self.current_email = None
        self.episode_id: str | None = None
        self.phase_index = 0
        self.total_reward = 0.0
        self.done = False
        self.history: list[PhaseResult] = []

    def reset(self, task_id: str | None = None, difficulty: str | None = None) -> Observation:
        self.current_task = self._select_task(task_id=task_id, difficulty=difficulty)
        self.current_email = self.current_task.fresh_email()
        self.episode_id = f"episode-{uuid4().hex[:10]}"
        self.phase_index = 0
        self.total_reward = 0.0
        self.done = False
        self.history = []
        return self._observation()

    def step(self, action: Action) -> StepResult:
        if self.current_task is None or self.current_email is None or self.episode_id is None:
            self.reset()

        assert self.current_task is not None
        phase = PHASES[self.phase_index]
        action_payload = action.model_dump(exclude_none=True)
        grading = self._grade_phase(phase, self.current_task, action_payload)

        reward = Reward(
            phase=phase,
            score=grading["score"],
            components=grading["components"],
            feedback=grading["feedback"],
            rubric=grading["rubric"],
        )
        self.total_reward = round(min(1.0, self.total_reward + reward.score), 4)
        self.history.append(
            PhaseResult(
                phase=phase,
                submitted_action=action_payload,
                reward=reward,
            )
        )

        self.phase_index += 1
        self.done = self.phase_index >= len(PHASES)
        observation = self._observation()
        info = StepInfo(
            task_id=self.current_task.task_id,
            difficulty=self.current_task.difficulty,
            phase_completed=phase,
            remaining_steps=max(0, len(PHASES) - self.phase_index),
            accumulated_reward=self.total_reward,
            notes=self._phase_note(phase),
        )
        return StepResult(observation=observation, reward=reward, done=self.done, info=info)

    def state(self) -> EnvironmentState:
        return EnvironmentState(
            episode_id=self.episode_id,
            task_id=self.current_task.task_id if self.current_task else None,
            difficulty=self.current_task.difficulty if self.current_task else None,
            current_phase=self._current_phase(),
            step_number=min(self.phase_index + 1, len(PHASES)) if self.current_task else 0,
            max_steps=len(PHASES),
            accumulated_reward=self.total_reward,
            done=self.done,
            current_observation=self._observation() if self.current_task and self.episode_id else None,
            phase_history=self.history,
            available_tasks=self.list_tasks(),
        )

    def list_tasks(self) -> list[BenchmarkTaskCard]:
        return [
            BenchmarkTaskCard(
                task_id=task.task_id,
                difficulty=task.difficulty,
                title=task.title,
                objective=task.objective,
                email_id=task.email.email_id,
            )
            for task in self.tasks
        ]

    def metadata(self) -> EnvironmentMetadata:
        from email_intelligence.openenv_models import Action as ActionModel
        from email_intelligence.openenv_models import Observation as ObservationModel
        from email_intelligence.openenv_models import Reward as RewardModel

        return EnvironmentMetadata(
            name="synaptrix-mailos-openenv",
            description=(
                "A real-world email triage environment that asks an agent to classify, "
                "prioritize, route, and respond to incoming email."
            ),
            version="0.1.0",
            task_count=len(self.tasks),
            supported_difficulties=["easy", "medium", "hard"],
            observation_model=ObservationModel.model_json_schema(),
            action_model=ActionModel.model_json_schema(),
            reward_model=RewardModel.model_json_schema(),
        )

    def schema(self) -> SchemaResponse:
        from email_intelligence.openenv_models import Action as ActionModel
        from email_intelligence.openenv_models import EnvironmentState as StateModel
        from email_intelligence.openenv_models import Observation as ObservationModel
        from email_intelligence.openenv_models import Reward as RewardModel

        return SchemaResponse(
            observation=ObservationModel.model_json_schema(),
            action=ActionModel.model_json_schema(),
            reward=RewardModel.model_json_schema(),
            state=StateModel.model_json_schema(),
        )

    def _select_task(self, task_id: str | None, difficulty: str | None) -> BenchmarkTask:
        if task_id:
            for task in self.tasks:
                if task.task_id == task_id:
                    return task
        if difficulty:
            for task in self.tasks:
                if task.difficulty == difficulty:
                    return task
        task = self.tasks[self._task_cycle_index % len(self.tasks)]
        self._task_cycle_index += 1
        return task

    def _current_phase(self) -> Phase:
        if self.done or self.current_task is None:
            return "completed"
        return PHASES[self.phase_index]

    def _observation(self) -> Observation:
        assert self.current_task is not None
        assert self.current_email is not None
        assert self.episode_id is not None

        phase = self._current_phase()
        return Observation(
            episode_id=self.episode_id,
            task_id=self.current_task.task_id,
            difficulty=self.current_task.difficulty,
            phase=phase,
            step_number=min(self.phase_index + 1, len(PHASES)),
            max_steps=len(PHASES),
            objective=self.current_task.objective,
            instructions=self._instructions_for(phase),
            email=EmailEnvelope(
                email_id=self.current_email.email_id,
                sender=self.current_email.sender,
                subject=self.current_email.subject,
                body=self.current_email.body,
                received_at=self.current_email.received_at,
            ),
            available_actions=self._available_actions_for(phase),
            accumulated_reward=self.total_reward,
        )

    def _grade_phase(self, phase: Phase, task: BenchmarkTask, action: dict[str, object]) -> dict[str, object]:
        if phase == "triage":
            return grade_triage(task, action)
        if phase == "routing":
            return grade_routing(task, action)
        return grade_response(task, action)

    def _instructions_for(self, phase: Phase) -> str:
        if phase == "triage":
            return (
                "Classify the email and estimate its priority and risk level. "
                "Focus only on category, priority, and risk fields."
            )
        if phase == "routing":
            return (
                "Choose the handling action, Gmail label, destination folder, and smart inbox lane. "
                "Focus only on routing fields."
            )
        if phase == "response":
            return (
                "Decide whether a reply should be sent and provide a short response summary. "
                "Focus only on send_reply and response_summary."
            )
        return "Episode complete. Call reset() to start another benchmark task."

    def _available_actions_for(self, phase: Phase) -> list[str]:
        if phase == "triage":
            return ["predicted_category", "predicted_priority", "predicted_risk_level"]
        if phase == "routing":
            return ["selected_action", "applied_label", "destination_folder", "inbox_lane"]
        if phase == "response":
            return ["send_reply", "response_summary"]
        return ["reset"]

    def _phase_note(self, phase: Phase) -> str:
        if phase == "triage":
            return "Triage scores reward accurate classification, urgency estimation, and risk detection."
        if phase == "routing":
            return "Routing scores reward the chosen action and Gmail automation decisions."
        return "Response scores reward correct reply behavior and a concise summary."
