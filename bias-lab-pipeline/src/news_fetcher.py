"""News article fetcher for The Bias Lab pipeline - Multiple Current Topics"""
import asyncio
import aiohttp
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
from newsapi import NewsApiClient
from newspaper import Article as NewspaperArticle
import feedparser
from .config import Config
from .article_cache import load_cached_articles, save_articles_to_cache, get_cache_info

# Current controversial topics for 2025
CURRENT_TOPICS = [
    "Figma IPO 2025",
    "Sam Altman Elon Musk AI dispute",
    "Trump tariffs trade war",
    "TikTok ban Supreme Court",
    "OpenAI AGI safety",
    "Google antitrust ruling",
    "Climate change regulations EPA",
    "Immigration border crisis 2025",
    "Ukraine Russia conflict 2025",
    "Inflation Federal Reserve rates",
    "Abortion and Reproductive Rights",
    "Diversity Equity and Inclusion",
    "Gun Violence"
]

class NewsFetcher:
    """Fetches articles from multiple news sources about current events."""
    
    def __init__(self):
        self.last_errors = []
        self.last_warnings = []
        
        if not Config.NEWSAPI_KEY:
            raise ValueError("NEWSAPI_KEY is required! Get your free key at https://newsapi.org/register")
        
        self.newsapi = NewsApiClient(api_key=Config.NEWSAPI_KEY)
        
        # Diverse sources across political spectrum
        self.sources = {
            'left': ['cnn', 'msnbc', 'the-washington-post', 'politico', 'the-guardian-us', 'vice-news'],
            'center': ['bbc-news', 'reuters', 'associated-press', 'bloomberg', 'the-economist', 'npr'],
            'right': ['fox-news', 'the-wall-street-journal', 'breitbart-news', 'the-american-conservative']
        }
        
        # RSS feeds for additional sources - DISABLED FOR NOW
        self.rss_feeds = [
            # "http://rss.cnn.com/rss/edition.rss",
            # "https://feeds.npr.org/1001/rss.xml",
            # "https://rss.reuters.com/news/politics",  # DNS issues
            # "https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml",
            # "https://feeds.washingtonpost.com/rss/politics",
            # "https://feeds.bbci.co.uk/news/politics/rss.xml"
        ]
        
    async def fetch_current_event_articles(self, topics: List[str] = None, max_per_topic: int = 5) -> List[Dict]:
        """Fetch articles about multiple current controversial events."""
        
        # Check cache first
        print("\n📂 Checking article cache...")
        cache_info = get_cache_info()
        
        if cache_info.get('exists'):
            print(f"   Cache age: {cache_info.get('age_hours', 0):.1f} hours")
            print(f"   Articles: {cache_info.get('article_count', 0)}")
            print(f"   Expires in: {cache_info.get('expires_in_hours', 0):.1f} hours")
        
        cached_articles = load_cached_articles()
        if cached_articles:
            return cached_articles[:Config.MAX_ARTICLES]
        
        # If no valid cache, fetch new articles
        print("🔄 Fetching fresh articles...")
        
        # Handle single string passed as topic (backward compatibility)
        if isinstance(topics, str):
            topics = [topics]
        
        # Use default current topics if none provided
        if not topics:
            topics = CURRENT_TOPICS[:3]  # Top 3 most controversial
            
        all_articles = []
        api_errors = []
        
        for topic in topics:
            print(f"\n📰 Fetching articles about: {topic}")
            
            # Fetch from NewsAPI
            topic_articles = await self._fetch_from_newsapi(topic, max_per_topic)
            
            # If NewsAPI doesn't return enough, try RSS feeds
            if len(topic_articles) < max_per_topic:
                rss_articles = await self._fetch_from_rss(topic, max_per_topic - len(topic_articles))
                topic_articles.extend(rss_articles)
            
            all_articles.extend(topic_articles)
            print(f"  ✓ Found {len(topic_articles)} articles for {topic}")
            
        # Deduplicate by URL and standardize all articles
        seen_urls = set()
        unique_articles = []
        
        print("\n🔧 Standardizing and enhancing articles...")
        for article in all_articles:
            if article['url'] not in seen_urls:
                seen_urls.add(article['url'])
                # Standardize EVERY article regardless of source
                standardized = await self._standardize_article(article)
                # Only keep if we have substantial content
                if len(standardized['full_text']) > 100:
                    unique_articles.append(standardized)
                    print(f"  ✓ {standardized['source']}: {len(standardized['full_text'])} chars")
                
        print(f"\n📊 Total quality articles: {len(unique_articles)}")
        
        # Save to cache if we got articles
        if unique_articles:
            save_articles_to_cache(unique_articles, {
                'topics': topics,
                'fetch_time': datetime.now().isoformat()
            })
        
        return unique_articles[:Config.MAX_ARTICLES]
    
    async def _fetch_from_newsapi(self, topic: str, limit: int) -> List[Dict]:
        """Fetch articles from NewsAPI for a specific topic."""
        try:
            # Get all sources as comma-separated string
            all_sources = ','.join([s for sources in self.sources.values() for s in sources])
            
            # Get articles from the last 7 days
            from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            
            news_results = self.newsapi.get_everything(
                q=topic,
                sources=all_sources,
                from_param=from_date,
                language='en',
                sort_by='relevancy',
                page_size=limit * 2  # Get extra to account for filtering
            )
            
            # Store errors for UI if any
            self.last_errors = []
            
            articles = []
            
            for article_data in news_results.get('articles', [])[:limit]:
                # Handle source field - can be either a dict or string
                source_data = article_data.get('source', '')
                if isinstance(source_data, dict):
                    source_name = source_data.get('name', 'Unknown')
                else:
                    source_name = str(source_data) if source_data else 'Unknown'
                
                article = {
                    'title': article_data.get('title', ''),
                    'url': article_data.get('url', ''),
                    'source': source_name,
                    'author': article_data.get('author', 'Unknown'),
                    'published_at': article_data.get('publishedAt', ''),
                    'description': article_data.get('description', ''),
                    'content': article_data.get('content', ''),
                    'full_text': ''  # Will be filled by standardizer
                }
                articles.append(article)
                    
            return articles
            
        except Exception as e:
            error_msg = str(e)
            if 'rateLimited' in error_msg:
                msg = f"NewsAPI rate limit: {topic}"
                self.last_warnings.append(msg)
            else:
                msg = f"NewsAPI error: {error_msg[:100]}"
                self.last_errors.append(msg)
            print(f"  ⚠️ NewsAPI error for '{topic}': {e}")
            return []
    
    async def _fetch_from_rss(self, topic: str, limit: int) -> List[Dict]:
        """Fetch articles from RSS feeds for a specific topic."""
        articles = []
        topic_lower = topic.lower()
        
        for feed_url in self.rss_feeds[:3]:  # Limit RSS feeds checked
            try:
                # Create connector that bypasses SSL verification for RSS feeds
                connector = aiohttp.TCPConnector(ssl=False)
                async with aiohttp.ClientSession(connector=connector) as session:
                    async with session.get(feed_url, timeout=5) as response:
                        content = await response.text()
                        feed = feedparser.parse(content)
                        
                        for entry in feed.entries[:10]:
                            # Check if entry is relevant to topic
                            relevant_text = f"{entry.get('title', '')} {entry.get('summary', '')}"
                            if not any(word in relevant_text.lower() for word in topic_lower.split()):
                                continue
                                
                            article = {
                                'title': entry.get('title', ''),
                                'url': entry.get('link', ''),
                                'source': feed.feed.get('title', 'Unknown'),
                                'author': entry.get('author', 'Unknown'),
                                'published_at': entry.get('published', datetime.now().isoformat()),
                                'description': entry.get('summary', ''),
                                'content': entry.get('description', ''),
                                'full_text': ''  # Will be filled by standardizer
                            }
                            
                            articles.append(article)
                            if len(articles) >= limit:
                                break
                                
            except Exception as e:
                print(f"    RSS feed error: {e}")
                continue
                
        return articles[:limit]
    
    async def _standardize_article(self, article: Dict) -> Dict:
        """Standardize article format and try to get full text."""
        description = article.get('description', '')
        content = article.get('content', '')
        
        # Remove the "[+XXXX chars]" suffix from NewsAPI content
        if content and '[+' in content:
            content = content.split('[+')[0].strip()
        
        # Start with what NewsAPI gives us (description + partial content)
        text = f"{description}\n\n{content}".strip() if content else description
        
        # Try to get the full article by scraping the URL
        if article.get('url'):
            try:
                scraped_text = await self._fetch_full_content(article['url'])
                if scraped_text and len(scraped_text) > len(text):
                    text = scraped_text
                    print(f"  ✓ Got full text for: {article.get('title', '')[:50]}...")
            except Exception as e:
                print(f"  ⚠️ Could not scrape full text: {str(e)[:50]}")
        
        # Structure the article
        standardized = {
            'title': article.get('title', ''),
            'url': article.get('url', ''),
            'source': article.get('source', 'Unknown'),
            'author': article.get('author', 'Unknown'),
            'published_at': article.get('published_at', datetime.now().isoformat()),
            'description': description,  # Keep for UI display (brief summary)
            'full_text': text  # The actual text for analysis (scraped or fallback)
        }
        
        return standardized
    
    async def _fetch_full_content(self, url: str) -> Optional[str]:
        """Fetch full article content using newspaper3k."""
        try:
            article = NewspaperArticle(url)
            article.download()
            article.parse()
            
            # Limit to reasonable length
            full_text = article.text[:5000] if article.text else ""
            return full_text if len(full_text) > 200 else None
            
        except Exception:
            # Fallback to basic extraction
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=5) as response:
                        if response.status == 200:
                            html = await response.text()
                            # Very basic text extraction
                            import re
                            text = re.sub(r'<[^>]+>', '', html)
                            text = re.sub(r'\s+', ' ', text)
                            return text[:3000] if len(text) > 200 else None
            except:
                return None
        return None
    
    # REMOVED: Mock articles method - not used anywhere
    # def get_mock_articles_with_bias(self) -> List[Dict]:
    #     """Return mock articles with clear bias patterns for testing."""
    #     return [
    #         {
    #             'title': "Biden's Radical Climate Agenda Destroys American Jobs",
    #             'url': 'https://example.com/article1',
    #             'source': 'Conservative Tribune',
    #             'author': 'John Smith',
    #             'published_at': datetime.now().isoformat(),
    #             'description': 'Critics blast the administration...',
    #             'content': '',
    #             'full_text': "The Biden administration's radical climate agenda continues its assault on American energy independence with devastating new regulations that critics say will destroy thousands of jobs. Sources close to the industry warn of catastrophic economic impacts. The controversial policy, rushed through without proper consideration, represents government overreach at its worst."
    #         },
    #         {
    #             'title': "EPA Announces New Carbon Emission Standards",
    #             'url': 'https://example.com/article2',
    #             'source': 'Reuters',
    #             'author': 'Jane Doe',
    #             'published_at': datetime.now().isoformat(),
    #             'description': 'The Environmental Protection Agency released...',
    #             'content': '',
    #             'full_text': "The Environmental Protection Agency released new regulations targeting carbon emissions from power plants on Tuesday. The policy aims to reduce greenhouse gas emissions by 30% by 2030, according to EPA documents. Industry representatives expressed concerns about implementation costs, while environmental groups praised the initiative."
    #         },
    #         {
    #             'title': "Corporate Polluters Escape Justice Again as Weak Climate Rules Fail Communities",
    #             'url': 'https://example.com/article3',
    #             'source': 'Progressive Voice',
    #             'author': 'Sarah Johnson',
    #             'published_at': datetime.now().isoformat(),
    #             'description': 'Environmental justice advocates say...',
    #             'content': '',
    #             'full_text': "Once again, corporate polluters have escaped meaningful accountability as the EPA's toothless new regulations fail to protect vulnerable communities. Environmental justice advocates say these inadequate measures represent a betrayal of campaign promises. The fossil fuel industry celebrates another victory over public health."
    #         },
    #         {
    #             'title': "Supreme Court Reviews Second Amendment Case",
    #             'url': 'https://example.com/article4',
    #             'source': 'CNN',
    #             'author': 'Mike Williams',
    #             'published_at': datetime.now().isoformat(),
    #             'description': 'The court issued a 5-4 decision...',
    #             'content': '',
    #             'full_text': "The court issued a 5-4 decision on Thursday. Supporters argue it will improve safety, while opponents claim it undermines individual liberties. According to the Department of Justice report, incidents declined 3%."
    #         },
    #         {
    #             'title': "Tech Giants Face Antitrust Scrutiny",
    #             'url': 'https://example.com/article5',
    #             'source': 'Wall Street Journal',
    #             'author': 'David Chen',
    #             'published_at': datetime.now().isoformat(),
    #             'description': 'Federal regulators examining market dominance...',
    #             'content': '',
    #             'full_text': "Federal regulators are intensifying their examination of major technology companies' market dominance. Industry analysts predict significant changes to business models if proposed regulations are enacted. Company representatives maintain their practices benefit consumers through innovation and competitive pricing."
    #         }
    #     ]