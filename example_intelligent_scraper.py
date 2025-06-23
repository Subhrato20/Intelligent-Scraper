#!/usr/bin/env python3
"""
Example usage of the Intelligent THT Scraper
Demonstrates both direct URL scraping and natural language requests
"""

import asyncio
import json
from intelligent_scraper import IntelligentScraper

async def example_direct_urls():
    """Example: Direct URL scraping (existing functionality)"""
    print("\n🌐 Example 1: Direct URL Scraping")
    print("=" * 50)
    
    scraper = IntelligentScraper("example_team")
    
    # Direct blog URL
    result = await scraper.process_request("https://interviewing.io/blog", max_items=3)
    print(f"✅ Blog scraping: {len(result.get('items', []))} items extracted")
    
    # Save result
    with open("example_direct_urls.json", "w") as f:
        json.dump(result, f, indent=2)
    print("📄 Saved to: example_direct_urls.json")

async def example_natural_language():
    """Example: Natural language requests (new functionality)"""
    print("\n🤖 Example 2: Natural Language Requests")
    print("=" * 50)
    
    # Note: This requires browser-use and an LLM API key
    try:
        from browser_use import Agent
        print("✅ browser-use is available")
        
        # You would need to set your API key here
        # llm_api_key = "your-api-key-here"
        # scraper = IntelligentScraper("example_team", llm_api_key=llm_api_key)
        
        print("📝 Example natural language requests:")
        print("  - 'Go to Quora software engineering and scrape the second post'")
        print("  - 'Visit Reddit r/programming and get the top 5 posts'")
        print("  - 'Search for React tutorials on Medium'")
        print("  - 'Find the latest posts on Hacker News'")
        
        # Uncomment to test (requires API key):
        # result = await scraper.process_request("Go to Quora software engineering and scrape the second post")
        # print(f"✅ Natural language: {len(result.get('items', []))} items extracted")
        
    except ImportError:
        print("⚠️  browser-use not available")
        print("   Install with: pip install browser-use")
        print("   This enables natural language requests")

async def example_hybrid_approach():
    """Example: Hybrid approach using both methods"""
    print("\n🔄 Example 3: Hybrid Approach")
    print("=" * 50)
    
    scraper = IntelligentScraper("example_team")
    
    # Test different types of requests
    test_requests = [
        "https://interviewing.io/blog",  # Direct URL
        "Go to Quora software engineering and scrape the second post",  # Natural language
        "https://quill.co/blog",  # Direct URL
        "Visit Reddit r/programming and get the top 5 posts",  # Natural language
    ]
    
    for i, request in enumerate(test_requests, 1):
        print(f"\n{i}. Testing: {request}")
        
        # Check if it's natural language
        is_nl = scraper.is_natural_language_request(request)
        print(f"   Type: {'Natural Language' if is_nl else 'Direct URL'}")
        
        if is_nl:
            print("   ⚠️  Requires browser-use and API key")
        else:
            try:
                result = await scraper.process_request(request, max_items=2)
                print(f"   ✅ Extracted {len(result.get('items', []))} items")
            except Exception as e:
                print(f"   ❌ Error: {e}")

async def example_enhanced_agent():
    """Example: Using the enhanced agent layer"""
    print("\n🎯 Example 4: Enhanced Agent Layer")
    print("=" * 50)
    
    from enhanced_agent_layer import run_enhanced_llm_agent
    
    # Test different types of requests
    test_messages = [
        "Import all content from https://interviewing.io/blog",
        "Go to Quora software engineering and scrape the second post",
        "Import this PDF aline_book.pdf",
        "Visit Reddit r/programming and get the top 5 posts"
    ]
    
    for message in test_messages:
        print(f"\n🤖 Testing: {message}")
        result = await run_enhanced_llm_agent(message, "example_team")
        
        if result:
            if "error" in result:
                print(f"   ❌ Error: {result['error']}")
            else:
                print(f"   ✅ Success: {len(result.get('items', []))} items")
        else:
            print("   ⚠️  No result")

async def main():
    """Run all examples"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║              Intelligent THT Scraper Examples                ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Run examples
    await example_direct_urls()
    await example_natural_language()
    await example_hybrid_approach()
    await example_enhanced_agent()
    
    print("\n" + "=" * 60)
    print("🎉 All examples completed!")
    print("\nTo use natural language requests:")
    print("1. Install browser-use: pip install browser-use")
    print("2. Set your LLM API key")
    print("3. Run: python intelligent_scraper.py")
    print("\nFor direct URLs (no setup required):")
    print("1. Run: python intelligent_scraper.py")
    print("2. Enter URLs directly")

if __name__ == "__main__":
    asyncio.run(main()) 