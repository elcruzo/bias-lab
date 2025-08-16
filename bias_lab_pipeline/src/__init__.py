"""The Bias Lab - Media bias detection pipeline components."""

from .config import Config
from .news_fetcher import NewsFetcher
from .bias_scorer import BiasScorer
from .cfa_engine import CFA_Engine
from .narrative_graph import NarrativeGraph
from .ensemble_scorer import EnsembleScorer, HeuristicScorer
from .conformal_prediction import ConformalPredictor
from .transparency_scorer import TransparencyScorer, get_transparency_scorer
from .claim_extraction import (
    TextProcessor,
    get_text_processor,
    ExtractedClaim,
    QuoteAttribution,
    ProcessedArticle
)
from .advanced_prompts import (
    get_best_prompt_for_article,
    format_chain_of_thought_prompt,
    format_multi_perspective_prompt
)

__all__ = [
    'Config',
    'NewsFetcher',
    'BiasScorer',
    'CFA_Engine',
    'NarrativeGraph',
    'EnsembleScorer',
    'HeuristicScorer',
    'ConformalPredictor',
    'TransparencyScorer',
    'get_transparency_scorer',
    'TextProcessor',
    'get_text_processor',
    'ExtractedClaim',
    'QuoteAttribution',
    'ProcessedArticle',
    'get_best_prompt_for_article',
    'format_chain_of_thought_prompt',
    'format_multi_perspective_prompt'
]

__version__ = '1.0.0'
