from env.models import TriageAction

def simple_agent(obs):

    text = (obs.subject + " " + obs.body).lower()

    if "sale" in text or "offer" in text or "buy now" in text:
        category = "Spam"
    elif "meeting" in text or "project" in text or "deadline" in text:
        category = "Work"
    else:
        category = "Personal"

    if "urgent" in text or "asap" in text:
        priority = "High"
    elif "meeting" in text:
        priority = "Medium"
    else:
        priority = "Low"

    if "dear" in text:
        tone = "Formal"
    elif "urgent" in text:
        tone = "Urgent"
    else:
        tone = "Casual"

    return TriageAction(
        category=category,
        priority=priority,
        tone=tone
    )
