import asyncio
import logging
import sys
import os
from dotenv import load_dotenv

from temporalio.client import Client

from workflows import GreetingWorkflow

logging.basicConfig(level=logging.INFO)

# Load environment variables from .env file
load_dotenv()

async def main():
    # Get name from command line or use default
    name = sys.argv[1] if len(sys.argv) > 1 else "World"
    
    # Connect to Temporal server using environment variables
    host = os.getenv("TEMPORAL_HOST", "localhost:7233")
    namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    task_queue = os.getenv("TEMPORAL_TASK_QUEUE", "default")
    api_key = os.getenv("TEMPORAL_API_KEY")
    
    # Connect with TLS and API key for Temporal Cloud
    client = await Client.connect(
        host,
        namespace=namespace,
        tls=True,
        api_key=api_key,
    )
    
    # Execute a workflow
    logging.info(f"Executing workflow for {name}")
    result = await client.execute_workflow(
        GreetingWorkflow.run,
        name,
        id=f"greeting-workflow-{name}",
        task_queue=task_queue,
    )
    
    logging.info(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())