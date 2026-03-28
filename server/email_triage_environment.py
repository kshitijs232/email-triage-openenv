"""
Email Triage Environment - Server-Side Environment Logic

This contains the "game rules" - how actions are scored and what happens.
"""

import uuid
import random
from copy import deepcopy
from typing import Optional, Any

from openenv.core.env_server.interfaces import Environment

# Handle both relative and absolute imports
try:
    from ..models import (
        EmailTriageAction,
        EmailTriageObservation,
        EmailTriageState,
        Email,
        EmailCategory,
        EmailPriority,
        EmailActionType,
    )
    from .emails_data import TASK_EMAILS, TASK_DESCRIPTIONS
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from models import (
        EmailTriageAction,
        EmailTriageObservation,
        EmailTriageState,
        Email,
        EmailCategory,
        EmailPriority,
        EmailActionType,
    )
    from server.emails_data import TASK_EMAILS, TASK_DESCRIPTIONS


class EmailTriageEnvironment(Environment):
    """
    Server-side Email Triage Environment.
    
    The agent receives emails and must classify them correctly.
    This class knows the correct answers and computes rewards.
    """
    
    def __init__(self):
        """Initialize the environment."""
        self._episode_id: str = ""
        self._task_id: str = ""
        self._seed: Optional[int] = None
        
        # Email queue
        self._emails: list[Email] = []
        self._current_index: int = 0
        
        # Scoring
        self._total_reward: float = 0.0
        self._correct_categories: int = 0
        self._correct_priorities: int = 0
        self._correct_actions: int = 0
        self._emails_processed: int = 0
        
        # Status
        self._is_complete: bool = False
        self._last_feedback: Optional[str] = None
        self._last_reward: float = 0.0
    
    def reset(
        self, 
        *, 
        task_id: str = "easy", 
        seed: Optional[int] = None,
        **kwargs
    ) -> EmailTriageObservation:
        """
        Reset the environment for a new episode.
        
        Args:
            task_id: Task difficulty ("easy", "medium", "hard")
            seed: Random seed for reproducibility
            
        Returns:
            Initial observation with first email
        """
        # Validate task
        if task_id not in TASK_EMAILS:
            raise ValueError(f"Unknown task_id: {task_id}. Choose from: {list(TASK_EMAILS.keys())}")
        
        # Initialize episode
        self._episode_id = str(uuid.uuid4())[:8]
        self._task_id = task_id
        self._seed = seed
        
        # Load emails (deep copy to avoid mutation)
        self._emails = deepcopy(TASK_EMAILS[task_id])
        
        # Shuffle if seed provided
        if seed is not None:
            random.seed(seed)
            random.shuffle(self._emails)
        
        # Reset state
        self._current_index = 0
        self._total_reward = 0.0
        self._correct_categories = 0
        self._correct_priorities = 0
        self._correct_actions = 0
        self._emails_processed = 0
        self._is_complete = False
        self._last_feedback = f"Starting {task_id} task: {TASK_DESCRIPTIONS[task_id]}"
        self._last_reward = 0.0
        
        return self._build_observation()
    
    def step(self, action: EmailTriageAction) -> EmailTriageObservation:
        """
        Process agent's action and return result.
        
        Args:
            action: Agent's classification decision
            
        Returns:
            Observation with feedback, reward, and next email
        """
        if self._is_complete:
            return self._build_observation()
        
        if self._current_index >= len(self._emails):
            self._is_complete = True
            return self._build_observation()
        
        # Get current email and its correct answers
        current_email = self._emails[self._current_index]
        
        # Verify action is for correct email
        if action.email_id != current_email.id:
            # Return observation with error in feedback
            self._last_feedback = f"Error: Action email_id mismatch: expected {current_email.id}"
            self._last_reward = 0.0
            return self._build_observation()
        
        # Grade the action
        reward, feedback = self._grade_action(action, current_email)
        
        # Update state
        self._last_reward = reward
        self._last_feedback = feedback
        self._total_reward += reward
        self._emails_processed += 1
        self._current_index += 1
        
        # Check if complete
        done = self._current_index >= len(self._emails)
        if done:
            self._is_complete = True
            final_score = self._total_reward / len(self._emails) if self._emails else 0.0
            self._last_feedback += f"\n\n📊 Episode Complete! Final Score: {final_score:.1%}"
        
        return self._build_observation()
    
    def _grade_action(self, action: EmailTriageAction, email: Email) -> tuple[float, str]:
        """
        Grade the agent's action against ground truth.
        
        Returns:
            Tuple of (reward, feedback_string)
        """
        reward = 0.0
        feedback_parts = []
        
        # 1. Category (30% of score)
        if action.category == email.correct_category:
            reward += 0.30
            feedback_parts.append(f"✓ Category correct ({action.category.value})")
            self._correct_categories += 1
        else:
            feedback_parts.append(f"✗ Category: you said {action.category.value}, correct was {email.correct_category.value}")
        
        # 2. Priority (30% of score)
        priority_levels = list(EmailPriority)
        action_level = priority_levels.index(action.priority)
        correct_level = priority_levels.index(email.correct_priority)
        
        if action.priority == email.correct_priority:
            reward += 0.30
            feedback_parts.append(f"✓ Priority correct ({action.priority.value})")
            self._correct_priorities += 1
        elif abs(action_level - correct_level) == 1:
            reward += 0.15  # Partial credit for being close
            feedback_parts.append(f"◐ Priority close: you said {action.priority.value}, correct was {email.correct_priority.value}")
        else:
            feedback_parts.append(f"✗ Priority: you said {action.priority.value}, correct was {email.correct_priority.value}")
        
        # 3. Action type (20% of score)
        if action.action_type == email.correct_action:
            reward += 0.20
            feedback_parts.append(f"✓ Action correct ({action.action_type.value})")
            self._correct_actions += 1
        else:
            feedback_parts.append(f"✗ Action: you said {action.action_type.value}, correct was {email.correct_action.value}")
        
        # 4. Response handling (20% of score)
        if email.requires_response:
            if action.action_type == EmailActionType.RESPOND and action.response_text:
                reward += 0.20
                feedback_parts.append("✓ Response provided when needed")
            else:
                feedback_parts.append("✗ This email needed a response")
        else:
            if action.action_type != EmailActionType.RESPOND or not action.response_text:
                reward += 0.20
                feedback_parts.append("✓ Correctly didn't draft unnecessary response")
            else:
                feedback_parts.append("◐ Response was unnecessary for this email")
        
        feedback = f"Email: {email.subject[:40]}...\n" + "\n".join(feedback_parts)
        feedback += f"\n→ Reward: {reward:.2f}"
        
        return reward, feedback
    
    def _build_observation(self) -> EmailTriageObservation:
        """Build the observation to send to agent."""
        # Get next email (if any)
        current_email = None
        if self._current_index < len(self._emails):
            email = self._emails[self._current_index]
            # Send email without ground truth
            current_email = Email(
                id=email.id,
                sender=email.sender,
                subject=email.subject,
                body=email.body,
                timestamp=email.timestamp,
                # Note: correct_* fields are excluded by Pydantic
            )
        
        return EmailTriageObservation(
            current_email=current_email,
            feedback=self._last_feedback,
            reward=self._last_reward,
            current_score=self._total_reward / self._emails_processed if self._emails_processed > 0 else 0.0,
            emails_processed=self._emails_processed,
            emails_remaining=len(self._emails) - self._current_index,
            done=self._is_complete,
            task_id=self._task_id,
        )
    
    @property
    def state(self) -> EmailTriageState:
        """Return current environment state."""
        return EmailTriageState(
            episode_id=self._episode_id,
            task_id=self._task_id,
            seed=self._seed,
            current_email_index=self._current_index,
            total_emails=len(self._emails),
            emails_processed=self._emails_processed,
            total_reward=self._total_reward,
            correct_categories=self._correct_categories,
            correct_priorities=self._correct_priorities,
            correct_actions=self._correct_actions,
            is_complete=self._is_complete,
            final_score=self._total_reward / len(self._emails) if self._is_complete and self._emails else None,
        )
