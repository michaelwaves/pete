import asyncio
import logging
import os
from dotenv import load_dotenv

from temporalio.client import Client
from temporalio.worker import Worker

from workflows import GreetingWorkflow
from activities import greeting_activities

logging.basicConfig(level=logging.INFO)

# Load environment variables from .env file
load_dotenv()

async def main():
    # Connect to Temporal server using environment variables
    host = os.getenv("TEMPORAL_HOST", "localhost:7233")
    namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    task_queue = os.getenv("TEMPORAL_TASK_QUEUE", "greeting-task-queue")
    api_key = os.getenv("TEMPORAL_API_KEY")
    
    # Connect with TLS and API key for Temporal Cloud
    client = await Client.connect(
        host,
        namespace=namespace,
        tls=True,
        api_key=api_key,
    )
    
    # Run the worker
    logging.info(f"Starting worker on task queue: {task_queue}...")
    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=[GreetingWorkflow],
        activities=[greeting_activities.greet],
    )
    
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())