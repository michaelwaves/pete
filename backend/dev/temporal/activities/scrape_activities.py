import logging
import os
import requests
from bs4 import BeautifulSoup
from temporalio import activity
from urllib.parse import urljoin

@activity.defn
async def scrape_website(url: str, max_depth: int = 1, max_pages: int = 10) -> dict:
    """
    Scrape a website using Python's requests and BeautifulSoup
    
    Args:
        url: The URL to scrape
        max_depth: Maximum crawling depth (default: 1)
        max_pages: Maximum pages to crawl (default: 10)
        
    Returns:
        dict: The scraped data
    """
    logging.info(f"Scraping website: {url} with max_depth: {max_depth}, max_pages: {max_pages}")
    
    try:
        # Initialize data structures
        visited_urls = set()
        pages_data = []
        urls_to_visit = [(url, 0)]  # (url, depth)
        
        # Headers to mimic a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        }
        
        # Crawl until no more URLs or limits reached
        while urls_to_visit and len(visited_urls) < max_pages:
            current_url, current_depth = urls_to_visit.pop(0)
            
            # Skip if already visited
            if current_url in visited_urls:
                continue
                
            logging.info(f"Scraping page: {current_url} (depth: {current_depth})")
            
            # Mark as visited
            visited_urls.add(current_url)
            
            try:
                # Send GET request
                response = requests.get(current_url, headers=headers, timeout=30)
                response.raise_for_status()  # Raise error for bad status codes
                
                # Parse HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract page title
                title = soup.title.text.strip() if soup.title else "No title"
                
                # Extract page metadata
                meta_description = ""
                meta_tag = soup.find('meta', attrs={'name': 'description'})
                if meta_tag and 'content' in meta_tag.attrs:
                    meta_description = meta_tag['content']
                
                # Extract main text content (paragraphs)
                paragraphs = [p.text.strip() for p in soup.find_all('p') if p.text.strip()]
                main_content = '\n\n'.join(paragraphs)
                
                # Extract heading structure
                headings = {}
                for i in range(1, 7):
                    h_tags = soup.find_all(f'h{i}')
                    if h_tags:
                        headings[f'h{i}'] = [h.text.strip() for h in h_tags]
                
                # Store page data
                page_data = {
                    'url': current_url,
                    'title': title,
                    'meta_description': meta_description,
                    'main_content': main_content,
                    'headings': headings,
                    'html_content_length': len(response.text),
                    'depth': current_depth
                }
                
                pages_data.append(page_data)
                
                # If not at max depth, add links to queue
                if current_depth < max_depth:
                    # Find all links on the page
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        # Convert relative URLs to absolute
                        if not href.startswith(('http://', 'https://', 'mailto:', 'tel:', '#')):
                            href = urljoin(current_url, href)
                        
                        # Only add internal links from the same domain
                        if href.startswith(url) and href not in visited_urls:
                            urls_to_visit.append((href, current_depth + 1))
                
            except requests.exceptions.RequestException as e:
                logging.error(f"Error scraping {current_url}: {str(e)}")
                continue
        
        logging.info(f"Successfully scraped {len(pages_data)} pages from {url}")
        
        return {
            "success": True,
            "url": url,
            "pages_scraped": len(pages_data),
            "pages_data": pages_data
        }
                
    except Exception as e:
        error_message = f"Error during web scraping: {str(e)}"
        logging.error(error_message)
        return {
            "success": False,
            "url": url,
            "error": error_message
        } 