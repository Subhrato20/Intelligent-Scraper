#!/usr/bin/env python3
"""
THT Scraper - A comprehensive web scraper for extracting content from various sources
and formatting it for knowledgebase import.
"""

import json
import re
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from urllib.parse import urljoin, urlparse, parse_qs
import requests
from bs4 import BeautifulSoup
try:
    import feedparser
    FEEDPARSER_AVAILABLE = True
except ImportError:
    FEEDPARSER_AVAILABLE = False
    logging.warning("feedparser not available - RSS functionality will be limited")
from newspaper import Article
import trafilatura
from readability import Document
import PyPDF2
import pypdf
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from markdownify import markdownify as md
from tqdm import tqdm
import click

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ContentExtractor:
    """Base class for content extraction strategies."""
    
    def extract(self, url: str) -> Optional[Dict[str, Any]]:
        """Extract content from a URL. Returns None if extraction fails."""
        raise NotImplementedError

class BlogExtractor(ContentExtractor):
    """Extracts content from blog posts using multiple strategies."""
    
    def __init__(self, use_selenium: bool = False):
        self.use_selenium = use_selenium
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def extract(self, url: str) -> Optional[Dict[str, Any]]:
        """Extract content from a blog post URL."""
        try:
            if self.use_selenium:
                return self._extract_with_selenium(url)
            else:
                return self._extract_with_requests(url)
        except Exception as e:
            logger.error(f"Failed to extract content from {url}: {e}")
            return None
    
    def _extract_with_requests(self, url: str) -> Optional[Dict[str, Any]]:
        """Extract content using requests and multiple parsing strategies."""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Try trafilatura first (best for article extraction)
            extracted = trafilatura.extract(response.text, include_formatting=True, include_links=True)
            if extracted and len(extracted.strip()) > 200:
                return self._parse_with_trafilatura(response.text, url)
            
            # Fallback to readability
            extracted = self._parse_with_readability(response.text, url)
            if extracted:
                return extracted
            
            # Fallback to newspaper3k
            extracted = self._parse_with_newspaper(url)
            if extracted:
                return extracted
            
            # Last resort: manual parsing
            return self._parse_manually(response.text, url)
            
        except Exception as e:
            logger.error(f"Request extraction failed for {url}: {e}")
            return None
    
    def _extract_with_selenium(self, url: str) -> Optional[Dict[str, Any]]:
        """Extract content using Selenium for JavaScript-heavy sites."""
        driver = None
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
            driver.get(url)
            
            # Wait for content to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Additional wait for dynamic content
            time.sleep(3)
            
            page_source = driver.page_source
            return self._parse_with_trafilatura(page_source, url)
            
        except Exception as e:
            logger.error(f"Selenium extraction failed for {url}: {e}")
            return None
        finally:
            if driver:
                driver.quit()
    
    def _parse_with_trafilatura(self, html: str, url: str) -> Optional[Dict[str, Any]]:
        """Parse content using trafilatura."""
        try:
            # Extract metadata
            metadata = trafilatura.extract_metadata(html, url)
            
            # Extract main content
            content = trafilatura.extract(html, include_formatting=True, include_links=True)
            
            if not content or len(content.strip()) < 100:
                return None
            
            # Convert to markdown
            markdown_content = trafilatura.extract(html, output_format='markdown')
            
            return {
                "title": metadata.title if metadata and metadata.title else self._extract_title_from_html(html),
                "content": markdown_content,
                "content_type": "blog",
                "source_url": url,
                "author": metadata.author if metadata and metadata.author else "",
                "user_id": ""
            }
        except Exception as e:
            logger.error(f"Trafilatura parsing failed: {e}")
            return None
    
    def _parse_with_readability(self, html: str, url: str) -> Optional[Dict[str, Any]]:
        """Parse content using readability-lxml."""
        try:
            doc = Document(html)
            title = doc.title()
            content = doc.summary()
            
            if not content or len(content.strip()) < 100:
                return None
            
            # Convert HTML to markdown
            markdown_content = md(content)
            
            return {
                "title": title,
                "content": markdown_content,
                "content_type": "blog",
                "source_url": url,
                "author": self._extract_author_from_html(html),
                "user_id": ""
            }
        except Exception as e:
            logger.error(f"Readability parsing failed: {e}")
            return None
    
    def _parse_with_newspaper(self, url: str) -> Optional[Dict[str, Any]]:
        """Parse content using newspaper3k."""
        try:
            article = Article(url)
            article.download()
            article.parse()
            
            if not article.text or len(article.text.strip()) < 100:
                return None
            
            # Convert to markdown (simple conversion)
            markdown_content = self._text_to_markdown(article.text)
            
            return {
                "title": article.title,
                "content": markdown_content,
                "content_type": "blog",
                "source_url": url,
                "author": article.authors[0] if article.authors else "",
                "user_id": ""
            }
        except Exception as e:
            logger.error(f"Newspaper parsing failed: {e}")
            return None
    
    def _parse_manually(self, html: str, url: str) -> Optional[Dict[str, Any]]:
        """Manual parsing as last resort."""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Try to find main content areas
            content_selectors = [
                'article', 'main', '.content', '.post-content', '.entry-content',
                '.article-content', '.blog-content', '.post-body'
            ]
            
            content = None
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem and len(content_elem.get_text().strip()) > 200:
                    content = content_elem
                    break
            
            if not content:
                # Fallback to body
                content = soup.find('body')
            
            if not content:
                return None
            
            # Extract text and convert to markdown
            text = content.get_text(separator='\n', strip=True)
            markdown_content = self._text_to_markdown(text)
            
            return {
                "title": self._extract_title_from_html(html),
                "content": markdown_content,
                "content_type": "blog",
                "source_url": url,
                "author": self._extract_author_from_html(html),
                "user_id": ""
            }
        except Exception as e:
            logger.error(f"Manual parsing failed: {e}")
            return None
    
    def _extract_title_from_html(self, html: str) -> str:
        """Extract title from HTML."""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            title = soup.find('title')
            if title:
                return title.get_text().strip()
            
            # Try h1
            h1 = soup.find('h1')
            if h1:
                return h1.get_text().strip()
            
            return "Untitled"
        except:
            return "Untitled"
    
    def _extract_author_from_html(self, html: str) -> str:
        """Extract author from HTML."""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Common author selectors
            author_selectors = [
                '.author', '.byline', '.post-author', '.entry-author',
                '[rel="author"]', '.author-name', '.writer'
            ]
            
            for selector in author_selectors:
                author_elem = soup.select_one(selector)
                if author_elem:
                    return author_elem.get_text().strip()
            
            return ""
        except:
            return ""
    
    def _text_to_markdown(self, text: str) -> str:
        """Convert plain text to basic markdown."""
        lines = text.split('\n')
        markdown_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Simple heuristics for headers
            if len(line) < 100 and line.isupper():
                markdown_lines.append(f"## {line}")
            elif len(line) < 80 and line.endswith(':'):
                markdown_lines.append(f"### {line}")
            else:
                markdown_lines.append(line)
        
        return '\n\n'.join(markdown_lines)

class RSSFeedExtractor(ContentExtractor):
    """Extracts content from RSS feeds."""
    
    def __init__(self, blog_extractor: BlogExtractor):
        self.blog_extractor = blog_extractor
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def extract(self, url: str) -> List[Dict[str, Any]]:
        """Extract content from RSS feed URL."""
        try:
            if FEEDPARSER_AVAILABLE:
                return self._extract_with_feedparser(url)
            else:
                return self._extract_with_manual_rss(url)
        except Exception as e:
            logger.error(f"RSS extraction failed for {url}: {e}")
            return []
    
    def _extract_with_feedparser(self, url: str) -> List[Dict[str, Any]]:
        """Extract using feedparser library."""
        feed = feedparser.parse(url)
        items = []
        
        for entry in feed.entries:
            if hasattr(entry, 'link'):
                logger.info(f"Extracting from RSS entry: {entry.link}")
                content = self.blog_extractor.extract(entry.link)
                if content:
                    items.append(content)
                time.sleep(1)  # Be respectful
        
        return items
    
    def _extract_with_manual_rss(self, url: str) -> List[Dict[str, Any]]:
        """Manual RSS parsing as fallback when feedparser is not available."""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'xml')
            items = []
            
            # Look for RSS/Atom entries
            entries = soup.find_all(['item', 'entry'])
            
            for entry in entries:
                link_elem = entry.find(['link', 'url'])
                if link_elem:
                    link = link_elem.get_text().strip()
                    if link.startswith('http'):
                        logger.info(f"Extracting from RSS entry: {link}")
                        content = self.blog_extractor.extract(link)
                        if content:
                            items.append(content)
                        time.sleep(1)  # Be respectful
            
            return items
        except Exception as e:
            logger.error(f"Manual RSS parsing failed: {e}")
            return []

class PDFExtractor(ContentExtractor):
    """Extracts content from PDF files."""
    
    def extract(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract content from PDF file."""
        try:
            items = []
            
            # Try with pypdf first (newer library)
            try:
                items = self._extract_with_pypdf(file_path)
            except Exception as e:
                logger.warning(f"pypdf failed, trying PyPDF2: {e}")
                items = self._extract_with_pypdf2(file_path)
            
            return items
        except Exception as e:
            logger.error(f"PDF extraction failed for {file_path}: {e}")
            return []
    
    def _extract_with_pypdf(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract using pypdf library."""
        items = []
        
        with open(file_path, 'rb') as file:
            pdf_reader = pypdf.PdfReader(file)
            
            # Extract metadata
            metadata = pdf_reader.metadata
            title = metadata.get('/Title', 'Untitled') if metadata else 'Untitled'
            author = metadata.get('/Author', '') if metadata else ''
            
            # Process pages in chunks
            chunk_size = 5  # pages per chunk
            total_pages = len(pdf_reader.pages)
            
            for chunk_start in range(0, total_pages, chunk_size):
                chunk_end = min(chunk_start + chunk_size, total_pages)
                chunk_text = ""
                
                for page_num in range(chunk_start, chunk_end):
                    page = pdf_reader.pages[page_num]
                    chunk_text += page.extract_text() + "\n\n"
                
                if chunk_text.strip():
                    # Convert to markdown
                    markdown_content = self._text_to_markdown(chunk_text)
                    
                    items.append({
                        "title": f"{title} - Pages {chunk_start + 1}-{chunk_end}",
                        "content": markdown_content,
                        "content_type": "book",
                        "source_url": f"file://{file_path}",
                        "author": author,
                        "user_id": ""
                    })
        
        return items
    
    def _extract_with_pypdf2(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract using PyPDF2 library (fallback)."""
        items = []
        
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Extract metadata
            metadata = pdf_reader.metadata
            title = metadata.get('/Title', 'Untitled') if metadata else 'Untitled'
            author = metadata.get('/Author', '') if metadata else ''
            
            # Process pages in chunks
            chunk_size = 5
            total_pages = len(pdf_reader.pages)
            
            for chunk_start in range(0, total_pages, chunk_size):
                chunk_end = min(chunk_start + chunk_size, total_pages)
                chunk_text = ""
                
                for page_num in range(chunk_start, chunk_end):
                    page = pdf_reader.pages[page_num]
                    chunk_text += page.extract_text() + "\n\n"
                
                if chunk_text.strip():
                    markdown_content = self._text_to_markdown(chunk_text)
                    
                    items.append({
                        "title": f"{title} - Pages {chunk_start + 1}-{chunk_end}",
                        "content": markdown_content,
                        "content_type": "book",
                        "source_url": f"file://{file_path}",
                        "author": author,
                        "user_id": ""
                    })
        
        return items
    
    def _text_to_markdown(self, text: str) -> str:
        """Convert PDF text to markdown."""
        lines = text.split('\n')
        markdown_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Simple heuristics for headers
            if len(line) < 100 and line.isupper():
                markdown_lines.append(f"## {line}")
            elif len(line) < 80 and line.endswith(':'):
                markdown_lines.append(f"### {line}")
            else:
                markdown_lines.append(line)
        
        return '\n\n'.join(markdown_lines)

class URLDiscoverer:
    """Discovers URLs from various sources."""
    
    def __init__(self, blog_extractor: BlogExtractor):
        self.blog_extractor = blog_extractor
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def discover_blog_urls(self, base_url: str, max_pages: int = 10) -> List[str]:
        """Discover blog post URLs from a blog homepage."""
        urls = set()
        
        try:
            # Try to find pagination
            page_urls = self._discover_pagination(base_url, max_pages)
            
            for page_url in page_urls:
                page_urls = self._extract_blog_urls_from_page(page_url)
                urls.update(page_urls)
                time.sleep(1)  # Be respectful
            
            return list(urls)
        except Exception as e:
            logger.error(f"URL discovery failed for {base_url}: {e}")
            return []
    
    def _discover_pagination(self, base_url: str, max_pages: int) -> List[str]:
        """Discover pagination URLs."""
        page_urls = [base_url]
        
        try:
            response = self.session.get(base_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for pagination links
            pagination_selectors = [
                '.pagination a', '.pager a', '.page-numbers a',
                'a[rel="next"]', '.next a', '.prev a'
            ]
            
            for selector in pagination_selectors:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href')
                    if href:
                        full_url = urljoin(base_url, href)
                        if full_url not in page_urls and len(page_urls) < max_pages:
                            page_urls.append(full_url)
            
            return page_urls[:max_pages]
        except Exception as e:
            logger.error(f"Pagination discovery failed: {e}")
            return [base_url]
    
    def _extract_blog_urls_from_page(self, page_url: str) -> List[str]:
        """Extract blog post URLs from a single page."""
        urls = []
        
        try:
            response = self.session.get(page_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Common selectors for blog post links
            link_selectors = [
                'article a', '.post a', '.blog-post a', '.entry a',
                '.post-title a', '.entry-title a', 'h2 a', 'h3 a'
            ]
            
            for selector in link_selectors:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href')
                    if href:
                        full_url = urljoin(page_url, href)
                        # Filter out non-blog URLs
                        if self._is_blog_post_url(full_url):
                            urls.append(full_url)
            
            return list(set(urls))
        except Exception as e:
            logger.error(f"URL extraction failed for {page_url}: {e}")
            return []
    
    def _is_blog_post_url(self, url: str) -> bool:
        """Check if URL looks like a blog post."""
        # Skip common non-blog URLs
        skip_patterns = [
            r'/tag/', r'/category/', r'/author/', r'/page/', r'/search',
            r'/about', r'/contact', r'/privacy', r'/terms', r'/feed',
            r'\.(pdf|doc|docx|jpg|jpeg|png|gif)$'
        ]
        
        for pattern in skip_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return False
        
        return True

class THTScraper:
    """Main scraper class that orchestrates content extraction."""
    
    def __init__(self, team_id: str, use_selenium: bool = False):
        self.team_id = team_id
        self.blog_extractor = BlogExtractor(use_selenium=use_selenium)
        self.rss_extractor = RSSFeedExtractor(self.blog_extractor)
        self.pdf_extractor = PDFExtractor()
        self.url_discoverer = URLDiscoverer(self.blog_extractor)
    
    def scrape_blog(self, blog_url: str, max_posts: int = 50) -> List[Dict[str, Any]]:
        """Scrape a blog for all posts."""
        logger.info(f"Starting blog scrape for: {blog_url}")
        
        # Check if it's an RSS feed
        if self._is_rss_feed(blog_url):
            logger.info("Detected RSS feed, using RSS extractor")
            return self.rss_extractor.extract(blog_url)
        
        # Discover blog post URLs
        logger.info("Discovering blog post URLs...")
        blog_urls = self.url_discoverer.discover_blog_urls(blog_url)
        
        if not blog_urls:
            logger.warning("No blog URLs discovered, trying direct extraction")
            content = self.blog_extractor.extract(blog_url)
            return [content] if content else []
        
        # Limit the number of posts
        blog_urls = blog_urls[:max_posts]
        logger.info(f"Found {len(blog_urls)} blog posts to scrape")
        
        # Extract content from each URL
        items = []
        for url in tqdm(blog_urls, desc="Scraping blog posts"):
            content = self.blog_extractor.extract(url)
            if content:
                items.append(content)
            time.sleep(1)  # Be respectful
        
        return items
    
    def scrape_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Scrape content from a PDF file."""
        logger.info(f"Starting PDF scrape for: {pdf_path}")
        return self.pdf_extractor.extract(pdf_path)
    
    def scrape_urls(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Scrape content from a list of URLs."""
        logger.info(f"Starting URL scrape for {len(urls)} URLs")
        
        items = []
        for url in tqdm(urls, desc="Scraping URLs"):
            content = self.blog_extractor.extract(url)
            if content:
                items.append(content)
            time.sleep(1)  # Be respectful
        
        return items
    
    def _is_rss_feed(self, url: str) -> bool:
        """Check if URL is an RSS feed."""
        rss_patterns = [r'\.xml$', r'/feed', r'/rss', r'/atom']
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in rss_patterns)
    
    def export_to_knowledgebase_format(self, items: List[Dict[str, Any]], output_file: str = None) -> Dict[str, Any]:
        """Export items to knowledgebase format."""
        knowledgebase_data = {
            "team_id": self.team_id,
            "items": items
        }
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(knowledgebase_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Exported {len(items)} items to {output_file}")
        
        return knowledgebase_data

def main():
    """Main CLI interface."""
    @click.command()
    @click.option('--team-id', required=True, help='Team ID for the knowledgebase')
    @click.option('--blog-url', help='Blog URL to scrape')
    @click.option('--pdf-path', help='PDF file path to scrape')
    @click.option('--urls', help='Comma-separated list of URLs to scrape')
    @click.option('--output', default='knowledgebase.json', help='Output file path')
    @click.option('--use-selenium', is_flag=True, help='Use Selenium for JavaScript-heavy sites')
    @click.option('--max-posts', default=50, help='Maximum number of blog posts to scrape')
    def scrape(team_id, blog_url, pdf_path, urls, output, use_selenium, max_posts):
        """THT Scraper - Extract content for knowledgebase import."""
        
        scraper = THTScraper(team_id, use_selenium=use_selenium)
        all_items = []
        
        if blog_url:
            logger.info(f"Scraping blog: {blog_url}")
            items = scraper.scrape_blog(blog_url, max_posts)
            all_items.extend(items)
        
        if pdf_path:
            logger.info(f"Scraping PDF: {pdf_path}")
            items = scraper.scrape_pdf(pdf_path)
            all_items.extend(items)
        
        if urls:
            url_list = [url.strip() for url in urls.split(',')]
            logger.info(f"Scraping URLs: {url_list}")
            items = scraper.scrape_urls(url_list)
            all_items.extend(items)
        
        if all_items:
            scraper.export_to_knowledgebase_format(all_items, output)
            logger.info(f"Successfully scraped {len(all_items)} items")
        else:
            logger.warning("No items were scraped")
    
    scrape()

if __name__ == "__main__":
    main() 