import { NextRequest, NextResponse } from 'next/server';
import { Client, Connection } from '@temporalio/client';

export async function POST(req: NextRequest) {
  try {
    const { url } = await req.json();

    if (!url) {
      return NextResponse.json({ error: 'URL is required' }, { status: 400 });
    }

    // Basic URL validation
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      return NextResponse.json({ error: 'Invalid URL format' }, { status: 400 });
    }

    // Get Temporal connection configuration from environment variables
    const temporalAddress = process.env.TEMPORAL_HOST || 'localhost:7233';
    const namespace = process.env.TEMPORAL_NAMESPACE || 'default';
    const taskQueue = process.env.TEMPORAL_TASK_QUEUE || 'default';
    const apiKey = process.env.TEMPORAL_API_KEY;

    if (!apiKey && temporalAddress.includes('api.temporal.io')) {
      console.error('API key is required for Temporal Cloud');
      return NextResponse.json({ 
        error: 'Temporal API key is missing. Please check your environment configuration.' 
      }, { status: 500 });
    }

    // Generate a workflow ID
    const timestamp = new Date().getTime();
    const workflowId = `scraper-workflow-${timestamp}`;

    try {
      console.log(`Connecting to Temporal server at ${temporalAddress}`);
      
      // Create a connection
      const connection = await Connection.connect({
        address: temporalAddress,
        // Use TLS for cloud connections
        tls: temporalAddress.includes('api.temporal.io'),
        // Add authorization at the connection level
        ...(temporalAddress.includes('api.temporal.io') && apiKey
          ? { 
              metadata: {
                authorization: `Bearer ${apiKey}`,
                'temporal-namespace': namespace
              }
            }
          : {})
      });
      
      // Create client
      const client = new Client({
        connection,
        namespace,
      });
      
      // Start the workflow
      console.log(`Starting WebScraperWithLLMWorkflow for ${url} using task queue: ${taskQueue}`);
      
      const handle = await client.workflow.start('WebScraperWithLLMWorkflow', {
        args: [
          url,                // URL to scrape
          undefined,          // Use default prompt template
          1,                  // max_depth
          10,                 // max_pages
          3,                  // max_pages_for_llm
          true,               // enable audio generation
          'orion',            // use Orion voice
          'arcana'            // TTS model
        ],
        taskQueue,
        workflowId,
      });
      
      console.log(`Workflow started: ID=${handle.workflowId}, RunID=${handle.firstExecutionRunId}`);
      
      // Return workflow information
      return NextResponse.json({
        message: 'Temporal workflow started successfully',
        workflowId: handle.workflowId,
        runId: handle.firstExecutionRunId,
        taskQueue,
        url,
        params: {
          maxPages: 10,
          maxDepth: 1,
          voiceId: 'orion',
          audioEnabled: true
        }
      });
    } catch (connectionError: any) {
      console.error('Error connecting to Temporal:', connectionError);
      
      // Enhanced error logging
      const errorDetails = {
        error: 'Failed to connect to Temporal service',
        message: connectionError.message,
        cause: connectionError.cause?.message,
        code: connectionError.cause?.code,
        details: connectionError.cause?.details,
        temporalConfig: {
          address: temporalAddress,
          namespace,
          taskQueue,
          hasApiKey: Boolean(apiKey),
        }
      };
      
      console.error('Detailed error information:', JSON.stringify(errorDetails, null, 2));
      
      return NextResponse.json({ 
        error: 'Failed to connect to Temporal service. Check server configuration.',
        details: errorDetails
      }, { status: 500 });
    }
  } catch (error) {
    console.error('Error processing request:', error);
    return NextResponse.json({ error: 'Failed to process request' }, { status: 500 });
  }
} 