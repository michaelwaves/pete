"""
Activities for the web scraper workflow.
"""
from activities.scrape_activities import scrape_website
from activities.llm_activities import analyze_with_gemini
from activities.audio_activities import generate_audio_from_text