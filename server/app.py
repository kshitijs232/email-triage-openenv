"""
Email Triage Environment - FastAPI Server

This single line creates all HTTP endpoints:
- POST /reset  -> env.reset()
- POST /step   -> env.step(action)  
- GET  /state  -> env.state
- GET  /health -> health check
- WS   /ws     -> WebSocket connection
"""

from openenv.core.env_server import create_app

# Handle both relative and absolute imports
try:
    from .email_triage_environment import EmailTriageEnvironment
    from ..models import EmailTriageAction, EmailTriageObservation
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from server.email_triage_environment import EmailTriageEnvironment
    from models import EmailTriageAction, EmailTriageObservation


# This creates the complete FastAPI application
app = create_app(
    EmailTriageEnvironment,
    EmailTriageAction,
    EmailTriageObservation
)


def main():
    """Entry point for the server."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
