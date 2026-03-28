#!/usr/bin/env python3
"""
Example AI Agent for Email Triage Environment

This agent uses GPT-4 to classify emails. It demonstrates how to:
1. Connect to the environment server
2. Process observations
3. Make decisions using an LLM
4. Send actions back to the environment

Usage:
    export OPENAI_API_KEY="your-key"
    python example_agent.py
"""

import asyncio
import os
import sys
from typing import Optional

# Add parent path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from email_triage_env import (
    EmailTriageEnv,
    EmailTriageAction,
    EmailTriageObservation,
    Email,
    EmailCategory,
    EmailPriority,
    EmailActionType,
)


# =============================================================================
# GPT-based Decision Making
# =============================================================================

SYSTEM_PROMPT = """You are an expert email triage assistant. Given an email, you must classify it and decide what action to take.

Categories:
- spam: Scams, phishing, unsolicited marketing
- work: Professional emails from colleagues, clients, about projects
- personal: Friends, family, personal matters
- newsletter: Subscribed content, digests, promotional from known senders
- urgent: Time-sensitive emails requiring immediate attention

Priorities:
- low: Can wait, informational only
- medium: Should address within a day or two
- high: Important, address today
- critical: Needs immediate attention

Actions:
- archive: Save for reference, no action needed
- respond: Needs a reply
- flag: Mark for follow-up
- delete: Remove (spam, irrelevant)

Respond ONLY with a JSON object:
{
    "category": "<category>",
    "priority": "<priority>",
    "action": "<action>",
    "response": "<draft response if action is 'respond', otherwise null>",
    "reasoning": "<brief explanation>"
}"""


async def ask_gpt(email: Email) -> dict:
    """
    Ask GPT-4 to classify an email.
    
    Returns a dict with category, priority, action, response, reasoning.
    """
    try:
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI()
        
        user_message = f"""Email to classify:

From: {email.sender}
Subject: {email.subject}
Time: {email.timestamp}

Body:
{email.body}
"""
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",  # Use gpt-4o for better accuracy
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=0.1,  # Low temperature for consistent classification
            response_format={"type": "json_object"}
        )
        
        import json
        result = json.loads(response.choices[0].message.content)
        return result
        
    except ImportError:
        print("⚠️  OpenAI not installed. Using rule-based fallback.")
        return rule_based_classify(email)
    except Exception as e:
        print(f"⚠️  GPT error: {e}. Using rule-based fallback.")
        return rule_based_classify(email)


def rule_based_classify(email: Email) -> dict:
    """
    Simple rule-based classifier as fallback.
    
    This demonstrates a baseline that doesn't require API keys.
    """
    subject_lower = email.subject.lower()
    body_lower = email.body.lower()
    sender_lower = email.sender.lower()
    
    # Spam detection
    spam_signals = [
        "won", "winner", "lottery", "prince", "nigeria",
        "urgent", "act now", "click here", "bank details",
        "million dollars", "congratulations", "free money"
    ]
    
    if any(signal in subject_lower or signal in body_lower for signal in spam_signals):
        # Check for phishing (fake domains)
        if "paypa1" in sender_lower or "amaz0n" in sender_lower:
            return {
                "category": "spam",
                "priority": "low",
                "action": "delete",
                "response": None,
                "reasoning": "Detected phishing attempt"
            }
        return {
            "category": "spam",
            "priority": "low", 
            "action": "delete",
            "response": None,
            "reasoning": "Detected spam keywords"
        }
    
    # Urgent detection
    urgent_signals = ["urgent", "critical", "immediately", "asap", "emergency", "today"]
    if any(signal in subject_lower or signal in body_lower for signal in urgent_signals):
        return {
            "category": "urgent",
            "priority": "critical",
            "action": "flag",
            "response": None,
            "reasoning": "Contains urgency indicators"
        }
    
    # Work detection (company domain)
    if "@company.com" in sender_lower:
        needs_response = "?" in email.body or "let me know" in body_lower
        return {
            "category": "work",
            "priority": "high" if "meeting" in body_lower else "medium",
            "action": "respond" if needs_response else "archive",
            "response": "Thanks for your email. I'll review and get back to you shortly." if needs_response else None,
            "reasoning": "Work email from company domain"
        }
    
    # Newsletter detection
    newsletter_signals = ["unsubscribe", "newsletter", "digest", "weekly", "daily"]
    if any(signal in body_lower for signal in newsletter_signals):
        return {
            "category": "newsletter",
            "priority": "low",
            "action": "archive",
            "response": None,
            "reasoning": "Contains newsletter indicators"
        }
    
    # Default to personal
    needs_response = "?" in email.body
    return {
        "category": "personal",
        "priority": "medium",
        "action": "respond" if needs_response else "archive",
        "response": "Thanks for reaching out! I'll get back to you soon." if needs_response else None,
        "reasoning": "Default classification"
    }


def gpt_result_to_action(email: Email, result: dict) -> EmailTriageAction:
    """Convert GPT's response dict to an EmailTriageAction."""
    return EmailTriageAction(
        email_id=email.id,
        category=EmailCategory(result["category"]),
        priority=EmailPriority(result["priority"]),
        action_type=EmailActionType(result["action"]),
        response_text=result.get("response"),
    )


# =============================================================================
# Main Agent Loop
# =============================================================================

async def run_agent(
    server_url: str = "http://localhost:8000",
    task_id: str = "easy",
    use_gpt: bool = True,
    verbose: bool = True,
):
    """
    Run the email triage agent.
    
    Args:
        server_url: URL of the environment server
        task_id: Task to perform ("easy", "medium", "hard")
        use_gpt: Whether to use GPT (True) or rule-based (False)
        verbose: Whether to print detailed output
    """
    print(f"\n{'='*60}")
    print(f"Email Triage Agent")
    print(f"Server: {server_url}")
    print(f"Task: {task_id}")
    print(f"Mode: {'GPT-4' if use_gpt else 'Rule-based'}")
    print(f"{'='*60}\n")
    
    async with EmailTriageEnv(server_url) as env:
        # Reset to start a new episode
        result = await env.reset(task_id=task_id)
        obs = result.observation
        
        print(f"📬 Starting task: {task_id}")
        print(f"📧 Total emails: {obs.emails_remaining}")
        print(f"\n{'-'*60}\n")
        
        step_count = 0
        total_reward = 0.0
        
        while not result.done and obs.current_email is not None:
            step_count += 1
            email = obs.current_email
            
            if verbose:
                print(f"📨 Email {step_count}:")
                print(f"   From: {email.sender}")
                print(f"   Subject: {email.subject[:50]}...")
            
            # Get classification decision
            if use_gpt:
                decision = await ask_gpt(email)
            else:
                decision = rule_based_classify(email)
            
            if verbose:
                print(f"   🤖 Decision: {decision['category']}/{decision['priority']}/{decision['action']}")
                print(f"   💭 Reasoning: {decision['reasoning']}")
            
            # Convert to action and step
            action = gpt_result_to_action(email, decision)
            result = await env.step(action)
            obs = result.observation
            reward = result.reward or 0.0
            
            total_reward += reward
            
            if verbose:
                print(f"   ⭐ Reward: {reward:.2f}")
                print(f"\n   Feedback:")
                for line in (obs.feedback or "").split("\n"):
                    print(f"   {line}")
                print(f"\n{'-'*60}\n")
        
        # Final summary
        print(f"\n{'='*60}")
        print(f"📊 FINAL RESULTS")
        print(f"{'='*60}")
        print(f"Emails processed: {step_count}")
        print(f"Total reward: {total_reward:.2f}")
        print(f"Average score: {obs.current_score:.1%}")
        print(f"{'='*60}\n")
        
        return obs.current_score


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Email Triage Agent")
    parser.add_argument(
        "--server", 
        default="http://localhost:8000",
        help="Environment server URL"
    )
    parser.add_argument(
        "--task",
        default="easy",
        choices=["easy", "medium", "hard"],
        help="Task difficulty level"
    )
    parser.add_argument(
        "--no-gpt",
        action="store_true",
        help="Use rule-based classifier instead of GPT"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Reduce output verbosity"
    )
    
    args = parser.parse_args()
    
    # Check for API key if using GPT
    if not args.no_gpt and not os.environ.get("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY not set. Using rule-based classifier.")
        args.no_gpt = True
    
    # Run the agent
    score = asyncio.run(
        run_agent(
            server_url=args.server,
            task_id=args.task,
            use_gpt=not args.no_gpt,
            verbose=not args.quiet,
        )
    )
    
    # Exit with non-zero if score is low
    sys.exit(0 if score >= 0.7 else 1)
