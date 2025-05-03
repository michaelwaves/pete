# Temporal Setup Guide

This guide will help you set up and troubleshoot your Temporal Cloud connection.

## Prerequisites

1. A Temporal Cloud account
2. An API key with the right permissions
3. Python and Node.js installed

## Configuration

The system uses two components:
- **Frontend (Next.js)**: Initiates workflows
- **Backend (Python)**: Defines workflow logic and runs worker process

### Environment Setup

Make sure your `.env` or `.env.local` file contains:

```
TEMPORAL_HOST=ap-northeast-1.aws.api.temporal.io:7233
TEMPORAL_NAMESPACE=pete-dev.mkdum
TEMPORAL_TASK_QUEUE=default
TEMPORAL_API_KEY=your-api-key
```

## Starting the Worker

The workflow worker **must** be running before you can start any workflows:

1. Run the provided batch script: `start-temporal-worker.bat`
2. Or manually run: `cd ../backend/dev/temporal && python worker.py`

## Common Errors

### 1. JWT is missing

This means your API key isn't being passed correctly. Check:
- Your `.env` file has the correct API key
- The connection is being made with the right authorization header

### 2. Request unauthorized / Permission Denied

This means your API key doesn't have sufficient permissions to:
- Connect to the namespace
- Execute workflows on the task queue

Solutions:
- Check your Temporal Cloud permissions in the dashboard
- Verify the namespace matches exactly what's in Temporal Cloud
- Ensure your API key has workflow execution permissions

### 3. Workflow not found / Workflow type not registered

This means your worker isn't running or hasn't registered the workflow:
- Start the worker using the provided script
- Check worker logs to ensure the workflow was registered successfully

## Testing the Connection

Use the front-end API endpoint to test starting a workflow:

```bash
curl -X POST http://localhost:3000/api/scrape-url \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com"}'
```

## Debugging

For better debugging, check:
- Worker logs in `backend/dev/temporal/worker.log`
- Next.js server logs for API errors
- Temporal Cloud UI for workflow execution status 