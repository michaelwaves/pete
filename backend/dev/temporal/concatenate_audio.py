"""
Simple script to concatenate audio files.
This script serves as a convenient wrapper around the audio concatenation functionality.

Usage:
    python concatenate_audio.py file1.wav file2.wav ... [--output output.wav] [--delete]
"""

import sys
from utils.audio_utils import main as audio_utils_main

if __name__ == "__main__":
    # Inject 'concatenate' command if not provided
    if len(sys.argv) > 1 and not sys.argv[1] in ['concatenate', '-h', '--help']:
        sys.argv.insert(1, 'concatenate')
    
    # Execute the main function from audio_utils
    audio_utils_main() 