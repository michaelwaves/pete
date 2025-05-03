from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
import logging

# Import our activities, using the same name as the function
with workflow.unsafe.imports_passed_through():
    from activities.scrape_activities import scrape_website
    from activities.llm_activities import analyze_with_gemini
    from activities.audio_activities import generate_audio_from_text, concatenate_audio_chunks, upload_audio_to_supabase

DEFAULT_PROMPT = """"I need a script for a short podcast episode, approximately 5-10 minutes long. The episode should be based on the following information: [Insert the information here. Be as detailed and organized as possible. You can use bullet points, paragraphs, or any format that makes sense for your information.]
Please structure the script to be engaging and easy to listen to. Include the following elements:

Catchy Introduction (approx. 30-60 seconds): Hook the listener, introduce the topic in an interesting way, and briefly state what they will learn in this episode.
Core Content (approx. 4-7 minutes): Break down the provided information into logical, digestible segments. Use clear and concise language. Consider using a conversational tone. You can include:

Key facts and figures.
Brief explanations of concepts.
Perhaps a short anecdote or example related to the information.
Organize this section with transitions to guide the listener.


Concluding Thoughts/Summary (approx. 1-2 minutes): Briefly summarize the main points, offer a final thought or call to action (if applicable, e.g., "learn more at..."), and thank the listener.
Suggestions for Sound Design/Music: Briefly suggest where intro/outro music or sound effects might be appropriate to enhance the listening experience. (Optional but helpful for the scriptwriter).
Important Considerations:

Maintain a conversational and friendly tone.
Avoid overly technical jargon if possible, or explain it clearly.
Keep sentences relatively short and easy to follow when spoken.
Ensure a smooth flow between sections.
Please write the script in a clear format, perhaps indicating who is speaking (e.g., HOST, NARRATOR) if you envision different voices, although a single voice is fine."""

@workflow.defn
class WebScraperWithLLMWorkflow:
    @workflow.run
    async def run(
        self, 
        url: str, 
        prompt_template: str = DEFAULT_PROMPT, 
        max_depth: int = 1, 
        max_pages: int = 10, 
        max_pages_for_llm: int = 3,
        generate_audio: bool = True,
        voice_id: str = "luna",
        tts_model: str = "arcana",
        combine_audio: bool = True,
        delete_chunks_after_combine: bool = False,
        upload_to_supabase: bool = True
    ) -> dict:
        """
        Workflow to scrape a website, analyze the content with Google's Gemini LLM,
        and generate audio narration using Rime.ai.
        
        Args:
            url: The URL of the website to scrape
            prompt_template: Template for the prompt to send to the LLM (default is comprehensive analysis)
            max_depth: Maximum crawling depth (default: 1)
            max_pages: Maximum pages to crawl (default: 10)
            max_pages_for_llm: Maximum number of pages to include in LLM analysis (default: 3)
            generate_audio: Whether to generate audio from the LLM analysis (default: True)
            voice_id: The Rime.ai voice ID to use (default: "luna")
            tts_model: The Rime.ai TTS model to use. Options:
                - "arcana": Higher quality, more lifelike voices for natural conversations
                - "mist_v2": Fast processing with good quality (recommended for real-time)
                - "mist": Legacy model (use only if needed)
                Note: The actual model ID may vary; consult Rime.ai documentation for current valid models
                Default: "arcana"
            combine_audio: Whether to automatically combine audio chunks into a single file (default: True)
            delete_chunks_after_combine: Whether to delete individual audio chunks after combining (default: False)
            upload_to_supabase: Whether to upload the audio to Supabase (default: True)
        
        Returns:
            dict: The analysis results from the LLM and audio generation, including Supabase URL if uploaded
        """
        # Configure retry policy for the activities
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=5),
            maximum_interval=timedelta(minutes=5),
            maximum_attempts=3,
            backoff_coefficient=2.0,
        )
        
        # Step 1: Execute the website scraping activity
        scraped_data = await workflow.execute_activity(
            scrape_website,
            args=[url, max_depth, max_pages],
            start_to_close_timeout=timedelta(minutes=15),
            retry_policy=retry_policy,
        )
        
        # Step 2: If scraping was successful, analyze with LLM
        if not scraped_data.get("success", False):
            return {
                "success": False,
                "error": "Web scraping failed",
                "scraping_error": scraped_data.get("error", "Unknown error")
            }
            
        # Execute the LLM analysis activity
        llm_result = await workflow.execute_activity(
            analyze_with_gemini,
            args=[scraped_data, prompt_template, max_pages_for_llm],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy,
        )
        
        # Step 3: If LLM analysis was successful and audio generation is enabled, generate audio
        if llm_result.get("success", False) and generate_audio:
            # Execute the audio generation activity
            audio_result = await workflow.execute_activity(
                generate_audio_from_text,
                args=[llm_result, voice_id, tts_model, "wav", "results/audio"],
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=retry_policy,
            )
            
            # Check if we need to combine audio chunks and we have multiple audio files
            if combine_audio and audio_result.get("success", False) and len(audio_result.get("audio_files", [])) > 1:
                # Execute the audio concatenation activity
                base_filename = f"analysis_{url.replace('://', '_').replace('/', '_').replace('.', '_')}"
                combined_output_path = f"results/audio/{base_filename}_combined.wav"
                
                concat_result = await workflow.execute_activity(
                    concatenate_audio_chunks,
                    args=[audio_result.get("audio_files", []), combined_output_path, delete_chunks_after_combine],
                    start_to_close_timeout=timedelta(minutes=5),
                    retry_policy=retry_policy,
                )
                
                # Add concatenation result to the audio result
                if concat_result.get("success", False):
                    audio_result["combined_audio_file"] = concat_result.get("audio_file")
                    audio_result["combined_audio_success"] = True
                    
                    # If we deleted the original chunks, update the audio_files list
                    if delete_chunks_after_combine:
                        audio_result["audio_files"] = [concat_result.get("audio_file")]
            
            # Combine results
            combined_result = {
                "success": llm_result.get("success", False),
                "url": url,
                "scraping": {
                    "pages_scraped": scraped_data.get("pages_scraped", 0),
                    "success": scraped_data.get("success", False)
                },
                "podcast": {
                    "script": llm_result.get("analysis", ""),
                    "model_used": llm_result.get("model_used", "unknown"),
                    "pages_analyzed": llm_result.get("pages_analyzed", 0),
                    "success": llm_result.get("success", False)
                },
                "audio": {
                    "file_paths": audio_result.get("audio_files", []),
                    "combined_file": audio_result.get("combined_audio_file", None),
                    "voice_id": voice_id,
                    "model": tts_model,
                    "success": audio_result.get("success", False),
                    "error": audio_result.get("error", None) if not audio_result.get("success", False) else None
                }
            }
            
            # Upload to Supabase if requested and we have a combined audio file or at least one audio file
            if upload_to_supabase and audio_result.get("success", False):
                try:
                    # Find the audio file to upload - check both possible field names
                    target_file = audio_result.get("combined_file", None)
                    if not target_file:
                        target_file = audio_result.get("combined_audio_file", None)
                    
                    # Fall back to first audio file if no combined file
                    if not target_file:
                        audio_files = audio_result.get("audio_files", [])
                        if audio_files:
                            target_file = audio_files[0]
                    
                    if not target_file:
                        logging.warning("No audio file available for Supabase upload")
                        combined_result["supabase"] = {
                            "success": False,
                            "error": "No audio file available for upload"
                        }
                    else:
                        # Execute the Supabase upload activity
                        supabase_result = await workflow.execute_activity(
                            upload_audio_to_supabase,
                            args=[target_file],
                            start_to_close_timeout=timedelta(minutes=5),
                        )
                        
                        # Add Supabase upload result to combined result
                        combined_result["supabase"] = {
                            "success": supabase_result.get("success", False),
                            "public_url": supabase_result.get("public_url", None),
                            "storage_path": supabase_result.get("storage_path", None),
                            "bucket": supabase_result.get("bucket", None),
                            "error": supabase_result.get("error", None) if not supabase_result.get("success", False) else None
                        }
                        
                        # Add podcast URL to root of result for easy access
                        if supabase_result.get("success", False):
                            combined_result["podcast_url"] = supabase_result.get("public_url", None)
                        else:
                            error_msg = supabase_result.get("error", "Unknown error")
                            if "row-level security" in error_msg.lower() or "policy" in error_msg.lower():
                                # Provide a more user-friendly message for RLS errors
                                logging.error(f"Supabase upload failed due to permissions: {error_msg}")
                                combined_result["supabase"]["friendly_error"] = (
                                    "Could not upload to Supabase due to permission settings. "
                                    "Please check your Supabase bucket configuration and Row Level Security policies. "
                                    "See README.md for instructions on setting up proper bucket permissions."
                                )
                            elif "bucket not found" in error_msg.lower() or "404" in error_msg.lower():
                                # Provide guidance for missing bucket
                                combined_result["supabase"]["friendly_error"] = (
                                    "Bucket not found in Supabase. Please create a bucket named 'public' "
                                    "in your Supabase dashboard and set appropriate permissions. "
                                    "See README.md for more details."
                                )
                except Exception as e:
                    logging.error(f"Error in Supabase upload: {str(e)}")
                    combined_result["supabase"] = {
                        "success": False,
                        "error": f"Unexpected error during upload: {str(e)}"
                    }
            
            return combined_result
        else:
            # Return just the LLM result if audio generation is disabled or LLM analysis failed
            return llm_result