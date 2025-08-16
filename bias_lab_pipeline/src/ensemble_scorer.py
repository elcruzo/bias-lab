"""Ensemble scoring system - Combines LLM scoring with heuristic fallbacks."""
import re
import time
import asyncio
from typing import Dict, List, Tuple, Optional
import numpy as np
from collections import Counter

class HeuristicScorer:
    """Rule-based heuristic scoring as fallback and validation."""
    
    def __init__(self):
        # Ideology indicators (simplified lexicons)
        self.left_indicators = [
            'progressive', 'inequality', 'systemic', 'marginalized', 'equity',
            'social justice', 'climate crisis', 'corporate greed', 'fascist'
        ]
        self.right_indicators = [
            'freedom', 'traditional', 'patriot', 'radical left', 'woke',
            'law and order', 'illegal aliens', 'job creators', 'socialist'
        ]
        
        # Emotional tone indicators
        self.inflammatory_words = [
            'shocking', 'outrageous', 'disgusting', 'horrifying', 'explosive',
            'slammed', 'destroyed', 'obliterated', 'furious', 'enraged'
        ]
        
        # Source transparency patterns
        self.vague_attribution = [
            'sources say', 'people say', 'experts believe', 'many think',
            'it is said', 'reportedly', 'allegedly', 'some claim'
        ]
        
        self.clear_attribution = [
            'according to', 'said', 'stated', 'confirmed', 'announced',
            'reported', 'testified', 'wrote', 'published'
        ]
    
    def score_ideology(self, text: str) -> Dict:
        """Score ideological stance using word frequencies."""
        text_lower = text.lower()
        
        left_count = sum(1 for word in self.left_indicators if word in text_lower)
        right_count = sum(1 for word in self.right_indicators if word in text_lower)
        
        total = left_count + right_count
        if total == 0:
            score = 50  # Neutral if no indicators
        else:
            # 0 = far left, 100 = far right
            score = int(100 * right_count / total)
        
        # Find evidence phrases
        evidence = []
        for word in self.left_indicators[:3]:
            if word in text_lower:
                # Find sentence containing the word
                for sent in text.split('.'):
                    if word in sent.lower():
                        evidence.append(sent.strip()[:100])
                        break
        
        return {
            'score': score,
            'evidence': evidence[:2],
            'reasoning': f"Found {left_count} left indicators, {right_count} right indicators"
        }
    
    def score_factual_grounding(self, text: str) -> Dict:
        """Score based on presence of facts, numbers, and sources."""
        # Count factual elements
        numbers = len(re.findall(r'\b\d+\.?\d*%?\b', text))
        quotes = len(re.findall(r'"[^"]{10,}"', text))
        dates = len(re.findall(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}', text))
        
        # Normalize by text length (per 100 words)
        word_count = len(text.split())
        if word_count == 0:
            score = 50
            density = 0
        else:
            density = (numbers + quotes * 2 + dates) / (word_count / 100)
            score = min(100, int(20 + density * 10))
        
        return {
            'score': score,
            'evidence': [f"Contains {numbers} numbers, {quotes} quotes"],
            'reasoning': f"Factual density: {density:.1f} per 100 words"
        }
    
    def score_emotional_tone(self, text: str) -> Dict:
        """Score emotional tone based on inflammatory language."""
        text_lower = text.lower()
        
        inflammatory_count = sum(1 for word in self.inflammatory_words if word in text_lower)
        word_count = len(text.split())
        
        if word_count == 0:
            score = 100  # Neutral if empty
        else:
            # Higher score = more neutral
            inflammatory_ratio = inflammatory_count / (word_count / 100)
            score = max(0, int(100 - inflammatory_ratio * 20))
        
        evidence = []
        for word in self.inflammatory_words:
            if word in text_lower:
                for sent in text.split('.'):
                    if word in sent.lower():
                        evidence.append(sent.strip()[:100])
                        break
                if len(evidence) >= 2:
                    break
        
        return {
            'score': score,
            'evidence': evidence,
            'reasoning': f"Found {inflammatory_count} inflammatory terms"
        }
    
    def score_source_transparency(self, text: str) -> Dict:
        """Score based on attribution quality."""
        text_lower = text.lower()
        
        vague_count = sum(1 for pattern in self.vague_attribution if pattern in text_lower)
        clear_count = sum(1 for pattern in self.clear_attribution if pattern in text_lower)
        
        # Count named sources (simplified)
        named_sources = len(re.findall(r'[A-Z][a-z]+ [A-Z][a-z]+(?:,|\s+said|\s+stated)', text))
        
        total_attributions = vague_count + clear_count + named_sources
        if total_attributions == 0:
            score = 30  # Low transparency if no attributions
        else:
            score = int(100 * (clear_count + named_sources) / total_attributions)
        
        return {
            'score': score,
            'evidence': [f"{named_sources} named sources, {vague_count} vague attributions"],
            'reasoning': f"Clear attribution ratio: {clear_count}/{total_attributions}"
        }
    
    def score_framing_choices(self, text: str) -> Dict:
        """Score framing neutrality based on loaded language."""
        # Simplified: combine ideology and emotion indicators
        ideology_score = self.score_ideology(text)['score']
        emotion_score = self.score_emotional_tone(text)['score']
        
        # Neutral framing if both ideology and emotion are neutral
        deviation_from_neutral = abs(ideology_score - 50) + (100 - emotion_score)
        score = max(0, int(100 - deviation_from_neutral / 2))
        
        return {
            'score': score,
            'evidence': [],
            'reasoning': f"Combines ideology deviation ({abs(ideology_score - 50)}) and emotional charge"
        }
    
    def score_all_dimensions(self, text: str) -> Dict:
        """Score all dimensions using heuristics."""
        return {
            'ideological_stance': self.score_ideology(text),
            'factual_grounding': self.score_factual_grounding(text),
            'framing_choices': self.score_framing_choices(text),
            'emotional_tone': self.score_emotional_tone(text),
            'source_transparency': self.score_source_transparency(text)
        }


class EnsembleScorer:
    """
    Combines LLM scoring with heuristic scoring.
    Provides fallback mechanism and cross-validation.
    """
    
    def __init__(self, llm_scorer, weights={'llm': 0.7, 'heuristic': 0.3}):
        self.llm_scorer = llm_scorer
        self.heuristic_scorer = HeuristicScorer()
        self.weights = weights
        self.cache = {}
        
    async def score_with_ensemble(self, article: Dict, use_cache: bool = True) -> Dict:
        """
        Score article using ensemble of LLM and heuristics.
        Falls back to heuristics if LLM fails.
        """
        # Handle case where article might be a string
        if isinstance(article, str):
            print(f"Warning: Expected article dict but got string")
            article = {'content': article, 'full_text': article, 'url': ''}
        
        article_hash = hash(article.get('url', ''))
        
        # Check cache
        if use_cache and article_hash in self.cache:
            cached = self.cache[article_hash]
            cached['from_cache'] = True
            return cached
        
        text = article.get('full_text', '')
        
        # Try LLM scoring
        llm_scores = None
        llm_failed = False
        
        try:
            llm_scores = await self.llm_scorer.score_article(article)
        except Exception as e:
            # print(f"LLM scoring failed: {e}")  # Commented out after debugging
            llm_failed = True
        
        # Always compute heuristic scores
        heuristic_results = self.heuristic_scorer.score_all_dimensions(text)
        
        # Combine scores
        if llm_scores and not llm_failed:
            # Weighted average of LLM and heuristic scores
            final_scores = {}
            highlighted_phrases = {}
            reasoning = {}
            
            dimensions = ['ideological_stance', 'factual_grounding', 'framing_choices',
                         'emotional_tone', 'source_transparency']
            
            for dim in dimensions:
                llm_score = llm_scores['scores'][dim]
                heuristic_score = heuristic_results[dim]['score']
                
                # Weighted average
                final_scores[dim] = int(
                    self.weights['llm'] * llm_score + 
                    self.weights['heuristic'] * heuristic_score
                )
                
                # Combine evidence
                highlighted_phrases[dim] = (
                    llm_scores.get('highlighted_phrases', {}).get(dim, []) +
                    heuristic_results[dim].get('evidence', [])
                )[:3]  # Keep top 3
                
                # Combine reasoning
                reasoning[dim] = f"LLM: {llm_scores.get('reasoning', {}).get(dim, 'N/A')}. " + \
                                f"Heuristic: {heuristic_results[dim]['reasoning']}"
            
            # Calculate variance for confidence
            score_variance = np.mean([
                abs(llm_scores['scores'][dim] - heuristic_results[dim]['score'])
                for dim in dimensions
            ])
            
            confidence = max(0.5, min(0.95, 1 - score_variance / 100))
            
            result = {
                'article_id': article_hash,
                'title': article.get('title', ''),
                'source': article.get('source', ''),
                'url': article.get('url', ''),
                'published_at': article.get('published_at', ''),
                'scores': final_scores,
                'highlighted_phrases': highlighted_phrases,
                'reasoning': reasoning,
                'confidence_interval': {
                    'lower': max(0, confidence - 0.1),
                    'upper': min(1, confidence + 0.1),
                    'confidence': confidence
                },
                'ensemble_method': 'weighted_average',
                'stale': False,
                'processing_time_ms': llm_scores.get('processing_time_ms', 0)
            }
            
        else:
            # Fallback to heuristics only
            final_scores = {dim: heuristic_results[dim]['score'] 
                          for dim in heuristic_results}
            highlighted_phrases = {dim: heuristic_results[dim].get('evidence', [])
                                  for dim in heuristic_results}
            reasoning = {dim: heuristic_results[dim]['reasoning']
                        for dim in heuristic_results}
            
            result = {
                'article_id': article_hash,
                'title': article.get('title', ''),
                'source': article.get('source', ''),
                'url': article.get('url', ''),
                'published_at': article.get('published_at', ''),
                'scores': final_scores,
                'highlighted_phrases': highlighted_phrases,
                'reasoning': reasoning,
                'confidence_interval': {
                    'lower': 0.3,
                    'upper': 0.7,
                    'confidence': 0.5  # Lower confidence for heuristics only
                },
                'ensemble_method': 'heuristic_fallback',
                'stale': True,  # Mark as stale when using fallback
                'processing_time_ms': 0
            }
        
        # Cache result
        self.cache[article_hash] = result
        
        return result
    
    async def score_multiple_with_ensemble(self, articles: List[Dict]) -> List[Dict]:
        """Score multiple articles concurrently with ensemble."""
        tasks = [self.score_with_ensemble(article) for article in articles]
        results = await asyncio.gather(*tasks)
        return results
