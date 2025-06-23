#!/usr/bin/env python3
"""
Example script demonstrating the crawl functionality with Firecrawl integration.
"""

import asyncio
import os
from dotenv import load_dotenv
from intelligent_scraper import IntelligentScraper

# Load environment variables
load_dotenv()

async def main():
    # Initialize the intelligent scraper
    team_id = "your_team_id"  # Replace with your actual team ID
    scraper = IntelligentScraper(team_id)
    
    # Example crawl requests
    crawl_requests = [
        "crawl https://interviewing.io/blog",
        "crawl https://quill.co/blog",
        "crawl https://medium.com/tag/python"
    ]
    
    for request in crawl_requests:
        print(f"\n{'='*50}")
        print(f"Processing: {request}")
        print(f"{'='*50}")
        
        try:
            result = await scraper.process_request(request)
            
            if "error" in result:
                print(f"Error: {result['error']}")
            else:
                print(f"Successfully crawled {len(result.get('items', []))} items")
                print(f"Results saved to scraped_data_*.json")
                
                # Show first item as preview
                if result.get('items'):
                    first_item = result['items'][0]
                    print(f"\nFirst item preview:")
                    print(f"Title: {first_item.get('title', 'No title')}")
                    print(f"URL: {first_item.get('source_url', 'No URL')}")
                    print(f"Content length: {len(first_item.get('content', ''))} characters")
                    
        except Exception as e:
            print(f"Exception occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 