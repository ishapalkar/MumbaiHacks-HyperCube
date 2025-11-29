"""Package initialization for the TokenTrust app.

This module ensures environment variables from the project's top-level
.env file are loaded when the package is imported. That prevents code in
submodules (like `agents.risk_agent` or `llms.groq_client`) from seeing
empty environments when the process is started from the `app/` folder or
when imports happen before a separate call to `load_dotenv()`.
"""
from dotenv import load_dotenv, find_dotenv
import logging

# Load the nearest .env file (searches upward) so package imports get env vars.
load_dotenv(find_dotenv())

# Basic package logger
logger = logging.getLogger(__name__)
logger.debug("Loaded environment from .env (if present)")
