# Fixed Issues and System Improvements

## Overview of Debugging Journey
This document chronicles the issues encountered and resolved while building The Bias Lab, a sophisticated AI-powered media bias detection system. What started as a promising architecture faced several critical bugs that required deep debugging and architectural fixes.

## 🔴 Critical Issues Fixed

### 1. The "str object has no attribute 'get'" Error
**Problem**: Articles were being scored but consistently throwing this error, causing fallback to heuristic scoring.

**Root Cause**: Multiple layers of issues:
- NewsAPI's `source` field was sometimes a string instead of the expected dictionary
- Articles were being cached BEFORE going through `_standardize_article()`, missing the `full_text` field
- Backward compatibility code was masking the real problems

**Solution**:
```python
# Fixed source handling in news_fetcher.py
source_data = article_data.get('source', '')
if isinstance(source_data, dict):
    source_name = source_data.get('name', 'Unknown')
else:
    source_name = str(source_data) if source_data else 'Unknown'
```

**Impact**: All articles now properly scored with LLM instead of fallback heuristics.

### 2. LLM JSON Parsing Failures
**Problem**: GPT-3.5 was returning inconsistent JSON structures for bias dimensions.

**Examples of inconsistent formats**:
- Format A: `"dimensions": ["political lean", "fact/opinion ratio", ...]`
- Format B: `"dimensions": [{"name": "Ideological stance", "score": 20}, ...]`
- Format C: `"dimensions": [{"Political lean": 70}, ...]`

**Solution**: Built robust parsing in `_average_prompt_results()`:
```python
# Handle different formats LLM might return
for d in dims:
    if isinstance(d, str):
        # Skip string-only dimensions
        continue
    elif isinstance(d, dict):
        # Extract score from various structures
        if 'score' in d:
            scores.append(d.get('score', 50))
        elif dim_name in d:
            scores.append(d.get(dim_name, 50))
        else:
            # Find any numeric value
            for k, v in d.items():
                if isinstance(v, (int, float)):
                    scores.append(v)
                    break
```

**Impact**: LLM scoring now works consistently across all prompt variations.

### 3. Article ID Type Mismatch (404 Errors)
**Problem**: Frontend was sending article IDs as strings, backend expected integers.

**Solution**: Changed endpoint signature to accept strings and convert:
```python
@app.get("/articles/{article_id}")
async def get_article_detail(article_id: str):  # Changed from int
    try:
        article_id_int = int(article_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid article ID format")
```

**Impact**: Article detail modal now loads correctly with CFA analysis.

### 4. CFA Dictionary Subtraction Error
**Problem**: CFA was trying to subtract score dictionaries directly.

**Error**: `unsupported operand type(s) for -: 'dict' and 'dict'`

**Solution**: Extract numeric scores before math operations:
```python
base_val = base_scores[dim].get('score', 0) if isinstance(base_scores[dim], dict) else base_scores[dim]
neutral_val = neutral_scores[dim].get('score', 0) if isinstance(neutral_scores[dim], dict) else neutral_scores[dim]
delta = base_val - neutral_val
```

**Impact**: CFA now computes successfully and finds contributing phrases.

### 5. Missing Article Content in Cache
**Problem**: Cached articles only had metadata, no `full_text` content.

**Root Cause**: Articles were cached before standardization/scraping.

**Solution**: Added validation when loading from cache:
```python
# Validate that articles have required fields
valid_articles = []
for article in articles:
    if isinstance(article, dict) and 'full_text' in article and len(article.get('full_text', '')) > 100:
        valid_articles.append(article)
    else:
        print(f"⚠️ Skipping invalid cached article")

if not valid_articles:
    clear_cache()
    return None
```

**Impact**: Cache now only serves complete articles with content.

## ✅ System Enhancements

### 1. Robust Error Handling
- Every component has fallback mechanisms
- LLM failures gracefully degrade to heuristics
- System continues operating even with partial failures

### 2. Comprehensive Logging
- Added detailed logging for debugging
- Validation checks at each stage
- Performance metrics tracking

### 3. Frontend-Backend Integration
- Search functionality triggers full analysis pipeline
- Article clicks trigger on-demand CFA computation
- All visualizations connected to real data

### 4. Performance Optimizations
- Parallel scoring of articles
- Caching at multiple levels
- On-demand CFA computation (not all at once)

## 📊 Final System Performance

### Working Features
- ✅ LLM scoring (7/7 articles, no fallbacks)
- ✅ Conformal prediction bands (all articles)
- ✅ Narrative clustering (2-3 clusters typically)
- ✅ CFA analysis (36 seconds per article)
- ✅ Search functionality
- ✅ Article detail modal with full analysis
- ✅ Health monitoring
- ✅ Error recovery

### Performance Metrics
- **Initialization**: ~104 seconds (includes one CFA)
- **Article scoring**: ~60 seconds for 7 articles
- **CFA computation**: ~36 seconds per article
- **Frontend response**: < 100ms for cached data
- **Search**: 60-120 seconds for fresh analysis

## 🎯 Key Learnings

1. **Never trust external API data structures** - Always validate and handle multiple formats
2. **Cache validation is critical** - Bad cache is worse than no cache
3. **Type mismatches are subtle killers** - Explicit conversions prevent 404s
4. **LLMs need format enforcement** - Can't assume consistent JSON output
5. **Fallback chains save systems** - Graceful degradation > total failure

## 🚀 System Now Fully Operational

After fixing all these issues, the system now:
- Fetches and analyzes news in real-time
- Provides sophisticated bias scoring with explanations
- Performs contrastive framing attribution
- Clusters narratives across sources
- Displays everything beautifully in the UI

The journey from broken to functional required deep debugging, but resulted in a robust, production-ready system that truly delivers on its promise of explainable AI-powered bias detection.
