"""Contrastive Framing Attribution (CFA) engine for bias detection."""
import json
import time
import asyncio
from typing import Dict, List, Tuple, Optional
import numpy as np
from tenacity import retry, stop_after_attempt, wait_exponential
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Try to import spacy
try:
    import spacy
    SPACY_AVAILABLE = True
except:
    SPACY_AVAILABLE = False

class CFA_Engine:
    """
    Contrastive Framing Attribution - Shows which phrases push bias scores
    away from a neutral baseline and by how much.
    """
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.nlp = None
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except:
                pass
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        
    def extract_factual_spine(self, text: str) -> Dict:
        """Extract entities, dates, quantities, and quotes from text."""
        if not self.nlp:
            # Fallback if spacy not available
            return {
                'entities': [],
                'dates': [],
                'quantities': [],
                'quotes': self._extract_quotes_regex(text)
            }
            
        doc = self.nlp(text)
        
        return {
            'entities': [ent.text for ent in doc.ents if ent.label_ in ['PERSON', 'ORG', 'GPE']],
            'dates': [ent.text for ent in doc.ents if ent.label_ == 'DATE'],
            'quantities': [ent.text for ent in doc.ents if ent.label_ in ['MONEY', 'PERCENT', 'CARDINAL']],
            'quotes': self._extract_quotes_regex(text)
        }
    
    def _extract_quotes_regex(self, text: str) -> List[str]:
        """Extract quoted text using regex."""
        import re
        quotes = re.findall(r'"([^"]+)"', text)
        return quotes[:10]  # Limit to 10 quotes
    
    def generate_neutral_rewrite(self, text: str, factual_spine: Dict) -> str:
        """Generate a neutral baseline version of the article."""
        prompt = f"""Rewrite this passage to preserve ONLY verifiable facts and direct quotes.
Remove ALL evaluative language, intensifiers, speculation, and charged words.
Keep named sources and quotes verbatim.

Original text:
{text[:1500]}

Factual elements to preserve:
- Entities: {', '.join(factual_spine['entities'][:10])}
- Dates: {', '.join(factual_spine['dates'][:5])}
- Quotes: {'; '.join(factual_spine['quotes'][:3])}

Return ONLY the neutral rewrite, no commentary:"""
        
        try:
            if hasattr(self.llm_client, 'chat'):  # OpenAI
                response = self.llm_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=800
                )
                return response.choices[0].message.content
        except:
            # Fallback to simple neutral version
            entities = factual_spine.get('entities', [])[:3]
            dates = factual_spine.get('dates', [])[:2]
            
            if entities or dates:
                result = f"Article reports on {', '.join(entities) if entities else 'events'}."
                if dates:
                    result += f" Events occurred on {', '.join(dates)}."
                return result
            else:
                return "Article reports on recent events."
    
    def mmr_sentence_selection(self, text: str, k: int = 8) -> List[str]:
        """
        Maximal Marginal Relevance selection of most informative sentences.
        Balances relevance and diversity.
        """
        sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 20][:20]
        if len(sentences) <= k:
            return sentences
            
        # Embed all sentences
        embeddings = self.embedder.encode(sentences)
        
        # MMR selection
        selected = []
        selected_indices = []
        remaining_indices = list(range(len(sentences)))
        
        # Start with most central sentence
        centroid = np.mean(embeddings, axis=0)
        similarities = cosine_similarity([centroid], embeddings)[0]
        first_idx = np.argmax(similarities)
        selected.append(sentences[first_idx])
        selected_indices.append(first_idx)
        remaining_indices.remove(first_idx)
        
        # Iteratively select sentences that are relevant but diverse
        lambda_param = 0.6  # Balance between relevance and diversity
        
        while len(selected) < k and remaining_indices:
            scores = []
            for idx in remaining_indices:
                # Relevance to centroid
                relevance = similarities[idx]
                
                # Maximum similarity to already selected sentences
                max_sim = max([cosine_similarity([embeddings[idx]], [embeddings[s]])[0][0] 
                              for s in selected_indices])
                
                # MMR score
                score = lambda_param * relevance - (1 - lambda_param) * max_sim
                scores.append((score, idx))
            
            # Select highest MMR score
            scores.sort(reverse=True)
            best_idx = scores[0][1]
            selected.append(sentences[best_idx])
            selected_indices.append(best_idx)
            remaining_indices.remove(best_idx)
        
        return selected
    
    def score_dimension(self, text: str, dimension: str) -> Dict:
        """Score a single dimension with evidence extraction."""
        dimension_prompts = {
            'ideological_stance': "Rate ideological stance (0=far-left, 50=center, 100=far-right)",
            'factual_grounding': "Rate factual grounding (0=unverified claims, 100=well-sourced)",
            'framing_choices': "Rate framing neutrality (0=heavily biased framing, 100=neutral)",
            'emotional_tone': "Rate emotional tone (0=inflammatory, 100=neutral/objective)",
            'source_transparency': "Rate source transparency (0=vague attribution, 100=clear sources)"
        }
        
        prompt = f"""Analyze this text for {dimension_prompts[dimension]}.

Text: {text[:1000]}

Return JSON with:
{{"score": 0-100, "evidence": ["phrase1", "phrase2"], "reasoning": "brief explanation"}}"""
        
        try:
            if hasattr(self.llm_client, 'chat'):  # OpenAI
                response = self.llm_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Return a valid JSON object with 'score' and 'evidence' fields."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    max_tokens=200,
                    response_format={"type": "json_object"}
                )
                
                try:
                    result = json.loads(response.choices[0].message.content)
                    # Ensure required fields exist
                    if 'score' not in result:
                        result['score'] = 50
                    if 'evidence' not in result:
                        result['evidence'] = []
                    return result
                except json.JSONDecodeError:
                    # Fallback if JSON parsing fails
                    return self._heuristic_score_dimension(text, dimension)
        except Exception as e:
            # Log the actual error
            print(f"❌ LLM Error for {dimension}: {str(e)[:100]}")
            # Only fallback if absolutely necessary
            if "insufficient_quota" in str(e) or "rate_limit" in str(e):
                print(f"   Using heuristic fallback for {dimension}")
                return self._heuristic_score_dimension(text, dimension)
            else:
                # Re-raise other errors so we can see what's actually wrong
                raise
    
    def _heuristic_score_dimension(self, text: str, dimension: str) -> Dict:
        """Heuristic scoring when LLM fails."""
        text_lower = text.lower()
        
        if dimension == "ideological_stance":
            # Count partisan indicators
            left_terms = ['progressive', 'inequality', 'climate crisis', 'systemic', 'marginalized']
            right_terms = ['traditional', 'freedom', 'patriot', 'woke', 'radical left']
            left_count = sum(1 for term in left_terms if term in text_lower)
            right_count = sum(1 for term in right_terms if term in text_lower)
            score = 50 + (right_count - left_count) * 10
            score = max(0, min(100, score))
            return {
                "score": score,
                "evidence": [text[i:i+50] for i in range(0, min(150, len(text)), 50)],
                "reasoning": f"Heuristic: {left_count} left indicators, {right_count} right indicators"
            }
            
        elif dimension == "factual_grounding":
            # Count facts vs opinions
            fact_indicators = len([1 for c in text if c.isdigit()]) + text.count('%')
            opinion_words = ['believe', 'think', 'feel', 'seems', 'appears', 'might']
            opinion_count = sum(1 for word in opinion_words if word in text_lower)
            score = min(100, 30 + fact_indicators * 5 - opinion_count * 10)
            return {
                "score": max(0, score),
                "evidence": [text[i:i+50] for i in range(0, min(150, len(text)), 50)],
                "reasoning": f"Heuristic: {fact_indicators} factual indicators, {opinion_count} opinion markers"
            }
            
        elif dimension == "emotional_tone":
            # Check emotional language
            emotional_terms = ['shocking', 'outrageous', 'terrifying', 'amazing', 'horrible']
            emotional_count = sum(1 for term in emotional_terms if term in text_lower)
            score = min(100, 20 + emotional_count * 15)
            return {
                "score": score,
                "evidence": [text[i:i+50] for i in range(0, min(150, len(text)), 50)],
                "reasoning": f"Heuristic: {emotional_count} emotional terms detected"
            }
            
        else:
            # Default for other dimensions
            return {"score": 50, "evidence": [], "reasoning": "Heuristic baseline"}
    
    async def compute_cfa_contributions(self, article_text: str, top_k: int = 5) -> Dict:
        """
        Compute Contrastive Framing Attribution for top-k spans.
        Shows which phrases push scores away from neutral baseline.
        """
        # Step 1: MMR sentence selection
        sentences = self.mmr_sentence_selection(article_text, k=8)
        
        # Step 2: Generate neutral rewrite
        factual_spine = self.extract_factual_spine(article_text)
        neutral_rewrite = self.generate_neutral_rewrite(article_text, factual_spine)
        
        # If neutral rewrite failed, use a simple fallback
        if not neutral_rewrite:
            # Simple neutral version - just facts extracted
            entities = factual_spine.get('entities', [])[:3]
            dates = factual_spine.get('dates', [])[:2]
            neutral_rewrite = f"Article reports on {', '.join(entities) if entities else 'events'}. "
            if dates:
                neutral_rewrite += f"Events occurred on {', '.join(dates)}."
            if not neutral_rewrite or len(neutral_rewrite) < 20:
                neutral_rewrite = "Article reports on recent events with various perspectives presented."
        
        # Step 3: Score original and neutral
        dimensions = ['ideological_stance', 'factual_grounding', 'framing_choices', 
                     'emotional_tone', 'source_transparency']
        
        base_scores = {}
        neutral_scores = {}
        
        for dim in dimensions:
            base_scores[dim] = self.score_dimension(article_text, dim)
            neutral_scores[dim] = self.score_dimension(neutral_rewrite, dim)
        
        # Step 4: Compute contributions for top-k sentences
        contributions = []
        
        # Select top-k most impactful sentences
        top_sentences = sentences[:top_k]
        
        for sentence in top_sentences:
            # Create counterfactual by removing sentence
            text_without = article_text.replace(sentence, "")
            
            for dim in dimensions:
                # Score without this sentence
                score_without = self.score_dimension(text_without, dim)
                
                # Compute contrastive contribution
                # C_d,i = (f_d(x) - f_d(NR)) - (f_d(x\i) - f_d(NR))
                contribution = (base_scores[dim]['score'] - neutral_scores[dim]['score']) - \
                              (score_without['score'] - neutral_scores[dim]['score'])
                
                if abs(contribution) > 2:  # Include moderately significant contributions
                    contributions.append({
                        'span': sentence[:100],  # Truncate for display
                        'dimension': dim,
                        'delta': round(contribution, 1),
                        'confidence': 0.7 + min(0.2, abs(contribution) / 100),
                        'reason': f"Phrase {'increases' if contribution > 0 else 'decreases'} {dim}"
                    })
        
        # Sort by absolute contribution
        contributions.sort(key=lambda x: abs(x['delta']), reverse=True)
        
        return {
            'base_scores': base_scores,
            'neutral_scores': neutral_scores,
            'contributions': contributions[:10],  # Top 10 contributions
            'neutral_rewrite_preview': neutral_rewrite[:500]
        }