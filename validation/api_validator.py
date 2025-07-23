import os
from dotenv import load_dotenv
import subprocess
import requests 
from groq import Groq, APIStatusError, APIConnectionError
import tempfile
import subprocess
import os
import signal
import time
import psutil
from pathlib import Path
import subprocess
import json
import time
import os
import tempfile
import threading
from typing import Dict, Any


def is_groq_key_valid(key) -> bool:
    """Return True if the GROQ_API_KEY is valid, else False."""
    api_key = key
    if not api_key:
        return False

    client = Groq(api_key=api_key)
    try:
        # A lightweight call to validate the key – fetch available models
        client.models.list()
        return True
    except (APIStatusError, APIConnectionError):
        return False

def is_ngrok_authtoken_valid(token: str, config_path: str = None) -> bool:
    """
    Validate an ngrok auth token using pyngrok.

    Args:
        token: ngrok auth token (string).
        config_path: optional path to ngrok config file.

    Returns:
        True if token is valid (agent status reachable), False otherwise.
    """
    cfg = conf.PyngrokConfig()
    if config_path:
        cfg.config_path = config_path

    try:
        # Set and persist the token
        ngrok.set_auth_token(token, pyngrok_config=cfg)  # :contentReference[oaicite:1]{index=1}

        # Attempt a harmless API call to verify it works
        _ = agent.get_agent_status(pyngrok_config=cfg)  # requires valid token :contentReference[oaicite:2]{index=2}

        return True

    except (PyngrokNgrokHTTPError, PyngrokError):
        # Happens when auth fails or agent isn't reachable
        return False


if __name__ == "__main__":

    print(is_ngrok_authtoken_valid())
    # print(is_groq_key_valid())