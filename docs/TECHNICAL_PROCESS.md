# The Bias Lab - Technical Process Flow

## How The System Works

### 1. Data Acquisition

When you search for a topic (e.g., "climate change"):

```
User Search → NewsAPI (primary) → RSS Feeds (fallback) → Web Scraping (full text)
```

Articles are **standardized** to ensure they all have:
- `title`, `url`, `source`, `author`, `published_at`
- `full_text` (scraped from actual article page)
- `description` (brief summary)

### 2. Bias Scoring Engine

Each article gets scored on 5 dimensions (0-100 scale):

**Ensemble Approach**: Combines LLM + Heuristics
- **70% LLM Score** (GPT-3.5 with 3 prompt variants, averaged)
- **30% Heuristic Score** (lexicon-based bias indicators)
- If LLM fails → 100% heuristic (marked as `stale`)

**The 5 Dimensions**:
1. **Ideological Stance**: Left (0) to Right (100)
2. **Factual Grounding**: Opinion (0) to Factual (100)
3. **Framing Choices**: Neutral (0) to Biased framing (100)
4. **Emotional Tone**: Calm (0) to Inflammatory (100)
5. **Source Transparency**: Anonymous (0) to Well-sourced (100)

### 3. Advanced Analysis

#### Contrastive Framing Attribution (CFA)
*The unique innovation - shows exactly which phrases create bias*

1. Generate a **neutral rewrite** of the article
2. Score both original and neutral versions
3. For key sentences, measure their impact:
   ```
   Contribution = (Original - Neutral) - (Without_Sentence - Neutral)
   ```
4. Identify phrases that push scores away from neutral

**Example Output**:
```
"surge overwhelms border agents" → +18.7 points on Framing dimension
(Uses emotionally charged language implying loss of control)
```

#### Narrative Clustering
Groups articles by how they frame the story:
- Build similarity graph using embeddings
- Detect communities with Louvain algorithm
- Generate descriptors for each narrative cluster

#### Confidence Bands
Statistical confidence intervals using conformal prediction:
- Calibrates on known article scores
- Provides uncertainty bounds for predictions
- Highlights when system is less confident

### 4. API Architecture

```
Frontend (Next.js) ←→ Backend (FastAPI)
                       ↓
              ┌────────┴────────┐
              │                 │
        Scoring Engine    Analysis Engine
         (Ensemble)         (CFA, Clusters)
              │                 │
              └────────┬────────┘
                       ↓
                  Data Layer
              (Cache, Articles DB)
```

**Key Endpoints**:
- `GET /articles` - List with scores
- `GET /articles/{id}` - Detailed analysis + CFA
- `POST /search?query=...` - Trigger fresh analysis
- `GET /narratives` - Narrative clusters
- `GET /health` - System metrics

### 5. Frontend Features

**Search & Analysis**:
1. User enters search query
2. Backend fetches & analyzes articles (~60s)
3. Results displayed in grid/list view
4. Click article for detailed modal

**Visualizations**:
- **Radar Charts**: 5D bias visualization
- **Network Graph**: Narrative cluster relationships
- **Phrase Highlighting**: CFA contributions color-coded
- **Confidence Bands**: Uncertainty visualization

### 6. Performance Optimizations

- **Parallel Processing**: Score all articles concurrently
- **Smart Caching**: Articles (24h), Scores (session), CFA (permanent)
- **On-demand CFA**: Compute only when article viewed
- **MMR Selection**: Analyze only most informative sentences

**Typical Performance**:
- Initial load: ~100s (7 articles + 1 CFA)
- Per article scoring: ~8s
- CFA computation: ~36s
- Cached response: <100ms

### 7. Error Handling

**Graceful Fallback Chain**:
```
LLM Scoring → Heuristic Scoring → Basic Sentiment
NewsAPI → RSS Feeds → Web Scraping → Cache
Full CFA → Partial CFA → Skip CFA
```

Every component has fallbacks to ensure the system keeps running even with failures.

## Quick Start Guide

### Backend Setup
```bash
cd bias-lab-pipeline
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 -m spacy download en_core_web_sm

# Add API keys to .env
echo "OPENAI_API_KEY=your_key" > .env
echo "NEWSAPI_KEY=your_key" >> .env

# Run server
python api/main.py
```

### Frontend Setup
```bash
cd bias-lab-ui
npm install
npm run dev
```

Visit `http://localhost:3000` and search for any news topic!

## Key Innovations

1. **Contrastive Framing Attribution**: First system to show phrase-level bias contributions
2. **Ensemble Scoring**: Combines AI and heuristics for robustness
3. **Signed Narrative Graphs**: Shows direction of framing differences
4. **Conformal Prediction**: Honest uncertainty quantification
5. **Real-time Analysis**: On-demand computation as users explore

## System Validation

✅ **Working Features**:
- LLM scoring (all articles)
- Conformal bands (all articles)
- Narrative clustering (2-3 clusters)
- CFA analysis (per article)
- Search functionality
- Article detail modal
- All visualizations
- Error recovery

The system successfully analyzes real news, identifies bias patterns, and explains its reasoning at the phrase level - a true advancement in explainable AI for media analysis.
