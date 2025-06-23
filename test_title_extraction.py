#!/usr/bin/env python3
"""
Test script to demonstrate improved title extraction
"""

import asyncio
from intelligent_scraper import IntelligentScraper

async def test_title_extraction():
    """Test the improved title extraction functionality."""
    
    print("🧪 Testing Improved Title Extraction")
    print("=" * 50)
    
    # Initialize scraper
    scraper = IntelligentScraper("test_team")
    
    # Test cases
    test_cases = [
        {
            "request": "Visit Reddit r/programming and get the top 5 posts",
            "expected": "Top Posts from r/programming"
        },
        {
            "request": "Go to Quora software engineering and scrape the second post",
            "expected": "Quora: Software Engineering"
        },
        {
            "request": "Search for React tutorials on Medium",
            "expected": "Medium Articles: React Tutorials"
        },
        {
            "request": "Search and scrape Wikipedia page for vibecoding",
            "expected": "Wikipedia: Vibecoding"
        },
        {
            "request": "Find Stack Overflow questions about Python",
            "expected": "Stack Overflow Questions"
        },
        {
            "request": "Get latest posts from Hacker News",
            "expected": "Hacker News Top Stories"
        }
    ]
    
    print("Testing title extraction from requests:")
    for i, test_case in enumerate(test_cases, 1):
        request = test_case["request"]
        expected = test_case["expected"]
        
        # Test the title creation
        title = scraper._create_title_from_request(request)
        
        print(f"\n{i}. Request: {request}")
        print(f"   Expected: {expected}")
        print(f"   Got:      {title}")
        print(f"   ✅ Match: {title == expected}")
    
    # Test content-based title extraction
    print(f"\n\nTesting content-based title extraction:")
    
    test_content = """
    # How to Build a React Application
    
    This is a comprehensive guide on building React applications...
    
    ## Getting Started
    
    First, you need to install Node.js...
    """
    
    title = scraper._extract_title_from_content(test_content)
    print(f"Content: {test_content[:100]}...")
    print(f"Extracted title: {title}")
    
    # Test JSON-based title extraction
    print(f"\n\nTesting JSON-based title extraction:")
    
    json_content = '''
    {
        "title": "Advanced Python Programming Techniques",
        "content": "Learn advanced Python programming...",
        "author": "John Doe"
    }
    '''
    
    title = scraper._extract_title_from_content(json_content)
    print(f"JSON content: {json_content}")
    print(f"Extracted title: {title}")

if __name__ == "__main__":
    asyncio.run(test_title_extraction()) 