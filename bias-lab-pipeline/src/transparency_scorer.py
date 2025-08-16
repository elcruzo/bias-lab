"""
Source Transparency Scoring Module

Implements the complete formula:
S_transp = 100 * σ(a₁d + a₂p + a₃r + a₄q - a₅u)

Where:
- d: Attribution density (# sources + # hyperlinks) / tokens
- p: Primary source linkage (official docs, court filings, etc.)
- r: Direct quote ratio
- q: Quote quality (% with names & titles)
- u: Anonymous source penalty
"""

import re
import math
from typing import Dict, List, Tuple
from urllib.parse import urlparse


class TransparencyScorer:
    """Scores articles for source transparency using weighted formula."""
    
    def __init__(self):
        # Tuned weights for formula components
        self.weights = {
            'attribution_density': 2.0,      # a₁
            'primary_sources': 3.0,          # a₂
            'quote_ratio': 1.5,              # a₃
            'quote_quality': 2.5,            # a₄
            'anonymous_penalty': 1.8         # a₅
        }
        
        # Official domains indicating primary sources
        self.primary_domains = [
            '.gov', '.edu', '.org', 'court', 'congress',
            'whitehouse', 'senate', 'house.gov', 'state.gov',
            'justice.gov', 'treasury.gov', 'federalreserve',
            'sec.gov', 'fda.gov', 'cdc.gov', 'nih.gov'
        ]
        
        # Anonymous source patterns
        self.anonymous_patterns = [
            r'sources? (?:said|say|told)',
            r'officials? (?:said|say|told)',
            r'according to (?:sources|officials)',
            r'people familiar with',
            r'someone close to',
            r'insider(?:s)? (?:said|say)',
            r'on condition of anonymity',
            r'speaking on background',
            r'declined to be (?:named|identified)'
        ]
    
    def score_transparency(self, article: Dict) -> Dict:
        """Calculate transparency score."""
        text = article.get('full_text', '')
        title = article.get('title', '')
        
        # Calculate components
        components = {
            'attribution_density': self._calc_attribution_density(text),
            'primary_sources': self._calc_primary_sources(text),
            'quote_ratio': self._calc_quote_ratio(text),
            'quote_quality': self._calc_quote_quality(text),
            'anonymous_penalty': self._calc_anonymous_penalty(text)
        }
        
        # Apply weighted formula
        weighted_sum = (
            self.weights['attribution_density'] * components['attribution_density'] +
            self.weights['primary_sources'] * components['primary_sources'] +
            self.weights['quote_ratio'] * components['quote_ratio'] +
            self.weights['quote_quality'] * components['quote_quality'] -
            self.weights['anonymous_penalty'] * components['anonymous_penalty']
        )
        
        # Apply sigmoid to get 0-100 score
        raw_score = 100 * self._sigmoid(weighted_sum)
        
        # Extract evidence
        evidence = self._extract_evidence(text)
        
        return {
            'score': round(raw_score, 1),
            'components': components,
            'weighted_sum': weighted_sum,
            'evidence': evidence,
            'interpretation': self._interpret_score(raw_score)
        }
    
    def _calc_attribution_density(self, text: str) -> float:
        """Calculate (# sources + # hyperlinks) / tokens."""
        if not text:
            return 0.0
        
        # Count explicit sources
        source_patterns = [
            r'(?:said|according to|told|reported by) ([A-Z][a-z]+ [A-Z][a-z]+)',
            r'([A-Z][a-z]+ [A-Z][a-z]+)(?:, .+?,)? (?:said|told|reported)',
            r'(?:Dr\.|Prof\.|Mr\.|Ms\.|Mrs\.) ([A-Z][a-z]+ [A-Z][a-z]+)'
        ]
        
        sources = set()
        for pattern in source_patterns:
            matches = re.findall(pattern, text)
            sources.update(matches)
        
        # Count hyperlinks
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, text)
        
        # Calculate density
        total_attributions = len(sources) + len(urls)
        tokens = len(text.split())
        
        return min(1.0, total_attributions / max(1, tokens) * 100)
    
    def _calc_primary_sources(self, text: str) -> float:
        """Calculate presence of primary source links."""
        urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', text)
        
        primary_count = 0
        for url in urls:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            if any(primary in domain for primary in self.primary_domains):
                primary_count += 1
        
        # Normalize to 0-1 scale
        return min(1.0, primary_count / 3)  # 3 primary sources = max score
    
    def _calc_quote_ratio(self, text: str) -> float:
        """Calculate ratio of direct quotes to total text."""
        if not text:
            return 0.0
        
        # Find quoted text
        quote_pattern = r'"([^"]+)"'
        quotes = re.findall(quote_pattern, text)
        
        quoted_chars = sum(len(q) for q in quotes)
        total_chars = len(text)
        
        return min(1.0, quoted_chars / max(1, total_chars) * 3)  # Scale factor
    
    def _calc_quote_quality(self, text: str) -> float:
        """Calculate % of quotes with full attribution (name + title)."""
        # Find quotes with context
        quote_contexts = re.findall(
            r'([^.!?]*?"[^"]+?"[^.!?]*)', 
            text, 
            re.MULTILINE
        )
        
        if not quote_contexts:
            return 0.0
        
        attributed_quotes = 0
        for context in quote_contexts:
            # Check for name and title near quote
            has_name = bool(re.search(r'[A-Z][a-z]+ [A-Z][a-z]+', context))
            has_title = bool(re.search(
                r'(?:president|director|ceo|spokesperson|minister|senator|'
                r'representative|professor|dr\.|analyst|expert|chief|head|'
                r'chairman|secretary|commissioner|officer)',
                context.lower()
            ))
            
            if has_name and has_title:
                attributed_quotes += 1
        
        return attributed_quotes / len(quote_contexts)
    
    def _calc_anonymous_penalty(self, text: str) -> float:
        """Calculate penalty for anonymous sources."""
        if not text:
            return 0.0
        
        text_lower = text.lower()
        anonymous_count = 0
        
        for pattern in self.anonymous_patterns:
            matches = re.findall(pattern, text_lower)
            anonymous_count += len(matches)
        
        # Normalize penalty (more anonymous = higher penalty)
        return min(1.0, anonymous_count / 5)  # 5 anonymous sources = max penalty
    
    def _sigmoid(self, x: float) -> float:
        """Sigmoid function for score normalization."""
        return 1 / (1 + math.exp(-x / 2))
    
    def _extract_evidence(self, text: str) -> Dict:
        """Extract specific evidence for transparency."""
        evidence = {
            'named_sources': [],
            'primary_links': [],
            'anonymous_mentions': [],
            'direct_quotes': []
        }
        
        # Extract named sources
        source_pattern = r'(?:said|according to|told) ([A-Z][a-z]+ [A-Z][a-z]+)'
        evidence['named_sources'] = list(set(re.findall(source_pattern, text)))[:5]
        
        # Extract primary source links
        urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', text)
        for url in urls[:10]:
            parsed = urlparse(url)
            if any(primary in parsed.netloc.lower() for primary in self.primary_domains):
                evidence['primary_links'].append(url)
        
        # Extract anonymous mentions
        text_lower = text.lower()
        for pattern in self.anonymous_patterns[:3]:
            matches = re.findall(f'[^.]*{pattern}[^.]*', text_lower)
            evidence['anonymous_mentions'].extend(matches[:2])
        
        # Extract direct quotes with attribution
        quote_contexts = re.findall(r'([^.!?]*?"[^"]{20,100}"[^.!?]*)', text)
        evidence['direct_quotes'] = quote_contexts[:3]
        
        return evidence
    
    def _interpret_score(self, score: float) -> str:
        """Provide interpretation of transparency score."""
        if score >= 80:
            return "Excellent transparency: Multiple named sources with titles, primary documentation"
        elif score >= 60:
            return "Good transparency: Named sources present, some primary references"
        elif score >= 40:
            return "Moderate transparency: Mix of named and anonymous sources"
        elif score >= 20:
            return "Poor transparency: Mostly anonymous or vague sourcing"
        else:
            return "Very poor transparency: Little to no source attribution"


def get_transparency_scorer():
    """Factory function to get transparency scorer instance."""
    return TransparencyScorer()
