"""
Email Triage Environment

A learning environment for training AI agents to manage email inboxes.
"""

# Handle both relative and absolute imports
try:
    from .client import (
        EmailTriageEnv,
        EmailTriageAction,
        EmailTriageObservation,
        EmailTriageState,
        Email,
        EmailCategory,
        EmailPriority,
        EmailActionType,
    )
except ImportError:
    from client import (
        EmailTriageEnv,
        EmailTriageAction,
        EmailTriageObservation,
        EmailTriageState,
        Email,
        EmailCategory,
        EmailPriority,
        EmailActionType,
    )

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

__version__ = "0.1.0"
