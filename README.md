---
title: Synaptrix MailOS OpenEnv
emoji: 📧
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
---

# Synaptrix MailOS OpenEnv

Synaptrix MailOS is an AI-powered multi-agent email decision intelligence system that classifies emails, detects urgency and risk, automates Gmail-style routing, generates tasks and reply drafts, and exposes an OpenEnv-compatible benchmark with graded tasks and reward-based evaluation.

## Features

- Multi-agent email understanding
  - classifies emails as `Work`, `Personal`, or `Spam`
- Risk and urgency analysis
  - estimates priority, tone, spam risk, and threat indicators
- Decision intelligence engine
  - recommends `Ignore`, `Respond`, or `Urgent Action`
- Gmail automation simulation
  - applies labels, routes folders, and organizes emails into smart inbox lanes
- Smart inbox organizer
  - separates emails into `Urgent`, `Important`, and `Others`
- Auto task generation
  - creates tasks from deadlines, meetings, and time-sensitive messages
- Auto-reply system
  - generates context-aware reply drafts and supports simulated sending
- Analytics and history
  - shows processed emails, rewards, risk trends, and action history
- OpenEnv benchmark support
  - includes typed models, `reset()`, `step()`, `state()`, 3 benchmark tasks, graders, and baseline scoring

## How To Run

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Start the app:

```bash
python app.py
```

3. Open the project in your browser:

```text
http://127.0.0.1:8000
```

## How To Use

1. Open the website.
2. Click `Analyze Email` to let the AI study the current email.
3. Check the result in `Summary`, `Automation`, `Tasks`, `Reply`, and `Analytics`.
4. Use manual actions like `Ignore`, `Respond`, or `Urgent Action` if you want to override the AI.
5. Open `Composer` to test your own custom email.
6. Open `Settings` to change theme, color vibe, density, and behavior.

## OpenEnv Endpoints

These routes are available for the benchmark environment:

- `GET /health`
- `GET /tasks`
- `POST /reset`
- `POST /step`
- `GET /state`
- `GET /metadata`
- `GET /schema`

The UI uses these routes:

- `GET /api/state`
- `POST /api/reset`
- `POST /api/analyze`
- `POST /api/step`
- `POST /api/open-email`
- `POST /api/send-reply`

## Benchmark Tasks

The project includes 3 benchmark tasks:

- `easy-spam-ignore`
  - detect obvious spam and ignore it safely
- `medium-reply-scheduling`
  - recognize a valid personal email and respond correctly
- `hard-security-escalation`
  - identify a critical work/security issue and escalate it urgently

## Baseline

Run the baseline scorer with:

```bash
python baseline.py
```

If `OPENAI_API_KEY` is available, the script can use the OpenAI client. Otherwise, it falls back to a deterministic reference policy and still produces reproducible scores in `baseline_scores.json`.

## Project Structure

- `email_intelligence/`
  - backend logic, agents, environment, tasks, graders, and API
- `static/`
  - frontend pages, styles, and scripts
- `app.py`
  - main application entrypoint
- `baseline.py`
  - baseline evaluation runner
- `openenv.yaml`
  - environment metadata
- `Dockerfile`
  - container setup for deployment

## Deployment

This project includes:

- `Dockerfile`
- `requirements.txt`
- `openenv.yaml`

So it is ready to be containerized and used for Hugging Face Space style deployment.
