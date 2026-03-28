"""
Email Triage Environment - Data Models

These models define the contract between client and server:
- Action: What the agent sends
- Observation: What the agent receives
- State: Internal tracking information
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class EmailCategory(str, Enum):
    """Email categories for triage."""
    SPAM = "spam"
    WORK = "work"
    PERSONAL = "personal"
    NEWSLETTER = "newsletter"
    URGENT = "urgent"


class EmailPriority(str, Enum):
    """Priority levels for emails."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EmailActionType(str, Enum):
    """Actions that can be taken on emails."""
    ARCHIVE = "archive"
    RESPOND = "respond"
    FLAG = "flag"
    DELETE = "delete"


class Email(BaseModel):
    """A single email to be triaged."""
    id: str = Field(..., description="Unique email identifier")
    sender: str = Field(..., description="Sender email address")
    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Email body content")
    timestamp: str = Field(..., description="When the email was received")
    
    # Ground truth (only known to server)
    correct_category: Optional[EmailCategory] = Field(None, exclude=True)
    correct_priority: Optional[EmailPriority] = Field(None, exclude=True)
    correct_action: Optional[EmailActionType] = Field(None, exclude=True)
    requires_response: Optional[bool] = Field(None, exclude=True)


class EmailTriageAction(BaseModel):
    """
    ACTION: What the agent sends to the environment.
    
    The agent decides how to categorize and handle each email.
    """
    email_id: str = Field(..., description="ID of the email being triaged")
    category: EmailCategory = Field(..., description="Classified category")
    priority: EmailPriority = Field(..., description="Assigned priority level")
    action_type: EmailActionType = Field(..., description="Action to take")
    response_text: Optional[str] = Field(
        None, 
        description="Draft response if action_type is 'respond'"
    )


class EmailTriageObservation(BaseModel):
    """
    OBSERVATION: What the agent receives from the environment.
    
    Contains the next email to process plus feedback on the last action.
    """
    # Current email to process
    current_email: Optional[Email] = Field(
        None, 
        description="Next email to triage (None if inbox empty)"
    )
    
    # Feedback from last action
    feedback: Optional[str] = Field(
        None, 
        description="Feedback on the previous action"
    )
    reward: float = Field(
        default=0.0, 
        description="Reward from last action (0.0 to 1.0)"
    )
    
    # Progress tracking
    current_score: float = Field(
        default=0.0, 
        description="Running average score"
    )
    emails_processed: int = Field(
        default=0, 
        description="Number of emails processed"
    )
    emails_remaining: int = Field(
        default=0, 
        description="Emails left in inbox"
    )
    
    # Episode status
    done: bool = Field(
        default=False, 
        description="True when inbox is empty"
    )
    task_id: Optional[str] = Field(
        None, 
        description="Current task identifier"
    )


class EmailTriageState(BaseModel):
    """
    STATE: Internal environment state.
    
    Used for tracking progress and reproducibility.
    """
    episode_id: str = Field(..., description="Unique episode identifier")
    task_id: str = Field(..., description="Current task being performed")
    seed: Optional[int] = Field(None, description="Random seed for reproducibility")
    
    # Progress
    current_email_index: int = Field(default=0, description="Index of current email")
    total_emails: int = Field(default=0, description="Total emails in task")
    emails_processed: int = Field(default=0, description="Emails completed")
    
    # Scoring
    total_reward: float = Field(default=0.0, description="Sum of all rewards")
    correct_categories: int = Field(default=0, description="Correct category predictions")
    correct_priorities: int = Field(default=0, description="Correct priority predictions")
    correct_actions: int = Field(default=0, description="Correct action predictions")
    
    # Status
    is_complete: bool = Field(default=False, description="Episode complete")
    final_score: Optional[float] = Field(None, description="Final average score")
