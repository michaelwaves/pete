import { NextRequest, NextResponse } from 'next/server';
import { Client, Connection } from '@temporalio/client';

export async function POST(req: NextRequest) {
  try {
    const { workflowId } = await req.json();

    if (!workflowId) {
      return NextResponse.json({ error: 'Workflow ID is required' }, { status: 400 });
    }

    // Get Temporal connection configuration from environment variables
    const temporalAddress = process.env.TEMPORAL_HOST || 'localhost:7233';
    const namespace = process.env.TEMPORAL_NAMESPACE || 'default';
    const apiKey = process.env.TEMPORAL_API_KEY;

    if (!apiKey && temporalAddress.includes('api.temporal.io')) {
      console.error('API key is required for Temporal Cloud');
      return NextResponse.json({ 
        error: 'Temporal API key is missing. Please check your environment configuration.' 
      }, { status: 500 });
    }

    try {
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
      
      // Get the workflow handle
      const handle = client.workflow.getHandle(workflowId);
      
      // Get the workflow description
      const description = await handle.describe();
      
      // Check if workflow is still running based on status
      const isRunning = description.status.name === 'RUNNING';
      
      // Get the workflow result if it's completed
      let result = null;
      if (description.status.name === 'COMPLETED') {
        try {
          result = await handle.result();
        } catch (error) {
          console.error('Error getting workflow result:', error);
        }
      }
      
      // Get more details if workflow failed
      let errorMessage = null;
      if (description.status.name === 'FAILED') {
        try {
          // This will throw the workflow's error
          await handle.result();
        } catch (error: any) {
          errorMessage = error.message || 'Workflow execution failed';
        }
      }
      
      return NextResponse.json({
        isRunning,
        status: description.status.name,
        result,
        error: errorMessage,
        workflowId,
        runId: description.runId,
        startTime: description.startTime,
        closeTime: description.closeTime
      });
      
    } catch (connectionError: any) {
      console.error('Error connecting to Temporal:', connectionError);
      
      return NextResponse.json({ 
        error: 'Failed to connect to Temporal service. Check server configuration.',
        details: connectionError.message
      }, { status: 500 });
    }
  } catch (error: any) {
    console.error('Error processing request:', error);
    return NextResponse.json({ 
      error: 'Failed to process request',
      details: error.message 
    }, { status: 500 });
  }
} 