#!/usr/bin/env python3
"""
Test suite for THT Scraper - validates scraping capabilities across different blog types.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import List, Dict, Any
from scraper import THTScraper, BlogExtractor, PDFExtractor

class TestSuite:
    """Test suite for validating scraper functionality."""
    
    def __init__(self):
        self.test_blogs = [
            "https://interviewing.io/blog",
            "https://quill.co/blog",
            "https://nilmamano.com/blog/category/dsa",
            "https://shreycation.substack.com",
            "https://blog.pragmaticengineer.com",
            "https://martin.kleppmann.com",
            "https://jvns.ca",
            "https://blog.codinghorror.com",
            "https://joel.onsoftware.com",
            "https://paulgraham.com"
        ]
        
        self.test_urls = [
            "https://interviewing.io/topics#companies",
            "https://interviewing.io/learn#interview-guides"
        ]
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return results."""
        results = {
            "total_blogs_tested": 0,
            "successful_scrapes": 0,
            "failed_scrapes": 0,
            "blog_results": {},
            "url_results": {},
            "pdf_results": {}
        }
        
        print("🧪 Starting THT Scraper Test Suite")
        print("=" * 50)
        
        # Test blog scraping
        print("\n📝 Testing Blog Scraping...")
        for blog_url in self.test_blogs:
            print(f"\nTesting: {blog_url}")
            result = self.test_blog_scraping(blog_url)
            results["blog_results"][blog_url] = result
            results["total_blogs_tested"] += 1
            
            if result["success"]:
                results["successful_scrapes"] += 1
                print(f"✅ Success: {result['items_count']} items extracted")
            else:
                results["failed_scrapes"] += 1
                print(f"❌ Failed: {result['error']}")
        
        # Test URL scraping
        print("\n🔗 Testing URL Scraping...")
        for url in self.test_urls:
            print(f"\nTesting: {url}")
            result = self.test_url_scraping(url)
            results["url_results"][url] = result
        
        # Test PDF extraction (if we have a sample)
        print("\n📄 Testing PDF Extraction...")
        result = self.test_pdf_extraction()
        results["pdf_results"] = result
        
        # Print summary
        self.print_summary(results)
        
        return results
    
    def test_blog_scraping(self, blog_url: str) -> Dict[str, Any]:
        """Test scraping a specific blog."""
        try:
            scraper = THTScraper("test_team")
            
            # Try with regular extraction first
            items = scraper.scrape_blog(blog_url, max_posts=3)
            
            if not items:
                # Try with Selenium
                scraper_selenium = THTScraper("test_team", use_selenium=True)
                items = scraper_selenium.scrape_blog(blog_url, max_posts=3)
            
            if items:
                return {
                    "success": True,
                    "items_count": len(items),
                    "sample_title": items[0]["title"] if items else "",
                    "sample_content_length": len(items[0]["content"]) if items else 0,
                    "content_types": list(set(item["content_type"] for item in items))
                }
            else:
                return {
                    "success": False,
                    "error": "No items extracted",
                    "items_count": 0
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "items_count": 0
            }
    
    def test_url_scraping(self, url: str) -> Dict[str, Any]:
        """Test scraping a specific URL."""
        try:
            scraper = THTScraper("test_team")
            items = scraper.scrape_urls([url])
            
            if items:
                return {
                    "success": True,
                    "items_count": len(items),
                    "sample_title": items[0]["title"] if items else "",
                    "sample_content_length": len(items[0]["content"]) if items else 0
                }
            else:
                return {
                    "success": False,
                    "error": "No items extracted",
                    "items_count": 0
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "items_count": 0
            }
    
    def test_pdf_extraction(self) -> Dict[str, Any]:
        """Test PDF extraction functionality."""
        try:
            # Create a simple test PDF
            test_pdf_path = self.create_test_pdf()
            
            if test_pdf_path and os.path.exists(test_pdf_path):
                scraper = THTScraper("test_team")
                items = scraper.scrape_pdf(test_pdf_path)
                
                # Clean up
                os.remove(test_pdf_path)
                
                if items:
                    return {
                        "success": True,
                        "items_count": len(items),
                        "sample_title": items[0]["title"] if items else "",
                        "sample_content_length": len(items[0]["content"]) if items else 0
                    }
                else:
                    return {
                        "success": False,
                        "error": "No items extracted from test PDF",
                        "items_count": 0
                    }
            else:
                return {
                    "success": False,
                    "error": "Could not create test PDF",
                    "items_count": 0
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "items_count": 0
            }
    
    def create_test_pdf(self) -> str:
        """Create a simple test PDF for testing."""
        try:
            import reportlab
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            temp_path = temp_file.name
            temp_file.close()
            
            # Create PDF
            c = canvas.Canvas(temp_path, pagesize=letter)
            c.setTitle("Test Document")
            c.setAuthor("Test Author")
            
            # Add some content
            c.drawString(100, 750, "Test Document Title")
            c.drawString(100, 720, "This is a test document for PDF extraction.")
            c.drawString(100, 700, "It contains multiple lines of text.")
            c.drawString(100, 680, "This should be extracted properly.")
            
            c.save()
            return temp_path
            
        except ImportError:
            # If reportlab is not available, return None
            return None
        except Exception:
            return None
    
    def print_summary(self, results: Dict[str, Any]):
        """Print test summary."""
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        total_tested = results["total_blogs_tested"]
        successful = results["successful_scrapes"]
        failed = results["failed_scrapes"]
        
        print(f"Total blogs tested: {total_tested}")
        print(f"Successful scrapes: {successful}")
        print(f"Failed scrapes: {failed}")
        print(f"Success rate: {(successful/total_tested*100):.1f}%" if total_tested > 0 else "N/A")
        
        print("\n📝 Blog Results:")
        for blog_url, result in results["blog_results"].items():
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {blog_url}: {result.get('items_count', 0)} items")
        
        print("\n🔗 URL Results:")
        for url, result in results["url_results"].items():
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {url}: {result.get('items_count', 0)} items")
        
        print("\n📄 PDF Results:")
        pdf_result = results["pdf_results"]
        status = "✅" if pdf_result.get("success") else "❌"
        print(f"  {status} PDF extraction: {pdf_result.get('items_count', 0)} items")
        
        # Save detailed results
        with open("test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        print(f"\n📄 Detailed results saved to: test_results.json")

def run_specific_test():
    """Run a specific test for debugging."""
    test_suite = TestSuite()
    
    # Test a specific blog
    blog_url = "https://quill.co/blog"
    print(f"Testing specific blog: {blog_url}")
    
    result = test_suite.test_blog_scraping(blog_url)
    print(f"Result: {json.dumps(result, indent=2)}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "specific":
        run_specific_test()
    else:
        test_suite = TestSuite()
        test_suite.run_all_tests() 