#!/usr/bin/env python3
"""
Inference Script for Email Triage Environment
==============================================

MANDATORY ENVIRONMENT VARIABLES:
    API_BASE_URL   The API endpoint for the LLM (default: HuggingFace router)
    MODEL_NAME     The model identifier to use for inference
    HF_TOKEN       Your HuggingFace API key

This script runs a baseline LLM agent against all 3 tasks (easy, medium, hard)
and reports reproducible scores.

Usage:
    export HF_TOKEN="hf_xxxxx"
    export MODEL_NAME="meta-llama/Llama-3.1-8B-Instruct"
    python inference.py
"""

import os
import sys
import json
import asyncio
import textwrap
import subprocess
import time
import signal
import atexit
from typing import Optional

import httpx
from openai import OpenAI

# Add parent path for imports when running from project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from client import EmailTriageEnv
from models import (
    EmailTriageAction,
    Email,
    EmailCategory,
    EmailPriority,
    EmailActionType,
)

# =============================================================================
# Configuration from Environment Variables
# =============================================================================

API_BASE_URL = os.getenv("API_BASE_URL") or "https://router.huggingface.co/v1"
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME") or "meta-llama/Llama-3.1-8B-Instruct"

# Environment configuration
ENV_URL = os.getenv("ENV_URL") or "http://localhost:8000"
ENV_PORT = int(os.getenv("ENV_PORT") or "8000")
MAX_STEPS_PER_TASK = 20
TEMPERATURE = 0.1
MAX_TOKENS = 500

# Tasks to evaluate
TASKS = ["easy", "medium", "hard"]

# Global server process handle
_server_process: subprocess.Popen | None = None


def start_server() -> subprocess.Popen:
    """Start the environment server as a subprocess."""
    global _server_process
    print(f"  Starting server on port {ENV_PORT}...")
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    _server_process = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn",
            "server.app:app",
            "--host", "0.0.0.0",
            "--port", str(ENV_PORT),
        ],
        cwd=script_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "PYTHONPATH": script_dir},
    )
    
    # Register cleanup
    atexit.register(stop_server)
    
    return _server_process


def stop_server() -> None:
    """Stop the server subprocess if running."""
    global _server_process
    if _server_process is not None:
        print("  Stopping server...")
        _server_process.terminate()
        try:
            _server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _server_process.kill()
        _server_process = None


# =============================================================================
# System Prompt for Email Triage
# =============================================================================

SYSTEM_PROMPT = textwrap.dedent("""
You are an expert email triage assistant. Given an email, classify it and decide what action to take.

CATEGORIES (choose exactly one):
- spam: Scams, phishing attempts, unsolicited marketing, suspicious links
- work: Professional emails from colleagues, clients, about projects/meetings
- personal: Friends, family, personal matters
- newsletter: Subscribed content, digests, promotional from known/legitimate senders
- urgent: Time-sensitive emails requiring immediate attention (deadlines, emergencies)

PRIORITIES (choose exactly one):
- low: Can wait, informational only, no action needed soon
- medium: Should address within a day or two
- high: Important, should address today
- critical: Needs immediate attention, time-sensitive

ACTIONS (choose exactly one):
- archive: Save for reference, no response needed
- respond: Needs a reply (you must provide response_text)
- flag: Mark for follow-up later
- delete: Remove (for spam, irrelevant content)

RESPONSE FORMAT - You MUST respond with ONLY a valid JSON object, no other text:
{
    "category": "<category>",
    "priority": "<priority>",
    "action": "<action>",
    "response_text": "<draft response if action is 'respond', otherwise null>"
}

IMPORTANT:
- For phishing emails (fake domains like paypa1.com, amaz0n.com), classify as "spam"
- If action is "respond", you MUST include a brief, professional response_text
- If action is NOT "respond", set response_text to null
- Be careful with urgency - "urgent" category is for genuinely time-sensitive matters
""").strip()


# =============================================================================
# LLM Client
# =============================================================================

def create_client() -> OpenAI:
    """Create OpenAI-compatible client with environment variables."""
    if not API_KEY:
        raise ValueError(
            "No API key found. Set HF_TOKEN or API_KEY environment variable."
        )
    return OpenAI(base_url=API_BASE_URL, api_key=API_KEY)


def build_user_prompt(email: Email, step: int, total: int) -> str:
    """Build the user prompt for classifying an email."""
    return textwrap.dedent(f"""
Email {step} of {total} to classify:

FROM: {email.sender}
SUBJECT: {email.subject}
TIMESTAMP: {email.timestamp}

BODY:
{email.body}

Respond with ONLY a JSON object containing category, priority, action, and response_text.
""").strip()


def parse_llm_response(response_text: str, email: Email) -> EmailTriageAction:
    """Parse LLM response into EmailTriageAction."""
    try:
        # Try to extract JSON from response
        response_text = response_text.strip()
        
        # Handle markdown code blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]
        
        data = json.loads(response_text.strip())
        
        # Validate and extract fields
        category = EmailCategory(data.get("category", "personal"))
        priority = EmailPriority(data.get("priority", "medium"))
        action = EmailActionType(data.get("action", "archive"))
        response_text_field = data.get("response_text")
        
        # Ensure response_text is provided if action is respond
        if action == EmailActionType.RESPOND and not response_text_field:
            response_text_field = "Thank you for your email. I will review and respond shortly."
        
        return EmailTriageAction(
            email_id=email.id,
            category=category,
            priority=priority,
            action_type=action,
            response_text=response_text_field if action == EmailActionType.RESPOND else None,
        )
        
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        # Fallback to safe defaults
        print(f"  Warning: Could not parse LLM response: {e}")
        return EmailTriageAction(
            email_id=email.id,
            category=EmailCategory.PERSONAL,
            priority=EmailPriority.MEDIUM,
            action_type=EmailActionType.ARCHIVE,
            response_text=None,
        )


def get_llm_classification(client: OpenAI, email: Email, step: int, total: int) -> EmailTriageAction:
    """Get email classification from LLM."""
    user_prompt = build_user_prompt(email, step, total)
    
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        response_text = completion.choices[0].message.content or ""
        return parse_llm_response(response_text, email)
        
    except Exception as e:
        print(f"  Error calling LLM: {e}")
        # Return safe fallback
        return EmailTriageAction(
            email_id=email.id,
            category=EmailCategory.PERSONAL,
            priority=EmailPriority.MEDIUM,
            action_type=EmailActionType.ARCHIVE,
            response_text=None,
        )


# =============================================================================
# Evaluation Loop
# =============================================================================

async def evaluate_task(client: OpenAI, env: EmailTriageEnv, task_id: str) -> dict:
    """
    Evaluate the LLM agent on a single task.
    
    Returns:
        dict with task_id, score (0.0-1.0), emails_processed, details
    """
    print(f"\n{'='*60}")
    print(f"Evaluating Task: {task_id}")
    print(f"{'='*60}")
    
    # Reset environment for this task
    result = await env.reset(task_id=task_id)
    obs = result.observation
    
    total_emails = obs.emails_remaining
    print(f"Total emails in task: {total_emails}")
    
    step = 0
    total_reward = 0.0
    details = []
    
    while not result.done and obs.current_email is not None and step < MAX_STEPS_PER_TASK:
        step += 1
        email = obs.current_email
        
        print(f"\n  Email {step}/{total_emails}: {email.subject[:50]}...")
        
        # Get LLM classification
        action = get_llm_classification(client, email, step, total_emails)
        print(f"    Decision: {action.category.value}/{action.priority.value}/{action.action_type.value}")
        
        # Step the environment
        result = await env.step(action)
        obs = result.observation
        reward = result.reward or 0.0
        
        total_reward += reward
        print(f"    Reward: {reward:.2f}")
        
        details.append({
            "email_id": email.id,
            "subject": email.subject[:50],
            "action": {
                "category": action.category.value,
                "priority": action.priority.value,
                "action_type": action.action_type.value,
            },
            "reward": reward,
        })
    
    # Calculate final score (normalized to 0.0-1.0)
    final_score = total_reward / total_emails if total_emails > 0 else 0.0
    
    print(f"\n  Task Complete!")
    print(f"  Emails Processed: {step}")
    print(f"  Total Reward: {total_reward:.2f}")
    print(f"  Final Score: {final_score:.2%}")
    
    return {
        "task_id": task_id,
        "score": final_score,
        "emails_processed": step,
        "total_reward": total_reward,
        "details": details,
    }


async def wait_for_server(env_url: str, max_retries: int = 15, delay: float = 2.0) -> None:
    """
    Wait for the environment server to be ready, starting it if needed.
    
    Args:
        env_url: URL of the environment server
        max_retries: Maximum number of health check attempts
        delay: Delay between retries in seconds
        
    Raises:
        ConnectionError: If server is not ready after all retries
    """
    health_url = f"{env_url.rstrip('/')}/health"
    last_error = None
    server_started = False
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for attempt in range(1, max_retries + 1):
            try:
                print(f"  Checking server health (attempt {attempt}/{max_retries})...")
                response = await client.get(health_url)
                if response.status_code == 200:
                    print("  Server is ready!")
                    return
                else:
                    last_error = f"Health check returned status {response.status_code}"
            except httpx.ConnectError as e:
                last_error = f"Connection refused: {e}"
                # If first few attempts fail, try starting the server ourselves
                if attempt == 2 and not server_started:
                    print("  Server not reachable. Attempting to start server...")
                    try:
                        start_server()
                        server_started = True
                        print("  Server process started. Waiting for it to be ready...")
                    except Exception as start_err:
                        print(f"  Failed to start server: {start_err}")
            except httpx.TimeoutException as e:
                last_error = f"Connection timeout: {e}"
            except Exception as e:
                last_error = f"Unexpected error: {e}"
            
            print(f"  Attempt {attempt} failed: {last_error}")
            if attempt < max_retries:
                print(f"  Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
    
    raise ConnectionError(
        f"Environment server at {env_url} is not ready after {max_retries} attempts. "
        f"Last error: {last_error}"
    )


async def run_evaluation() -> dict:
    """
    Run evaluation on all tasks and return results.
    
    Returns:
        dict with overall results and per-task breakdown
    """
    print("\n" + "="*70)
    print("EMAIL TRIAGE ENVIRONMENT - INFERENCE EVALUATION")
    print("="*70)
    print(f"API Base URL: {API_BASE_URL}")
    print(f"Model: {MODEL_NAME}")
    print(f"Environment: {ENV_URL}")
    print(f"Tasks: {', '.join(TASKS)}")
    print("="*70)
    
    # Create LLM client
    client = create_client()
    
    # Results storage
    results = {
        "model": MODEL_NAME,
        "api_base_url": API_BASE_URL,
        "tasks": {},
        "overall_score": 0.0,
    }
    
    # Wait for environment server to be ready
    print("\nWaiting for environment server...")
    try:
        await wait_for_server(ENV_URL)
    except ConnectionError as e:
        print(f"ERROR: Could not connect to environment server: {e}")
        # Return empty results with 0 score
        for task_id in TASKS:
            results["tasks"][task_id] = {
                "task_id": task_id,
                "score": 0.0,
                "emails_processed": 0,
                "total_reward": 0.0,
                "details": [],
                "error": str(e),
            }
        return results
    
    # Run evaluation for each task
    try:
        async with EmailTriageEnv(ENV_URL) as env:
            for task_id in TASKS:
                try:
                    task_result = await evaluate_task(client, env, task_id)
                    results["tasks"][task_id] = task_result
                except Exception as e:
                    print(f"ERROR: Task {task_id} failed: {e}")
                    results["tasks"][task_id] = {
                        "task_id": task_id,
                        "score": 0.0,
                        "emails_processed": 0,
                        "total_reward": 0.0,
                        "details": [],
                        "error": str(e),
                    }
    except Exception as e:
        print(f"ERROR: Failed to connect to environment: {e}")
        # Set 0 score for any remaining tasks
        for task_id in TASKS:
            if task_id not in results["tasks"]:
                results["tasks"][task_id] = {
                    "task_id": task_id,
                    "score": 0.0,
                    "emails_processed": 0,
                    "total_reward": 0.0,
                    "details": [],
                    "error": str(e),
                }
    
    # Calculate overall score (average across tasks)
    task_scores = [results["tasks"][t]["score"] for t in TASKS]
    results["overall_score"] = sum(task_scores) / len(task_scores) if task_scores else 0.0
    
    # Print summary
    print("\n" + "="*70)
    print("FINAL RESULTS SUMMARY")
    print("="*70)
    print(f"{'Task':<12} {'Score':<12} {'Emails':<12}")
    print("-"*70)
    for task_id in TASKS:
        t = results["tasks"][task_id]
        print(f"{task_id:<12} {t['score']:.2%}       {t['emails_processed']}")
    print("-"*70)
    print(f"{'OVERALL':<12} {results['overall_score']:.2%}")
    print("="*70)
    
    return results


# =============================================================================
# Main Entry Point
# =============================================================================

def main() -> None:
    """Main entry point for inference script."""
    
    # Validate environment
    if not API_KEY:
        print("ERROR: No API key found.")
        print("Please set HF_TOKEN or API_KEY environment variable.")
        print("\nExample:")
        print('  export HF_TOKEN="hf_xxxxx"')
        print('  export MODEL_NAME="meta-llama/Llama-3.1-8B-Instruct"')
        print("  python inference.py")
        sys.exit(1)
    
    # Run evaluation
    try:
        results = asyncio.run(run_evaluation())
        
        # Save results to file
        output_file = "inference_results.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to: {output_file}")
        
        # Exit with appropriate code
        # Score >= 0.5 is considered passing
        if results["overall_score"] >= 0.5:
            print("\n✓ Evaluation PASSED")
            sys.exit(0)
        else:
            print("\n✗ Evaluation needs improvement")
            sys.exit(1)
            
    except Exception as e:
        print(f"\nERROR: Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
