import asyncio
import logging
import os
from dotenv import load_dotenv

from temporalio.client import Client, TLSConfig
from temporalio.worker import Worker

from workflows import WebScraperWithLLMWorkflow
from activities.scrape_activities import scrape_website
from activities.llm_activities import analyze_with_gemini
from activities.audio_activities import generate_audio_from_text, concatenate_audio_chunks, upload_audio_to_supabase

async def main():
    # Load environment variables
    load_dotenv()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("worker.log")
        ]
    )
    
    # Set the host, using localhost as default
    host = os.getenv("TEMPORAL_HOST", "localhost:7233")
    namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    api_key = os.getenv("TEMPORAL_API_KEY")
    
    # Connect to the server
    logging.info(f"Connecting to Temporal server at {host}")
    
    # For cloud connections, we need TLS and API key
    if "api.temporal.io" in host:
        # Connect with TLS and API key (for SDK v1.6.0+)
        client = await Client.connect(
            host,
            namespace=namespace,
            tls=True,
            api_key=api_key,
            rpc_metadata={"temporal-namespace": namespace},
        )
    else:
        # Local connection without TLS
        client = await Client.connect(host, namespace=namespace)
    
    # Create the result directories if they don't exist
    os.makedirs("results", exist_ok=True)
    os.makedirs("results/audio", exist_ok=True)
    
    # Run the worker
    logging.info("Starting worker...")
    worker = Worker(
        client,
        task_queue=os.getenv("TEMPORAL_TASK_QUEUE", "default"),
        workflows=[WebScraperWithLLMWorkflow],
        activities=[
            scrape_website, 
            analyze_with_gemini, 
            generate_audio_from_text, 
            concatenate_audio_chunks,
            upload_audio_to_supabase
        ],
    )
    
    logging.info("Worker started successfully")
    logging.info("Registered workflow: WebScraperWithLLMWorkflow")
    logging.info("Registered activities: scrape_website, analyze_with_gemini, generate_audio_from_text, concatenate_audio_chunks, upload_audio_to_supabase")
    logging.info("Waiting for tasks...")
    
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())