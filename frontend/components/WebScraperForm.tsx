"use client";

import { useState, FormEvent, useEffect, useCallback } from 'react';
import AudioPlayer from './AudioPlayer';

interface WorkflowResult {
  success: boolean;
  url: string;
  podcast_url: string;
  scraping: {
    pages_scraped: number;
    success: boolean;
  };
  podcast: {
    script: string;
    model_used: string;
    pages_analyzed: number;
    success: boolean;
  };
  audio: {
    file_paths: string[];
    combined_file: string;
    voice_id: string;
    model: string;
    success: boolean;
  };
  supabase: {
    success: boolean;
    public_url: string;
    storage_path: string;
    bucket: string;
  };
}

const WebScraperForm = () => {
  const [url, setUrl] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [workflowDetails, setWorkflowDetails] = useState<any>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [workflowStatus, setWorkflowStatus] = useState('');
  const [workflowResult, setWorkflowResult] = useState<WorkflowResult | null>(null);

  // Function to check workflow status
  const checkWorkflowStatus = useCallback(async (workflowId: string) => {
    try {
      const response = await fetch('/api/workflow-status', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ workflowId }),
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Failed to check workflow status');
      }
      
      setWorkflowStatus(data.status);
      
      if (!data.isRunning && data.result) {
        setWorkflowResult(data.result);
        setIsPolling(false);
        setMessage('Workflow completed successfully!');
      } else if (!data.isRunning && data.error) {
        setError('Workflow failed: ' + data.error);
        setIsPolling(false);
      }
      
      return data;
    } catch (err: any) {
      console.error('Error checking workflow status:', err);
      setError(err.message || 'Failed to check workflow status');
      setIsPolling(false);
      return null;
    }
  }, []);

  // Setup polling when workflow is started
  useEffect(() => {
    let intervalId: NodeJS.Timeout;
    
    if (isPolling && workflowDetails?.workflowId) {
      intervalId = setInterval(() => {
        checkWorkflowStatus(workflowDetails.workflowId);
      }, 5000); // Poll every 5 seconds
    }
    
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [isPolling, workflowDetails, checkWorkflowStatus]);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    
    if (!url) {
      setError('Please enter a URL');
      return;
    }
    
    // Basic URL validation
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      setError('Please enter a valid URL starting with http:// or https://');
      return;
    }
    
    setIsProcessing(true);
    setError('');
    setMessage('');
    setWorkflowDetails(null);
    setWorkflowResult(null);
    setWorkflowStatus('');
    
    try {
      const response = await fetch('/api/scrape-url', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url }),
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Failed to process URL');
      }
      
      setMessage(data.message || 'Temporal workflow started successfully!');
      setWorkflowDetails(data);
      setIsPolling(true);
      
      // Check status immediately to get initial state
      await checkWorkflowStatus(data.workflowId);
      
    } catch (err: any) {
      setError(err.message || 'Failed to process URL. Please try again.');
      console.error('Scraper error:', err);
    } finally {
      setIsProcessing(false);
    }
  };

  // Status indicator component
  const StatusIndicator = () => (
    <div className="flex items-center mt-4">
      <div className="relative">
        <div className={`w-3 h-3 rounded-full ${
          workflowStatus === 'COMPLETED' ? 'bg-green-500' : 
          workflowStatus === 'RUNNING' ? 'bg-blue-500' : 
          workflowStatus === 'FAILED' ? 'bg-red-500' : 'bg-gray-300'
        }`}>
          {workflowStatus === 'RUNNING' && (
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
          )}
        </div>
      </div>
      <span className="ml-2 text-sm text-gray-700">
        {workflowStatus === 'COMPLETED' ? 'Workflow completed' : 
         workflowStatus === 'RUNNING' ? 'Workflow running...' : 
         workflowStatus === 'FAILED' ? 'Workflow failed' : 
         'Status unknown'}
      </span>
    </div>
  );

  return (
    <div className="max-w-4xl mx-auto p-6 bg-white rounded-lg shadow-md w-full">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label 
            htmlFor="website-url" 
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            Enter Website URL
          </label>
          
          <input
            id="website-url"
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com"
            className="block w-full px-3 py-2 border border-gray-300 rounded-md 
                      focus:outline-none focus:ring-blue-500 focus:border-blue-500
                      placeholder:text-gray-500"
            disabled={isProcessing}
          />
        </div>
        
        {error && (
          <div className="p-2 bg-red-50 text-red-500 rounded">
            {error}
          </div>
        )}
        
        {message && (
          <div className="p-2 bg-green-50 text-green-500 rounded">
            {message}
          </div>
        )}
        
        <button
          type="submit"
          disabled={!url || isProcessing || isPolling}
          className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 
                    text-white font-medium rounded-md
                    focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500
                    disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isProcessing ? 'Processing...' : isPolling ? 'Workflow Running...' : 'Start Temporal Workflow'}
        </button>
      </form>
      
      {workflowDetails && (
        <div className="mt-6">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Temporal Workflow Details</h3>
          <div className="bg-gray-50 p-3 rounded text-sm">
            <p className="text-gray-700"><span className="font-semibold text-gray-900">Workflow ID:</span> {workflowDetails.workflowId}</p>
            {workflowDetails.runId && <p className="text-gray-700"><span className="font-semibold text-gray-900">Run ID:</span> {workflowDetails.runId}</p>}
            <p className="text-gray-700"><span className="font-semibold text-gray-900">URL:</span> {workflowDetails.url}</p>
            {workflowDetails.taskQueue && <p className="text-gray-700"><span className="font-semibold text-gray-900">Task Queue:</span> {workflowDetails.taskQueue}</p>}
            
            <StatusIndicator />
            
            {isPolling && (
              <p className="mt-2 text-sm text-blue-600">
                Waiting for workflow to complete... This may take several minutes.
              </p>
            )}
            
            <p className="mt-2 text-xs text-gray-700">
              The Temporal workflow will:
            </p>
            <ul className="list-disc ml-5 mt-1 text-xs text-gray-700">
              <li>Scrape the website content</li>
              <li>Analyze it with an AI model</li>
              <li>Generate audio narration</li>
              <li>Store results for later retrieval</li>
            </ul>
          </div>
        </div>
      )}
      
      {workflowResult && workflowResult.success && workflowResult.podcast_url && (
        <div className="mt-8">
          <AudioPlayer 
            audioUrl={workflowResult.podcast_url} 
            podcastScript={workflowResult.podcast.script} 
          />
        </div>
      )}
    </div>
  );
};

export default WebScraperForm; 