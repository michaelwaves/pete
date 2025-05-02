import logging
from temporalio import activity

@activity.defn
async def greet(name: str) -> str:
    logging.info(f"Creating greeting for {name}")
    return f"Hello, {name}!"