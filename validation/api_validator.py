import os
from dotenv import load_dotenv
import subprocess
import requests 
load_dotenv()
from groq import Groq, APIStatusError, APIConnectionError
import tempfile
import subprocess
import os
import signal
import time
import psutil
from pathlib import Path

def is_groq_key_valid() -> bool:
    """Return True if the GROQ_API_KEY is valid, else False."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return False

    client = Groq(api_key=api_key)
    try:
        # A lightweight call to validate the key – fetch available models
        client.models.list()
        return True
    except (APIStatusError, APIConnectionError):
        return False

import subprocess
import os
import signal
import time
import psutil
from pathlib import Path

def setup_ngrok_tunnel(token, port=5000):
    """
    Setup ngrok tunnel with the provided token.
    
    Args:
        token (str): The ngrok authtoken
        port (int): The port to expose (default: 5000)
    
    Returns:
        bool: True if tunnel is successfully established, False if authentication fails
    """
    
    def kill_ngrok_processes():
        """Kill all existing ngrok processes"""
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if 'ngrok' in proc.info['name'].lower():
                    proc.kill()
                    print(f"Killed ngrok process: {proc.info['pid']}")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    
    def remove_authtoken():
        """Remove authtoken from ngrok configuration"""
        try:
            # Get the ngrok config file path
            config_path = Path.home() / "Library" / "Application Support" / "ngrok" / "ngrok.yml"
            
            if config_path.exists():
                # Read the current config
                with open(config_path, 'r') as f:
                    content = f.read()
                
                # Remove authtoken line
                lines = content.split('\n')
                filtered_lines = [line for line in lines if not line.strip().startswith('authtoken:')]
                
                # Write back the filtered content
                with open(config_path, 'w') as f:
                    f.write('\n'.join(filtered_lines))
                
                print("Authtoken removed from configuration")
            else:
                print("Ngrok config file not found")
                
        except Exception as e:
            print(f"Error removing authtoken: {e}")
    
    try:
        # Kill any existing ngrok processes first
        kill_ngrok_processes()
        time.sleep(2)  # Wait for processes to terminate
        
        # Step 1: Add the authtoken
        print("Adding authtoken to ngrok configuration...")
        add_token_cmd = ['ngrok', 'config', 'add-authtoken', token]
        result = subprocess.run(add_token_cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            print(f"Error adding authtoken: {result.stderr}")
            return False
        
        print("Authtoken added successfully")
        
        # Step 2: Start the HTTP tunnel
        print(f"Starting ngrok HTTP tunnel on port {port}...")
        tunnel_cmd = ['ngrok', 'http', str(port)]
        
        # Start ngrok as a background process
        process = subprocess.Popen(
            tunnel_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a bit for ngrok to start and check for errors
        time.sleep(3)
        
        # Check if the process is still running
        if process.poll() is None:
            print(f"Ngrok tunnel started successfully on port {port}")
            print(f"Process ID: {process.pid}")
            
            # Kill the process since we just wanted to test it
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            
            return True
        else:
            # Process has terminated, check for errors
            stdout, stderr = process.communicate()
            error_output = stderr + stdout
            
            # Check for authentication errors
            if "authentication failed" in error_output or "ERR_NGROK_105" in error_output:
                print("Authentication failed - invalid authtoken")
                print("Removing invalid authtoken from configuration...")
                remove_authtoken()
                return False
            else:
                print(f"Ngrok failed with error: {error_output}")
                return False
                
    except subprocess.TimeoutExpired:
        print("Ngrok command timed out")
        return False
    except FileNotFoundError:
        print("Ngrok not found. Please install ngrok first.")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

# Example usage
if __name__ == "__main__":
    # Test with a sample token
    test_token = os.getenv("NGROK_AUTH_TOKEN")
    print(test_token)
    
    success = setup_ngrok_tunnel(test_token)
    
    if success:
        print("✅ Ngrok tunnel setup successful!")
    else:
        print("❌ Ngrok tunnel setup failed!")