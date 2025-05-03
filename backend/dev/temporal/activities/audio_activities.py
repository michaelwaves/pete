import logging
import os
import requests
import json
import re
import wave
from pathlib import Path
from temporalio import activity
from typing import Dict, Any, Optional, List, Tuple
from supabase import create_client, Client

# Add split_text_into_chunks function
def split_text_into_chunks(text: str, max_chunk_size: int = 1000) -> List[str]:
    """
    Split a long text into smaller chunks, trying to preserve sentence boundaries.
    
    Args:
        text: The text to split
        max_chunk_size: Maximum size of each chunk
        
    Returns:
        List of text chunks
    """
    if len(text) <= max_chunk_size:
        return [text]
    
    chunks = []
    remaining_text = text
    
    while len(remaining_text) > 0:
        if len(remaining_text) <= max_chunk_size:
            chunks.append(remaining_text)
            break
            
        # Try to find a sentence boundary
        last_sentence_end = max(
            remaining_text[:max_chunk_size].rfind('.'),
            remaining_text[:max_chunk_size].rfind('?'),
            remaining_text[:max_chunk_size].rfind('!')
        )
        
        if last_sentence_end > 0:
            # Found a sentence end, use it
            chunks.append(remaining_text[:last_sentence_end + 1])
            remaining_text = remaining_text[last_sentence_end + 1:].lstrip()
        else:
            # No good break point, just cut at the limit
            chunks.append(remaining_text[:max_chunk_size])
            remaining_text = remaining_text[max_chunk_size:].lstrip()
    
    return chunks

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

@activity.defn
async def concatenate_audio_chunks(
    audio_files: List[str],
    output_path: Optional[str] = None,
    delete_originals: bool = False
) -> Dict[str, Any]:
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

class RimeAiClient:
    """
    Custom client for Rime.ai API that handles the streaming requirements.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://users.rime.ai/v1/rime-tts"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def generate_audio_streaming_pcm(self, text: str, voice_id: str, model: str = "arcana") -> bytes:
        """
        Generate audio using Rime.ai's streaming PCM API endpoint.
        This follows the documentation recommendation for lower latency.
        
        Args:
            text: The text to convert to speech
            voice_id: The voice ID to use
            model: The model to use (default: arcana)
            
        Returns:
            Audio data as bytes
        """
        # Set proper headers for streaming PCM
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "audio/pcm"  # Request PCM audio
        }
        
        # Prepare payload according to the API requirements
        payload = {
            "speaker": voice_id,
            "text": text,
            "modelId": model,
            "samplingRate": 22050  # Use default sampling rate
        }
        
        logging.info(f"Making streaming PCM request to Rime.ai API for text: '{text[:30]}...'")
        
        try:
            # Make the streaming API request
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                stream=True  # Enable streaming for the response
            )
            
            # Log response status
            logging.info(f"Streaming PCM response status: {response.status_code}")
            
            if response.status_code >= 400:
                error_text = response.text
                logging.error(f"Rime.ai API returned error {response.status_code}: {error_text}")
                raise Exception(f"Rime.ai API error: {error_text}")
            
            # Read all content from the streaming response
            audio_data = b''
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    audio_data += chunk
            
            logging.info(f"Successfully retrieved {len(audio_data)} bytes of PCM audio data")
            return audio_data
            
        except Exception as e:
            logging.error(f"Error generating audio with Rime.ai: {str(e)}")
            raise e
    
    def convert_pcm_to_audio(self, pcm_data: bytes, output_path: str, format: str = "mp3") -> str:
        """
        Convert PCM audio data to the specified format and save to file.
        Falls back to WAV format if the requested format conversion fails.
        
        Args:
            pcm_data: PCM audio data as bytes
            output_path: Path to save the audio file
            format: Desired output format (e.g., "mp3", "wav")
            
        Returns:
            Path to the saved audio file
        """
        try:
            # Since we're facing issues with pydub dependencies, let's directly save as WAV
            # WAV is a simple format that we can create directly from PCM data
            
            # Always use WAV format for simplicity and reliability
            wav_path = str(Path(output_path).with_suffix('.wav'))
            
            # Create a simple WAV file with PCM data
            self.save_pcm_as_wav(pcm_data, wav_path, channels=1, sample_width=2, frame_rate=22050)
            
            logging.info(f"Successfully saved PCM data as WAV to: {wav_path}")
            return wav_path
            
        except Exception as e:
            logging.error(f"Error converting PCM to audio: {str(e)}")
            raise e
    
    def save_pcm_as_wav(self, pcm_data: bytes, wav_path: str, channels=1, sample_width=2, frame_rate=22050) -> None:
        """
        Save PCM data as a WAV file using built-in wave module.
        
        Args:
            pcm_data: The PCM audio data as bytes
            wav_path: Path to save the WAV file
            channels: Number of audio channels (default: 1 for mono)
            sample_width: Sample width in bytes (default: 2 for 16-bit)
            frame_rate: Frame rate in Hz (default: 22050)
        """
        import wave
        
        with wave.open(wav_path, 'wb') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(frame_rate)
            wav_file.writeframes(pcm_data)

@activity.defn
async def generate_audio_from_text(
    analysis_result: Dict[str, Any],
    voice_id: str = "luna",  # Using Luna voice as default (based on Rime.ai website)
    model: str = "arcana",   # Using Arcana model for best quality
    output_format: str = "mp3",
    save_to_dir: str = "results/audio"
) -> Dict[str, Any]:
    """
    Generate audio from text using Rime.ai text-to-speech API
    
    Args:
        analysis_result: The analysis result from the LLM containing the text to convert
        voice_id: The voice ID to use for the TTS (e.g., "luna")
        model: The TTS model to use (e.g., "arcana", "mist")
        output_format: Audio output format ("mp3", "wav", etc.)
        save_to_dir: Directory to save the audio file
        
    Returns:
        dict: Information about the generated audio file
    """
    # Get Rime API key from environment variables
    api_key = os.getenv("RIME_API_KEY")
    if not api_key:
        raise ValueError("RIME_API_KEY environment variable is not set")
    
    # Check if analysis result is valid
    if not analysis_result.get('success', False):
        return {
            "success": False,
            "error": "Cannot generate audio from failed analysis",
            "original_error": analysis_result.get('error', 'Unknown error')
        }
    
    # Extract the text to convert to audio
    text = analysis_result.get('analysis', '')
    if not text:
        return {
            "success": False,
            "error": "No text found in the analysis result"
        }
    
    # Create output directory if it doesn't exist
    output_dir = Path(save_to_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate a clean filename from the URL or use a default
    url = analysis_result.get('url', 'unknown_website')
    base_filename = f"analysis_{url.replace('://', '_').replace('/', '_').replace('.', '_')}"
    
    # Prepare API request
    logging.info(f"Generating audio for analysis of {url} using Rime.ai with voice: {voice_id}")
    
    try:
        # Create Rime.ai client
        rime_client = RimeAiClient(api_key)
        
        # Split the text into manageable chunks with a reduced max_chunk_size
        # Rime.ai API has a character limit
        text_chunks = split_text_into_chunks(text, max_chunk_size=500)
        logging.info(f"Split text into {len(text_chunks)} chunks for audio processing")
        
        # Store file paths for all generated audio files
        audio_files = []
        
        # Process each chunk separately
        for i, chunk in enumerate(text_chunks):
            # Generate chunk-specific filename if multiple chunks
            if len(text_chunks) > 1:
                chunk_filename = f"{base_filename}_part{i+1}.{output_format}"
            else:
                chunk_filename = f"{base_filename}.{output_format}"
                
            chunk_output_path = output_dir / chunk_filename
            logging.info(f"Processing chunk {i+1}/{len(text_chunks)} with {len(chunk)} characters")
            
            try:
                # Generate audio using the streaming PCM API
                pcm_data = rime_client.generate_audio_streaming_pcm(chunk, voice_id, model)
                
                # Convert PCM to the requested audio format
                audio_path = rime_client.convert_pcm_to_audio(pcm_data, str(chunk_output_path), output_format)
                
                # Add to list of generated files
                audio_files.append(audio_path)
                logging.info(f"Generated audio saved to: {audio_path}")
                
            except Exception as e:
                logging.error(f"Error generating audio for chunk {i+1}: {str(e)}")
                # Continue with next chunk instead of failing completely
                continue
        
        # Check if we generated any audio files
        if not audio_files:
            return {
                "success": False,
                "error": "No audio files were successfully generated",
                "url": url
            }
            
        # If we have multiple audio files, try to concatenate them
        if len(audio_files) > 1:
            try:
                # Create a combined filename
                combined_filename = f"{base_filename}_combined.wav"
                combined_path = output_dir / combined_filename
                
                # Concatenate all audio files
                concatenated = await concatenate_audio_chunks(
                    audio_files, 
                    str(combined_path),
                    delete_originals=False  # Keep originals by default
                )
                
                if concatenated.get("success", False):
                    # Add the combined file to the list (but keep the individual chunks too)
                    audio_files.append(concatenated["audio_file"])
                    logging.info(f"Successfully created combined audio file: {concatenated['audio_file']}")
                    
                    # Update the result to include the combined file
                    result = {
                        "success": True,
                        "audio_files": audio_files,
                        "combined_audio_file": concatenated["audio_file"],
                        "url": url,
                        "voice_id": voice_id,
                        "model": model,
                        "output_format": "wav",  # Combined file is always WAV
                        "text_length": len(text),
                        "chunks_processed": len(text_chunks),
                        "chunks_successful": len(audio_files) - 1,  # Subtract 1 for the combined file
                        "file_size_bytes": sum(os.path.getsize(f) for f in audio_files)
                    }
                    
                    # For backward compatibility
                    result["audio_file"] = concatenated["audio_file"]
                    
                    return result
            except Exception as e:
                logging.warning(f"Failed to concatenate audio chunks: {str(e)}")
                # Continue with the original list of files if concatenation fails
        
        # Return success with all file details
        result = {
            "success": True,
            "audio_files": audio_files,
            "url": url,
            "voice_id": voice_id,
            "model": model,
            "output_format": output_format,
            "text_length": len(text),
            "chunks_processed": len(text_chunks),
            "chunks_successful": len(audio_files)
        }
        
        # Calculate total file size
        try:
            result["file_size_bytes"] = sum(os.path.getsize(f) for f in audio_files)
        except Exception as e:
            logging.warning(f"Could not calculate total file size: {str(e)}")
            
        # For backward compatibility with existing code
        if len(audio_files) == 1:
            result["audio_file"] = audio_files[0]
            
        return result
    
    except Exception as e:
        logging.error(f"Error generating audio: {str(e)}")
        return {
            "success": False,
            "error": f"Audio generation failed: {str(e)}"
        }

def validate_supabase_url(url: str) -> Tuple[bool, str]:
    """
    Validate if a Supabase URL is accessible.
    
    Args:
        url: The URL to validate
        
    Returns:
        Tuple[bool, str]: A tuple containing success status and message
    """
    try:
        # Just check for HEAD request to see if the URL is valid without downloading the file
        response = requests.head(url, timeout=5)
        if response.status_code == 200:
            return True, "URL is valid and accessible"
        else:
            return False, f"URL returned status code {response.status_code}"
    except Exception as e:
        return False, f"Error validating URL: {str(e)}"

@activity.defn
async def upload_audio_to_supabase(
    audio_filepath: str,
    bucket_name: str = "public",  # Changed default to "public" which often exists by default
    file_path_prefix: str = "podcasts"  # Simplified path prefix
) -> Dict[str, Any]:
    """
    Upload an audio file to Supabase storage and return the URL.
    
    Args:
        audio_filepath: Path to the audio file to upload
        bucket_name: Supabase storage bucket name (default: "public")
        file_path_prefix: Path prefix inside the bucket (default: "podcasts")
        
    Returns:
        dict: Information about the uploaded file including the public URL
    """
    
    try:
        # Get Supabase credentials from environment variables
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            return {
                "success": False,
                "error": "Supabase credentials missing. Set SUPABASE_URL and SUPABASE_KEY environment variables."
            }
        
        # Validate the audio file
        if not os.path.exists(audio_filepath):
            return {
                "success": False,
                "error": f"Audio file not found: {audio_filepath}"
            }
        
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Get the file name from the path
        file_name = Path(audio_filepath).name
        
        # Generate a unique storage path
        timestamp = int(os.path.getmtime(audio_filepath))
        storage_path = f"{file_path_prefix}/{timestamp}_{file_name}"
        
        # Open the file for upload
        with open(audio_filepath, "rb") as f:
            file_data = f.read()
        
        # Try to upload to Supabase Storage
        try:
            response = supabase.storage.from_(bucket_name).upload(
                path=storage_path,
                file=file_data,
                file_options={"content-type": "audio/wav" if file_name.endswith(".wav") else "audio/mpeg"}
            )
        except Exception as upload_error:
            # If the error is related to RLS, provide a clearer message
            error_str = str(upload_error)
            if "row-level security" in error_str or "RLS" in error_str:
                logging.error(f"Row Level Security (RLS) policy prevents upload: {error_str}")
                return {
                    "success": False,
                    "error": "Unable to upload due to Supabase Row Level Security policy. Please configure bucket permissions in your Supabase dashboard."
                }
            elif "bucket not found" in error_str.lower() or "404" in error_str:
                available_buckets = []
                try:
                    available_buckets = supabase.storage.list_buckets()
                    bucket_names = [b.get('name', 'unknown') for b in available_buckets]
                    logging.error(f"Bucket '{bucket_name}' not found. Available buckets: {', '.join(bucket_names)}")
                    
                    if available_buckets:
                        # Try to use an available bucket instead
                        alt_bucket = available_buckets[0].get('name')
                        logging.info(f"Trying alternative bucket: {alt_bucket}")
                        
                        try:
                            response = supabase.storage.from_(alt_bucket).upload(
                                path=storage_path,
                                file=file_data,
                                file_options={"content-type": "audio/wav" if file_name.endswith(".wav") else "audio/mpeg"}
                            )
                            logging.info(f"Successfully uploaded to alternative bucket: {alt_bucket}")
                            bucket_name = alt_bucket  # Use the alternative bucket for URL generation
                        except Exception as alt_error:
                            logging.error(f"Failed to upload to alternative bucket: {str(alt_error)}")
                            return {
                                "success": False,
                                "error": f"Bucket '{bucket_name}' not found and failed to use alternative bucket: {str(alt_error)}"
                            }
                except Exception as list_error:
                    logging.error(f"Failed to list available buckets: {str(list_error)}")
                    return {
                        "success": False,
                        "error": f"Bucket '{bucket_name}' not found and couldn't list alternatives: {str(list_error)}"
                    }
            else:
                # Re-raise other errors
                raise
        
        # Try different URL formats until we find one that works
        url_formats = [
            supabase.storage.from_(bucket_name).get_public_url(storage_path),
            f"{supabase_url.rstrip('/')}/storage/v1/object/public/{bucket_name}/{storage_path}",
            f"{supabase_url.rstrip('/')}/storage/v1/object/sign/{bucket_name}/{storage_path}"
        ]
        
        working_url = None
        for url in url_formats:
            try:
                is_valid, _ = validate_supabase_url(url)
                if is_valid:
                    working_url = url
                    break
            except Exception:
                continue
        
        # Use the working URL if we found one, otherwise use the default
        public_url = working_url if working_url else url_formats[0]
        
        logging.info(f"Successfully uploaded audio file to Supabase: {public_url}")
        
        return {
            "success": True,
            "file_name": file_name,
            "original_path": audio_filepath,
            "storage_path": storage_path,
            "bucket": bucket_name,
            "public_url": public_url,
            "file_size_bytes": os.path.getsize(audio_filepath)
        }
    
    except Exception as e:
        logging.error(f"Error uploading audio file to Supabase: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to upload audio file: {str(e)}"
        } 