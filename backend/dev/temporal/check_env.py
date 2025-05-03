"""
Environment configuration checker.

This script checks the environment configuration and validates API keys.
"""

import os
import sys
import platform
import logging
from dotenv import load_dotenv

def check_env_variable(name, is_secret=False, min_length=None, required=True):
    """Check if an environment variable is set and valid."""
    value = os.getenv(name)
    
    if value is None:
        if required:
            print(f"❌ {name}: Not set")
            return False
        else:
            print(f"⚠️ {name}: Not set (optional)")
            return True
    
    # For secrets, show only first and last few characters
    if is_secret and len(value) > 8:
        display_value = f"{value[:4]}...{value[-4:]}"
    elif is_secret:
        display_value = "****"
    else:
        display_value = value
    
    # Check minimum length
    if min_length and len(value) < min_length:
        print(f"❌ {name}: Set but too short (expected at least {min_length} chars, got {len(value)})")
        return False
    
    print(f"✓ {name}: {display_value}")
    return True

def main():
    """Main function to check environment configuration."""
    # Load environment variables from .env file
    load_dotenv()
    
    print("=== Environment Configuration Checker ===")
    print(f"Python version: {platform.python_version()}")
    print(f"Operating system: {platform.system()} {platform.release()}")
    print("")
    
    # Check directories
    print("=== Directory Structure ===")
    for directory in ["results", "results/audio"]:
        if os.path.exists(directory):
            print(f"✓ {directory}: Found")
        else:
            print(f"❌ {directory}: Not found")
            try:
                os.makedirs(directory, exist_ok=True)
                print(f"  ✓ Created {directory}")
            except Exception as e:
                print(f"  ❌ Failed to create {directory}: {str(e)}")
    
    print("")
    
    # Check environment variables
    print("=== API Keys and Configuration ===")
    # Check Temporal configuration
    temporal_ok = check_env_variable("TEMPORAL_HOST", required=False) 
    temporal_ok &= check_env_variable("TEMPORAL_NAMESPACE", required=False)
    temporal_ok &= check_env_variable("TEMPORAL_API_KEY", is_secret=True, required=False)
    
    # Check Rime.ai API key (critical for audio generation)
    rime_ok = check_env_variable("RIME_API_KEY", is_secret=True, min_length=10)
    
    # Check Google API key (for Gemini)
    google_ok = check_env_variable("GOOGLE_API_KEY", is_secret=True, min_length=10)
    
    print("")
    
    # Summary
    print("=== Configuration Summary ===")
    if temporal_ok:
        print("✓ Temporal configuration is valid")
    else:
        print("⚠️ Temporal configuration may be incomplete")
    
    if rime_ok:
        print("✓ Rime.ai API key is configured")
    else:
        print("❌ Rime.ai API key is missing or invalid")
        print("  Please set the RIME_API_KEY environment variable or add it to your .env file.")
        print("  You can get an API key from https://rime.ai")
    
    if google_ok:
        print("✓ Google API key is configured")
    else:
        print("❌ Google API key is missing or invalid")
        print("  Please set the GOOGLE_API_KEY environment variable or add it to your .env file.")
    
    print("")
    
    # Final advice
    if not rime_ok:
        print("To fix the Rime.ai API key issue:")
        print("1. Get a valid API key from Rime.ai")
        print("2. Add it to your .env file like this: RIME_API_KEY=your_api_key_here")
        print("3. Run this script again to verify the configuration")
        print("4. Test the API with: python test_rime_api.py")
    else:
        print("Configuration looks good! You can now:")
        print("1. Test the Rime.ai API with: python test_rime_api.py")
        print("2. Run the worker with: uv run worker.py")
        print("3. List audio files with: python list_audio_files.py")
    
    return 0 if rime_ok and google_ok else 1

if __name__ == "__main__":
    sys.exit(main()) 