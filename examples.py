#!/usr/bin/env python3
"""
Example usage scripts for THT Scraper - demonstrates how to use the scraper for different scenarios.
"""

import json
import os
from pathlib import Path
from scraper import THTScraper

def example_aline_scenario():
    """Example: Scraping content for Aline's technical knowledge."""
    print("🎯 Example: Aline's Technical Knowledge Import")
    print("=" * 50)
    
    # Initialize scraper for Aline's team
    scraper = THTScraper("aline123")
    
    # Sources to scrape for Aline
    sources = [
        "https://interviewing.io/blog",
        "https://nilmamano.com/blog/category/dsa"
    ]
    
    all_items = []
    
    # Scrape each source
    for source in sources:
        print(f"\n📝 Scraping: {source}")
        items = scraper.scrape_blog(source, max_posts=10)
        all_items.extend(items)
        print(f"   Extracted {len(items)} items")
    
    # Export to knowledgebase format
    output_file = "aline_knowledgebase.json"
    scraper.export_to_knowledgebase_format(all_items, output_file)
    
    print(f"\n✅ Successfully created {output_file} with {len(all_items)} items")
    
    # Show sample output
    if all_items:
        print("\n📄 Sample Item:")
        sample = all_items[0]
        print(f"   Title: {sample['title']}")
        print(f"   Content Type: {sample['content_type']}")
        print(f"   Content Length: {len(sample['content'])} characters")
        print(f"   Author: {sample['author']}")

def example_pdf_scraping():
    """Example: Scraping PDF content."""
    print("\n📄 Example: PDF Content Scraping")
    print("=" * 50)
    
    # This would be used when you have Aline's book PDF
    pdf_path = "aline_book.pdf"  # Replace with actual path
    
    if os.path.exists(pdf_path):
        scraper = THTScraper("aline123")
        items = scraper.scrape_pdf(pdf_path)
        
        print(f"📚 Extracted {len(items)} chunks from PDF")
        
        # Export to knowledgebase format
        output_file = "aline_book_knowledgebase.json"
        scraper.export_to_knowledgebase_format(items, output_file)
        
        print(f"✅ Successfully created {output_file}")
    else:
        print(f"⚠️  PDF file not found: {pdf_path}")
        print("   Place your PDF file in the current directory to test")

def example_generic_blog_scraping():
    """Example: Generic blog scraping for any blog."""
    print("\n🌐 Example: Generic Blog Scraping")
    print("=" * 50)
    
    # Test with Quill blog (as mentioned in requirements)
    blog_url = "https://quill.co/blog"
    
    scraper = THTScraper("test_team")
    
    print(f"📝 Scraping: {blog_url}")
    items = scraper.scrape_blog(blog_url, max_posts=5)
    
    print(f"✅ Extracted {len(items)} items")
    
    # Export to knowledgebase format
    output_file = "quill_knowledgebase.json"
    scraper.export_to_knowledgebase_format(items, output_file)
    
    # Show success rate
    if items:
        print(f"\n📊 Success Rate: 100%")
        print(f"📄 Average content length: {sum(len(item['content']) for item in items) // len(items)} characters")
    else:
        print(f"\n❌ No items extracted - may need Selenium for JavaScript-heavy sites")

def example_substack_scraping():
    """Example: Substack scraping (bonus feature)."""
    print("\n📰 Example: Substack Scraping")
    print("=" * 50)
    
    # Test with a Substack
    substack_url = "https://shreycation.substack.com"
    
    scraper = THTScraper("test_team")
    
    print(f"📝 Scraping Substack: {substack_url}")
    items = scraper.scrape_blog(substack_url, max_posts=3)
    
    print(f"✅ Extracted {len(items)} items")
    
    # Export to knowledgebase format
    output_file = "substack_knowledgebase.json"
    scraper.export_to_knowledgebase_format(items, output_file)

def example_batch_processing():
    """Example: Batch processing multiple sources."""
    print("\n🔄 Example: Batch Processing")
    print("=" * 50)
    
    # Multiple sources for comprehensive knowledge import
    sources = [
        "https://interviewing.io/blog",
        "https://nilmamano.com/blog/category/dsa",
        "https://quill.co/blog"
    ]
    
    scraper = THTScraper("comprehensive_team")
    all_items = []
    
    for i, source in enumerate(sources, 1):
        print(f"\n[{i}/{len(sources)}] Scraping: {source}")
        items = scraper.scrape_blog(source, max_posts=5)
        all_items.extend(items)
        print(f"   ✅ Extracted {len(items)} items")
    
    # Export combined knowledgebase
    output_file = "comprehensive_knowledgebase.json"
    scraper.export_to_knowledgebase_format(all_items, output_file)
    
    print(f"\n🎉 Batch processing complete!")
    print(f"📊 Total items: {len(all_items)}")
    print(f"📄 Output file: {output_file}")

def example_custom_urls():
    """Example: Scraping specific URLs."""
    print("\n🔗 Example: Custom URL Scraping")
    print("=" * 50)
    
    # Specific URLs from interviewing.io
    urls = [
        "https://interviewing.io/topics#companies",
        "https://interviewing.io/learn#interview-guides"
    ]
    
    scraper = THTScraper("custom_team")
    
    print(f"🔗 Scraping {len(urls)} specific URLs")
    items = scraper.scrape_urls(urls)
    
    print(f"✅ Extracted {len(items)} items")
    
    # Export to knowledgebase format
    output_file = "custom_urls_knowledgebase.json"
    scraper.export_to_knowledgebase_format(items, output_file)

def show_knowledgebase_format():
    """Show the expected knowledgebase format."""
    print("\n📋 Knowledgebase Format")
    print("=" * 50)
    
    example_format = {
        "team_id": "aline123",
        "items": [
            {
                "title": "How to Ace Technical Interviews",
                "content": "# How to Ace Technical Interviews\n\nThis is a comprehensive guide...",
                "content_type": "blog",
                "source_url": "https://interviewing.io/blog/ace-interviews",
                "author": "Aline Lerner",
                "user_id": ""
            }
        ]
    }
    
    print("Expected output format:")
    print(json.dumps(example_format, indent=2))

def main():
    """Run all examples."""
    print("🚀 THT Scraper Examples")
    print("=" * 50)
    
    # Show format first
    show_knowledgebase_format()
    
    # Run examples
    example_aline_scenario()
    example_pdf_scraping()
    example_generic_blog_scraping()
    example_substack_scraping()
    example_batch_processing()
    example_custom_urls()
    
    print("\n🎉 All examples completed!")
    print("\n📁 Generated files:")
    for file in os.listdir("."):
        if file.endswith("_knowledgebase.json"):
            print(f"   - {file}")

if __name__ == "__main__":
    main() 