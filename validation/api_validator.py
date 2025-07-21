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


def validate_ngrok_authtoken_real(token: str, timeout: int = 10) -> Dict[str, Any]:
    """
    Validates ngrok authtoken by actually testing it with ngrok commands.
    
    Args:
        token (str): The authtoken to validate
        timeout (int): Timeout in seconds for the validation test
        
    Returns:
        dict: {
            'valid': bool,
            'error': str or None,
            'method': str (how validation was performed)
        }
    """
    
    if not token or not isinstance(token, str):
        return {
            'valid': False,
            'error': 'Token is empty or not a string',
            'method': 'input_validation'
        }
    
    token = token.strip()
    
    # Method 1: Try to set the authtoken and test with a quick command
    try:
        # First, try to configure the authtoken
        config_result = subprocess.run(
            ['ngrok', 'config', 'add-authtoken', token],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if config_result.returncode != 0:
            return {
                'valid': False,
                'error': f'Failed to set authtoken: {config_result.stderr}',
                'method': 'config_command'
            }
        
        # Method 2: Try to get account info (quick validation)
        try:
            account_result = subprocess.run(
                ['ngrok', 'api', 'credentials', 'list'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if account_result.returncode == 0:
                return {
                    'valid': True,
                    'error': None,
                    'method': 'api_credentials'
                }
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            pass  # Try next method
        
        # Method 3: Try to start a tunnel briefly to test authentication
        return _test_tunnel_authentication(token, timeout)
        
    except subprocess.TimeoutExpired:
        return {
            'valid': False,
            'error': 'Timeout while configuring authtoken',
            'method': 'config_timeout'
        }
    except FileNotFoundError:
        return {
            'valid': False,
            'error': 'ngrok command not found. Please install ngrok first.',
            'method': 'ngrok_not_found'
        }
    except Exception as e:
        return {
            'valid': False,
            'error': f'Unexpected error: {str(e)}',
            'method': 'exception'
        }

def _test_tunnel_authentication(token: str, timeout: int) -> Dict[str, Any]:
    """
    Test authentication by attempting to start a tunnel briefly.
    """
    tunnel_process = None
    try:
        # Try to start ngrok with a high port (likely unused)
        tunnel_process = subprocess.Popen(
            ['ngrok', 'http', '65432'],  # High port number, likely unused
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a bit for ngrok to start and authenticate
        time.sleep(3)
        
        # Check if process is still running (good sign)
        if tunnel_process.poll() is None:
            # Process is running, likely authenticated successfully
            tunnel_process.terminate()
            tunnel_process.wait(timeout=2)
            return {
                'valid': True,
                'error': None,
                'method': 'tunnel_test'
            }
        else:
            # Process terminated, check output for errors
            stdout, stderr = tunnel_process.communicate()
            
            # Check for authentication errors
            combined_output = (stdout + stderr).lower()
            if 'authentication failed' in combined_output or 'authtoken' in combined_output:
                return {
                    'valid': False,
                    'error': 'Authentication failed - invalid authtoken',
                    'method': 'tunnel_auth_error'
                }
            else:
                # Some other error, but not necessarily auth-related
                return {
                    'valid': True,  # Assume valid if no auth error
                    'error': None,
                    'method': 'tunnel_other_error'
                }
                
    except Exception as e:
        return {
            'valid': False,
            'error': f'Error testing tunnel: {str(e)}',
            'method': 'tunnel_exception'
        }
    finally:
        # Clean up process if still running
        if tunnel_process and tunnel_process.poll() is None:
            try:
                tunnel_process.terminate()
                tunnel_process.wait(timeout=2)
            except:
                tunnel_process.kill()

def is_ngrok_authtoken_valid(token) -> bool:
    """
    Simple boolean function to check if ngrok authtoken is valid.
    
    Args:
        token (str): The authtoken to validate
        
    Returns:
        bool: True if valid, False otherwise
    """

    if not token: 
        return False
    
    result = validate_ngrok_authtoken_real(token)

    if result['valid']:
        validate_and_setup_ngrok(token)
    return result['valid']

# Advanced usage with custom validation
def validate_and_setup_ngrok(token: str) -> Dict[str, Any]:
    """
    Validates token and sets it up if valid.
    
    Returns:
        dict: Validation result with setup status
    """
    validation = validate_ngrok_authtoken_real(token)
    
    if validation['valid']:
        try:
            # If valid, ensure it's properly configured
            subprocess.run(['ngrok', 'config', 'add-authtoken', token], 
                         capture_output=True, check=True)
            validation['setup_complete'] = True
        except subprocess.CalledProcessError:
            validation['setup_complete'] = False
    
    return validation


if __name__ == "__main__":

    print(is_ngrok_authtoken_valid())
    # print(is_groq_key_valid())