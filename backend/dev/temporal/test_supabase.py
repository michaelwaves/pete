#!/usr/bin/env python3
"""
Test Supabase connectivity and bucket access
"""

import os
import sys
import json
import logging
import requests
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

def test_supabase_connection():
    """
    Test the Supabase connection and bucket access
    """
    # Load environment variables
    load_dotenv()
    
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        logging.error("Missing Supabase credentials. Set SUPABASE_URL and SUPABASE_KEY in .env file")
        return False
    
    logging.info(f"Testing connection to Supabase: {supabase_url}")
    
    try:
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # List available buckets with detailed information
        try:
            response = supabase.storage.list_buckets()
            buckets = response
            
            if not buckets:
                logging.warning("No buckets found in your Supabase project")
                buckets = []
            
            logging.info(f"Found {len(buckets)} buckets:")
            for bucket in buckets:
                logging.info(f"  - {bucket['name']} (public: {bucket.get('public', False)})")
                
            # Try to list all buckets with raw API call
            try:
                headers = {
                    "apikey": supabase_key,
                    "Authorization": f"Bearer {supabase_key}"
                }
                
                bucket_url = f"{supabase_url}/storage/v1/bucket"
                response = requests.get(bucket_url, headers=headers)
                
                logging.info(f"Raw bucket API response (status {response.status_code}):")
                try:
                    raw_buckets = response.json()
                    logging.info(json.dumps(raw_buckets, indent=2))
                except:
                    logging.info(f"Raw response: {response.text}")
            except Exception as e:
                logging.error(f"Error listing buckets with direct API call: {str(e)}")
                
        except Exception as e:
            logging.error(f"Error listing buckets: {str(e)}")
            buckets = []
        
        # Check for the default bucket
        default_bucket = "files"
        bucket_exists = any(b['name'] == default_bucket for b in buckets)
        
        if not bucket_exists:
            logging.warning(f"Default bucket '{default_bucket}' not found. Attempting to create it...")
            try:
                # Attempt to create the bucket
                supabase.storage.create_bucket(default_bucket, {"public": True})
                logging.info(f"Successfully created bucket '{default_bucket}'")
                bucket_exists = True
            except Exception as e:
                logging.error(f"Failed to create bucket: {str(e)}")
                
                # Try the raw API approach
                try:
                    headers = {
                        "apikey": supabase_key,
                        "Authorization": f"Bearer {supabase_key}",
                        "Content-Type": "application/json"
                    }
                    
                    bucket_url = f"{supabase_url}/storage/v1/bucket"
                    data = {
                        "id": default_bucket,
                        "name": default_bucket,
                        "public": True
                    }
                    
                    response = requests.post(bucket_url, headers=headers, json=data)
                    
                    if response.status_code == 200 or response.status_code == 201:
                        logging.info(f"Successfully created bucket '{default_bucket}' via direct API call")
                        bucket_exists = True
                    else:
                        logging.error(f"Failed to create bucket via API: {response.status_code} {response.text}")
                except Exception as api_e:
                    logging.error(f"Error creating bucket with direct API call: {str(api_e)}")
        
        # Test uploading a file if bucket exists or use an existing bucket
        test_bucket_name = default_bucket
        if not bucket_exists and buckets:
            # Use the first available bucket as fallback
            test_bucket_name = buckets[0]['name']
            logging.info(f"Using existing bucket '{test_bucket_name}' for testing")
        
        if bucket_exists or buckets:
            # Create a small test file
            test_file_path = Path("test_supabase_upload.txt")
            test_file_path.write_text("This is a test file to verify Supabase connectivity")
            
            try:
                # Upload the file
                storage_path = "test/test_file.txt"
                with open(test_file_path, "rb") as f:
                    file_data = f.read()
                
                # Upload to Supabase Storage
                try:
                    response = supabase.storage.from_(test_bucket_name).upload(
                        path=storage_path,
                        file=file_data,
                        file_options={"content-type": "text/plain"}
                    )
                    logging.info(f"Successfully uploaded test file to bucket '{test_bucket_name}'")
                    
                    # Try multiple URL formats to see which one works
                    url_formats = [
                        supabase.storage.from_(test_bucket_name).get_public_url(storage_path),
                        f"{supabase_url.rstrip('/')}/storage/v1/object/public/{test_bucket_name}/{storage_path}",
                        f"{supabase_url.rstrip('/')}/storage/v1/object/sign/{test_bucket_name}/{storage_path}"
                    ]
                    
                    logging.info("Testing URL formats:")
                    working_url = None
                    for i, url in enumerate(url_formats):
                        logging.info(f"Testing URL format {i+1}: {url}")
                        try:
                            # Test URL accessibility
                            response = requests.head(url, timeout=5)
                            logging.info(f"  - Status code: {response.status_code}")
                            if response.status_code == 200:
                                logging.info(f"  - SUCCESS: This URL format works!")
                                working_url = url
                            else:
                                logging.info(f"  - Not accessible (status code {response.status_code})")
                        except Exception as e:
                            logging.info(f"  - Error: {str(e)}")
                    
                    if working_url:
                        logging.info(f"\n✅ WORKING URL FORMAT: {working_url}\n")
                        # Extract the pattern for future use
                        pattern = working_url.replace(test_bucket_name, "{bucket_name}").replace(storage_path, "{file_path}")
                        logging.info(f"URL PATTERN TO USE: {pattern}")
                    else:
                        logging.warning("No working URL format found!")
                        
                except Exception as upload_e:
                    logging.error(f"Failed to upload to bucket '{test_bucket_name}': {str(upload_e)}")
                    
                # Try to list file contents
                try:
                    files = supabase.storage.from_(test_bucket_name).list()
                    logging.info(f"Files in bucket '{test_bucket_name}':")
                    for file in files:
                        logging.info(f"  - {file.get('name', 'unknown')}")
                except Exception as list_e:
                    logging.error(f"Failed to list files in bucket '{test_bucket_name}': {str(list_e)}")
                
                # Clean up
                try:
                    supabase.storage.from_(test_bucket_name).remove([storage_path])
                    logging.info("Test file removed from Supabase")
                except Exception as e:
                    logging.error(f"Failed to remove test file: {str(e)}")
                
            except Exception as e:
                logging.error(f"Failed to upload test file: {str(e)}")
            finally:
                # Remove local test file
                if test_file_path.exists():
                    test_file_path.unlink()
        else:
            logging.error("No buckets available for testing uploads")
            return False
        
        return True
        
    except Exception as e:
        logging.error(f"Failed to connect to Supabase: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_supabase_connection()
    if success:
        logging.info("✅ Supabase connection and tests completed")
    else:
        logging.error("❌ Supabase connection test failed")
        sys.exit(1) 