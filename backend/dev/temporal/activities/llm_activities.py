import logging
import os
import json
import google.generativeai as genai
from temporalio import activity
from typing import Dict, List, Any, Optional

# The specific model the user wants to use
PREFERRED_MODEL = "gemini-2.0-flash"

@activity.defn
async def analyze_with_gemini(
    scraped_data: Dict[str, Any], 
    prompt_template: str = "Analyze this website content and provide a summary.", 
    max_pages: int = 3
) -> Dict[str, Any]:
    """
    Analyze scraped website data using Google's Gemini LLM.
    
    Args:
        scraped_data: The data returned from scrape_website activity
        prompt_template: The template for the prompt to send to Gemini
        max_pages: Maximum number of pages to include in the analysis (to avoid token limits)
        
    Returns:
        dict: The analysis results from Gemini
    """
    # Get API key from environment
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set")
    
    # Configure the Gemini API
    genai.configure(api_key=api_key)
    
    # First, list available models to find if our preferred model is available
    try:
        models = genai.list_models()
        available_models = [model.name for model in models]
        logging.info(f"Available models: {available_models}")
        
        # Try to use the preferred model first (gemini-2.0-flash)
        if any(PREFERRED_MODEL in m for m in available_models):
            # Look for an exact match or closest match
            model_name = next((m for m in available_models if PREFERRED_MODEL in m), None)
            logging.info(f"Using requested model: {model_name}")
        else:
            # If the preferred model isn't available, find any Gemini model
            logging.warning(f"Requested model '{PREFERRED_MODEL}' not found. Looking for alternatives.")
            
            # Find a suitable Gemini model as fallback
            gemini_models = [m for m in available_models if "gemini" in m.lower()]
            
            if not gemini_models:
                logging.error("No Gemini models found in available models")
                raise ValueError("No Gemini models available for your API key")
            
            # Select a Gemini model that supports text generation (prefer 2.0 if available)
            model_name = None
            for m in gemini_models:
                if "2.0" in m.lower():
                    model_name = m
                    break
            
            # If no "2.0" model found, use the first available Gemini model
            if not model_name and gemini_models:
                model_name = gemini_models[0]
                
            logging.info(f"Selected alternative model: {model_name}")
        
        # Initialize the model with the selected name
        model = genai.GenerativeModel(model_name)
        
    except Exception as e:
        logging.error(f"Error setting up Gemini model: {str(e)}")
        # Fall back to the basic model name as last resort
        try:
            logging.info(f"Falling back to '{PREFERRED_MODEL}' as direct model name")
            model = genai.GenerativeModel(PREFERRED_MODEL)
        except Exception as fallback_error:
            # If that fails, try the standard gemini-pro model
            try:
                logging.info("Falling back to 'gemini-pro' as last resort")
                model = genai.GenerativeModel("gemini-pro")
            except Exception as final_error:
                raise ValueError(f"Could not initialize any Gemini model: {str(e)}, Fallback errors: {str(fallback_error)}, {str(final_error)}")
    
    logging.info(f"Analyzing scraped data from {scraped_data.get('url', 'unknown URL')} with Gemini")
    
    try:
        # Validate input data
        if not scraped_data.get('success', False):
            return {
                "success": False,
                "error": "Scraped data indicates unsuccessful scraping",
                "original_error": scraped_data.get('error', 'Unknown error')
            }
        
        # Get pages data from the scraped result
        pages_data = scraped_data.get('pages_data', [])
        if not pages_data:
            return {
                "success": False,
                "error": "No pages data found in the scraped data"
            }
        
        # Limit the number of pages to process (to avoid token limits)
        pages_to_process = pages_data[:max_pages]
        logging.info(f"Processing {len(pages_to_process)} pages out of {len(pages_data)} total scraped pages")
        
        # Prepare content for the LLM
        website_content = ""
        for idx, page in enumerate(pages_to_process):
            website_content += f"\n\n--- PAGE {idx+1}: {page.get('url', 'No URL')} ---\n"
            website_content += f"TITLE: {page.get('title', 'No title')}\n"
            website_content += f"META DESCRIPTION: {page.get('meta_description', 'No meta description')}\n"
            
            # Add headings
            headings = page.get('headings', {})
            if headings:
                website_content += "HEADINGS:\n"
                for heading_type, heading_list in headings.items():
                    for heading in heading_list:
                        website_content += f"{heading_type}: {heading}\n"
            
            # Add main content (limit to avoid token issues)
            main_content = page.get('main_content', '')
            if len(main_content) > 4000:
                main_content = main_content[:4000] + "... (content truncated)"
            website_content += f"CONTENT:\n{main_content}\n"
        
        # Prepare the full prompt
        full_prompt = f"""{prompt_template}

WEBSITE DATA:
{website_content}

Please provide a detailed analysis based on the prompt.
"""

        # Send to Gemini
        logging.info("Sending data to Gemini for analysis")
        
        # Set generation config appropriate for Gemini 2.0 Flash
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
        }
        
        # Generate the content with the configured model
        response = model.generate_content(
            full_prompt,
            generation_config=generation_config
        )
        
        # Process response
        if hasattr(response, 'text'):
            analysis_text = response.text
        else:
            # Handle alternative response format
            analysis_text = str(response)
        
        # Return results
        return {
            "success": True,
            "url": scraped_data.get('url'),
            "analysis": analysis_text,
            "model_used": getattr(model, 'model_name', str(model)),
            "pages_analyzed": len(pages_to_process),
            "total_pages_scraped": len(pages_data)
        }
                
    except Exception as e:
        error_message = f"Error during Gemini analysis: {str(e)}"
        logging.error(error_message)
        return {
            "success": False,
            "url": scraped_data.get('url', 'unknown URL'),
            "error": error_message
        } 