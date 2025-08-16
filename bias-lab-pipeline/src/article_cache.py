"""
File-based article cache to avoid hitting API rate limits.
Stores fetched articles in a JSON file with timestamps.
Cache expires after 24 hours.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

import tempfile

# Use temp directory for Render deployment (ephemeral but works)
CACHE_DIR = Path(tempfile.gettempdir()) / "bias_lab_cache"
CACHE_FILE = CACHE_DIR / "articles_cache.json"
CACHE_DURATION_HOURS = 24

def ensure_cache_dir():
    """Create cache directory if it doesn't exist."""
    CACHE_DIR.mkdir(exist_ok=True)

def is_cache_valid(cache_data: Dict) -> bool:
    """Check if cache is still valid (less than 24 hours old)."""
    if not cache_data or 'timestamp' not in cache_data:
        return False
    
    cache_time = datetime.fromisoformat(cache_data['timestamp'])
    now = datetime.now()
    age = now - cache_time
    
    return age < timedelta(hours=CACHE_DURATION_HOURS)

def load_cached_articles() -> Optional[List[Dict]]:
    """Load articles from cache if valid."""
    ensure_cache_dir()
    
    if not CACHE_FILE.exists():
        print("📂 No cache file found")
        return None
    
    try:
        with open(CACHE_FILE, 'r') as f:
            cache_data = json.load(f)
        
        if is_cache_valid(cache_data):
            age_hours = (datetime.now() - datetime.fromisoformat(cache_data['timestamp'])).total_seconds() / 3600
            print(f"✅ Using cached articles ({age_hours:.1f} hours old)")
            articles = cache_data['articles']
            
            # CRITICAL: Validate that articles have required fields
            valid_articles = []
            for article in articles:
                if isinstance(article, dict) and 'full_text' in article and len(article.get('full_text', '')) > 100:
                    valid_articles.append(article)
                else:
                    print(f"⚠️ Skipping invalid cached article: {article.get('title', 'Unknown')[:50]}")
            
            if not valid_articles:
                print("❌ No valid articles in cache (missing full_text)")
                clear_cache()
                return None
                
            return valid_articles
        else:
            print("⏰ Cache expired (> 24 hours old)")
            return None
            
    except Exception as e:
        print(f"❌ Error loading cache: {e}")
        return None

def save_articles_to_cache(articles: List[Dict], metadata: Dict = None):
    """Save articles to cache with timestamp."""
    ensure_cache_dir()
    
    cache_data = {
        'timestamp': datetime.now().isoformat(),
        'article_count': len(articles),
        'articles': articles,
        'metadata': metadata or {}
    }
    
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache_data, f, indent=2, default=str)
        print(f"💾 Saved {len(articles)} articles to cache")
        print(f"   Cache location: {CACHE_FILE}")
    except Exception as e:
        print(f"❌ Error saving cache: {e}")

def clear_cache():
    """Clear the cache file."""
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()
        print("🗑️ Cache cleared")

def get_cache_info() -> Dict:
    """Get information about current cache."""
    if not CACHE_FILE.exists():
        return {'exists': False}
    
    try:
        with open(CACHE_FILE, 'r') as f:
            cache_data = json.load(f)
        
        cache_time = datetime.fromisoformat(cache_data['timestamp'])
        age = datetime.now() - cache_time
        
        return {
            'exists': True,
            'timestamp': cache_data['timestamp'],
            'age_hours': age.total_seconds() / 3600,
            'valid': is_cache_valid(cache_data),
            'article_count': cache_data.get('article_count', 0),
            'expires_in_hours': max(0, CACHE_DURATION_HOURS - (age.total_seconds() / 3600))
        }
    except Exception as e:
        return {'exists': True, 'error': str(e)}
