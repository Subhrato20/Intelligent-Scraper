#!/usr/bin/env python3
"""
Enhanced Agent Layer for THT Scraper
- Integrates intelligent scraper with existing agent layer
- Supports both function-calling and natural language requests
- Provides unified interface for all scraping capabilities
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from intelligent_scraper import IntelligentScraper

# --- Tool Wrappers for Function Calling ---
async def scrape_intelligent(team_id: str, request: str, max_items: int = 10, use_selenium: bool = False) -> Dict[str, Any]:
    """
    Intelligent scraping that handles both URLs and natural language.
    """
    scraper = IntelligentScraper(team_id, use_selenium=use_selenium)
    return await scraper.process_request(request, max_items)

def scrape_blog(team_id: str, blog_url: str, max_posts: int = 50, use_selenium: bool = False) -> Dict[str, Any]:
    """
    Legacy blog scraping function for backward compatibility.
    """
    scraper = IntelligentScraper(team_id, use_selenium=use_selenium)
    # Run synchronously for backward compatibility
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(scraper.handle_direct_url(blog_url, max_posts))
        return result
    finally:
        loop.close()

def scrape_pdf(team_id: str, pdf_path: str) -> Dict[str, Any]:
    """
    Legacy PDF scraping function for backward compatibility.
    """
    scraper = IntelligentScraper(team_id)
    # Run synchronously for backward compatibility
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(scraper.handle_direct_url(pdf_path))
        return result
    finally:
        loop.close()

def scrape_urls(team_id: str, urls: List[str], use_selenium: bool = False) -> Dict[str, Any]:
    """
    Legacy URL scraping function for backward compatibility.
    """
    scraper = IntelligentScraper(team_id, use_selenium=use_selenium)
    # Run synchronously for backward compatibility
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(scraper.handle_direct_url(urls[0] if len(urls) == 1 else urls[0]))
        return result
    finally:
        loop.close()

# --- Enhanced Tool Schemas for LLM ---
enhanced_openai_tools = [
    {
        "type": "function",
        "function": {
            "name": "scrape_intelligent",
            "description": "Intelligent scraping that handles both direct URLs and natural language requests. Use this for complex requests like 'go to Quora software engineering and scrape the second post' or direct URLs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "team_id": {"type": "string", "description": "Team ID for the knowledgebase"},
                    "request": {"type": "string", "description": "Either a direct URL or natural language request like 'go to Quora software engineering and scrape the second post'"},
                    "max_items": {"type": "integer", "default": 10, "description": "Maximum number of items to extract"},
                    "use_selenium": {"type": "boolean", "default": False, "description": "Use Selenium for JavaScript-heavy sites"}
                },
                "required": ["team_id", "request"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scrape_blog",
            "description": "Scrape all posts from a blog URL and return in knowledgebase format.",
            "parameters": {
                "type": "object",
                "properties": {
                    "team_id": {"type": "string"},
                    "blog_url": {"type": "string"},
                    "max_posts": {"type": "integer", "default": 50},
                    "use_selenium": {"type": "boolean", "default": False}
                },
                "required": ["team_id", "blog_url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scrape_pdf",
            "description": "Scrape content from a PDF file and return in knowledgebase format.",
            "parameters": {
                "type": "object",
                "properties": {
                    "team_id": {"type": "string"},
                    "pdf_path": {"type": "string"}
                },
                "required": ["team_id", "pdf_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scrape_urls",
            "description": "Scrape content from a list of URLs and return in knowledgebase format.",
            "parameters": {
                "type": "object",
                "properties": {
                    "team_id": {"type": "string"},
                    "urls": {"type": "array", "items": {"type": "string"}},
                    "use_selenium": {"type": "boolean", "default": False}
                },
                "required": ["team_id", "urls"]
            }
        }
    }
]

# --- LLM Orchestration with Enhanced Capabilities ---
async def run_enhanced_llm_agent(user_message: str, team_id: str = "test_team", llm_api_key: Optional[str] = None):
    """
    Enhanced LLM agent that can handle both function calling and natural language requests.
    """
    print(f"\n🤖 [Enhanced LLM] Received user message: {user_message}")
    
    # Check if it's a natural language request that should use browser-use directly
    scraper = IntelligentScraper(team_id, llm_api_key=llm_api_key)
    
    if scraper.is_natural_language_request(user_message):
        print(f"[Enhanced LLM] Detected natural language request, using browser-use")
        result = await scraper.process_request(user_message)
    else:
        # Use simple heuristics for backward compatibility
        print(f"[Enhanced LLM] Using function calling approach")
        if "pdf" in user_message.lower():
            pdf_path = user_message.split()[-1]
            print(f"[Enhanced LLM] Calling scrape_pdf with: team_id={team_id}, pdf_path={pdf_path}")
            result = scrape_pdf(team_id, pdf_path)
        elif "blog" in user_message.lower() or "http" in user_message.lower():
            # Extract URL
            tokens = user_message.split()
            url = next((t for t in tokens if t.startswith("http")), None)
            print(f"[Enhanced LLM] Calling scrape_blog with: team_id={team_id}, blog_url={url}")
            result = scrape_blog(team_id, url)
        elif "urls" in user_message.lower():
            # Extract URLs (comma-separated)
            urls = [t for t in user_message.split() if t.startswith("http")]
            print(f"[Enhanced LLM] Calling scrape_urls with: team_id={team_id}, urls={urls}")
            result = scrape_urls(team_id, urls)
        else:
            print("[Enhanced LLM] Could not determine tool to call.")
            return None
    
    print(f"[Enhanced LLM] Tool call result: {len(result.get('items', []))} items.")
    return result

# --- CLI for Demo/Testing ---
async def main():
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║            Enhanced THT Scraper Agent Layer                 ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    print("Enhanced capabilities:")
    print("  - Direct URLs: 'https://interviewing.io/blog'")
    print("  - Natural language: 'Go to Quora software engineering and scrape the second post'")
    print("  - Complex requests: 'Visit Reddit r/programming and get the top 5 posts'")
    print("  - PDF files: 'Import this PDF aline_book.pdf'")
    print("Type 'exit' to quit.")
    
    team_id = input("\nTeam ID (default: test_team): ").strip() or "test_team"
    
    # Check for browser-use
    try:
        from browser_use import Agent
        llm_api_key = input("\nLLM API Key (optional, for natural language): ").strip() or None
    except ImportError:
        print("\n⚠️  browser-use not available. Install with: pip install browser-use")
        print("   Only direct URLs and basic requests will work.")
        llm_api_key = None
    
    while True:
        user_message = input("\nUser: ").strip()
        if user_message.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break
        
        result = await run_enhanced_llm_agent(user_message, team_id, llm_api_key)
        
        if result:
            if "error" in result:
                print(f"\n[Agent] Error: {result['error']}")
            else:
                print(f"\n[Agent] Output: {json.dumps(result, indent=2)[:1000]}...\n[truncated]")
                
                # Save to file
                output_file = f"enhanced_agent_{team_id}.json"
                with open(output_file, 'w') as f:
                    json.dump(result, f, indent=2)
                print(f"📄 Saved to: {output_file}")
        else:
            print("[Agent] No result.")

if __name__ == "__main__":
    asyncio.run(main()) 