# Website Scraper with LLM Analysis and Audio Generation

A distributed web scraping system based on Temporal workflows, with LLM-powered content analysis and text-to-speech capabilities.

## Features

- **Web Scraping**: Crawl websites and extract their content
- **LLM Analysis**: Analyze scraped content using Google's Gemini AI
- **Audio Generation**: Convert analysis results to audio using Rime.ai's text-to-speech API
- **Fault Tolerance**: Automatic retries for failed scrapes and analysis
- **Scalability**: Distributed task execution using Temporal workflows

## Getting Started

### Prerequisites

- Python 3.9+
- Temporal server running locally or in the cloud
- Google AI API key (for Gemini LLM)
- Rime.ai API key (for Text-to-Speech)

### Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   ```
   # Create a .env file with the following content
   GOOGLE_API_KEY=your_google_api_key
   RIME_API_KEY=your_rime_api_key
   ```

### Usage

1. Start the Temporal worker:
   ```
   python worker.py
   ```

2. Run the scraper with LLM analysis and audio generation:
   ```
   python run_scraper_with_llm.py https://example.com
   ```

### Available Command-Line Options

```
python run_scraper_with_llm.py URL [options]

positional arguments:
  url                   URL to scrape

options:
  -h, --help            show this help message and exit
  --max-depth MAX_DEPTH
                        Maximum crawling depth (default: 1)
  --max-pages MAX_PAGES
                        Maximum pages to crawl (default: 10)
  --max-pages-for-llm MAX_PAGES_FOR_LLM
                        Maximum number of pages to include in LLM analysis (default: 3)
  --output OUTPUT       Output file path for results (default: results_<timestamp>.json)
  --no-audio            Disable audio generation
  --voice VOICE         Rime.ai voice ID (default: luna, options: luna, orion, astra, etc.)
  --tts-model TTS_MODEL
                        Rime.ai TTS model (default: arcana, options: arcana, mage, etc.)
```

## Architecture

The system uses Temporal workflows to orchestrate the scraping, analysis, and audio generation process:

1. **WebScraperWithLLMWorkflow**: The main workflow that coordinates all activities
2. **Activities**:
   - `scrape_website`: Scrapes a given URL and its linked pages
   - `analyze_with_gemini`: Analyzes the scraped content using Google's Gemini LLM
   - `generate_audio_from_text`: Converts the analysis text to speech using Rime.ai

## Output

Results are saved in two formats:
- A JSON file containing the full analysis, model information, and metadata
- An MP3 audio file containing the narrated analysis

## Example Usage

Simple website analysis with default settings:
```
python run_scraper_with_llm.py https://example.com
```

Advanced usage with custom parameters:
```
python run_scraper_with_llm.py https://example.com --max-depth 2 --max-pages 20 --voice orion --tts-model mage
```

Disable audio generation:
```
python run_scraper_with_llm.py https://example.com --no-audio
```

## License

This project is licensed under the MIT License - see the LICENSE file for details. 