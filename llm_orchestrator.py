import os
import json
import openai
import requests
import re
from scraper import THTScraper

# --- Tool Wrappers ---
def scrape_blog(team_id: str, blog_url: str, max_posts: int = 50, use_selenium: bool = False):
    scraper = THTScraper(team_id, use_selenium=use_selenium)
    items = scraper.scrape_blog(blog_url, max_posts=max_posts)
    return scraper.export_to_knowledgebase_format(items)

def scrape_pdf(team_id: str, pdf_path: str):
    scraper = THTScraper(team_id)
    items = scraper.scrape_pdf(pdf_path)
    return scraper.export_to_knowledgebase_format(items)

def scrape_urls(team_id: str, urls: list, use_selenium: bool = False):
    scraper = THTScraper(team_id, use_selenium=use_selenium)
    items = scraper.scrape_urls(urls)
    return scraper.export_to_knowledgebase_format(items)

def scrape_google_drive_pdf(team_id: str, drive_url: str):
    """Download PDF from Google Drive and scrape it."""
    print(f"📥 Downloading PDF from Google Drive: {drive_url}")
    
    # Extract file ID from Google Drive URL
    file_id_match = re.search(r'/file/d/([a-zA-Z0-9-_]+)', drive_url)
    if not file_id_match:
        raise ValueError("Could not extract file ID from Google Drive URL")
    
    file_id = file_id_match.group(1)
    download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
    
    # Download the PDF
    response = requests.get(download_url, stream=True)
    response.raise_for_status()
    
    # Save to temporary file
    temp_filename = f"temp_drive_pdf_{file_id}.pdf"
    with open(temp_filename, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    print(f"✅ Downloaded PDF to: {temp_filename}")
    
    try:
        # Scrape the downloaded PDF
        result = scrape_pdf(team_id, temp_filename)
        
        # Clean up temporary file
        os.remove(temp_filename)
        print(f"🧹 Cleaned up temporary file: {temp_filename}")
        
        return result
    except Exception as e:
        # Clean up on error too
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
        raise e

# --- Tool Schemas ---
openai_tools = [
    {
        "type": "function",
        "function": {
            "name": "scrape_blog",
            "description": "Scrape all posts from a blog and return in knowledgebase format. Use this for blog URLs like https://interviewing.io/blog",
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
            "description": "Scrape content from a local PDF file and return in knowledgebase format. Use this for local PDF files like 'aline_book.pdf'",
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
            "name": "scrape_google_drive_pdf",
            "description": "Download and scrape content from a PDF file stored on Google Drive. Use this for Google Drive URLs like https://drive.google.com/file/d/FILE_ID/view",
            "parameters": {
                "type": "object",
                "properties": {
                    "team_id": {"type": "string"},
                    "drive_url": {"type": "string"}
                },
                "required": ["team_id", "drive_url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scrape_urls",
            "description": "Scrape content from a list of URLs and return in knowledgebase format. Use this for individual web pages or multiple URLs",
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

# --- LLM Orchestration ---
def orchestrate_with_llm(user_message, team_id="test_team"):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable not set.")
    
    client = openai.OpenAI(api_key=api_key)
    messages = [
        {
            "role": "system", 
            "content": """You are an agent that helps import technical knowledge into a knowledgebase. 
You MUST use one of the available tools to fulfill the user's request. Do not respond with text - always call a tool.

- For blog URLs (like https://interviewing.io/blog), use scrape_blog
- For local PDF files (like 'aline_book.pdf'), use scrape_pdf  
- For Google Drive PDF URLs (like https://drive.google.com/file/d/FILE_ID/view), use scrape_google_drive_pdf
- For individual web pages or multiple URLs, use scrape_urls

Always extract the relevant information from the user's request and call the appropriate tool."""
        },
        {"role": "user", "content": user_message}
    ]
    
    print(f"🤖 Sending request to GPT-4o: {user_message}")
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=openai_tools,
        tool_choice="auto"
    )
    
    print(f"🤖 LLM Response: {response.choices[0].message.content}")
    
    # Check if the LLM made a tool call
    if not response.choices[0].message.tool_calls:
        print("❌ LLM didn't call any tools. This might mean:")
        print("   - The request wasn't clear enough")
        print("   - The LLM didn't understand what to scrape")
        print("   - Try being more specific (e.g., 'scrape this blog: https://example.com')")
        return None
    
    tool_call = response.choices[0].message.tool_calls[0]
    function_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)
    
    print(f"✅ LLM chose tool: {function_name}")
    print(f"📋 Arguments: {arguments}")

    # Call the actual Python function
    try:
        if function_name == "scrape_blog":
            result = scrape_blog(**arguments)
        elif function_name == "scrape_pdf":
            result = scrape_pdf(**arguments)
        elif function_name == "scrape_google_drive_pdf":
            result = scrape_google_drive_pdf(**arguments)
        elif function_name == "scrape_urls":
            result = scrape_urls(**arguments)
        else:
            raise ValueError(f"Unknown function: {function_name}")

        print(f"✅ Successfully scraped {len(result['items'])} items")
        print(f"📄 Sample result: {json.dumps(result, indent=2)[:1000]}...\n[truncated]")
        return result
        
    except Exception as e:
        print(f"❌ Error running {function_name}: {e}")
        return None

if __name__ == "__main__":
    print("🚀 THT Scraper with GPT-4o Orchestration")
    print("=" * 50)
    print("Examples:")
    print("- scrape this blog: https://interviewing.io/blog")
    print("- scrape this PDF: aline_book.pdf")
    print("- scrape this PDF from Google Drive: https://drive.google.com/file/d/FILE_ID/view")
    print("- scrape these URLs: https://quill.co/blog, https://nilmamano.com/blog")
    print()
    
    user_message = input("User: ")
    team_id = input("Team ID (default: test_team): ").strip() or "test_team"
    
    result = orchestrate_with_llm(user_message, team_id)
    
    if result:
        # Save to file
        output_file = f"{team_id}_knowledgebase.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"💾 Results saved to: {output_file}")
    else:
        print("❌ No results generated") 