#!/usr/bin/env python3
"""
Test script to verify the crawl functionality creates the correct JSON structure.
"""

import asyncio
import os
import json
from dotenv import load_dotenv
from intelligent_scraper import IntelligentScraper

# Load environment variables
load_dotenv()

async def test_crawl_structure():
    """Test that crawl creates the correct JSON structure."""
    
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
            return
        
        items = result.get('items', [])
        print(f"✅ Successfully crawled {len(items)} items")
        
        # Find the generated JSON file
        import glob
        json_files = glob.glob("scraped_data_*.json")
        if not json_files:
            print("❌ No JSON file found")
            return
        
        # Get the most recent file
        latest_file = max(json_files, key=os.path.getctime)
        print(f"📄 Checking structure of: {latest_file}")
        
        # Read and verify the structure
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Verify it's an array
        if not isinstance(data, list):
            print("❌ Error: JSON should be an array")
            return
        
        print(f"✅ JSON is an array with {len(data)} objects")
        
        # Verify each object has the correct structure
        for i, obj in enumerate(data):
            if not isinstance(obj, dict):
                print(f"❌ Error: Object {i} is not a dictionary")
                continue
            
            if "team_id" not in obj:
                print(f"❌ Error: Object {i} missing team_id")
                continue
            
            if "items" not in obj:
                print(f"❌ Error: Object {i} missing items")
                continue
            
            if not isinstance(obj["items"], list):
                print(f"❌ Error: Object {i} items is not a list")
                continue
            
            print(f"✅ Object {i}: team_id='{obj['team_id']}', items={len(obj['items'])}")
            
            # Check first item structure
            if obj["items"]:
                first_item = obj["items"][0]
                required_fields = ["title", "content", "content_type", "source_url", "author", "user_id"]
                for field in required_fields:
                    if field not in first_item:
                        print(f"❌ Error: Object {i} first item missing {field}")
                        break
                else:
                    print(f"✅ Object {i} first item has all required fields")
        
        print(f"\n🎉 Structure verification complete! File: {latest_file}")
        
    except Exception as e:
        print(f"❌ Exception occurred: {e}")

if __name__ == "__main__":
    asyncio.run(test_crawl_structure()) 