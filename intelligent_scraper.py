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

# Import Firecrawl for crawling functionality
try:
    from firecrawl import AsyncFirecrawlApp, ScrapeOptions
    FIRECRAWL_AVAILABLE = True
except ImportError:
    FIRECRAWL_AVAILABLE = False
    logging.warning("firecrawl-py not available - crawling functionality will be limited")

# Import OpenAI for intelligent decision making
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("openai not available - intelligent decision making will be limited")

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
        
        # Initialize Firecrawl if available
        self.firecrawl_app = None
        if FIRECRAWL_AVAILABLE:
            firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
            if firecrawl_api_key:
                try:
                    self.firecrawl_app = AsyncFirecrawlApp(api_key=firecrawl_api_key)
                    logger.info("Firecrawl app initialized successfully")
                except Exception as e:
                    logger.warning(f"Failed to initialize Firecrawl app: {e}")
            else:
                logger.warning("Firecrawl available but no API key found. Set FIRECRAWL_API_KEY in .env file")
        else:
            logger.info("Firecrawl not available - crawling functionality disabled")
        
        # Initialize OpenAI for intelligent decision making
        self.openai_client = None
        if OPENAI_AVAILABLE:
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if openai_api_key:
                try:
                    self.openai_client = OpenAI(api_key=openai_api_key)
                    logger.info("OpenAI client initialized successfully")
                except Exception as e:
                    logger.warning(f"Failed to initialize OpenAI client: {e}")
            else:
                logger.warning("OpenAI available but no API key found. Set OPENAI_API_KEY in .env file")
        else:
            logger.info("OpenAI not available - intelligent decision making disabled")
    
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
    
    def is_crawl_request(self, request: str) -> bool:
        """
        Determine if the request is a crawl command.
        """
        request_lower = request.lower().strip()
        return request_lower.startswith('crawl ')
    
    def extract_url_from_crawl_request(self, request: str) -> Optional[str]:
        """
        Extract URL from a crawl request like "crawl https://example.com".
        """
        request_lower = request.lower().strip()
        if request_lower.startswith('crawl '):
            url_part = request[6:].strip()  # Remove "crawl " prefix
            # Check if it's a valid URL
            if url_part.startswith(('http://', 'https://', 'www.')):
                return url_part
        return None
    
    async def process_request(self, request: str, max_items: int = 10) -> Dict[str, Any]:
        """
        Process either a direct URL or natural language request.
        """
        if self.is_natural_language_request(request):
            return await self.handle_natural_language_request(request, max_items)
        elif self.is_crawl_request(request):
            return await self.handle_crawl_request(request)
        else:
            # Check if it's a URL and use intelligent decision making
            if self._is_url(request):
                return await self.handle_intelligent_url_processing(request, max_items)
            else:
                return await self.handle_direct_url(request, max_items)
    
    def _is_url(self, text: str) -> bool:
        """
        Check if the text looks like a URL.
        """
        url_patterns = [
            r'^https?://',
            r'^www\.',
            r'^[a-zA-Z0-9-]+\.(com|org|net|edu|io|co|dev)$'
        ]
        
        for pattern in url_patterns:
            if re.search(pattern, text.strip()):
                return True
        return False
    
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
    
    async def handle_crawl_request(self, request: str) -> Dict[str, Any]:
        """
        Handle crawl requests using Firecrawl.
        """
        if not FIRECRAWL_AVAILABLE or not self.firecrawl_app:
            return {
                "error": "Firecrawl not available. Install with: pip install firecrawl-py and set FIRECRAWL_API_KEY",
                "items": []
            }
        
        url = self.extract_url_from_crawl_request(request)
        if not url:
            return {
                "error": "Invalid crawl request. Use format: 'crawl https://example.com'",
                "items": []
            }
        
        logger.info(f"Processing crawl request for: {url}")
        
        try:
            # Use hardcoded limit of 5 as requested
            response = await self.firecrawl_app.crawl_url(
                url=url,
                limit=5,
                scrape_options=ScrapeOptions(
                    formats=['markdown'],
                    onlyMainContent=True
                )
            )
            
            # Parse the response and convert to knowledgebase format
            return self._parse_firecrawl_result(response, url)
            
        except Exception as e:
            logger.error(f"Error processing crawl request for {url}: {e}")
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
                    "title": self._extract_meaningful_title(content, original_request),
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
    
    def _parse_firecrawl_result(self, response: Any, original_url: str) -> Dict[str, Any]:
        """
        Parse Firecrawl result and convert to knowledgebase format.
        """
        try:
            items = []
            
            # Check if response has data
            if hasattr(response, 'data') and response.data:
                for item in response.data:
                    if hasattr(item, 'markdown') and item.markdown:
                        items.append({
                            "title": self._extract_title_from_markdown(item.markdown) or f"Page from {original_url}",
                            "content": item.markdown,
                            "content_type": "web_page",
                            "source_url": getattr(item, 'url', original_url),
                            "author": "",
                            "user_id": ""
                        })
            
            # Generate unique ID for the output file
            import time
            timestamp = int(time.time())
            
            # Create the correct structure - each item as a separate object in the array
            output_data = []
            for item in items:
                output_data.append({
                    "team_id": self.team_id,
                    "items": [item]  # Each item gets its own object with team_id and items array
                })
            
            # Save to JSON file
            output_filename = f"scraped_data_{timestamp}.json"
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Crawl results saved to {output_filename}")
            
            # Return the first item for compatibility with existing code
            return {
                "team_id": self.team_id,
                "items": items
            }
            
        except Exception as e:
            logger.error(f"Error parsing Firecrawl result: {e}")
            return {"error": str(e), "items": []}
    
    def _extract_title_from_markdown(self, markdown_content: str) -> Optional[str]:
        """
        Extract title from markdown content.
        """
        lines = markdown_content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()
            elif line.startswith('## '):
                return line[3:].strip()
        return None
    
    def _extract_meaningful_title(self, content: str, original_request: str) -> str:
        """
        Extract a meaningful title from content or request.
        """
        # First, try to extract title from content
        title = self._extract_title_from_content(content)
        if title:
            return title
        
        # If no title found in content, create a better title from the request
        return self._create_title_from_request(original_request)
    
    def _extract_title_from_content(self, content: str) -> Optional[str]:
        """
        Extract meaningful title from content using various strategies.
        """
        # Strategy 1: Look for markdown headers
        header_patterns = [
            r'^#\s+(.+)$',  # # Title
            r'^##\s+(.+)$',  # ## Title
            r'^###\s+(.+)$',  # ### Title
            r'<h1[^>]*>(.+?)</h1>',  # <h1>Title</h1>
            r'<h2[^>]*>(.+?)</h2>',  # <h2>Title</h2>
        ]
        
        lines = content.split('\n')
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            for pattern in header_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    title = match.group(1).strip()
                    if len(title) > 5 and len(title) < 200:  # Reasonable length
                        return self._clean_title(title)
        
        # Strategy 2: Look for JSON-like structures with title
        json_patterns = [
            r'"title"\s*:\s*"([^"]+)"',
            r'"name"\s*:\s*"([^"]+)"',
            r'"heading"\s*:\s*"([^"]+)"',
        ]
        
        for pattern in json_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                if len(title) > 5 and len(title) < 200:
                    return self._clean_title(title)
        
        # Strategy 3: Look for the first meaningful line
        for line in lines[:20]:  # Check first 20 lines
            line = line.strip()
            # Skip empty lines, markdown formatting, etc.
            if (line and 
                not line.startswith('#') and 
                not line.startswith('*') and 
                not line.startswith('-') and
                not line.startswith('```') and
                len(line) > 10 and 
                len(line) < 150):
                return self._clean_title(line)
        
        return None
    
    def _create_title_from_request(self, request: str) -> str:
        """
        Create a meaningful title from the original request.
        """
        # Remove common prefixes
        request_lower = request.lower()
        
        # Extract key information from request
        if 'reddit' in request_lower:
            # Extract subreddit name
            subreddit_match = re.search(r'r/([a-zA-Z0-9_]+)', request_lower)
            if subreddit_match:
                subreddit = subreddit_match.group(1)
                return f"Top Posts from r/{subreddit}"
        
        elif 'quora' in request_lower:
            # Extract topic - look for words after "quora" and before "and" or end
            topic_match = re.search(r'quora\s+([^a]+?)(?:\s+and|\s*$)', request_lower)
            if topic_match:
                topic = topic_match.group(1).strip()
                return f"Quora: {topic.title()}"
        
        elif 'medium' in request_lower:
            # Extract search terms - look for words after "for" and before end
            search_match = re.search(r'search.*?for\s+([^a]+?)(?:\s*$)', request_lower)
            if search_match:
                search_terms = search_match.group(1).strip()
                return f"Medium Articles: {search_terms.title()}"
        
        elif 'wikipedia' in request_lower:
            # Extract search terms - look for words after "for" and before end
            search_match = re.search(r'wikipedia.*?for\s+([^a]+?)(?:\s*$)', request_lower)
            if search_match:
                search_terms = search_match.group(1).strip()
                return f"Wikipedia: {search_terms.title()}"
        
        elif 'stack overflow' in request_lower or 'stackoverflow' in request_lower:
            return "Stack Overflow Questions"
        
        elif 'hacker news' in request_lower or 'hn' in request_lower:
            return "Hacker News Top Stories"
        
        # Generic fallback
        words = request.split()
        if len(words) > 3:
            # Take first few meaningful words
            meaningful_words = [w for w in words[:6] if len(w) > 2 and w.lower() not in ['go', 'to', 'and', 'get', 'the', 'top', 'posts', 'from', 'for', 'about']]
            if meaningful_words:
                return f"{' '.join(meaningful_words[:4]).title()}"
        
        # Last resort: clean up the original request
        return self._clean_title(request)
    
    def _clean_title(self, title: str) -> str:
        """
        Clean and format a title.
        """
        # Remove extra whitespace
        title = re.sub(r'\s+', ' ', title.strip())
        
        # Remove markdown formatting
        title = re.sub(r'[*_`#]', '', title)
        
        # Remove HTML tags
        title = re.sub(r'<[^>]+>', '', title)
        
        # Remove URLs
        title = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', title)
        
        # Capitalize first letter of each word (title case)
        title = title.title()
        
        # Limit length
        if len(title) > 100:
            title = title[:97] + "..."
        
        return title.strip()
    
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
                # Extract and clean title
                raw_title = item.get('title', '')
                if raw_title:
                    title = self._clean_title(raw_title)
                else:
                    # If no title in item, try to extract from content
                    content = item.get('content', str(item))
                    title = self._extract_meaningful_title(content, original_request)
                
                knowledgebase_items.append({
                    "title": title,
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
        Determine if a URL is likely a blog homepage (not an individual blog post).
        """
        # Check if it's likely an individual blog post (has specific post identifiers)
        post_indicators = [
            '/blog/', '/posts/', '/articles/', '/news/',  # Common blog post paths
            '/202', '/2023/', '/2024/', '/2025/',  # Year-based posts
            '/jan/', '/feb/', '/mar/', '/apr/', '/may/', '/jun/',  # Month-based posts
            '/jul/', '/aug/', '/sep/', '/oct/', '/nov/', '/dec/',
            'post-', 'article-', 'blog-',  # Post identifiers
            '.html', '.php', '.aspx'  # File extensions
        ]
        
        url_lower = url.lower()
        
        # If URL contains post indicators, it's likely an individual post
        for indicator in post_indicators:
            if indicator in url_lower:
                return False
        
        # Check if it's likely a blog homepage
        blog_homepage_indicators = [
            '/blog$', '/posts$', '/articles$', '/news$',  # Ends with blog paths
            'medium.com', 'substack.com', 'wordpress.com'  # Known blog platforms
        ]
        
        for indicator in blog_homepage_indicators:
            if indicator.endswith('$'):
                # Use regex for end-of-string matching
                if re.search(indicator, url_lower):
                    return True
            elif indicator in url_lower:
                return True
        
        return False
    
    async def intelligently_decide_scraping_strategy(self, url: str) -> str:
        """
        Use OpenAI o1-mini to intelligently decide whether to scrape or crawl a URL.
        Returns 'scrape' or 'crawl' based on the analysis.
        """
        if not OPENAI_AVAILABLE or not self.openai_client:
            # Fallback to simple heuristics
            return self._fallback_scraping_decision(url)
        
        try:
            # Create a more specific prompt for the o1-mini model
            decision_prompt = f"""
            Analyze this URL and determine if it's a single page or a collection of pages.
            
            URL: {url}
            
            Rules:
            - If the URL points to a specific article, blog post, or single page → respond "scrape"
            - If the URL points to a homepage, blog index, or collection of pages → respond "crawl"
            
            Examples:
            - https://example.com/blog/post-123 → scrape (specific post)
            - https://example.com/blog → crawl (blog homepage)
            - https://example.com/article/how-to-code → scrape (specific article)
            - https://example.com/news → crawl (news homepage)
            - https://example.com/docs/getting-started → scrape (specific doc page)
            - https://example.com/docs → crawl (docs homepage)
            - https://example.com/blog/2024/01/my-post → scrape (specific post)
            - https://example.com/category/python → crawl (category page)
            
            Look for these patterns:
            - URLs with /post/, /article/, /entry/, /story/, /2024/, /2023/ → usually scrape
            - URLs ending with .html, .php, .aspx → usually scrape
            - URLs with just /blog, /news, /docs, /category → usually crawl
            - URLs with many slashes and specific titles → usually scrape
            
            Respond with exactly one word: "scrape" or "crawl"
            """
            
            # Call o1-mini for intelligent decision (fixed parameter)
            response = self.openai_client.chat.completions.create(
                model="o1-mini",
                messages=[
                    {"role": "user", "content": decision_prompt}
                ],
                max_completion_tokens=10,  # Fixed: use max_completion_tokens instead of max_tokens
                temperature=0.1
            )
            
            decision = response.choices[0].message.content.strip().lower()
            
            # Validate the response
            if decision in ['scrape', 'crawl']:
                logger.info(f"Intelligent decision for {url}: {decision}")
                return decision
            else:
                logger.warning(f"Invalid decision from o1-mini: {decision}, using fallback")
                return self._fallback_scraping_decision(url)
                
        except Exception as e:
            logger.error(f"Error in intelligent decision making: {e}")
            return self._fallback_scraping_decision(url)
    
    def _fallback_scraping_decision(self, url: str) -> str:
        """
        Fallback decision logic when o1-mini is not available.
        """
        url_lower = url.lower()
        
        # Patterns that suggest single pages (scrape)
        single_page_patterns = [
            '/post/', '/article/', '/entry/', '/story/', '/blog/',
            '/2024/', '/2023/', '/2022/', '/2021/', '/2020/',
            '.html', '.php', '.aspx', '.jsp',
            '/page/', '/single/', '/view/',
            # Specific title patterns
            '/how-to-', '/guide-', '/tutorial-', '/learn-',
            '/getting-started', '/introduction', '/overview'
        ]
        
        # Patterns that suggest collection pages (crawl)
        collection_patterns = [
            '/blog$', '/news$', '/docs$', '/articles$',
            '/category/', '/tag/', '/topic/',
            '/archive/', '/index$', '/home$',
            '/search', '/filter', '/browse'
        ]
        
        # Check for single page patterns first
        for pattern in single_page_patterns:
            if pattern in url_lower:
                logger.info(f"Fallback decision: scrape (pattern: {pattern})")
                return "scrape"
        
        # Check for collection patterns
        for pattern in collection_patterns:
            if pattern in url_lower:
                logger.info(f"Fallback decision: crawl (pattern: {pattern})")
                return "crawl"
        
        # Count slashes to estimate depth
        slash_count = url.count('/')
        if slash_count >= 4:  # Deep URL, likely single page
            logger.info(f"Fallback decision: scrape (deep URL with {slash_count} slashes)")
            return "scrape"
        else:  # Shallow URL, likely collection
            logger.info(f"Fallback decision: crawl (shallow URL with {slash_count} slashes)")
            return "crawl"
    
    async def handle_intelligent_url_processing(self, url: str, max_items: int = 10) -> Dict[str, Any]:
        """
        Intelligently decide whether to scrape or crawl a URL using o1-mini.
        """
        logger.info(f"Intelligently processing URL: {url}")
        
        try:
            # Use o1-mini to decide the best strategy
            strategy = await self.intelligently_decide_scraping_strategy(url)
            
            if strategy == 'crawl':
                logger.info(f"Intelligent decision: crawling {url}")
                crawl_request = f"crawl {url}"
                return await self.handle_crawl_request(crawl_request)
            else:
                logger.info(f"Intelligent decision: scraping {url}")
                return await self.handle_direct_url(url, max_items)
                
        except Exception as e:
            logger.error(f"Error in intelligent URL processing: {e}")
            # Fallback to direct URL handling
            return await self.handle_direct_url(url, max_items)

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
                
                # Append to file instead of overwriting
                output_file = f"scraped_data_{team_id}.json"
                if os.path.exists(output_file):
                    with open(output_file, 'r') as f:
                        try:
                            all_results = json.load(f)
                        except Exception:
                            all_results = []
                else:
                    all_results = []
                all_results.append(result)
                with open(output_file, 'w') as f:
                    json.dump(all_results, f, indent=2)
                
                print(f"📄 Appended to: {output_file}")
                
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