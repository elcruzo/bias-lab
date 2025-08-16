# The Bias Lab - AI-Powered Media Bias Detection

> **Work Sample Submission** by Ayomide Adekoya - Complete AI bias detection platform built in 24 hours.

## 🎯 What This Is

An **AI bias detection MVP** that analyzes media bias across news articles using advanced AI techniques. Demonstrates the complete technical stack needed for The Bias Lab's vision.

## ✨ Key Features

- **5-Dimension Bias Scoring**: Ideological stance, factual grounding, framing choices, emotional tone, source transparency
- **Contrastive Framing Attribution**: Identifies exact phrases contributing to bias
- **Narrative Clustering**: Groups similar story framings using graph theory
- **Real-time Processing**: Sub-500ms response times with intelligent caching
- **Interactive Dashboard**: Professional UI with D3.js visualizations

## 🚀 Quick Start

### Backend
```bash
cd bias-lab-pipeline
source venv/bin/activate
python api/main.py
```

### Frontend
```bash
cd bias-lab-ui
npm install
npm run dev
```

Visit `http://localhost:3000`

## 📚 Documentation

- **[📋 Submission Checklist](docs/SUBMISSION_CHECKLIST.md)** - Complete technical verification
- **[📝 Work Sample Details](docs/WORK_SAMPLE.md)** - Detailed submission summary
- **[🚀 Deployment Guide](docs/DEPLOYMENT.md)** - Step-by-step deployment

## 🎯 Requirements Met

✅ **All Core Requirements + Bonuses**
- Data ingestion from NewsAPI/RSS
- 5-dimension scoring (0-100 scale)
- GPT-3.5 with prompt engineering
- Sub-500ms performance
- JSON API with confidence intervals
- Narrative clustering
- Phrase-level bias attribution

## 🧠 Advanced AI Techniques

- **Ensemble Scoring**: LLM + heuristics for reliability
- **Conformal Prediction**: Uncertainty quantification
- **Graph Theory**: Louvain algorithm for clustering
- **Semantic Embeddings**: Sentence transformers

## 🏗️ Architecture

```
Frontend (Next.js) → API (FastAPI) → AI Pipeline → Visualizations
                                   ↓
NewsAPI/RSS → Processing → Scoring → Analysis
```

## 📊 Performance

- **Speed**: <500ms per article
- **Scale**: 10-20 articles simultaneously  
- **Reliability**: Ensemble fallbacks
- **Accuracy**: Multi-prompt validation

---

**Ready for production deployment and integration into The Bias Lab's MVP.** 🚀