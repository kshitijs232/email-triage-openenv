#!/usr/bin/env python3
"""
Baseline Evaluation Script for Email Triage Environment

Runs evaluation across all tasks and reports metrics.

Usage:
    # Start server first:
    cd examples/email_triage_env/server
    uvicorn app:app --port 8000

    # Then run baseline:
    python run_baseline.py
"""

import asyncio
import sys
import os
from dataclasses import dataclass
from typing import Optional

# Add parent path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from email_triage_env import EmailTriageEnv
from email_triage_env.example_agent import ask_gpt, rule_based_classify, gpt_result_to_action


@dataclass
class TaskResult:
    """Results from running one task."""
    task_id: str
    total_emails: int
    total_reward: float
    average_score: float
    correct_categories: int
    correct_priorities: int
    correct_actions: int


async def evaluate_task(
    env: EmailTriageEnv, 
    task_id: str,
    use_gpt: bool = False,
) -> TaskResult:
    """Run evaluation on a single task."""
    result = await env.reset(task_id=task_id)
    obs = result.observation
    
    step_count = 0
    total_reward = 0.0
    
    while not result.done and obs.current_email is not None:
        email = obs.current_email
            
        # Get decision
        if use_gpt:
            decision = await ask_gpt(email)
        else:
            decision = rule_based_classify(email)
        
        action = gpt_result_to_action(email, decision)
        result = await env.step(action)
        obs = result.observation
        reward = result.reward or 0.0
        
        step_count += 1
        total_reward += reward
    
    # Get final state for detailed metrics
    state = await env.state()
    
    return TaskResult(
        task_id=task_id,
        total_emails=step_count,
        total_reward=total_reward,
        average_score=obs.current_score,
        correct_categories=state.correct_categories,
        correct_priorities=state.correct_priorities,
        correct_actions=state.correct_actions,
    )


async def run_baseline(
    server_url: str = "http://localhost:8000",
    use_gpt: bool = False,
):
    """Run baseline evaluation across all tasks."""
    tasks = ["easy", "medium", "hard"]
    results: list[TaskResult] = []
    
    print("\n" + "="*70)
    print("EMAIL TRIAGE ENVIRONMENT - BASELINE EVALUATION")
    print("="*70)
    print(f"Server: {server_url}")
    print(f"Mode: {'GPT-4' if use_gpt else 'Rule-based'}")
    print("="*70 + "\n")
    
    async with EmailTriageEnv(server_url) as env:
        for task_id in tasks:
            print(f"▶ Evaluating task: {task_id}...", end=" ", flush=True)
            result = await evaluate_task(env, task_id, use_gpt)
            results.append(result)
            print(f"Score: {result.average_score:.1%}")
    
    # Print summary table
    print("\n" + "="*70)
    print("RESULTS SUMMARY")
    print("="*70)
    print(f"{'Task':<10} {'Emails':<8} {'Score':<10} {'Cat':<6} {'Pri':<6} {'Act':<6}")
    print("-"*70)
    
    for r in results:
        print(f"{r.task_id:<10} {r.total_emails:<8} {r.average_score:>8.1%}"
              f"   {r.correct_categories}/{r.total_emails:<4}"
              f" {r.correct_priorities}/{r.total_emails:<4}"
              f" {r.correct_actions}/{r.total_emails:<4}")
    
    print("-"*70)
    
    # Overall metrics
    total_emails = sum(r.total_emails for r in results)
    total_reward = sum(r.total_reward for r in results)
    avg_score = sum(r.average_score for r in results) / len(results)
    
    print(f"{'TOTAL':<10} {total_emails:<8} {avg_score:>8.1%}")
    print("="*70)
    
    # Detailed breakdown
    print("\nDETAILED METRICS:")
    print(f"  Category accuracy: {sum(r.correct_categories for r in results)}/{total_emails}")
    print(f"  Priority accuracy: {sum(r.correct_priorities for r in results)}/{total_emails}")
    print(f"  Action accuracy:   {sum(r.correct_actions for r in results)}/{total_emails}")
    print()
    
    return avg_score


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Baseline evaluation")
    parser.add_argument(
        "--server",
        default="http://localhost:8000",
        help="Environment server URL"
    )
    parser.add_argument(
        "--gpt",
        action="store_true",
        help="Use GPT-4 instead of rule-based"
    )
    
    args = parser.parse_args()
    
    if args.gpt and not os.environ.get("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set")
        sys.exit(1)
    
    score = asyncio.run(run_baseline(args.server, args.gpt))
    sys.exit(0 if score >= 0.6 else 1)
