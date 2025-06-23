#!/usr/bin/env python3
"""
Test script for the crawl functionality.
"""

import asyncio
import os
from dotenv import load_dotenv
from intelligent_scraper import IntelligentScraper

# Load environment variables
load_dotenv()

async def test_crawl():
    """Test the crawl functionality."""
    
    # Check if Firecrawl API key is available
    firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
    if not firecrawl_api_key:
        print("❌ FIRECRAWL_API_KEY not found in environment variables")
        print("Please set FIRECRAWL_API_KEY in your .env file")
        return
    
    print("✅ FIRECRAWL_API_KEY found")
    
    # Initialize scraper
    scraper = IntelligentScraper("test_team_id")
    
    # Test crawl request
    test_url = "https://interviewing.io/blog"
    crawl_request = f"crawl {test_url}"
    
    print(f"\n🔄 Testing crawl request: {crawl_request}")
    
    try:
        result = await scraper.process_request(crawl_request)
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            items = result.get('items', [])
            print(f"✅ Successfully crawled {len(items)} items")
            
            if items:
                print(f"\n📄 First item preview:")
                first_item = items[0]
                print(f"   Title: {first_item.get('title', 'No title')}")
                print(f"   URL: {first_item.get('source_url', 'No URL')}")
                print(f"   Content length: {len(first_item.get('content', ''))} characters")
                
                # Show first 200 characters of content
                content = first_item.get('content', '')
                if content:
                    preview = content[:200] + "..." if len(content) > 200 else content
                    print(f"   Content preview: {preview}")
            
            print(f"\n💾 Results saved to scraped_data_*.json")
            
    except Exception as e:
        print(f"❌ Exception occurred: {e}")

if __name__ == "__main__":
    asyncio.run(test_crawl()) 