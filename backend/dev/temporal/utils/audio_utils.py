"""
Audio utility functions for working with audio files outside of Temporal activities.
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import List, Optional

def setup_logging():
    """Set up basic logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
        ]
    )

def concatenate_wav_files(wav_files: List[str], output_path: str) -> str:
    """
    Concatenate multiple WAV files into a single WAV file.
    
    Args:
        wav_files: List of paths to WAV files to concatenate
        output_path: Path to save the concatenated WAV file
        
    Returns:
        Path to the concatenated WAV file
    """
    if not wav_files:
        raise ValueError("No WAV files provided for concatenation")
    
    if len(wav_files) == 1:
        # If there's only one file, just copy it
        import shutil
        shutil.copy2(wav_files[0], output_path)
        return output_path
    
    import wave
    
    # Get info from the first file
    with wave.open(wav_files[0], 'rb') as first_wav:
        params = first_wav.getparams()
    
    # Open output file with same parameters as the first file
    with wave.open(output_path, 'wb') as output_wav:
        output_wav.setparams(params)
        
        # Write data from each file
        for wav_file in wav_files:
            with wave.open(wav_file, 'rb') as input_wav:
                # Check if parameters match
                if input_wav.getparams() != params:
                    logging.warning(f"WAV file {wav_file} has different parameters than the first file. Results may be unpredictable.")
                
                # Read and write all frames
                output_wav.writeframes(input_wav.readframes(input_wav.getnframes()))
    
    logging.info(f"Successfully concatenated {len(wav_files)} WAV files into: {output_path}")
    return output_path

def concatenate_audio_files(
    audio_files: List[str],
    output_path: Optional[str] = None,
    delete_originals: bool = False
) -> dict:
    """
    Concatenate multiple audio files into a single file.
    
    Args:
        audio_files: List of paths to audio files to concatenate
        output_path: Path to save the concatenated audio file (optional)
        delete_originals: Whether to delete the original files after concatenation
        
    Returns:
        dict: Information about the concatenated audio file
    """
    if not audio_files:
        return {
            "success": False,
            "error": "No audio files provided for concatenation"
        }
    
    # Check that all files exist
    for file_path in audio_files:
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"File not found: {file_path}"
            }
    
    # Check that all files are WAV files
    for file_path in audio_files:
        if not file_path.lower().endswith('.wav'):
            return {
                "success": False,
                "error": f"File is not a WAV file: {file_path}"
            }
    
    try:
        # If no output path is provided, create one based on the first file
        if not output_path:
            first_file_path = Path(audio_files[0])
            base_dir = first_file_path.parent
            
            # Create a filename without the part number
            filename = first_file_path.stem
            if "_part" in filename:
                filename = filename.split("_part")[0]
            
            output_path = str(base_dir / f"{filename}_combined.wav")
        
        # Make sure the output path has a .wav extension
        output_path = str(Path(output_path).with_suffix('.wav'))
        
        # Concatenate the WAV files
        concatenated_path = concatenate_wav_files(audio_files, output_path)
        
        # Delete original files if requested
        if delete_originals:
            for file_path in audio_files:
                try:
                    if os.path.exists(file_path) and file_path != concatenated_path:
                        os.remove(file_path)
                        logging.info(f"Deleted original file: {file_path}")
                except Exception as e:
                    logging.warning(f"Failed to delete original file {file_path}: {str(e)}")
        
        # Get file size
        file_size = os.path.getsize(concatenated_path)
        
        return {
            "success": True,
            "audio_file": concatenated_path,
            "original_files": len(audio_files),
            "file_size_bytes": file_size,
            "originals_deleted": delete_originals
        }
    
    except Exception as e:
        logging.error(f"Error concatenating audio files: {str(e)}")
        return {
            "success": False,
            "error": f"Audio concatenation failed: {str(e)}"
        }

def main():
    """Command-line entry point for audio utilities."""
    parser = argparse.ArgumentParser(description="Audio utilities for working with audio files")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Concatenate command
    concat_parser = subparsers.add_parser("concatenate", help="Concatenate WAV files")
    concat_parser.add_argument("files", nargs="+", help="List of WAV files to concatenate")
    concat_parser.add_argument("-o", "--output", help="Output file path")
    concat_parser.add_argument("-d", "--delete", action="store_true", help="Delete original files after concatenation")
    
    args = parser.parse_args()
    
    setup_logging()
    
    if args.command == "concatenate":
        logging.info(f"Concatenating {len(args.files)} files...")
        result = concatenate_audio_files(args.files, args.output, args.delete)
        
        if result["success"]:
            print(f"Successfully concatenated files to: {result['audio_file']}")
            print(f"File size: {result['file_size_bytes'] / 1024 / 1024:.2f} MB")
        else:
            print(f"Error: {result['error']}")
            sys.exit(1)
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 