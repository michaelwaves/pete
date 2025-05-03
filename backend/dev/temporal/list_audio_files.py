"""
Utility script to list and manage audio files in the results directory.

This script helps you:
1. List all WAV files in the results/audio directory
2. View information about the audio files
3. Concatenate selected files using the concatenate_audio utility
"""

import os
import sys
import glob
import wave
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict

def get_audio_info(wav_path: str) -> Dict:
    """
    Get information about a WAV file.
    
    Args:
        wav_path: Path to the WAV file
        
    Returns:
        Dictionary containing audio information
    """
    try:
        with wave.open(wav_path, 'rb') as wav_file:
            # Get basic parameters
            channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            frame_rate = wav_file.getframerate()
            n_frames = wav_file.getnframes()
            
            # Calculate duration in seconds
            duration = n_frames / frame_rate
            
            # Get file size and creation time
            file_size = os.path.getsize(wav_path)
            creation_time = os.path.getctime(wav_path)
            modified_time = os.path.getmtime(wav_path)
            
            return {
                'path': wav_path,
                'filename': os.path.basename(wav_path),
                'channels': channels,
                'sample_width': sample_width,
                'frame_rate': frame_rate,
                'n_frames': n_frames,
                'duration': duration,
                'file_size': file_size,
                'created': datetime.fromtimestamp(creation_time),
                'modified': datetime.fromtimestamp(modified_time)
            }
    except Exception as e:
        return {
            'path': wav_path,
            'filename': os.path.basename(wav_path),
            'error': str(e)
        }

def list_audio_files(directory: str = "results/audio", pattern: str = "*.wav") -> List[Dict]:
    """
    List all audio files in the specified directory.
    
    Args:
        directory: Directory to search for audio files
        pattern: File pattern to match
        
    Returns:
        List of dictionaries containing file information
    """
    # Make sure directory exists
    if not os.path.exists(directory):
        print(f"Directory {directory} does not exist")
        return []
    
    # Find all matching files
    file_pattern = os.path.join(directory, pattern)
    files = glob.glob(file_pattern)
    
    # Sort by modification time (newest first)
    files.sort(key=os.path.getmtime, reverse=True)
    
    # Get information about each file
    return [get_audio_info(f) for f in files]

def format_size(size_bytes: int) -> str:
    """Format file size in a human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024 or unit == 'GB':
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024

def format_duration(seconds: float) -> str:
    """Format duration in minutes:seconds format."""
    minutes = int(seconds / 60)
    seconds = int(seconds % 60)
    return f"{minutes}:{seconds:02d}"

def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(description="List and manage audio files")
    parser.add_argument("--dir", default="results/audio", help="Directory to search for audio files")
    parser.add_argument("--pattern", default="*.wav", help="File pattern to match")
    parser.add_argument("--concat", action="store_true", help="Show instructions for concatenating files")
    
    args = parser.parse_args()
    
    # List audio files
    audio_files = list_audio_files(args.dir, args.pattern)
    
    if not audio_files:
        print(f"No audio files found in {args.dir} matching pattern {args.pattern}")
        return 1
    
    # Print information about the files
    print(f"\n=== Audio Files in {args.dir} ===")
    print(f"Found {len(audio_files)} files matching pattern {args.pattern}\n")
    
    print(f"{'#':<3} {'Filename':<40} {'Duration':<8} {'Size':<10} {'Modified':<20}")
    print("-" * 90)
    
    for i, file_info in enumerate(audio_files):
        if 'error' in file_info:
            print(f"{i+1:<3} {file_info['filename']:<40} ERROR: {file_info['error']}")
        else:
            print(f"{i+1:<3} {file_info['filename']:<40} {format_duration(file_info['duration']):<8} "
                  f"{format_size(file_info['file_size']):<10} {file_info['modified'].strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Show concatenation instructions if requested
    if args.concat and len(audio_files) > 1:
        print("\n=== Audio Concatenation Instructions ===")
        print("To concatenate files, use the concatenate_audio.py script:")
        
        # Create example command with the first 2 files
        example_files = [file_info['path'] for file_info in audio_files[:2]]
        example_cmd = "python concatenate_audio.py " + " ".join([f'"{f}"' for f in example_files])
        print(f"\nExample: {example_cmd}\n")
        
        print("You can specify an output file with --output:")
        print(f"{example_cmd} --output \"results/audio/combined_output.wav\"\n")
        
        print("To delete original files after concatenation, add --delete")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 