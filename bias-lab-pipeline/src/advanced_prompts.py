"""Prompt templates for bias detection."""
from typing import Dict, List, Any
import json

# Few-shot examples with known bias patterns
FEW_SHOT_EXAMPLES = [
    {
        "title": "Biden Administration Pushes Radical Climate Agenda",
        "text": "The Biden administration continues its assault on American energy independence with sweeping new regulations that critics say will devastate the economy. Sources close to the administration admit privately that these policies prioritize ideology over practical concerns.",
        "analysis": {
            "ideological_stance": {"score": 85, "confidence": 0.9, "rationale": "Loaded language like 'radical agenda' and 'assault' clearly indicates right-leaning bias"},
            "factual_grounding": {"score": 25, "confidence": 0.8, "rationale": "Anonymous sources and unsupported claims about 'devastating' economy"},
            "framing_choices": {"score": 90, "confidence": 0.9, "rationale": "Frames policy as 'assault' rather than presenting multiple perspectives"},
            "emotional_tone": {"score": 80, "confidence": 0.85, "rationale": "Inflammatory language like 'assault' and 'devastate' designed to provoke"},
            "source_transparency": {"score": 15, "confidence": 0.9, "rationale": "Relies on anonymous 'sources close to administration' without verification"}
        }
    },
    {
        "title": "EPA Announces New Carbon Emission Standards",
        "text": "The Environmental Protection Agency released new regulations targeting carbon emissions from power plants on Tuesday. The policy aims to reduce greenhouse gas emissions by 30% by 2030, according to EPA documents. Industry representatives expressed concerns about implementation costs, while environmental groups praised the initiative.",
        "analysis": {
            "ideological_stance": {"score": 50, "confidence": 0.7, "rationale": "Neutral language presents policy without partisan framing"},
            "factual_grounding": {"score": 85, "confidence": 0.9, "rationale": "Specific numbers, official sources, and documented policy details"},
            "framing_choices": {"score": 20, "confidence": 0.8, "rationale": "Presents both policy goals and industry concerns without selective emphasis"},
            "emotional_tone": {"score": 10, "confidence": 0.9, "rationale": "Clinical, factual tone without charged language"},
            "source_transparency": {"score": 90, "confidence": 0.9, "rationale": "Clear attribution to EPA documents and identified industry groups"}
        }
    },
    {
        "title": "Corporate Polluters Escape Justice Again",
        "text": "Once again, corporate polluters have escaped meaningful accountability as the EPA's toothless new regulations fail to protect vulnerable communities. Environmental justice advocates slam these inadequate measures as a betrayal of campaign promises.",
        "analysis": {
            "ideological_stance": {"score": 15, "confidence": 0.85, "rationale": "Strong left-leaning language emphasizing corporate wrongdoing and environmental justice"},
            "factual_grounding": {"score": 30, "confidence": 0.7, "rationale": "Makes broad claims without specific evidence or data"},
            "framing_choices": {"score": 85, "confidence": 0.8, "rationale": "Frames issue entirely from environmental justice perspective"},
            "emotional_tone": {"score": 75, "confidence": 0.8, "rationale": "Emotionally charged with words like 'escape justice' and 'betrayal'"},
            "source_transparency": {"score": 40, "confidence": 0.7, "rationale": "References advocates generally without specific attribution"}
        }
    }
]

CHAIN_OF_THOUGHT_PROMPT = """You are a media analyst. Analyze this news article systematically.

## STEP 1: CONTENT ANALYSIS
First, identify the key elements:
- Main claims and assertions
- Sources cited (named vs anonymous)
- Quotes and attributions  
- Language choices and tone
- What information is emphasized vs buried
- Key statistics or data presented

## STEP 2: BIAS DETECTION PER DIMENSION

For each dimension, follow this systematic reasoning:

### IDEOLOGICAL STANCE (0=far left, 50=center, 100=far right)
- Identify partisan language and policy framing
- Look for ideological keywords and phrases
- Consider which political perspective the language favors
- Check for partisan sources or think tanks cited
- Note any one-sided presentation of political issues

### FACTUAL GROUNDING (0=speculation, 100=well-sourced)
- Count specific facts, data, and statistics
- Evaluate source credibility and verification
- Identify official documents or studies cited
- Assess speculation vs documented claims
- Check for hedging language vs confident assertions

### FRAMING CHOICES (0=balanced, 100=selective)
- Identify perspectives included vs excluded
- Note emphasis patterns (headline vs buried)
- Evaluate if multiple viewpoints are represented
- Check for context and background information
- Assess completeness of the narrative

### EMOTIONAL TONE (0=neutral, 100=inflammatory)
- Identify charged language and intensifiers
- Assess clinical/factual vs emotional/provocative language
- Look for dramatic or sensational phrasing
- Consider intended emotional impact on readers
- Check for fear-mongering or outrage-inducing language

### SOURCE TRANSPARENCY (0=anonymous, 100=named/verifiable)
- Count named vs unnamed sources
- Evaluate source specificity and credentials
- Check for "sources say" or "officials claim" patterns
- Assess if claims can be independently verified
- Look for primary source documentation

## STEP 3: EVIDENCE EXTRACTION
For each dimension, identify 2-5 exact phrases from the article that support your score.

## STEP 4: CONFIDENCE ASSESSMENT
Rate your confidence based on:
- Clarity and strength of bias indicators
- Consistency of patterns throughout the text
- Amount of evidence available for analysis

## EXAMPLES:

{examples}

## NOW ANALYZE THIS ARTICLE:

**Title:** {title}
**Text:** {text}

Follow the systematic approach above. Return your analysis as JSON with this structure:

{{
  "reasoning": {{
    "content_analysis": "Key observations about claims, sources, and presentation...",
    "ideological_stance_reasoning": "Detailed reasoning for political lean score...",
    "factual_grounding_reasoning": "Detailed reasoning for evidence quality score...",
    "framing_choices_reasoning": "Detailed reasoning for perspective balance score...", 
    "emotional_tone_reasoning": "Detailed reasoning for language intensity score...",
    "source_transparency_reasoning": "Detailed reasoning for attribution clarity score..."
  }},
  "dimensions": [
    {{
      "dimension": "ideological_stance",
      "score": 0-100,
      "confidence": 0.0-1.0,
      "rationale": "Brief explanation",
      "highlighted_phrases": ["exact phrase 1", "exact phrase 2"]
    }},
    // ... other dimensions
  ],
  "overall_confidence": 0.0-1.0
}}"""

MULTI_PERSPECTIVE_PROMPT = """Analyze this article from multiple analytical perspectives to ensure comprehensive bias detection.

## PERSPECTIVE 1: LINGUISTIC ANALYSIS
Examine word choice, sentence structure, and rhetorical devices:
- Active vs passive voice usage
- Nominalization and abstraction
- Metaphors and analogies used
- Presuppositions and implications

## PERSPECTIVE 2: NARRATIVE STRUCTURE
Analyze how the story is constructed:
- Lead paragraph framing
- Information hierarchy
- Causal relationships implied
- Timeline presentation

## PERSPECTIVE 3: SOURCE ANALYSIS
Evaluate the sources and evidence:
- Diversity of sources
- Authority and expertise
- Potential conflicts of interest
- Balance of perspectives

## PERSPECTIVE 4: CONTEXTUAL COMPLETENESS
Assess what's included and excluded:
- Historical context provided
- Alternative explanations considered
- Counterarguments addressed
- Relevant statistics included

Article:
Title: {title}
Text: {text}

Synthesize insights from all perspectives into bias scores."""

ENSEMBLE_PROMPTS = {
    "chain_of_thought": CHAIN_OF_THOUGHT_PROMPT,
    "multi_perspective": MULTI_PERSPECTIVE_PROMPT,
}

def format_chain_of_thought_prompt(title: str, text: str, include_examples: bool = True) -> str:
    """Format the chain-of-thought prompt with examples."""
    examples_text = ""
    
    if include_examples:
        for i, ex in enumerate(FEW_SHOT_EXAMPLES[:2], 1):
            examples_text += f"\n### Example {i}:\n"
            examples_text += f"**Title:** {ex['title']}\n"
            examples_text += f"**Text:** {ex['text']}\n"
            examples_text += f"**Analysis:**\n```json\n{json.dumps(ex['analysis'], indent=2)}\n```\n"
    
    return CHAIN_OF_THOUGHT_PROMPT.format(
        title=title,
        text=text[:3000],  # Limit text length for token management
        examples=examples_text
    )

def format_multi_perspective_prompt(title: str, text: str) -> str:
    """Format the multi-perspective analysis prompt."""
    return MULTI_PERSPECTIVE_PROMPT.format(
        title=title,
        text=text[:3000]
    )

def get_best_prompt_for_article(title: str, text: str, strategy: str = "chain_of_thought") -> str:
    """Get prompt based on article characteristics."""
    
    # Analyze article characteristics
    text_length = len(text)
    has_quotes = '"' in text
    has_numbers = any(char.isdigit() for char in text)
    
    # Choose strategy based on article type
    if text_length < 500:
        # Short articles benefit from examples
        return format_chain_of_thought_prompt(title, text, include_examples=True)
    elif has_quotes and has_numbers:
        # Data-rich articles benefit from systematic analysis
        return format_chain_of_thought_prompt(title, text, include_examples=False)
    else:
        # Opinion pieces benefit from multi-perspective analysis
        return format_multi_perspective_prompt(title, text)

def create_validation_prompt(title: str, text: str, initial_scores: Dict) -> str:
    """Create a prompt to validate and refine initial bias scores."""
    return f"""Review and validate these bias scores for accuracy:

Article: {title}
Initial Scores: {json.dumps(initial_scores, indent=2)}

For each score, determine if it accurately reflects the article's bias. 
If not, provide a corrected score with justification.
Focus on:
1. Internal consistency between dimensions
2. Whether evidence supports the scores
3. Any missed bias indicators

Return refined scores in the same JSON format."""
