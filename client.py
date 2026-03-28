"""
Email Triage Environment - Client

This is the CLIENT-SIDE code that communicates with the server.
It extends EnvClient to handle HTTP/WebSocket communication.
"""

from typing import Any
from openenv.core.env_client import EnvClient
from openenv.core.client_types import StepResult

# Handle both relative and absolute imports
try:
    from .models import (
        EmailTriageAction,
        EmailTriageObservation,
        EmailTriageState,
        Email,
        EmailCategory,
        EmailPriority,
        EmailActionType,
    )
except ImportError:
    from models import (
        EmailTriageAction,
        EmailTriageObservation,
        EmailTriageState,
        Email,
        EmailCategory,
        EmailPriority,
        EmailActionType,
    )


class EmailTriageEnv(EnvClient[EmailTriageAction, EmailTriageObservation, EmailTriageState]):
    """
    Client for the Email Triage Environment.
    
    Provides a clean Python API while handling HTTP communication internally.
    
    Example:
        async with EmailTriageEnv("http://localhost:8000") as env:
            obs = await env.reset(task_id="easy")
            while not obs.done:
                action = decide_action(obs.current_email)
                obs, reward, done, truncated, info = await env.step(action)
    """
    
    def _step_payload(self, action: EmailTriageAction) -> dict[str, Any]:
        """
        Convert Action object to JSON for HTTP request.
        
        Called automatically when you call env.step(action).
        """
        return {
            "email_id": action.email_id,
            "category": action.category.value,
            "priority": action.priority.value,
            "action_type": action.action_type.value,
            "response_text": action.response_text,
        }
    
    def _parse_result(self, payload: dict[str, Any]) -> StepResult[EmailTriageObservation]:
        """
        Convert JSON response to StepResult with Observation object.
        
        Called automatically when server responds.
        Server returns: {"observation": {...}, "reward": float, "done": bool}
        """
        # Get observation data from the payload
        obs_data = payload.get("observation", payload)
        
        # Parse the current email if present
        current_email = None
        if obs_data.get("current_email"):
            email_data = obs_data["current_email"]
            current_email = Email(
                id=email_data["id"],
                sender=email_data["sender"],
                subject=email_data["subject"],
                body=email_data["body"],
                timestamp=email_data["timestamp"],
            )
        
        obs = EmailTriageObservation(
            current_email=current_email,
            feedback=obs_data.get("feedback"),
            reward=obs_data.get("reward", 0.0),
            current_score=obs_data.get("current_score", 0.0),
            emails_processed=obs_data.get("emails_processed", 0),
            emails_remaining=obs_data.get("emails_remaining", 0),
            done=obs_data.get("done", False),
            task_id=obs_data.get("task_id"),
        )
        
        return StepResult(
            observation=obs,
            reward=payload.get("reward", 0.0),
            done=payload.get("done", False),
        )
    
    def _parse_state(self, payload: dict[str, Any]) -> EmailTriageState:
        """
        Convert JSON response to State object.
        
        Called when you access env.state.
        """
        return EmailTriageState(
            episode_id=payload.get("episode_id", "unknown"),
            task_id=payload.get("task_id", "unknown"),
            seed=payload.get("seed"),
            current_email_index=payload.get("current_email_index", 0),
            total_emails=payload.get("total_emails", 0),
            emails_processed=payload.get("emails_processed", 0),
            total_reward=payload.get("total_reward", 0.0),
            correct_categories=payload.get("correct_categories", 0),
            correct_priorities=payload.get("correct_priorities", 0),
            correct_actions=payload.get("correct_actions", 0),
            is_complete=payload.get("is_complete", False),
            final_score=payload.get("final_score"),
        )


# Convenience exports
__all__ = [
    "EmailTriageEnv",
    "EmailTriageAction",
    "EmailTriageObservation",
    "EmailTriageState",
    "Email",
    "EmailCategory",
    "EmailPriority", 
    "EmailActionType",
]
