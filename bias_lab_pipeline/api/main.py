"""The Bias Lab API - Main FastAPI application with CFA and ensemble scoring."""
import os
import sys

# Add the parent directory to Python path for local imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Silence the tokenizers parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import asyncio
import time
from datetime import datetime
import json
from concurrent.futures import ThreadPoolExecutor

# Relative imports from src package
try:
    from src.config import Config
    from src.news_fetcher import NewsFetcher
    from src.bias_scorer import BiasScorer
    from src.cfa_engine import CFA_Engine
    from src.narrative_graph import NarrativeGraph
    from src.ensemble_scorer import EnsembleScorer, HeuristicScorer
    from src.conformal_prediction import ConformalPredictor
except ImportError:
    # Fallback for different deployment environments
    from bias_lab_pipeline.src.config import Config
    from bias_lab_pipeline.src.news_fetcher import NewsFetcher
    from bias_lab_pipeline.src.bias_scorer import BiasScorer
    from bias_lab_pipeline.src.cfa_engine import CFA_Engine
    from bias_lab_pipeline.src.narrative_graph import NarrativeGraph
    from bias_lab_pipeline.src.ensemble_scorer import EnsembleScorer, HeuristicScorer
    from bias_lab_pipeline.src.conformal_prediction import ConformalPredictor
try:
    from src.transparency_scorer import get_transparency_scorer
    from src.article_cache import get_cache_info, clear_cache
except ImportError:
    from bias_lab_pipeline.src.transparency_scorer import get_transparency_scorer
    from bias_lab_pipeline.src.article_cache import get_cache_info, clear_cache

# Initialize FastAPI app
app = FastAPI(
    title="The Bias Lab API",
    description="AI-powered media bias detection with Contrastive Framing Attribution",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://*.vercel.app",
        "https://bias-lab.vercel.app",  # Your production domain
        "*"  # Allow all for demo (remove in production)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
class AppState:
    def __init__(self):
        self.articles = []
        self.scores = []
        self.narratives = []
        self.cfa_results = {}
        self.health_metrics = {
            'requests_total': 0,
            'avg_latency_ms': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'llm_failures': 0,
            'fallback_uses': 0
        }
        self.initialized = False
        self.last_update = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.errors = []  # Track errors for UI
        self.warnings = []  # Track warnings like rate limits
        self.using_cache = False

state = AppState()

# Response models
class HealthResponse(BaseModel):
    status: str
    uptime_seconds: float
    metrics: Dict
    last_update: Optional[str]
    config_valid: bool
    prompt_rev: str = "v1.0"

class ArticleResponse(BaseModel):
    article_id: str  # Changed from int to str to avoid JS precision issues
    title: str
    source: str
    url: str
    published_at: str
    scores: Dict[str, float]
    confidence_interval: Dict
    highlighted_phrases: Dict[str, List[str]]
    processing_time_ms: float
    stale: bool = False
    transparency_analysis: Optional[Dict] = None

class NarrativeResponse(BaseModel):
    cluster_id: int
    descriptor: str
    article_ids: List[str]  # Changed from List[int] to List[str] for JS compatibility
    sources: List[str]
    polarity: Dict
    mean_framing_score: float

# Initialize components
async def initialize_components():
    """Initialize all ML components and fetch initial data."""
    global state
    init_start_time = time.time()
    
    print("Initializing The Bias Lab components...")
    
    # Validate config
    valid, errors = Config.validate()
    if not valid:
        print(f"Configuration errors: {errors}")
        print("Using mock data mode...")
    
    # Initialize LLM client
    llm_client = None
    if Config.LLM_PROVIDER == "openai" and Config.OPENAI_API_KEY:
        from openai import OpenAI
        llm_client = OpenAI(api_key=Config.OPENAI_API_KEY)
    
    # Initialize components
    fetcher = NewsFetcher()
    base_scorer = BiasScorer() if llm_client else None
    cfa_engine = CFA_Engine(llm_client) if llm_client else None
    ensemble = EnsembleScorer(base_scorer) if base_scorer else EnsembleScorer(None)
    narrative_graph = NarrativeGraph()
    conformal = ConformalPredictor()
    transparency_scorer = get_transparency_scorer()
    
    # Fetch articles (using current controversial topics)
    print("Fetching articles about current controversial topics...")
    # Pass as a list of topics
    articles = await fetcher.fetch_current_event_articles(["Israel Hamas Gaza conflict 2024", "Trump tariffs 2025", "OpenAI AGI safety"])
    
    # Store any errors/warnings from news fetcher
    state.errors.extend(fetcher.last_errors)
    state.warnings.extend(fetcher.last_warnings)
    
    if not articles:
        print("No articles fetched due to API rate limits or network issues")
        # Mock data fallback removed - method doesn't exist
        # articles = fetcher._get_mock_articles()
        state.errors.append("No articles available - NewsAPI rate limit reached or network error")
    
    state.articles = articles
    print(f"Fetched {len(articles)} articles")
    
    # Score articles with ensemble (parallel processing)
    print("Scoring articles with ensemble...")
    start_time = time.time()
    
    if base_scorer:
        state.scores = await ensemble.score_multiple_with_ensemble(articles)
        # Add transparency analysis to each score
        for i, score in enumerate(state.scores):
            if i < len(articles):
                score['transparency_analysis'] = transparency_scorer.score_transparency(articles[i])
        
        # # Log scoring results (commented out after debugging)
        # num_llm_scored = sum(1 for s in state.scores if not s.get('stale', False))
        # num_heuristic = sum(1 for s in state.scores if s.get('stale', False))
        # print(f"  LLM-scored: {num_llm_scored}, Heuristic fallback: {num_heuristic}")
        # 
        # # Show a sample score
        # if state.scores:
        #     sample_score = state.scores[0]
        #     dimensions = list(sample_score.get('scores', {}).keys())[:3]
        #     scores = [sample_score['scores'].get(d, 0) for d in dimensions]
        #     print(f"  Sample dimensions: {dimensions}")
        #     print(f"  Sample scores: {scores}")
    else:
        # Use heuristics only if no LLM
        print("  ⚠️ No LLM client, using heuristic scoring only")
        heuristic_scorer = HeuristicScorer()
        state.scores = []
        for article in articles:
            text = article.get('full_text', '')
            heuristic_results = heuristic_scorer.score_all_dimensions(text)
            state.scores.append({
                'article_id': hash(article.get('url', '')),
                'title': article.get('title', ''),
                'source': article.get('source', ''),
                'url': article.get('url', ''),
                'scores': {dim: heuristic_results[dim]['score'] for dim in heuristic_results},
                'highlighted_phrases': {dim: heuristic_results[dim].get('evidence', []) 
                                       for dim in heuristic_results},
                'confidence_interval': {'lower': 0.4, 'upper': 0.6, 'confidence': 0.5},
                'stale': True,
                'processing_time_ms': 0,
                'transparency_analysis': transparency_scorer.score_transparency(article)
            })
    
    scoring_time = (time.time() - start_time) * 1000
    print(f"✓ Scoring completed in {scoring_time:.0f}ms ({len(state.scores)} articles)")
    
    # Add conformal prediction bands
    print("Adding conformal prediction bands...")
    conformal_start = time.time()
    scores_before = len(state.scores)
    state.scores = conformal.batch_add_conformal_bands(articles, state.scores)
    conformal_time = (time.time() - conformal_start) * 1000
    
    # # Check if bands were actually added (commented out after debugging)
    # bands_added = sum(1 for s in state.scores if 'confidence_bands' in s and s['confidence_bands'])
    print(f"✓ Conformal bands added in {conformal_time:.0f}ms")
    # print(f"  Bands added to {bands_added}/{scores_before} articles")
    
    # Generate narrative clusters
    print("Building narrative graph and clusters...")
    narrative_start = time.time()
    state.narratives = narrative_graph.get_narrative_clusters(articles, state.scores)
    narrative_time = (time.time() - narrative_start) * 1000
    print(f"✓ Found {len(state.narratives)} narrative clusters in {narrative_time:.0f}ms")
    
    # # Log details about narratives (commented out after debugging)
    # for i, narrative in enumerate(state.narratives):
    #     article_count = len(narrative.get('articles', []))
    #     sources = narrative.get('sources', [])[:3]  # First 3 sources
    #     descriptor = narrative.get('descriptor', 'Unknown')[:50]  # First 50 chars
    #     print(f"  Cluster {i}: {article_count} articles, sources: {sources}")
    #     print(f"    Descriptor: {descriptor}...")
    
    # Run CFA on a sample article (expensive, so just one for demo)
    if not cfa_engine:
        print("⚠️ CFA engine not available (no OpenAI key)")
    elif len(articles) == 0:
        print("⚠️ No articles available for CFA analysis")
    elif cfa_engine and len(articles) > 0:
        sample_article = articles[0]
        # article_title = sample_article.get('title', 'Unknown')[:60]
        # article_text_len = len(sample_article.get('full_text', ''))
        
        print(f"Computing CFA for sample article...")
        # print(f"  Article text length: {article_text_len} chars")
        cfa_start_time = time.time()
        
        try:
            article_text = sample_article.get('full_text', '')
            if not article_text:
                print("  ⚠️ Article has no full_text, skipping CFA")
                sample_cfa = None
            else:
                sample_cfa = await cfa_engine.compute_cfa_contributions(article_text)
                state.cfa_results[state.scores[0]['article_id']] = sample_cfa
            
            cfa_time = (time.time() - cfa_start_time) * 1000
            
            # # Log CFA results details (commented out after debugging)
            if sample_cfa:
                # contributions = sample_cfa.get('contributions', [])
                # num_contributions = len(contributions)
                # base_scores = sample_cfa.get('base_scores', {})
                # neutral_scores = sample_cfa.get('neutral_scores', {})
                
                # # Calculate overall framing difference
                # deltas = []
                # for dim in base_scores.keys():
                #     if dim in neutral_scores:
                #         base_val = base_scores[dim].get('score', 50) if isinstance(base_scores[dim], dict) else base_scores[dim]
                #         neutral_val = neutral_scores[dim].get('score', 50) if isinstance(neutral_scores[dim], dict) else neutral_scores[dim]
                #         deltas.append(abs(base_val - neutral_val))
                # total_delta = sum(deltas) / max(len(deltas), 1) if deltas else 0
                
                print(f"✓ CFA computation complete in {cfa_time:.0f}ms")
                # print(f"  Found {num_contributions} contributing phrases")
                # print(f"  Avg framing delta from neutral: {total_delta:.1f} points")
                
                # # Show score comparison
                # if base_scores and neutral_scores:
                #     print(f"  Base vs Neutral scores:")
                #     for dim in ['ideological_stance', 'emotional_tone', 'framing_choices']:
                #         if dim in base_scores and dim in neutral_scores:
                #             # Extract the numeric score from the dict
                #             base_val = base_scores[dim].get('score', 0) if isinstance(base_scores[dim], dict) else base_scores[dim]
                #             neutral_val = neutral_scores[dim].get('score', 0) if isinstance(neutral_scores[dim], dict) else neutral_scores[dim]
                #             delta = base_val - neutral_val
                #             print(f"    {dim}: {base_val} → {neutral_val} (Δ{delta:+.0f})")
                
                # if num_contributions > 0:
                #     top_contrib = contributions[0]
                #     # CFA uses 'span' not 'phrase' for the text
                #     phrase_text = top_contrib.get('span', top_contrib.get('phrase', ''))
                #     print(f"  Top phrase: '{phrase_text[:50]}...'")
                #     print(f"    Delta: {top_contrib.get('delta', 0):.1f} on {top_contrib.get('dimension', 'unknown')}")
                # elif total_delta < 5:
                #     print(f"  ℹ️ No significant framing detected (delta < 5 points)")
            else:
                print(f"✓ CFA computation complete in {cfa_time:.0f}ms")
        except Exception as e:
            print(f"⚠️ CFA computation failed: {str(e)[:100]}")
            state.errors.append(f"CFA failed: {str(e)[:100]}")
    
    state.initialized = True
    state.last_update = datetime.now().isoformat()
    
    # Update metrics
    state.health_metrics['avg_latency_ms'] = scoring_time / len(articles) if articles else 0
    
    # Calculate total initialization time
    total_init_time = time.time() - init_start_time
    
    # # Validation check (commented out after debugging)
    # validation_issues = []
    # if len(state.scores) != len(articles):
    #     validation_issues.append(f"Score count mismatch: {len(state.scores)} scores for {len(articles)} articles")
    # 
    # for score in state.scores:
    #     if 'scores' not in score or not score['scores']:
    #         validation_issues.append(f"Score missing dimensions for article: {score.get('title', 'Unknown')[:30]}")
    # 
    # if len(state.narratives) == 0 and len(articles) > 0:
    #     validation_issues.append("No narrative clusters found despite having articles")
    
    print("\n" + "="*60)
    print("✓ INITIALIZATION COMPLETE!")
    print("="*60)
    print(f"  Articles: {len(articles)}")
    print(f"  Scores: {len(state.scores)}")
    print(f"  Narrative clusters: {len(state.narratives)}")
    print(f"  CFA analyses: {len(state.cfa_results)}")
    print(f"  Total time: {total_init_time:.1f}s")
    # 
    # if validation_issues:
    #     print("\n  ⚠️ Validation Issues:")
    #     for issue in validation_issues:
    #         print(f"    - {issue}")
    # else:
    #     print("\n  ✓ All components validated successfully")
    # 
    print("="*60 + "\n")

@app.on_event("startup")
async def startup_event():
    """Initialize components on startup."""
    await initialize_components()

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint with performance metrics."""
    state.health_metrics['requests_total'] += 1
    
    uptime = time.time() - app.state.start_time if hasattr(app, 'state') and hasattr(app.state, 'start_time') else 0
    
    valid, _ = Config.validate()
    
    return HealthResponse(
        status="healthy" if state.initialized else "initializing",
        uptime_seconds=uptime,
        metrics=state.health_metrics,
        last_update=state.last_update,
        config_valid=valid
    )

@app.get("/articles", response_model=List[ArticleResponse])
async def get_articles():
    """Get all articles with bias scores."""
    state.health_metrics['requests_total'] += 1
    
    if not state.initialized:
        raise HTTPException(status_code=503, detail="System initializing, please wait...")
    
    return [
        ArticleResponse(
            article_id=str(score['article_id']),  # Convert to string for JS compatibility
            title=score['title'],
            source=score['source'],
            url=score['url'],
            published_at=article.get('published_at', ''),
            scores=score['scores'],
            confidence_interval=score.get('confidence_interval', {}),
            highlighted_phrases=score.get('highlighted_phrases', {}),
            processing_time_ms=score.get('processing_time_ms', 0),
            stale=score.get('stale', False),
            transparency_analysis=score.get('transparency_analysis', None)
        )
        for article, score in zip(state.articles, state.scores)
    ]

@app.get("/articles/{article_id}")
async def get_article_detail(article_id: str):
    """Get detailed breakdown for a specific article including CFA if available."""
    state.health_metrics['requests_total'] += 1
    
    if not state.initialized:
        raise HTTPException(status_code=503, detail="System initializing, please wait...")
    
    # Convert article_id to int (it's a hash value sent as string)
    try:
        article_id_int = int(article_id)
    except ValueError:
        print(f"❌ Invalid article ID format: {article_id}")
        raise HTTPException(status_code=400, detail="Invalid article ID format")
    
    # Debug: Show available article IDs
    available_ids = [score['article_id'] for score in state.scores]
    print(f"🔍 Looking for article ID: {article_id_int}")
    print(f"📋 Available IDs: {available_ids}")
    
    # Find article
    article_idx = None
    for i, score in enumerate(state.scores):
        if score['article_id'] == article_id_int:
            article_idx = i
            break
    
    if article_idx is None:
        print(f"❌ Article not found. Requested: {article_id_int}, Available: {available_ids}")
        raise HTTPException(status_code=404, detail=f"Article not found. Available IDs: {available_ids}")
    
    article = state.articles[article_idx]
    score = state.scores[article_idx]
    
    # Build detailed response
    detail = {
        'article_id': str(article_id_int),  # Convert to string for JS compatibility
        'title': article['title'],
        'source': article['source'],
        'url': article['url'],
        'author': article.get('author', 'Unknown'),
        'published_at': article.get('published_at', ''),
        'description': article.get('description', ''),
        'content_preview': article.get('full_text', '')[:500],
        'scores': score['scores'],
        'confidence_interval': score.get('confidence_interval', {}),
        'confidence_bands': score.get('confidence_bands', {}),
        'highlighted_phrases': score.get('highlighted_phrases', {}),
        'reasoning': score.get('reasoning', {}),
        'ensemble_method': score.get('ensemble_method', 'unknown'),
        'stale': score.get('stale', False),
        'processing_time_ms': score.get('processing_time_ms', 0)
    }
    
    # Add CFA results if available, or compute on-demand
    if article_id_int in state.cfa_results:
        detail['cfa_analysis'] = state.cfa_results[article_id_int]
    else:
        # Compute CFA on-demand for this article
        if Config.OPENAI_API_KEY:
            try:
                # Import already available at top via direct import mechanism
                from openai import OpenAI
                
                llm_client = OpenAI(api_key=Config.OPENAI_API_KEY)
                cfa_engine = CFA_Engine(llm_client)
                
                article_text = article.get('full_text', '')[:5000]
                if article_text and len(article_text) > 100:
                    # print(f"Computing CFA for article {article_id_int}...")  # Commented out after debugging
                    cfa_result = await cfa_engine.compute_cfa_contributions(article_text, top_k=5)
                    state.cfa_results[article_id_int] = cfa_result
                    detail['cfa_analysis'] = cfa_result
                    # print(f"CFA computed for article {article_id_int}")  # Commented out after debugging
            except Exception as e:
                # print(f"Failed to compute CFA: {e}")  # Commented out after debugging
                detail['cfa_error'] = str(e)[:200]
    
    # Add transparency analysis if available
    if score and 'transparency_analysis' in score:
        detail['transparency_analysis'] = score['transparency_analysis']
    else:
        # Calculate transparency if not available
        transparency_scorer = get_transparency_scorer()
        detail['transparency_analysis'] = transparency_scorer.score_transparency(article)
    
    # Extract primary sources (from transparency analysis)
    if 'transparency_analysis' in detail:
        detail['primary_source_links'] = detail['transparency_analysis'].get('evidence', {}).get('primary_links', [])
    else:
        # Fallback extraction
        import re
        urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', article.get('full_text', ''))
        official_sources = [url for url in urls if any(
            domain in url for domain in ['.gov', '.org', 'court', 'official']
        )]
        detail['primary_source_links'] = official_sources[:5]
    
    return detail

@app.get("/narratives", response_model=List[NarrativeResponse])
async def get_narratives():
    """Get narrative clusters showing how different outlets frame the story."""
    state.health_metrics['requests_total'] += 1
    
    if not state.initialized:
        raise HTTPException(status_code=503, detail="System initializing, please wait...")
    
    return [
        NarrativeResponse(
            cluster_id=narrative['cluster_id'],
            descriptor=narrative['descriptor'],
            article_ids=[str(state.scores[i]['article_id']) for i in narrative['article_ids']],  # Convert to strings
            sources=narrative['sources'],
            polarity=narrative['polarity'],
            mean_framing_score=narrative['mean_framing_score']
        )
        for narrative in state.narratives
    ]

@app.post("/search")
async def search_news(
    query: str = Query(..., description="Search query for news topics"),
    max_articles: int = Query(10, description="Maximum articles to fetch"),
    background_tasks: BackgroundTasks = None
):
    """Search for specific news topics and analyze them."""
    state.health_metrics['requests_total'] += 1
    
    print(f"User searching for: {query} (max {max_articles} articles)")
    
    # Clear cache to get fresh results
    clear_cache()
    
    # Fetch articles for the specific query
    fetcher = NewsFetcher()
    articles = await fetcher.fetch_current_event_articles([query], max_per_topic=max_articles)
    
    if not articles:
        raise HTTPException(status_code=404, detail=f"No articles found for '{query}'")
    
    # Update state with new articles
    state.articles = articles
    print(f"Found {len(articles)} articles for '{query}'")
    
    # Score the new articles
    base_scorer = BiasScorer() if Config.OPENAI_API_KEY else None
    if base_scorer:
        ensemble = EnsembleScorer(base_scorer)
        state.scores = await ensemble.score_multiple_with_ensemble(articles)
    else:
        # Fallback to heuristics
        heuristic_scorer = HeuristicScorer()
        state.scores = []
        for article in articles:
            text = article.get('full_text', '')
            heuristic_results = heuristic_scorer.score_all_dimensions(text)
            state.scores.append({
                'article_id': hash(article.get('url', '')),
                'title': article.get('title', ''),
                'source': article.get('source', ''),
                'url': article.get('url', ''),
                'scores': {dim: heuristic_results[dim]['score'] for dim in heuristic_results},
                'highlighted_phrases': {dim: heuristic_results[dim].get('evidence', []) 
                                       for dim in heuristic_results},
                'confidence_interval': {'lower': 0.4, 'upper': 0.6, 'confidence': 0.5},
                'stale': True,
                'processing_time_ms': 0
            })
    
    # Update narratives
    narrative_graph = NarrativeGraph()
    state.narratives = narrative_graph.get_narrative_clusters(articles, state.scores)
    
    state.last_update = datetime.now().isoformat()
    
    return {
        "message": f"Found and analyzed {len(articles)} articles",
        "query": query,
        "article_count": len(articles),
        "status": "completed"
    }

@app.post("/refresh")
async def refresh_articles(background_tasks: BackgroundTasks):
    """Refresh articles and re-score (runs in background)."""
    state.health_metrics['requests_total'] += 1
    
    background_tasks.add_task(initialize_components)
    
    return {"message": "Refresh started in background", "status": "processing"}

@app.get("/cache/info")
async def cache_info():
    """Get information about the article cache."""
    info = get_cache_info()
    return {
        "cache": info,
        "using_cache": state.using_cache,
        "message": "Cache is valid and will be used" if info.get('valid') else "Cache expired or missing"
    }

@app.delete("/cache/clear")
async def clear_article_cache():
    """Clear the article cache to force fetching fresh articles."""
    clear_cache()
    state.using_cache = False
    return {"message": "Cache cleared successfully", "status": "success"}

@app.get("/errors")
async def get_errors():
    """Get current errors and warnings from the system."""
    return {
        "errors": state.errors[-10:],  # Last 10 errors
        "warnings": state.warnings[-10:],  # Last 10 warnings
        "has_errors": len(state.errors) > 0,
        "has_warnings": len(state.warnings) > 0
    }

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "The Bias Lab API",
        "version": "1.0.0",
        "description": "AI-powered media bias detection with Contrastive Framing Attribution",
        "endpoints": {
            "/health": "System health and metrics",
            "/articles": "List all articles with bias scores",
            "/articles/{id}": "Detailed article analysis with CFA",
            "/narratives": "Narrative clusters and framing patterns",
            "/cache/info": "Get cache status",
            "/cache/clear": "Clear article cache",
            "/errors": "Get system errors and warnings",
            "/docs": "Interactive API documentation"
        },
        "key_features": [
            "Contrastive Framing Attribution (CFA)",
            "Signed Narrative Graph clustering",
            "Conformal prediction confidence bands",
            "Ensemble scoring with fallback",
            "24-hour article caching"
        ],
        "prompt_rev": "v1.0"
    }

if __name__ == "__main__":
    import uvicorn
    
    # Set start time for uptime tracking
    app.state.start_time = time.time()
    
    uvicorn.run(app, host=Config.API_HOST, port=Config.API_PORT)
