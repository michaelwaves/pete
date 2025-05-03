# Web Scraper with LLM Analysis

This project implements a web scraping system with integrated LLM analysis using Temporal.io for workflow orchestration. It's designed to be reliable, scalable, and easy to use.

## Features

- **Web Scraping**: Scrape websites with configurable depth and page limits
- **LLM Analysis**: Analyze scraped content using Google's Gemini LLM
- **Temporal Workflows**: Reliable execution with automatic retries and error handling

## Setup

### 1. Install dependencies

```bash
# Install dependencies using the provided script
python install_deps.py

# Or manually with pip
pip install -r requirements.txt
```

### 2. Configure environment variables

Create a `.env` file with the following contents:

```
# Temporal Cloud credentials
TEMPORAL_HOST=<your-temporal-host>
TEMPORAL_NAMESPACE=<your-namespace>
TEMPORAL_TASK_QUEUE=default
TEMPORAL_API_KEY=<your-temporal-api-key>

# Google Gemini API key
GEMINI_API_KEY=<your-gemini-api-key>

# Supabase credentials
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

## Usage

### 1. Run the worker

```bash
python worker.py
```

### 2. Run the Scraper with LLM Analysis

```bash
python run_scraper_with_llm.py <url> [max_depth] [max_pages]

# Example
python run_scraper_with_llm.py https://example.com 2 10
```

### Parameters

- `url`: The URL of the website to scrape (required)
- `max_depth`: Maximum crawling depth (default: 1)
- `max_pages`: Maximum pages to crawl (default: 10)

The LLM analysis will be limited to the first 3 pages to avoid token limits.

## Workflow Architecture

The **WebScraperWithLLMWorkflow** performs two main steps:

1. **Web Scraping**:
   - Crawls the website up to the specified depth and page limit
   - Extracts titles, meta descriptions, headings, and content
   - Organizes data in a structured format

2. **LLM Analysis**:
   - Sends the structured data to Google's Gemini LLM
   - Uses a comprehensive built-in prompt that covers:
     - Content quality analysis
     - SEO fundamentals
     - User experience
     - Audience targeting
     - Calls to action
     - Actionable recommendations

## Supabase Integration

The workflow now supports uploading the generated audio files to Supabase Storage. When enabled, the workflow will:

1. Generate audio from the LLM analysis
2. Optionally combine audio chunks into a single file
3. Upload the combined file (or the first audio file if no combined file exists) to Supabase
4. Return the public URL in the workflow results

### Storage Bucket Configuration

Make sure you have a storage bucket in your Supabase project with appropriate permissions. By default, the workflow will attempt to use a bucket named `public`.

#### Important: Supabase Row Level Security (RLS)

If you're encountering 403 Unauthorized errors or "Row Level Security policy violation" messages, you need to configure your Supabase bucket permissions:

1. Log in to your Supabase dashboard
2. Go to Storage section
3. Create a bucket named `public` if it doesn't already exist
4. Click on "Policies" for the bucket
5. Create a new policy that allows uploads and downloads for the appropriate users:

For public read access:
```sql
-- Allow public read access to all files
CREATE POLICY "Public Access"
ON storage.objects
FOR SELECT
USING (bucket_id = 'public');
```

For authenticated write access:
```sql
-- Allow authenticated users to upload files
CREATE POLICY "Authenticated Upload"
ON storage.objects
FOR INSERT
TO authenticated
USING (bucket_id = 'public');
```

You can customize the bucket name and file path prefix when starting the workflow:

```python
# JavaScript/TypeScript example (client-side)
const handle = await client.workflow.start('WebScraperWithLLMWorkflow', {
  args: [
    url,
    undefined,  // Use default prompt
    1,          // max_depth
    10,         // max_pages
    3,          // max_pages_for_llm
    true,       // enable audio
    'luna',     // voice
    'arcana',   // tts model
    true,       // combine audio
    false,      // delete chunks
    true        // upload to Supabase
  ],
  taskQueue,
  workflowId,
});

# Python example (server-side)
handle = await client.start_workflow(
    "WebScraperWithLLMWorkflow",
    [
        url,
        None,       # Use default prompt
        1,          # max_depth
        10,         # max_pages
        3,          # max_pages_for_llm
        True,       # enable audio
        "luna",     # voice
        "arcana",   # tts model
        True,       # combine audio
        False,      # delete chunks
        True        # upload to Supabase
    ],
    id=workflow_id,
    task_queue=task_queue,
)
```

### Advanced Usage

For advanced customization, you can directly call the `upload_audio_to_supabase` activity with custom parameters:

```python
supabase_result = await workflow.execute_activity(
    upload_audio_to_supabase,
    args=[
        audio_file_path,          # Path to audio file
        "custom_bucket_name",     # Optional: custom bucket name
        "custom/path/prefix"      # Optional: custom path prefix
    ],
    start_to_close_timeout=timedelta(minutes=5),
)
```

## Results

Analysis results are saved to the `results/` directory in text format. The system will show a preview of the analysis in the terminal after completion. 