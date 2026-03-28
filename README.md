---
title: Email Triage OpenEnv
emoji: 📧
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
---

# Email Triage Environment

A real-world OpenEnv environment for training and evaluating AI agents on email inbox management tasks.

[![OpenEnv](https://img.shields.io/badge/OpenEnv-compatible-blue)](https://github.com/meta-pytorch/OpenEnv)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Environment Description & Motivation

**Email triage is a daily task for millions of knowledge workers.** The average professional receives 121 emails per day and spends 28% of their workday managing email. This environment simulates realistic email inbox management where an AI agent must:

1. **Classify** incoming emails into categories (spam, work, personal, newsletter, urgent)
2. **Prioritize** them appropriately (low, medium, high, critical)
3. **Take action** (archive, respond, flag, delete)
4. **Draft responses** when needed

### Why This Environment?

- **Real-world utility**: Email management automation has immediate practical value
- **Rich decision space**: Multiple dimensions to optimize (category, priority, action, response)
- **Partial observability**: Agent only sees email content, not sender history or context
- **Nuanced evaluation**: Distinguishing spam from newsletters, phishing from legitimate alerts
- **Scalable difficulty**: Easy (obvious spam) to hard (subtle phishing, context-dependent urgency)

---

## Action Space

The agent submits an `EmailTriageAction` with the following fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email_id` | `string` | Yes | ID of the email being processed |
| `category` | `EmailCategory` | Yes | Classification: `spam`, `work`, `personal`, `newsletter`, `urgent` |
| `priority` | `EmailPriority` | Yes | Priority level: `low`, `medium`, `high`, `critical` |
| `action_type` | `EmailActionType` | Yes | Action to take: `archive`, `respond`, `flag`, `delete` |
| `response_text` | `string` | If action=respond | Draft response text (required when action_type is "respond") |

### Example Action

```python
from models import EmailTriageAction, EmailCategory, EmailPriority, EmailActionType

action = EmailTriageAction(
    email_id="easy_001",
    category=EmailCategory.SPAM,
    priority=EmailPriority.LOW,
    action_type=EmailActionType.DELETE,
    response_text=None
)
```

---

## Observation Space

The agent receives an `EmailTriageObservation` containing:

| Field | Type | Description |
|-------|------|-------------|
| `current_email` | `Email` | The email to process (None when inbox empty) |
| `feedback` | `string` | Feedback from the previous action |
| `reward` | `float` | Reward from last action (0.0 to 1.0) |
| `current_score` | `float` | Running average score across episode |
| `emails_processed` | `int` | Number of emails completed |
| `emails_remaining` | `int` | Emails left in inbox |
| `done` | `bool` | True when inbox is empty |
| `task_id` | `string` | Current task identifier |

### Email Structure

Each email contains:
- `id`: Unique identifier
- `sender`: Email address of sender
- `subject`: Subject line
- `body`: Full email body text
- `timestamp`: When the email was received

---

## Tasks & Difficulty Levels

### Task: `easy` (3 emails)
**Obvious classifications with clear signals**
- Lottery scam spam (fake domain, urgent money language)
- Work meeting request (company domain, clear ask)
- Personal family message

**Expected Score**: 90-100% for capable models

### Task: `medium` (5 emails)
**Priority ambiguity and subtle spam**
- Newsletter vs promotional spam distinction
- Urgent work requests vs normal work
- Nigerian prince scam (classic phishing)
- Order confirmations (personal vs promotional)

**Expected Score**: 60-85% for capable models

### Task: `hard` (10 emails)
**Complex scenarios requiring careful analysis**
- Phishing with lookalike domains (paypa1.com, amaz0n.com)
- Forwarded complaint chains (escalation detection)
- Context-dependent urgency (deadlines in email body)
- Legitimate bank fraud alerts vs phishing
- Work emails with personal elements
- Charity receipts (personal vs newsletter)

**Expected Score**: 40-70% for frontier models

---

## Reward Function

Rewards are computed per-action with partial credit:

| Component | Weight | Description |
|-----------|--------|-------------|
| **Category** | 30% | Correct classification (spam, work, etc.) |
| **Priority** | 30% | Exact priority match = full, ±1 level = half credit |
| **Action** | 20% | Correct action type (archive, respond, etc.) |
| **Response** | 20% | Provided response when needed, didn't when unnecessary |

### Scoring Formula

```
step_reward = (0.3 × category_correct) 
            + (0.3 × priority_score)  # 1.0 if exact, 0.5 if ±1, 0 otherwise
            + (0.2 × action_correct)
            + (0.2 × response_appropriate)

final_score = sum(step_rewards) / num_emails  # Normalized to 0.0-1.0
```

### Example Rewards

| Action Quality | Reward |
|----------------|--------|
| All correct | 1.0 |
| Category + action correct, priority off by 1 | 0.65 |
| Only category correct | 0.3 |
| All wrong | 0.0 |

---

## Setup & Usage

### Prerequisites

- Python 3.10+
- Docker (for containerized deployment)
- HuggingFace account (for HF Spaces deployment)

### Local Development

```bash
# Clone the repository
git clone https://github.com/your-username/email-triage-env
cd email-triage-env

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install openenv-core

# Start the server
python -m uvicorn server.app:app --host 0.0.0.0 --port 8000
```

### Running Inference

```bash
# Set environment variables
export HF_TOKEN="hf_xxxxx"  # Get from huggingface.co/settings/tokens
export MODEL_NAME="meta-llama/Llama-3.1-8B-Instruct"
export API_BASE_URL="https://router.huggingface.co/v1"
export ENV_URL="http://localhost:8000"

# Run inference
python inference.py
```

### Docker Deployment

```bash
# Build the image
docker build -t email-triage-env .

# Run the container
docker run -p 8000:8000 email-triage-env

# Test health endpoint
curl http://localhost:8000/health
```

### HuggingFace Spaces Deployment

```bash
# Using OpenEnv CLI
openenv push your-username/email-triage-env

# Or manually upload to HuggingFace Spaces with Docker SDK
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check (returns `{"status": "healthy"}`) |
| `/reset` | POST | Reset environment, start new episode |
| `/step` | POST | Submit action, receive observation |
| `/state` | GET | Get current environment state |
| `/ws` | WebSocket | Persistent connection for efficient multi-step |

### Example API Usage

```bash
# Reset with easy task
curl -X POST http://localhost:8000/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "easy"}'

# Submit an action
curl -X POST http://localhost:8000/step \
  -H "Content-Type: application/json" \
  -d '{"email_id": "easy_001", "category": "spam", "priority": "low", "action_type": "delete"}'
```

---

## Baseline Scores

Scores from running `inference.py` with different models:

| Model | Easy | Medium | Hard | Overall |
|-------|------|--------|------|---------|
| Rule-based (no LLM) | 100% | 60% | ~50% | ~70% |
| GPT-4o-mini | ~95% | ~80% | ~65% | ~80% |
| Llama-3.1-8B-Instruct | ~90% | ~70% | ~55% | ~72% |

*Note: Actual scores may vary based on prompt engineering and model versions.*

---

## File Structure

```
email_triage_env/
├── inference.py           # MANDATORY: Baseline inference script
├── Dockerfile             # Container definition
├── openenv.yaml           # OpenEnv spec metadata
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── models.py              # Pydantic models (Action, Observation, State)
├── client.py              # Client-side API
├── __init__.py
├── server/
│   ├── app.py             # FastAPI server
│   ├── email_triage_environment.py  # Environment logic
│   ├── emails_data.py     # Task datasets (18 emails)
│   ├── Dockerfile         # Alternative Dockerfile location
│   └── __init__.py
├── example_agent.py       # Example GPT/rule-based agent
├── run_baseline.py        # Batch evaluation script
├── architecture.md        # Architecture documentation
└── guidelines.md          # Competition guidelines
```

---

## License

MIT License - See LICENSE file for details.

---

## Author

Kshitij Srivastava (kshitijs232@gmail.com)

---

## Acknowledgments

Built using the [OpenEnv](https://github.com/meta-pytorch/OpenEnv) framework by Meta PyTorch.
