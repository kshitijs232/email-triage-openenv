# Email Triage Environment - Architecture Guide

## Overview

This document explains the complete architecture of an OpenEnv environment using Email Triage as a working example.

---

## Architecture Diagram

```
╔════════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║                    ┌──────────────────────────────────────┐                    ║
║                    │         YOUR COMPUTER (Client)       │                    ║
║                    │                                      │                    ║
║  ┌──────────────────────────────────────────────────────────────────────────┐  ║
║  │                                                                          │  ║
║  │   AGENT (example_agent.py)          CLIENT (client.py)                   │  ║
║  │   ════════════════════════          ═══════════════════                  │  ║
║  │                                                                          │  ║
║  │   ┌────────────────────┐            ┌────────────────────┐               │  ║
║  │   │  1. See email      │            │  EmailTriageEnv    │               │  ║
║  │   │  2. Ask GPT what   │  Action    │                    │               │  ║
║  │   │     to do          │ ────────>  │  - Converts to JSON│               │  ║
║  │   │  3. Get next email │            │  - Sends HTTP      │               │  ║
║  │   │                    │ <────────  │  - Parses response │               │  ║
║  │   └────────────────────┘Observation └────────────────────┘               │  ║
║  │                                              │                           │  ║
║  └──────────────────────────────────────────────┼───────────────────────────┘  ║
║                                                 │                              ║
║                                    HTTP Request │ POST /step                   ║
║                                    {"action": { │ "category": "spam"}}         ║
║                                                 │                              ║
║                    ════════════════════════════════════════════════            ║
║                                      NETWORK                                   ║
║                    ════════════════════════════════════════════════            ║
║                                                 │                              ║
║                                    HTTP Response│ {"observation": {            ║
║                                                 │   "next_email": "...",       ║
║                                                 │   "reward": 0.3}}            ║
║                                                 ▼                              ║
║  ┌──────────────────────────────────────────────────────────────────────────┐  ║
║  │                                                                          │  ║
║  │   SERVER (app.py)                   ENVIRONMENT (email_triage_env.py)    │  ║
║  │   ═══════════════                   ═════════════════════════════════    │  ║
║  │                                                                          │  ║
║  │   ┌────────────────────┐            ┌────────────────────┐               │  ║
║  │   │  FastAPI Server    │            │  EmailTriageEnv    │               │  ║
║  │   │                    │            │                    │               │  ║
║  │   │  POST /reset ──────────────────>│  reset()           │               │  ║
║  │   │  POST /step  ──────────────────>│  step(action)      │               │  ║
║  │   │  GET  /state ──────────────────>│  state             │               │  ║
║  │   │                    │            │                    │               │  ║
║  │   └────────────────────┘            │  - Has the emails  │               │  ║
║  │                                     │  - Knows answers   │               │  ║
║  │                                     │  - Computes reward │               │  ║
║  │                                     └────────────────────┘               │  ║
║  │                                                                          │  ║
║  │                     DOCKER CONTAINER / HUGGINGFACE SPACE                 │  ║
║  └──────────────────────────────────────────────────────────────────────────┘  ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝
```

---

## Data Flow Sequence

```
TIME →

AGENT                   CLIENT                    NETWORK          SERVER
  │                       │                          │                │
  │ "Start easy task"     │                          │                │
  │ ─────────────────────>│  POST /reset             │                │
  │                       │  {"task_id": "easy"}     │                │
  │                       │ ────────────────────────>│                │
  │                       │                          │ ──────────────>│
  │                       │                          │                │ reset()
  │                       │                          │                │ - Load 3 emails
  │                       │                          │                │ - Return first
  │                       │                          │                │
  │                       │  {"observation": {       │                │
  │                       │    "current_email": {    │                │
  │                       │      "subject": "YOU WON"│                │
  │                       │    }}}                   │                │
  │                       │ <────────────────────────│                │
  │  obs.current_email    │                          │                │
  │ <─────────────────────│                          │                │
  │                       │                          │                │
  │                       │                          │                │
  │  GPT says: "spam"     │                          │                │
  │ ─────────────────────>│  POST /step              │                │
  │  EmailTriageAction(   │  {"category": "spam",    │                │
  │    category="spam"    │   "priority": "low"}     │                │
  │  )                    │ ────────────────────────>│                │
  │                       │                          │ ──────────────>│
  │                       │                          │                │ step(action)
  │                       │                          │                │ - Compare to answer
  │                       │                          │                │ - spam == spam ✓
  │                       │                          │                │ - reward = 0.3
  │                       │                          │                │ - Get next email
  │                       │                          │                │
  │                       │  {"observation": {...},  │                │
  │                       │   "reward": 0.3,         │                │
  │                       │   "done": false}         │                │
  │                       │ <────────────────────────│                │
  │  obs.reward = 0.3     │                          │                │
  │ <─────────────────────│                          │                │
  │                       │                          │                │
  │  ... (repeat) ...     │                          │                │
  │                       │                          │                │
  │  obs.done = true      │                          │                │
  │  Final score: 80%     │                          │                │
```

---

## File Structure

```
email_triage_env/
├── __init__.py              # Public exports
├── models.py                # Data contracts (Action, Observation, State)
├── client.py                # Client-side: talks to server over HTTP
├── openenv.yaml             # OpenEnv metadata
├── pyproject.toml           # Python dependencies
├── README.md                # Documentation
├── architecture.md          # This file
│
├── server/                  # SERVER-SIDE CODE (runs in Docker)
│   ├── __init__.py
│   ├── app.py               # FastAPI server (creates HTTP endpoints)
│   ├── email_triage_environment.py  # Environment logic
│   ├── emails_data.py       # Email datasets for tasks
│   └── Dockerfile           # Container definition
│
├── example_agent.py         # Example AI agent using GPT
└── run_baseline.py          # Baseline evaluation script
```

---

## Component Responsibilities

### 1. Models (`models.py`) - SHARED
**Used by both client and server**

| Class | Purpose |
|-------|---------|
| `EmailTriageAction` | What agent sends: category, priority, action, response |
| `EmailTriageObservation` | What agent receives: current email, feedback, score |
| `EmailTriageState` | Internal tracking: episode ID, progress, correct count |
| `Email` | Single email structure |

### 2. Environment (`server/email_triage_environment.py`) - SERVER
**Contains the "game rules" and correct answers**

| Method | Purpose |
|--------|---------|
| `__init__()` | Initialize state |
| `reset(task_id, seed)` | Start new episode, load emails, return first observation |
| `step(action)` | Grade action, compute reward, return next observation |
| `state` | Property returning current state |

### 3. Server (`server/app.py`) - SERVER
**Exposes environment over HTTP**

One line creates all endpoints:
```python
app = create_app(EmailTriageEnvironment, EmailTriageAction, EmailTriageObservation)
```

| Endpoint | Maps To |
|----------|---------|
| `POST /reset` | `env.reset()` |
| `POST /step` | `env.step(action)` |
| `GET /state` | `env.state` |
| `GET /health` | Health check |
| `WS /ws` | WebSocket for persistent connections |

### 4. Client (`client.py`) - CLIENT
**Handles network communication**

| Method | Purpose |
|--------|---------|
| `_step_payload(action)` | Convert Action → JSON for HTTP |
| `_parse_result(payload)` | Convert JSON → Observation |
| `_parse_state(payload)` | Convert JSON → State |

### 5. Agent (`example_agent.py`) - CLIENT
**Your AI code that makes decisions**

The agent is YOUR code. It:
1. Connects to server via Client
2. Receives observations
3. Makes decisions (using GPT, rules, RL, etc.)
4. Sends actions
5. Never sees correct answers!

---

## Key Concepts

### Actions
What the agent sends to the environment:
```python
action = EmailTriageAction(
    email_id="email_001",
    category="spam",        # spam, work, personal, newsletter, urgent
    priority="low",         # low, medium, high, critical
    action_type="delete",   # archive, respond, flag, delete
    response_text=None      # Only if action_type="respond"
)
```

### Observations
What the agent receives back:
```python
observation.current_email   # The email to process
observation.feedback        # "✓ Category correct" or "✗ Wrong"
observation.reward          # 0.0 to 1.0 for this step
observation.current_score   # Running average score
observation.done            # True when inbox empty
observation.emails_remaining # How many left
```

### Rewards
How the environment scores agent decisions:

| Correct Decision | Reward |
|-----------------|--------|
| Category correct | +0.30 |
| Priority correct | +0.30 |
| Priority close (off by 1) | +0.15 |
| Action type correct | +0.20 |
| Response when needed | +0.20 |
| No response when not needed | +0.20 |

### Tasks
Different difficulty levels:

| Task | Emails | Difficulty |
|------|--------|------------|
| `easy` | 3 | Clear categories, obvious spam |
| `medium` | 5 | Ambiguous priorities |
| `hard` | 10 | Complex chains, subtle spam |

---

## Running the Environment

### 1. Start the Server
```bash
# From email_triage_env directory
cd server
uvicorn app:app --host 0.0.0.0 --port 8000
```

### 2. Run the Agent
```bash
# In another terminal
export OPENAI_API_KEY="your-key"
python example_agent.py
```

### 3. Or Use Docker
```bash
# Build
docker build -t email-triage-env -f server/Dockerfile .

# Run
docker run -p 8000:8000 email-triage-env
```

---

## Why This Architecture?

| Feature | Benefit |
|---------|---------|
| **Client-Server Split** | Agent can't cheat by seeing answers |
| **HTTP API** | Any language can interact (Python, JS, Rust) |
| **Docker Container** | Same code runs locally and in cloud |
| **Typed Models** | IDE autocomplete, catch errors early |
| **Reproducible** | Seed parameter gives same emails every time |
| **Scalable** | Deploy to Kubernetes for parallel evaluation |
