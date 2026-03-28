"""Server-side components for Email Triage Environment."""

# Handle both relative and absolute imports
try:
    from .email_triage_environment import EmailTriageEnvironment
    from .app import app
except ImportError:
    from server.email_triage_environment import EmailTriageEnvironment
    from server.app import app

__all__ = ["EmailTriageEnvironment", "app"]
