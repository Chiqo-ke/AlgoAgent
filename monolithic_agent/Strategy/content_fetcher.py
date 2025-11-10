"""
Content Fetcher - Web scraping and content extraction for strategy discovery
Handles URLs from YouTube, articles, social media, and other sources.
"""

import requests
import re
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
import time

class ContentFetcher:
    """
    Fetches and extracts content from various web sources for strategy discovery.
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def fetch_content(self, url: str) -> Dict[str, Any]:
        """
        Main entry point to fetch content from any supported URL.
        
        Returns:
            Dict with: url, type, title, content, author, fetched_at, snippet
        """
        url_type = self._classify_url(url)
        
        try:
            if url_type == "youtube":
                return self._fetch_youtube_content(url)
            elif url_type == "tiktok":
                return self._fetch_tiktok_content(url)
            elif url_type == "social_post":
                return self._fetch_social_content(url)
            else:
                return self._fetch_web_article(url)
        except Exception as e:
            return {
                "url": url,
                "type": "other",
                "title": "Failed to fetch",
                "content": f"Error fetching content: {str(e)}",
                "author": "unknown",
                "fetched_at": datetime.now().isoformat(),
                "snippet": f"Failed to fetch: {str(e)[:100]}..."
            }
    
    def _classify_url(self, url: str) -> str:
        """Classify the URL type based on domain."""
        domain = urlparse(url).netloc.lower()
        
        if "youtube.com" in domain or "youtu.be" in domain:
            return "youtube"
        elif "tiktok.com" in domain:
            return "tiktok"
        elif any(social in domain for social in ["twitter.com", "x.com", "reddit.com", "facebook.com", "instagram.com"]):
            return "social_post"
        elif "pdf" in url.lower() or url.lower().endswith(".pdf"):
            return "pdf"
        else:
            return "web_article"
    
    def _fetch_youtube_content(self, url: str) -> Dict[str, Any]:
        """
        Fetch YouTube video information and transcript if available.
        Note: This is a simplified implementation - in production, you'd use youtube-dl 
        or YouTube API for better transcript extraction.
        """
        video_id = self._extract_youtube_video_id(url)
        if not video_id:
            raise ValueError("Invalid YouTube URL")
        
        # Fetch video page for metadata
        response = self.session.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title_tag = soup.find('meta', property='og:title')
        title = title_tag['content'] if title_tag else "Unknown YouTube Video"
        
        # Extract description
        desc_tag = soup.find('meta', property='og:description')
        description = desc_tag['content'] if desc_tag else ""
        
        # Try to extract channel name
        channel_pattern = r'"ownerChannelName":"([^"]+)"'
        channel_match = re.search(channel_pattern, response.text)
        author = channel_match.group(1) if channel_match else "Unknown Channel"
        
        # In a real implementation, you'd use youtube-transcript-api or similar
        # For now, we'll use the description as content
        content = f"Title: {title}\n\nDescription: {description}"
        
        # Try to extract any strategy-related keywords
        strategy_keywords = self._extract_strategy_keywords(content)
        if strategy_keywords:
            content += f"\n\nExtracted strategy keywords: {', '.join(strategy_keywords)}"
        
        snippet = description[:200] + "..." if len(description) > 200 else description
        
        return {
            "url": url,
            "type": "youtube",
            "title": title,
            "content": content,
            "author": author,
            "fetched_at": datetime.now().isoformat(),
            "snippet": snippet
        }
    
    def _fetch_web_article(self, url: str) -> Dict[str, Any]:
        """Fetch content from a web article."""
        response = self.session.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title = self._extract_title(soup)
        
        # Extract author
        author = self._extract_author(soup)
        
        # Extract main content
        content = self._extract_article_content(soup)
        
        # Create snippet
        snippet = content[:300] + "..." if len(content) > 300 else content
        
        return {
            "url": url,
            "type": "web_article",
            "title": title,
            "content": content,
            "author": author,
            "fetched_at": datetime.now().isoformat(),
            "snippet": snippet
        }
    
    def _fetch_tiktok_content(self, url: str) -> Dict[str, Any]:
        """
        Fetch TikTok content (simplified implementation).
        In production, you'd need specialized tools for TikTok scraping.
        """
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            # Extract basic info from page
            soup = BeautifulSoup(response.content, 'html.parser')
            title_tag = soup.find('title')
            title = title_tag.text if title_tag else "TikTok Video"
            
            return {
                "url": url,
                "type": "tiktok",
                "title": title,
                "content": f"TikTok video: {title}. Note: Full transcript extraction requires specialized tools.",
                "author": "TikTok User",
                "fetched_at": datetime.now().isoformat(),
                "snippet": "TikTok video content - transcript extraction limited"
            }
        except Exception as e:
            raise ValueError(f"Failed to fetch TikTok content: {str(e)}")
    
    def _fetch_social_content(self, url: str) -> Dict[str, Any]:
        """Fetch content from social media posts."""
        response = self.session.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        title = self._extract_title(soup)
        content = self._extract_social_post_content(soup)
        author = self._extract_author(soup)
        
        return {
            "url": url,
            "type": "social_post",
            "title": title,
            "content": content,
            "author": author,
            "fetched_at": datetime.now().isoformat(),
            "snippet": content[:200] + "..." if len(content) > 200 else content
        }
    
    def _extract_youtube_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL."""
        patterns = [
            r'youtube\.com/watch\?v=([^&]+)',
            r'youtu\.be/([^?]+)',
            r'youtube\.com/embed/([^?]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract title from HTML soup."""
        # Try various title extraction methods
        title_selectors = [
            'meta[property="og:title"]',
            'meta[name="twitter:title"]',
            'title',
            'h1'
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    return element.get('content', 'Unknown Title')
                else:
                    return element.get_text(strip=True)
        
        return "Unknown Title"
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """Extract author from HTML soup."""
        author_selectors = [
            'meta[name="author"]',
            'meta[property="article:author"]',
            '.author',
            '.byline',
            '[rel="author"]'
        ]
        
        for selector in author_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    return element.get('content', 'Unknown Author')
                else:
                    return element.get_text(strip=True)
        
        return "Unknown Author"
    
    def _extract_article_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from article."""
        # Remove unwanted elements
        for unwanted in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            unwanted.decompose()
        
        # Try common content selectors
        content_selectors = [
            'article',
            '.article-content',
            '.post-content',
            '.entry-content',
            'main',
            '.content'
        ]
        
        for selector in content_selectors:
            content_element = soup.select_one(selector)
            if content_element:
                return content_element.get_text(strip=True, separator='\n')
        
        # Fallback to body content
        body = soup.find('body')
        if body:
            return body.get_text(strip=True, separator='\n')
        
        return "Could not extract content"
    
    def _extract_social_post_content(self, soup: BeautifulSoup) -> str:
        """Extract content from social media posts."""
        # This is highly platform-specific and would need customization
        # for each social platform
        content_selectors = [
            '[data-testid="tweetText"]',  # Twitter
            '.post-content',
            '.status-content',
            'p'
        ]
        
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                return '\n'.join(elem.get_text(strip=True) for elem in elements[:3])
        
        return "Could not extract social post content"
    
    def _extract_strategy_keywords(self, text: str) -> List[str]:
        """Extract trading strategy related keywords from text."""
        strategy_keywords = [
            'scalping', 'day trading', 'swing trading', 'position trading',
            'EMA', 'SMA', 'RSI', 'MACD', 'bollinger bands', 'fibonacci',
            'support', 'resistance', 'breakout', 'trend following',
            'mean reversion', 'momentum', 'volume', 'price action',
            'stop loss', 'take profit', 'risk management', 'position sizing',
            'entry', 'exit', 'signal', 'indicator', 'backtest',
            'timeframe', 'chart pattern', 'candlestick'
        ]
        
        text_lower = text.lower()
        found_keywords = []
        
        for keyword in strategy_keywords:
            if keyword in text_lower:
                found_keywords.append(keyword)
        
        return found_keywords
    
    def batch_fetch(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Fetch content from multiple URLs."""
        results = []
        for url in urls:
            try:
                result = self.fetch_content(url)
                results.append(result)
                time.sleep(1)  # Be respectful to servers
            except Exception as e:
                results.append({
                    "url": url,
                    "type": "other",
                    "title": "Error",
                    "content": f"Failed to fetch: {str(e)}",
                    "author": "unknown",
                    "fetched_at": datetime.now().isoformat(),
                    "snippet": f"Error: {str(e)}"
                })
        return results


# Utility function for testing
def test_content_fetcher():
    """Test the content fetcher with sample URLs."""
    fetcher = ContentFetcher()
    
    # Test URLs (replace with real ones for testing)
    test_urls = [
        "https://example.com/trading-strategy-article",
        # Add more test URLs as needed
    ]
    
    for url in test_urls:
        try:
            result = fetcher.fetch_content(url)
            print(f"Successfully fetched: {result['title']}")
            print(f"Type: {result['type']}")
            print(f"Snippet: {result['snippet'][:100]}...")
            print("-" * 50)
        except Exception as e:
            print(f"Failed to fetch {url}: {str(e)}")


if __name__ == "__main__":
    test_content_fetcher()