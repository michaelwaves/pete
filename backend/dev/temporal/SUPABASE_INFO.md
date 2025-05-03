# Supabase Storage Configuration Guide

This guide explains how to set up Supabase Storage for this project.

## Understanding Supabase Storage

Supabase Storage is a file storage service built on top of PostgreSQL. Files are stored in "buckets" which have their own security rules through Row Level Security (RLS) policies.

## Current Issues

The following issues may occur with Supabase Storage:

1. **Bucket Not Found Error (404)**:
   - Indicates the bucket being used doesn't exist in your Supabase project
   - Solution: Create a bucket with the correct name in the Supabase dashboard

2. **Row-Level Security Policy Violation (403)**:
   - Indicates your user doesn't have permission to upload to the bucket
   - Solution: Configure proper RLS policies for your bucket

## How to Configure Supabase

### Step 1: Create a Bucket

1. Log in to your [Supabase Dashboard](https://app.supabase.io/)
2. Select your project
3. Go to "Storage" in the left sidebar
4. Click "Create bucket"
5. Name the bucket `public` (or whatever name you prefer)
6. Make sure "Public bucket" is checked if you want the files to be publicly accessible

### Step 2: Configure Row Level Security Policies

For a bucket to be usable, you need to define Row Level Security (RLS) policies:

1. Go to the "Policies" tab for your bucket
2. Create a policy for file selection (read access):

```sql
-- Allow public read access to all files
CREATE POLICY "Public Access"
ON storage.objects
FOR SELECT
USING (bucket_id = 'public');
```

3. Create a policy for file insertion (upload):

```sql
-- Allow authenticated users to upload files
CREATE POLICY "Authenticated Upload"
ON storage.objects
FOR INSERT
TO authenticated
USING (bucket_id = 'public');
```

### Step 3: Update Your Code Configuration

Make sure your code specifies the correct bucket name:

```python
# When calling the workflow
await client.start_workflow(
    "WebScraperWithLLMWorkflow",
    [
        # ... other parameters
        True,  # upload to Supabase
    ],
    # ... other parameters
)

# Or when directly calling the activity
supabase_result = await workflow.execute_activity(
    upload_audio_to_supabase,
    args=[
        audio_file_path,
        "public",  # bucket name - must match your Supabase bucket
        "podcasts"  # path prefix
    ],
    start_to_close_timeout=timedelta(minutes=5),
)
```

## Troubleshooting

If you're still having issues:

1. **Check Bucket Visibility**: Make sure the bucket is public if you want public access
2. **Verify API Key Permissions**: Ensure your API key has proper permissions
3. **Test with the included script**: Run `python test_supabase.py` to check your configuration
4. **Check Public URL Format**: The correct format should be `https://[project-ref].supabase.co/storage/v1/object/public/[bucket]/[file-path]`

## Need More Help?

Refer to the [Supabase Storage documentation](https://supabase.com/docs/guides/storage) for more details. 