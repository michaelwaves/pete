from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

# Import our activity, using the same name as the function
with workflow.unsafe.imports_passed_through():
    from activities.greeting_activities import greet

@workflow.defn
class GreetingWorkflow:
    @workflow.run
    async def run(self, name: str) -> str:
        # Configure retry policy for the activity
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=10),
            maximum_attempts=3,
        )
        
        # Execute the activity with the retry policy
        return await workflow.execute_activity(
            greet,
            name,
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=retry_policy,
        )