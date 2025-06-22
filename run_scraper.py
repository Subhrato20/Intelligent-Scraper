#!/usr/bin/env python3
"""
Simple CLI interface for THT Scraper - provides an interactive way to use the scraper.
"""

import sys
import os
from pathlib import Path
from scraper import THTScraper

def print_banner():
    """Print the scraper banner."""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                    THT Scraper 🚀                            ║
    ║              Technical Content Extractor                     ║
    ║                                                              ║
    ║  Built for technical thought leaders like Aline             ║
    ║  Import your expertise into AI-powered comment tools        ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

def get_team_id():
    """Get team ID from user."""
    print("\n🎯 Step 1: Enter your Team ID")
    print("   This will be used in the output knowledgebase file")
    team_id = input("   Team ID (e.g., aline123): ").strip()
    
    if not team_id:
        print("   Using default: test_team")
        team_id = "test_team"
    
    return team_id

def get_source_type():
    """Get source type from user."""
    print("\n📝 Step 2: Choose your content source")
    print("   1. Blog URL (e.g., https://interviewing.io/blog)")
    print("   2. PDF File (e.g., Aline's book)")
    print("   3. Multiple URLs (comma-separated)")
    print("   4. Run test suite")
    print("   5. Run examples")
    
    while True:
        choice = input("\n   Enter your choice (1-5): ").strip()
        if choice in ['1', '2', '3', '4', '5']:
            return choice
        print("   Please enter a number between 1 and 5")

def get_blog_url():
    """Get blog URL from user."""
    print("\n🌐 Step 3: Enter the blog URL")
    print("   Examples:")
    print("   - https://interviewing.io/blog")
    print("   - https://quill.co/blog")
    print("   - https://nilmamano.com/blog/category/dsa")
    
    url = input("\n   Blog URL: ").strip()
    
    if not url:
        print("   Using example: https://interviewing.io/blog")
        url = "https://interviewing.io/blog"
    
    return url

def get_pdf_path():
    """Get PDF file path from user."""
    print("\n📄 Step 3: Enter the PDF file path")
    print("   Make sure the PDF file is in the current directory")
    
    pdf_path = input("\n   PDF file path: ").strip()
    
    if not pdf_path:
        print("   Please provide a valid PDF file path")
        return get_pdf_path()
    
    if not os.path.exists(pdf_path):
        print(f"   ❌ File not found: {pdf_path}")
        print("   Please check the file path and try again")
        return get_pdf_path()
    
    return pdf_path

def get_urls():
    """Get multiple URLs from user."""
    print("\n🔗 Step 3: Enter multiple URLs (comma-separated)")
    print("   Examples:")
    print("   - https://interviewing.io/blog,https://quill.co/blog")
    print("   - https://url1.com,https://url2.com,https://url3.com")
    
    urls_input = input("\n   URLs: ").strip()
    
    if not urls_input:
        print("   Using example URLs")
        urls_input = "https://interviewing.io/blog,https://quill.co/blog"
    
    urls = [url.strip() for url in urls_input.split(',')]
    return urls

def get_max_posts():
    """Get maximum number of posts to scrape."""
    print("\n📊 Step 4: Maximum number of posts to scrape")
    print("   (Higher numbers = more content but longer processing time)")
    
    while True:
        try:
            max_posts = input("\n   Max posts (default: 10): ").strip()
            if not max_posts:
                return 10
            max_posts = int(max_posts)
            if max_posts > 0:
                return max_posts
            print("   Please enter a positive number")
        except ValueError:
            print("   Please enter a valid number")

def get_output_file():
    """Get output file name from user."""
    print("\n💾 Step 5: Output file name")
    print("   The file will be saved in JSON format")
    
    output = input("\n   Output file (default: knowledgebase.json): ").strip()
    
    if not output:
        return "knowledgebase.json"
    
    if not output.endswith('.json'):
        output += '.json'
    
    return output

def get_selenium_choice():
    """Ask if user wants to use Selenium."""
    print("\n🤖 Step 6: Use Selenium for JavaScript-heavy sites?")
    print("   - Yes: Better for modern, dynamic websites")
    print("   - No: Faster, works for most traditional blogs")
    
    choice = input("\n   Use Selenium? (y/n, default: n): ").strip().lower()
    
    return choice in ['y', 'yes']

def scrape_blog(team_id, blog_url, max_posts, output_file, use_selenium):
    """Scrape a blog."""
    print(f"\n🚀 Starting blog scrape...")
    print(f"   Team ID: {team_id}")
    print(f"   Blog URL: {blog_url}")
    print(f"   Max Posts: {max_posts}")
    print(f"   Use Selenium: {use_selenium}")
    print(f"   Output: {output_file}")
    
    try:
        scraper = THTScraper(team_id, use_selenium=use_selenium)
        items = scraper.scrape_blog(blog_url, max_posts=max_posts)
        
        if items:
            scraper.export_to_knowledgebase_format(items, output_file)
            print(f"\n✅ Success! Extracted {len(items)} items")
            print(f"📄 Saved to: {output_file}")
            
            # Show sample
            if items:
                sample = items[0]
                print(f"\n📝 Sample item:")
                print(f"   Title: {sample['title'][:50]}...")
                print(f"   Content Length: {len(sample['content'])} characters")
                print(f"   Author: {sample['author']}")
        else:
            print(f"\n❌ No items extracted")
            print("   Try using Selenium for JavaScript-heavy sites")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("   Check the URL and try again")

def scrape_pdf(team_id, pdf_path, output_file):
    """Scrape a PDF."""
    print(f"\n🚀 Starting PDF scrape...")
    print(f"   Team ID: {team_id}")
    print(f"   PDF Path: {pdf_path}")
    print(f"   Output: {output_file}")
    
    try:
        scraper = THTScraper(team_id)
        items = scraper.scrape_pdf(pdf_path)
        
        if items:
            scraper.export_to_knowledgebase_format(items, output_file)
            print(f"\n✅ Success! Extracted {len(items)} chunks")
            print(f"📄 Saved to: {output_file}")
            
            # Show sample
            if items:
                sample = items[0]
                print(f"\n📝 Sample chunk:")
                print(f"   Title: {sample['title']}")
                print(f"   Content Length: {len(sample['content'])} characters")
        else:
            print(f"\n❌ No content extracted from PDF")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("   Check the PDF file and try again")

def scrape_urls(team_id, urls, output_file, use_selenium):
    """Scrape multiple URLs."""
    print(f"\n🚀 Starting URL scrape...")
    print(f"   Team ID: {team_id}")
    print(f"   URLs: {len(urls)} URLs")
    print(f"   Use Selenium: {use_selenium}")
    print(f"   Output: {output_file}")
    
    try:
        scraper = THTScraper(team_id, use_selenium=use_selenium)
        items = scraper.scrape_urls(urls)
        
        if items:
            scraper.export_to_knowledgebase_format(items, output_file)
            print(f"\n✅ Success! Extracted {len(items)} items")
            print(f"📄 Saved to: {output_file}")
        else:
            print(f"\n❌ No items extracted")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")

def run_test_suite():
    """Run the test suite."""
    print("\n🧪 Running test suite...")
    print("   This will test the scraper on various blog types")
    
    try:
        from test_scraper import TestSuite
        test_suite = TestSuite()
        results = test_suite.run_all_tests()
        
        print(f"\n✅ Test suite completed!")
        print(f"📊 Results saved to: test_results.json")
        
    except Exception as e:
        print(f"\n❌ Error running test suite: {e}")

def run_examples():
    """Run the examples."""
    print("\n📚 Running examples...")
    print("   This will demonstrate various scraping scenarios")
    
    try:
        from examples import main as run_examples_main
        run_examples_main()
        
        print(f"\n✅ Examples completed!")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")

def main():
    """Main interactive CLI function."""
    print_banner()
    
    try:
        # Get team ID
        team_id = get_team_id()
        
        # Get source type
        source_type = get_source_type()
        
        if source_type == '1':  # Blog URL
            blog_url = get_blog_url()
            max_posts = get_max_posts()
            output_file = get_output_file()
            use_selenium = get_selenium_choice()
            
            scrape_blog(team_id, blog_url, max_posts, output_file, use_selenium)
            
        elif source_type == '2':  # PDF File
            pdf_path = get_pdf_path()
            output_file = get_output_file()
            
            scrape_pdf(team_id, pdf_path, output_file)
            
        elif source_type == '3':  # Multiple URLs
            urls = get_urls()
            output_file = get_output_file()
            use_selenium = get_selenium_choice()
            
            scrape_urls(team_id, urls, output_file, use_selenium)
            
        elif source_type == '4':  # Test suite
            run_test_suite()
            
        elif source_type == '5':  # Examples
            run_examples()
        
        print(f"\n🎉 All done! Check the output files in the current directory.")
        
    except KeyboardInterrupt:
        print(f"\n\n👋 Scraping cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("   Please check your inputs and try again")

if __name__ == "__main__":
    main() 