"""Claim extraction and text preprocessing for bias detection."""
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Load spacy model
SPACY_AVAILABLE = False
nlp = None
try:
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
        SPACY_AVAILABLE = True
    except OSError:
        # Try to download model if not found
        try:
            import subprocess
            subprocess.check_call(["python", "-m", "spacy", "download", "en_core_web_sm"])
            nlp = spacy.load("en_core_web_sm")
            SPACY_AVAILABLE = True
        except:
            print("⚠️ Could not load spaCy model, using fallbacks")
            pass
except:
    pass

@dataclass
class ExtractedClaim:
    text: str
    claim_type: str  # "factual", "opinion", "attribution", "prediction"
    confidence: float
    source: Optional[str] = None
    entities: Optional[List[str]] = None
    sentence_index: int = 0

@dataclass
class QuoteAttribution:
    quote: str
    speaker: Optional[str]
    speaker_title: Optional[str]
    attribution_type: str  # "direct", "indirect", "anonymous"
    confidence: float

@dataclass
class ProcessedArticle:
    title: str
    text: str
    sentences: List[str]
    claims: List[ExtractedClaim]
    quotes: List[QuoteAttribution]
    entities: Dict[str, List[str]]
    bias_indicators: Dict[str, List[str]]
    key_phrases: List[str]

class TextProcessor:
    """Text processing for bias detection."""
    
    def __init__(self):
        self.nlp = nlp
        
        # Bias indicator patterns
        self.bias_patterns = {
            "hedge_words": [
                "allegedly", "reportedly", "supposedly", "claims", "suggests", 
                "appears", "seems", "purportedly", "ostensibly"
            ],
            "intensifiers": [
                "extremely", "absolutely", "completely", "totally", "utterly", 
                "devastating", "catastrophic", "massive", "unprecedented"
            ],
            "emotional_language": [
                "outrageous", "shocking", "alarming", "terrifying", "wonderful", 
                "amazing", "horrifying", "disgusting", "appalling", "incredible"
            ],
            "partisan_terms": [
                "radical", "extremist", "progressive", "conservative", "liberal", 
                "socialist", "fascist", "woke", "deep state", "mainstream media"
            ],
            "anonymous_sources": [
                "sources say", "officials say", "people familiar", "according to sources",
                "insiders claim", "experts believe", "many think", "it is said"
            ],
            "certainty_markers": [
                "definitely", "certainly", "obviously", "clearly", "undoubtedly",
                "unquestionably", "indisputably", "absolutely", "surely"
            ],
            "uncertainty_markers": [
                "might", "could", "may", "perhaps", "possibly", "potentially",
                "seemingly", "apparently", "probably", "likely"
            ],
            "loaded_verbs": [
                "slam", "blast", "destroy", "obliterate", "eviscerate", "assault",
                "attack", "savage", "pummel", "hammer", "crush"
            ]
        }
        
    def process_article(self, title: str, text: str) -> ProcessedArticle:
        """Process article for bias analysis."""
        sentences = self._split_sentences(text)
        claims = self._extract_claims(sentences)
        quotes = self._extract_quotes(text)
        entities = self._extract_entities(text)
        bias_indicators = self._detect_bias_indicators(text)
        key_phrases = self._extract_key_phrases(text)
        
        return ProcessedArticle(
            title=title,
            text=text,
            sentences=sentences,
            claims=claims,
            quotes=quotes,
            entities=entities,
            bias_indicators=bias_indicators,
            key_phrases=key_phrases,
        )
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        if SPACY_AVAILABLE and self.nlp:
            doc = self.nlp(text[:10000])  # Limit for performance
            return [sent.text.strip() for sent in doc.sents if sent.text.strip()]
        
        # Fallback: regex split
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        return [s.strip() for s in sentences if len(s.strip()) > 20]
    
    def _extract_claims(self, sentences: List[str]) -> List[ExtractedClaim]:
        """Extract different types of claims from sentences."""
        claims = []
        
        for i, sentence in enumerate(sentences):
            # Factual claims with numbers/statistics
            if re.search(r'\b\d+(?:\.\d+)?(?:%|percent|million|billion|thousand)\b', sentence):
                claims.append(ExtractedClaim(
                    text=sentence,
                    claim_type="factual",
                    confidence=0.8,
                    sentence_index=i
                ))
            
            # Attribution claims
            elif re.search(r'\b(said|stated|announced|declared|claimed|argued|told|explained|confirmed)\b', sentence, re.IGNORECASE):
                claims.append(ExtractedClaim(
                    text=sentence,
                    claim_type="attribution",
                    confidence=0.7,
                    sentence_index=i
                ))
            
            # Opinion claims
            elif re.search(r'\b(believe|think|feel|opinion|view|perspective|argue|suggest)\b', sentence, re.IGNORECASE):
                claims.append(ExtractedClaim(
                    text=sentence,
                    claim_type="opinion",
                    confidence=0.9,
                    sentence_index=i
                ))
            
            # Prediction claims
            elif re.search(r'\b(will|would|could|might|expect|predict|forecast|anticipate|project)\b', sentence, re.IGNORECASE):
                claims.append(ExtractedClaim(
                    text=sentence,
                    claim_type="prediction",
                    confidence=0.6,
                    sentence_index=i
                ))
                
        return claims
    
    def _extract_quotes(self, text: str) -> List[QuoteAttribution]:
        """Extract quotes with attribution information."""
        quotes = []
        
        # Pattern for quotes with attribution
        pattern = r'"([^"]+)"\s*,?\s*([^.]*?)(?:said|stated|declared|announced|claimed|argued|told|explained)(?:\s+([^.]*?))?[.!?]'
        
        for match in re.finditer(pattern, text, re.IGNORECASE):
            quote_text = match.group(1)
            attribution = match.group(2).strip() if match.group(2) else ""
            
            # Extract speaker name
            speaker = None
            speaker_title = None
            
            if attribution:
                # Look for proper names
                name_match = re.search(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', attribution)
                if name_match:
                    speaker = name_match.group(1)
                
                # Look for titles
                title_match = re.search(
                    r'\b(President|Senator|Representative|CEO|Director|Secretary|Minister|Judge|Professor|Dr\.)\b',
                    attribution, re.IGNORECASE
                )
                if title_match:
                    speaker_title = title_match.group(1)
            
            # Determine attribution type
            if speaker:
                attribution_type = "direct"
                confidence = 0.9
            elif "sources" in attribution.lower() or "officials" in attribution.lower():
                attribution_type = "anonymous"
                confidence = 0.3
            else:
                attribution_type = "indirect"
                confidence = 0.5
            
            quotes.append(QuoteAttribution(
                quote=quote_text,
                speaker=speaker,
                speaker_title=speaker_title,
                attribution_type=attribution_type,
                confidence=confidence
            ))
            
        return quotes
    
    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities from text."""
        entities = {"PERSON": [], "ORG": [], "GPE": [], "DATE": []}
        
        if SPACY_AVAILABLE and self.nlp:
            doc = self.nlp(text[:5000])  # Limit for performance
            for ent in doc.ents:
                if ent.label_ in entities:
                    entities[ent.label_].append(ent.text)
            
            # Deduplicate
            for key in entities:
                entities[key] = list(set(entities[key]))[:10]
        else:
            # Fallback: regex for capitalized sequences
            candidates = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b', text)
            entities["PERSON"] = list(set(candidates))[:10]
            
        return entities
    
    def _detect_bias_indicators(self, text: str) -> Dict[str, List[str]]:
        """Detect bias indicator phrases in text."""
        indicators = {}
        text_lower = text.lower()
        
        for category, patterns in self.bias_patterns.items():
            found = []
            for pattern in patterns:
                # Find all occurrences
                if pattern.lower() in text_lower:
                    # Get the actual text (preserving case)
                    for match in re.finditer(re.escape(pattern), text, re.IGNORECASE):
                        found.append(text[match.start():match.end()])
            
            indicators[category] = found[:10]  # Limit to 10 per category
            
        return indicators
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases that indicate bias."""
        key_phrases = []
        
        patterns = [
            r'\b(?:critics|supporters|opponents|proponents)\s+(?:say|argue|claim|believe)\b',
            r'\b(?:according to|sources say|officials say|people familiar)\b',
            r'\b(?:devastating|alarming|shocking|outrageous)\s+\w+\b',
            r'\b(?:radical|extremist|progressive|conservative|liberal)\s+\w+\b',
            r'\b(?:slammed|blasted|destroyed|obliterated)\b',
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                phrase = match.group()
                if len(phrase) > 3:  # Skip very short matches
                    key_phrases.append(phrase)
                    
        return key_phrases[:20]  # Limit to 20 key phrases
    
    def get_bias_summary(self, processed: ProcessedArticle) -> Dict[str, Any]:
        """Generate a summary of bias indicators."""
        # Count different types of claims
        claim_counts = {}
        for claim_type in ["factual", "opinion", "attribution", "prediction"]:
            claim_counts[claim_type] = sum(1 for c in processed.claims if c.claim_type == claim_type)
        
        # Count quote types
        quote_counts = {}
        for quote_type in ["direct", "indirect", "anonymous"]:
            quote_counts[quote_type] = sum(1 for q in processed.quotes if q.attribution_type == quote_type)
        
        # Count bias indicators
        bias_indicator_counts = {cat: len(indicators) for cat, indicators in processed.bias_indicators.items()}
        
        return {
            "total_claims": len(processed.claims),
            "claim_breakdown": claim_counts,
            "total_quotes": len(processed.quotes),
            "quote_breakdown": quote_counts,
            "bias_indicators": bias_indicator_counts,
            "key_phrases_count": len(processed.key_phrases),
            "entities": {k: len(v) for k, v in processed.entities.items()},
            "sentence_count": len(processed.sentences)
        }

# Global processor instance
_processor = None

def get_text_processor() -> TextProcessor:
    """Get or create global text processor."""
    global _processor
    if _processor is None:
        _processor = TextProcessor()
    return _processor