#!/usr/bin/env python3
"""
Intelligent Scraper Layer for THT Scraper
- Handles both direct URL scraping and natural language requests
- Uses browser-use for complex interactions and site navigation
- Falls back to existing scraper for direct content extraction
"""

import asyncio
import re
import json
import logging
import os
from typing import List, Dict, Any, Optional, Union
from urllib.parse import urljoin, urlparse
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Import existing scraper components
from scraper import THTScraper, BlogExtractor

# Import browser-use for intelligent navigation
try:
    from browser_use import Agent
    from langchain_openai import ChatOpenAI
    BROWSER_USE_AVAILABLE = True
except ImportError:
    BROWSER_USE_AVAILABLE = False
    logging.warning("browser-use not available - natural language requests will be limited")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IntelligentScraper:
    """
    Intelligent scraper that can handle both direct URLs and natural language requests.
    """
    
    def __init__(self, team_id: str, llm_api_key: Optional[str] = None, use_selenium: bool = False):
        self.team_id = team_id
        self.use_selenium = use_selenium
        
        # Get API key from parameter or environment variable
        self.llm_api_key = llm_api_key or os.getenv("OPENAI_API_KEY")
        
        # Initialize existing scraper
        self.scraper = THTScraper(team_id, use_selenium=use_selenium)
        
        # Initialize browser-use if available
        self.browser_agent = None
        if BROWSER_USE_AVAILABLE and self.llm_api_key:
            try:
                self.browser_agent = ChatOpenAI(model="gpt-4o", api_key=self.llm_api_key)
                logger.info("Browser agent initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize browser agent: {e}")
        elif BROWSER_USE_AVAILABLE and not self.llm_api_key:
            logger.warning("browser-use available but no API key found. Set OPENAI_API_KEY in .env file")
        else:
            logger.info("browser-use not available - natural language requests disabled")
    
    def is_natural_language_request(self, request: str) -> bool:
        """
        Determine if the request is natural language or a direct URL.
        """
        # Check if it looks like a URL
        url_patterns = [
            r'^https?://',
            r'^www\.',
            r'^[a-zA-Z0-9-]+\.(com|org|net|edu|io|co|dev)$'
        ]
        
        for pattern in url_patterns:
            if re.search(pattern, request.strip()):
                return False
        
        # Check for natural language indicators
        nl_indicators = [
            'go to', 'visit', 'scrape', 'find', 'search', 'get', 'extract',
            'second', 'third', 'first', 'last', 'post', 'article', 'page'
        ]
        
        request_lower = request.lower()
        return any(indicator in request_lower for indicator in nl_indicators)
    
    async def process_request(self, request: str, max_items: int = 10) -> Dict[str, Any]:
        """
        Process either a direct URL or natural language request.
        """
        if self.is_natural_language_request(request):
            return await self.handle_natural_language_request(request, max_items)
        else:
            return await self.handle_direct_url(request, max_items)
    
    async def handle_direct_url(self, url: str, max_items: int = 10) -> Dict[str, Any]:
        """
        Handle direct URL scraping using existing scraper.
        """
        logger.info(f"Processing direct URL: {url}")
        
        try:
            # Determine if it's a blog, PDF, or individual page
            if url.endswith('.pdf') or 'pdf' in url.lower():
                items = self.scraper.scrape_pdf(url)
            elif self._is_likely_blog(url):
                items = self.scraper.scrape_blog(url, max_posts=max_items)
            else:
                items = self.scraper.scrape_urls([url])
            
            return self.scraper.export_to_knowledgebase_format(items)
            
        except Exception as e:
            logger.error(f"Error processing direct URL {url}: {e}")
            return {"error": str(e), "items": []}
    
    async def handle_natural_language_request(self, request: str, max_items: int = 10) -> Dict[str, Any]:
        """
        Handle natural language requests using browser-use.
        """
        if not BROWSER_USE_AVAILABLE or not self.browser_agent:
            return {
                "error": "browser-use not available. Install with: pip install browser-use",
                "items": []
            }
        
        logger.info(f"Processing natural language request: {request}")
        
        try:
            # Create browser agent with enhanced task description
            enhanced_task = self._enhance_task_description(request, max_items)
            
            agent = Agent(
                task=enhanced_task,
                llm=self.browser_agent,
            )
            
            # Run the agent
            result = await agent.run()
            
            # Parse the result and convert to knowledgebase format
            return self._parse_browser_result(result, request)
            
        except Exception as e:
            logger.error(f"Error processing natural language request: {e}")
            return {"error": str(e), "items": []}
    
    def _enhance_task_description(self, request: str, max_items: int) -> str:
        """
        Enhance the natural language request with specific instructions.
        """
        base_task = f"""
        {request}
        
        Additional requirements:
        - Extract the content in a structured format
        - Include title, content, author if available
        - Convert content to clean markdown format
        - Limit to {max_items} items maximum
        - Return the data in a format that can be parsed as JSON
        """
        
        return base_task.strip()
    
    def _parse_browser_result(self, result: Any, original_request: str) -> Dict[str, Any]:
        """
        Parse browser-use result and convert to knowledgebase format.
        """
        try:
            # Try to extract structured data from the result
            if hasattr(result, 'content'):
                content = result.content
            else:
                content = str(result)
            
            # Look for JSON-like content
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group())
                    return self._convert_to_knowledgebase_format(data, original_request)
                except json.JSONDecodeError:
                    pass
            
            # Fallback: create a single item from the content
            return {
                "team_id": self.team_id,
                "items": [{
                    "title": f"Content from: {original_request}",
                    "content": content,
                    "content_type": "web_page",
                    "source_url": f"request://{original_request}",
                    "author": "",
                    "user_id": ""
                }]
            }
            
        except Exception as e:
            logger.error(f"Error parsing browser result: {e}")
            return {"error": str(e), "items": []}
    
    def _convert_to_knowledgebase_format(self, data: Dict[str, Any], original_request: str) -> Dict[str, Any]:
        """
        Convert parsed data to knowledgebase format.
        """
        items = []
        
        # Handle different data structures
        if isinstance(data, dict):
            if 'items' in data:
                items = data['items']
            elif 'posts' in data:
                items = data['posts']
            elif 'articles' in data:
                items = data['articles']
            else:
                # Single item
                items = [data]
        
        elif isinstance(data, list):
            items = data
        
        # Convert items to knowledgebase format
        knowledgebase_items = []
        for item in items:
            if isinstance(item, dict):
                knowledgebase_items.append({
                    "title": item.get('title', f"Content from: {original_request}"),
                    "content": item.get('content', str(item)),
                    "content_type": item.get('content_type', 'web_page'),
                    "source_url": item.get('source_url', f"request://{original_request}"),
                    "author": item.get('author', ''),
                    "user_id": ""
                })
        
        return {
            "team_id": self.team_id,
            "items": knowledgebase_items
        }
    
    def _is_likely_blog(self, url: str) -> bool:
        """
        Determine if a URL is likely a blog.
        """
        blog_indicators = [
            '/blog', '/posts', '/articles', '/news', '/feed',
            'medium.com', 'substack.com', 'wordpress.com'
        ]
        
        url_lower = url.lower()
        return any(indicator in url_lower for indicator in blog_indicators)

# --- CLI Interface ---
async def main():
    """
    Interactive CLI for the intelligent scraper.
    """
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║              Intelligent THT Scraper                        ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    print("You can now use natural language requests!")
    print("Examples:")
    print("  - 'https://interviewing.io/blog' (direct URL)")
    print("  - 'Go to Quora software engineering and scrape the second post'")
    print("  - 'Visit Reddit r/programming and get the top 5 posts'")
    print("  - 'Search for React tutorials on Medium'")
    print("Type 'exit' to quit.")
    
    # Get configuration
    team_id = input("\nTeam ID (default: test_team): ").strip() or "test_team"
    
    # Check for browser-use and API key
    if not BROWSER_USE_AVAILABLE:
        print("\n⚠️  browser-use not available. Install with: pip install browser-use")
        print("   Only direct URLs will work for now.")
        llm_api_key = None
    else:
        # Check if API key is available in environment
        env_api_key = os.getenv("OPENAI_API_KEY")
        if env_api_key:
            print(f"\n✅ Found OpenAI API key in environment")
            llm_api_key = None  # Will be loaded automatically
        else:
            print(f"\n⚠️  No OpenAI API key found in environment (.env file)")
            print("   Create a .env file with: OPENAI_API_KEY=your-key-here")
            llm_api_key = input("   Or enter API key manually (optional): ").strip() or None
    
    # Initialize scraper
    scraper = IntelligentScraper(team_id, llm_api_key=llm_api_key)
    
    # Show status
    if BROWSER_USE_AVAILABLE and scraper.browser_agent:
        print(f"\n✅ Natural language requests: ENABLED")
    elif BROWSER_USE_AVAILABLE:
        print(f"\n⚠️  Natural language requests: DISABLED (no API key)")
    else:
        print(f"\n⚠️  Natural language requests: DISABLED (browser-use not available)")
    
    print(f"✅ Direct URL scraping: ENABLED")
    
    while True:
        try:
            request = input("\n🤖 Your request: ").strip()
            
            if request.lower() in ['exit', 'quit']:
                print("Goodbye!")
                break
            
            if not request:
                continue
            
            print(f"\n🚀 Processing: {request}")
            
            # Process the request
            result = await scraper.process_request(request)
            
            if "error" in result:
                print(f"\n❌ Error: {result['error']}")
            else:
                print(f"\n✅ Success! Extracted {len(result.get('items', []))} items")
                
                # Save to file
                output_file = f"intelligent_scrape_{team_id}.json"
                with open(output_file, 'w') as f:
                    json.dump(result, f, indent=2)
                
                print(f"📄 Saved to: {output_file}")
                
                # Show sample
                if result.get('items'):
                    sample = result['items'][0]
                    print(f"\n📝 Sample item:")
                    print(f"   Title: {sample['title'][:50]}...")
                    print(f"   Content Length: {len(sample['content'])} characters")
                    print(f"   Type: {sample['content_type']}")
        
        except KeyboardInterrupt:
            print("\n\n👋 Scraping cancelled by user")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 