"""Bias scoring engine using LLM analysis."""
import json
import time
import asyncio
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import numpy as np
from tenacity import retry, stop_after_attempt, wait_exponential
from .config import Config
from .claim_extraction import get_text_processor
from .advanced_prompts import get_best_prompt_for_article

@dataclass
class BiasScore:
    """Bias scores for an article."""
    ideological_stance: float  # 0=far-left, 50=center, 100=far-right
    factual_grounding: float   # 0=unverified claims, 100=well-sourced
    framing_choices: float      # 0=heavily framed, 100=neutral presentation
    emotional_tone: float       # 0=inflammatory, 100=neutral
    source_transparency: float  # 0=vague attribution, 100=clear sources
    confidence: float          # Overall confidence in scoring
    highlighted_phrases: Dict[str, List[str]]  # Phrases that influenced each dimension
    claim_summary: Optional[Dict] = None  # Summary of extracted claims
    
class BiasScorer:
    """Scores articles for bias using LLM analysis with chain-of-thought."""
    
    def __init__(self):
        self.llm_client = self._initialize_llm()
        self.text_processor = get_text_processor()
        self.scoring_cache = {}
        
    def _initialize_llm(self):
        """Initialize the appropriate LLM client."""
        if Config.LLM_PROVIDER == "openai":
            from openai import OpenAI
            try:
                client = OpenAI(api_key=Config.OPENAI_API_KEY)
                # Quick test to verify it works
                test_response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=1
                )
                print("✅ OpenAI client initialized and working with credits!")
                return client
            except Exception as e:
                print(f"⚠️ OpenAI initialization error: {str(e)[:100]}")
                if "insufficient_quota" in str(e):
                    print("   Falling back to heuristic scoring...")
                return None
        else:
            raise ValueError(f"Unsupported LLM provider: {Config.LLM_PROVIDER}")
    
    def _create_prompt_variants(self, article: Dict) -> List[str]:
        """Create 3 prompt variants for ensemble averaging."""
        title = article.get('title', '')
        text = article.get('full_text', '')[:3000]
        
        # Process article for context
        processed = self.text_processor.process_article(title, text)
        bias_summary = self.text_processor.get_bias_summary(processed)
        
        # Variant 1: Chain-of-thought with claim analysis
        prompt1 = get_best_prompt_for_article(title=title, text=text)
        
        # Variant 2: Direct analytical prompt
        prompt2 = f"""Analyze this article for bias indicators and return results in JSON format.

Title: {title}
Text: {text[:1500]}

Evaluate these 5 dimensions:
1. Ideological stance (0=far left, 100=far right): Look for policy positions
2. Factual grounding (0=opinion, 100=factual): Count verifiable claims
3. Framing choices (0=neutral, 100=loaded): Identify charged language
4. Emotional tone (0=calm, 100=inflammatory): Assess emotional language
5. Source transparency (0=anonymous, 100=attributed): Check source quality

Provide scores and quote specific evidence.
Return a valid JSON response with this structure: {{"dimensions": [...], "evidence": {{...}}}}"""
        
        # Variant 3: Contrastive prompt
        prompt3 = f"""Compare this article against neutral journalism standards and return JSON format analysis.

Article: {title}
{text[:1500]}

Analysis required:
- Political lean: What ideological markers are present?
- Fact/opinion ratio: How much is verifiable vs. interpretation?
- Language framing: Which words shape perception?
- Emotional manipulation: What feelings are evoked?
- Source credibility: Who is quoted and how?

Score each dimension 0-100 with supporting quotes.
Return valid JSON with "dimensions" and "evidence" fields in this format: {{"dimensions": [...], "evidence": {{...}}}}"""
        
        return [prompt1, prompt2, prompt3]
    
    def _create_prompt(self, article: Dict) -> str:
        """Create prompt for bias scoring."""
        # Return first variant for backward compatibility
        return self._create_prompt_variants(article)[0]
    
    def _create_prompt_with_context(self, article: Dict) -> tuple:
        """Create prompt with article context and bias indicators."""
        # Get text content with fallback
        text_content = article.get('full_text', '')
        
        # First, process the article for claims and bias indicators
        processed = self.text_processor.process_article(
            article.get('title', ''),
            text_content[:3000]
        )
        
        # Get bias summary
        bias_summary = self.text_processor.get_bias_summary(processed)
        
        # Get prompt for scoring
        prompt = get_best_prompt_for_article(
            title=article.get('title', ''),
            text=text_content
        )
        
        # Add claim analysis context
        prompt += f"\n\n## CLAIM ANALYSIS CONTEXT:\n"
        prompt += f"- Total claims: {bias_summary['total_claims']}\n"
        prompt += f"- Claim types: {json.dumps(bias_summary['claim_breakdown'])}\n"
        prompt += f"- Quote types: {json.dumps(bias_summary['quote_breakdown'])}\n"
        prompt += f"- Bias indicators found: {json.dumps(bias_summary['bias_indicators'])}\n"
        prompt += f"- Named entities: {json.dumps(bias_summary['entities'])}\n"
        
        return prompt, bias_summary

    def _average_prompt_results(self, results: List[Dict]) -> Dict:
        """Average multiple LLM results from ensemble prompts."""
        if not results:
            return {}
        
        # Extract dimensions from all results
        all_dimensions = []
        for result in results:
            if 'dimensions' in result:
                dims = result.get('dimensions', [])
                # Handle different formats LLM might return
                for d in dims:
                    if isinstance(d, str):
                        # Format: ["political lean", "fact/opinion ratio", ...]
                        # Skip string-only dimensions, they have no scores
                        continue
                    elif isinstance(d, dict):
                        all_dimensions.append(d)
        
        # Group by dimension name and average
        dimension_groups = {}
        
        # Normalize dimension names to standard format
        name_mapping = {
            'political lean': 'ideological_stance',
            'ideological stance': 'ideological_stance',
            'fact/opinion ratio': 'factual_grounding',
            'factual grounding': 'factual_grounding',
            'language framing': 'framing_choices',
            'framing choices': 'framing_choices',
            'emotional manipulation': 'emotional_tone',
            'emotional tone': 'emotional_tone',
            'source transparency': 'source_transparency',
        }
        
        for dim in all_dimensions:
            # Handle different dict structures
            if 'dimension' in dim:
                # Format: {"dimension": "name", "score": 50}
                dim_name = dim.get('dimension', '')
            elif 'name' in dim:
                # Format: {"name": "Ideological stance", "score": 50}
                dim_name = dim.get('name', '')
            else:
                # Format: {"Political lean": 70} - key is the dimension name
                dim_name = list(dim.keys())[0] if dim else ''
            
            # Normalize the dimension name
            dim_name_lower = dim_name.lower()
            dim_name_normalized = name_mapping.get(dim_name_lower, dim_name_lower.replace(' ', '_'))
            
            if dim_name_normalized and dim_name_normalized not in dimension_groups:
                dimension_groups[dim_name_normalized] = []
            if dim_name_normalized:
                dimension_groups[dim_name_normalized].append(dim)
        
        # Average each dimension
        averaged_dimensions = []
        for dim_name, dims in dimension_groups.items():
            scores = []
            for d in dims:
                if 'score' in d:
                    # Format: {"dimension": "name", "score": 50}
                    scores.append(d.get('score', 50))
                else:
                    # Try to find a numeric value using any key that could be a dimension name
                    score_found = False
                    for k, v in d.items():
                        if isinstance(v, (int, float)):
                            scores.append(v)
                            score_found = True
                            break
                    if not score_found:
                        # Default score if we can't find any
                        scores.append(50)
            phrases = []
            rationales = []
            
            for d in dims:
                phrases.extend(d.get('highlighted_phrases', []))
                rationales.append(d.get('rationale', ''))
            
            # Deduplicate phrases
            unique_phrases = list(set(phrases))[:5]
            
            averaged_dimensions.append({
                'dimension': dim_name,
                'score': sum(scores) / len(scores),
                'highlighted_phrases': unique_phrases,
                'rationale': ' '.join(filter(None, rationales))[:500]
            })
        
        return {'dimensions': averaged_dimensions}
    
    def _average_scores(self, scores: List[Dict]) -> Dict:
        """Average multiple score dictionaries from ensemble prompts."""
        if not scores:
            return {}
        
        # Initialize averaged result
        averaged = {
            'ideological_stance': 0,
            'factual_grounding': 0,
            'framing_choices': 0,
            'emotional_tone': 0,
            'source_transparency': 0,
            'evidence': {},
            'highlighted_phrases': []
        }
        
        # Average numeric scores
        for dim in ['ideological_stance', 'factual_grounding', 'framing_choices', 
                    'emotional_tone', 'source_transparency']:
            values = [s.get(dim, 50) for s in scores if dim in s]
            if values:
                averaged[dim] = sum(values) / len(values)
        
        # Combine evidence
        for score in scores:
            if 'evidence' in score:
                for key, value in score['evidence'].items():
                    if key not in averaged['evidence']:
                        averaged['evidence'][key] = []
                    if isinstance(value, list):
                        averaged['evidence'][key].extend(value)
                    else:
                        averaged['evidence'][key].append(value)
        
        # Combine highlighted phrases
        for score in scores:
            if 'highlighted_phrases' in score:
                averaged['highlighted_phrases'].extend(score['highlighted_phrases'])
        
        # Deduplicate highlighted phrases
        seen = set()
        unique_phrases = []
        for phrase in averaged['highlighted_phrases']:
            phrase_text = phrase.get('text', '') if isinstance(phrase, dict) else str(phrase)
            if phrase_text not in seen:
                seen.add(phrase_text)
                unique_phrases.append(phrase)
        averaged['highlighted_phrases'] = unique_phrases[:10]
        
        return averaged
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def score_article(self, article: Dict, use_ensemble: bool = True) -> Dict:
        """Score a single article for bias with optional ensemble averaging."""
        start_time = time.time()
        
        # Check cache
        article_hash = hash(article.get('url', ''))
        if article_hash in self.scoring_cache:
            cached = self.scoring_cache[article_hash]
            cached['from_cache'] = True
            return cached
        
                 # Check if LLM client is available
        if not self.llm_client:
            print("⚠️ No LLM client available, using heuristic scoring")
            return self._get_heuristic_scores(article)
            
        try:
            # Use ensemble of 3 prompts if enabled
            if use_ensemble and self.llm_client:
                prompts = self._create_prompt_variants(article)
                all_results = []
                
                for i, prompt in enumerate(prompts):
                    try:
                        if Config.LLM_PROVIDER == "openai":
                            response = self.llm_client.chat.completions.create(
                                model="gpt-3.5-turbo",
                                messages=[
                                    {"role": "system", "content": "You are an expert media bias analyst. Always provide detailed, evidence-based analysis in valid JSON format."},
                                    {"role": "user", "content": prompt}
                                ],
                                temperature=0.2 + (i * 0.1),  # Vary temperature slightly for diversity
                                max_tokens=2000,
                                response_format={"type": "json_object"}
                            )
                            response_content = response.choices[0].message.content
                            result = json.loads(response_content)
                            all_results.append(result)
                    except Exception as e:
                        # print(f"Prompt variant {i+1} failed: {e}")  # Commented out after debugging
                        continue
                
                # Average results if we got multiple
                if len(all_results) > 1:
                    result = self._average_prompt_results(all_results)
                elif all_results:
                    result = all_results[0]
                else:
                    # All prompts failed, use single prompt fallback
                    prompt, bias_summary = self._create_prompt_with_context(article)
                    response = self.llm_client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are an expert media bias analyst. Always provide detailed, evidence-based analysis in valid JSON format."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.2,
                        max_tokens=2000,
                        response_format={"type": "json_object"}
                    )
                    result = json.loads(response.choices[0].message.content)
            else:
                # Single prompt mode
                prompt, bias_summary = self._create_prompt_with_context(article)
                
                if Config.LLM_PROVIDER == "openai":
                    response = self.llm_client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are an expert media bias analyst. Always provide detailed, evidence-based analysis in valid JSON format."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.2,  # Low temperature for consistency
                        max_tokens=2000,
                        response_format={"type": "json_object"}
                    )
                    result = json.loads(response.choices[0].message.content)
            
            # Extract dimensions from result
            dimensions_data = result.get('dimensions', [])
            
            # Process article for claim analysis
            article_text = article.get('full_text', '')
            processed = self.text_processor.process_article(
                article.get('title', ''),
                article_text[:3000] if isinstance(article_text, str) else ''
            )
            bias_summary = self.text_processor.get_bias_summary(processed)
            
            # Build scores dictionary
            scores = {}
            highlighted_phrases = {}
            reasoning = {}
            
            for dim in dimensions_data:
                dim_name = dim.get('dimension', '')
                scores[dim_name] = dim.get('score', 50)
                highlighted_phrases[dim_name] = dim.get('highlighted_phrases', [])
                reasoning[dim_name] = dim.get('rationale', '')
            
            # Ensure all dimensions are present
            for dim_name in Config.BIAS_DIMENSIONS:
                if dim_name not in scores:
                    scores[dim_name] = 50
                    highlighted_phrases[dim_name] = []
                    reasoning[dim_name] = "Unable to analyze"
            
            # Calculate processing time
            processing_time = (time.time() - start_time) * 1000
            
            # Calculate overall confidence based on evidence
            confidence = result.get('overall_confidence', 0.5)
            if bias_summary['total_claims'] > 10:
                confidence = min(0.95, confidence + 0.1)
            
            # Build formatted result
            formatted_result = {
                'article_id': article_hash,
                'title': article.get('title', ''),
                'source': article.get('source', ''),
                'url': article.get('url', ''),
                'published_at': article.get('published_at', ''),
                'scores': scores,
                'highlighted_phrases': highlighted_phrases,
                'reasoning': reasoning,
                'claim_summary': bias_summary,
                'confidence_interval': {
                    'lower': max(0, confidence - 0.1),
                    'upper': min(1, confidence + 0.1),
                    'confidence': confidence
                },
                'processing_time_ms': processing_time,
                'analysis_metadata': {
                    'total_claims': bias_summary['total_claims'],
                    'quote_types': bias_summary['quote_breakdown'],
                    'bias_indicators': bias_summary['bias_indicators']
                }
            }
            
            # Cache the result
            self.scoring_cache[article_hash] = formatted_result
            
            return formatted_result
            
        except Exception as e:
            # print(f"LLM scoring failed for article, using heuristics: {str(e)[:100]}")  # Commented out after debugging
            # Return heuristic-based scores on error
            return self._get_heuristic_scores(article)
    
    def _get_heuristic_scores(self, article: Dict) -> Dict:
        """Generate heuristic-based scores when LLM fails."""
        # Get article text
        article_text = article.get('full_text', '')
        
        # Process article for bias indicators
        processed = self.text_processor.process_article(
            article.get('title', ''),
            article_text[:3000] if isinstance(article_text, str) else ''
        )
        bias_summary = self.text_processor.get_bias_summary(processed)
        

        
        # Calculate heuristic scores based on indicators
        scores = {}
        
        # Ideological stance based on partisan terms
        partisan_count = bias_summary['bias_indicators'].get('partisan_terms', 0)
        if partisan_count > 5:
            scores['ideological_stance'] = 75 if 'conservative' in str(processed.bias_indicators) else 25
        else:
            scores['ideological_stance'] = 50
        
        # Factual grounding based on claim types
        factual_ratio = bias_summary['claim_breakdown'].get('factual', 0) / max(1, bias_summary['total_claims'])
        scores['factual_grounding'] = int(factual_ratio * 100)
        
        # Framing choices based on quote diversity
        anonymous_quotes = bias_summary['quote_breakdown'].get('anonymous', 0)
        scores['framing_choices'] = max(0, 100 - (anonymous_quotes * 20))
        
        # Emotional tone based on emotional language
        emotional_count = bias_summary['bias_indicators'].get('emotional_language', 0)
        scores['emotional_tone'] = max(0, 100 - (emotional_count * 10))
        
        # Source transparency based on quote attribution
        direct_quotes = bias_summary['quote_breakdown'].get('direct', 0)
        total_quotes = bias_summary['total_quotes']
        if total_quotes > 0:
            scores['source_transparency'] = int((direct_quotes / total_quotes) * 100)
        else:
            scores['source_transparency'] = 30
        
        return {
            'article_id': hash(article.get('url', '')),
            'title': article.get('title', ''),
            'source': article.get('source', ''),
            'url': article.get('url', ''),
            'published_at': article.get('published_at', ''),
            'scores': scores,
            'highlighted_phrases': {dim: [] for dim in scores},
            'reasoning': {dim: 'Heuristic analysis based on text indicators' for dim in scores},
            'claim_summary': bias_summary,
            'confidence_interval': {
                'lower': 0.3,
                'upper': 0.7,
                'confidence': 0.5
            },
            'processing_time_ms': 0,
            'fallback': True
        }
    
    async def score_multiple_articles(self, articles: List[Dict]) -> List[Dict]:
        """Score multiple articles concurrently for efficiency."""
        tasks = [self.score_article(article) for article in articles]
        results = await asyncio.gather(*tasks)
        return results
    
    def calculate_accuracy_metrics(self, scored_articles: List[Dict]) -> Dict:
        """Calculate accuracy metrics for bias detection."""
        dimension_errors = {dim: [] for dim in Config.BIAS_DIMENSIONS}
        bias_type_correct = {"left": 0, "right": 0, "center": 0}
        bias_type_total = {"left": 0, "right": 0, "center": 0}
        
        for article in scored_articles:
            scores = article.get('scores', {})
            
            # Classify overall bias
            ideology = scores.get('ideological_stance', 50)
            if ideology < 35:
                bias_type = "left"
            elif ideology > 65:
                bias_type = "right"
            else:
                bias_type = "center"
            
            bias_type_total[bias_type] += 1
            
            # Check if classification matches source reputation
            source = article.get('source', '').lower()
            if bias_type == "left" and any(s in source for s in ['cnn', 'msnbc', 'guardian']):
                bias_type_correct["left"] += 1
            elif bias_type == "right" and any(s in source for s in ['fox', 'breitbart', 'conservative']):
                bias_type_correct["right"] += 1
            elif bias_type == "center" and any(s in source for s in ['reuters', 'ap', 'bbc']):
                bias_type_correct["center"] += 1
        
        # Calculate overall accuracy
        total_correct = sum(bias_type_correct.values())
        total_articles = sum(bias_type_total.values())
        overall_accuracy = total_correct / max(1, total_articles)
        
        return {
            'overall_accuracy': overall_accuracy,
            'bias_type_accuracy': bias_type_correct,
            'bias_type_total': bias_type_total,
            'dimension_confidence': {
                dim: np.mean([a['confidence_interval']['confidence'] 
                             for a in scored_articles 
                             if dim in a.get('scores', {})])
                for dim in Config.BIAS_DIMENSIONS
            }
        }