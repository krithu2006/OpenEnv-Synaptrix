import json
import random
from env.models import EmailObservation, TriageAction, StepResult

class EmailTriageEnv:

    def __init__(self):
        with open("data/emails.json") as f:
            self.data = json.load(f)
        self.current_email = None
        self.step_count = 0

    def reset(self):
        self.current_email = random.choice(self.data)
        self.step_count = 0

        return EmailObservation(
            email_id=self.current_email["email_id"],
            subject=self.current_email["subject"],
            body=self.current_email["body"],
            sender=self.current_email["sender"],
            timestamp=self.current_email["timestamp"]
        )

    def step(self, action: TriageAction):
        self.step_count += 1
        correct = self.current_email

        score = 0
        total = 3

        if action.category == correct["category"]:
            score += 1

        if action.priority and action.priority == correct["priority"]:
            score += 1

        if action.tone and action.tone == correct["tone"]:
            score += 1

        reward = score / total

        return StepResult(
            observation=self.reset(),
            reward=reward,
            done=True,
            info={
                "correct": correct,
                "step_count": self.step_count
            }
        )

    def state(self):
        return {
            "current_email": self.current_email,
            "steps": self.step_count
        }
