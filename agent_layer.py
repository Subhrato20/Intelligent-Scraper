#!/usr/bin/env python3
"""
Agent Layer for THT Scraper
- Exposes scraping functions as tools for LLM orchestration (OpenAI function-calling style)
- Modular: can be adapted for other LLMs or agent frameworks
"""

import os
import json
import sys
from typing import List, Dict, Any
from scraper import THTScraper

# --- Tool Wrappers ---
def scrape_blog(team_id: str, blog_url: str, max_posts: int = 50, use_selenium: bool = False) -> Dict[str, Any]:
    scraper = THTScraper(team_id, use_selenium=use_selenium)
    items = scraper.scrape_blog(blog_url, max_posts=max_posts)
    return scraper.export_to_knowledgebase_format(items)

def scrape_pdf(team_id: str, pdf_path: str) -> Dict[str, Any]:
    scraper = THTScraper(team_id)
    items = scraper.scrape_pdf(pdf_path)
    return scraper.export_to_knowledgebase_format(items)

def scrape_urls(team_id: str, urls: List[str], use_selenium: bool = False) -> Dict[str, Any]:
    scraper = THTScraper(team_id, use_selenium=use_selenium)
    items = scraper.scrape_urls(urls)
    return scraper.export_to_knowledgebase_format(items)

# --- Tool Schemas for LLM ---
openai_tools = [
    {
        "type": "function",
        "function": {
            "name": "scrape_blog",
            "description": "Scrape all posts from a blog and return in knowledgebase format.",
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

# --- LLM Orchestration Example (OpenAI) ---
def run_llm_agent(user_message: str, team_id: str = "test_team"):  # Demo only
    """
    Simulate an LLM agent that receives a user message, decides which tool to call,
    and returns the result. (In production, this would use OpenAI's API or similar.)
    """
    print(f"\n🤖 [LLM] Received user message: {user_message}")
    # For demo, we'll use simple heuristics to pick a tool
    if "pdf" in user_message.lower():
        pdf_path = user_message.split()[-1]
        print(f"[LLM] Calling scrape_pdf with: team_id={team_id}, pdf_path={pdf_path}")
        result = scrape_pdf(team_id, pdf_path)
    elif "blog" in user_message.lower() or "http" in user_message.lower():
        # Extract URL
        tokens = user_message.split()
        url = next((t for t in tokens if t.startswith("http")), None)
        print(f"[LLM] Calling scrape_blog with: team_id={team_id}, blog_url={url}")
        result = scrape_blog(team_id, url)
    elif "urls" in user_message.lower():
        # Extract URLs (comma-separated)
        urls = [t for t in user_message.split() if t.startswith("http")]
        print(f"[LLM] Calling scrape_urls with: team_id={team_id}, urls={urls}")
        result = scrape_urls(team_id, urls)
    else:
        print("[LLM] Could not determine tool to call.")
        return None
    print(f"[LLM] Tool call result: {len(result['items'])} items.")
    return result

# --- CLI for Demo/Testing ---
def main():
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                THT Scraper Agent Layer Demo                 ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    print("Type a high-level request (e.g. 'Import all technical content from https://interviewing.io/blog')")
    print("Or: 'Import this PDF aline_book.pdf' or 'Import these URLs https://a.com https://b.com'")
    print("Type 'exit' to quit.")
    team_id = input("Team ID (default: test_team): ").strip() or "test_team"
    while True:
        user_message = input("\nUser: ").strip()
        if user_message.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break
        result = run_llm_agent(user_message, team_id)
        if result:
            print(f"\n[Agent] Output: {json.dumps(result, indent=2)[:1000]}...\n[truncated]")
        else:
            print("[Agent] No result.")

if __name__ == "__main__":
    main() 