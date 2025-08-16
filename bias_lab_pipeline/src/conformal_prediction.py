"""Conformal prediction for confidence intervals."""
import numpy as np
from typing import Dict, List, Tuple, Optional
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

class ConformalPredictor:
    """
    Implements conformal prediction for bias score confidence intervals.
    """
    
    def __init__(self, alpha: float = 0.1):
        """
        Initialize conformal predictor.
        
        Args:
            alpha: Significance level (0.1 for 90% confidence intervals)
        """
        self.alpha = alpha
        self.calibration_scores = []
        self.nonconformity_scores = []
        self.ridge_model = Ridge(alpha=1.0)
        self.scaler = StandardScaler()
        self.is_calibrated = False
        
    def extract_features(self, article: Dict, scores: Dict) -> np.ndarray:
        """
        Extract features for nonconformity prediction.
        Simple features based on article metadata and score patterns.
        """
        features = []
        
        # Text length feature
        text = article.get('full_text', '')
        features.append(len(text.split()))
        
        # Source reliability proxy (simplified)
        trusted_sources = ['Reuters', 'AP', 'BBC', 'Bloomberg']
        features.append(1.0 if article.get('source') in trusted_sources else 0.0)
        
        # Score variance across dimensions
        dimension_scores = [scores['scores'][dim] for dim in scores['scores']]
        features.append(np.std(dimension_scores))
        
        # Extreme score indicator
        features.append(1.0 if any(s < 20 or s > 80 for s in dimension_scores) else 0.0)
        
        # Average score
        features.append(np.mean(dimension_scores))
        
        # Max deviation from center
        features.append(max(abs(s - 50) for s in dimension_scores))
        
        return np.array(features)
    
    def calibrate(self, calibration_articles: List[Dict], calibration_scores: List[Dict]):
        """
        Calibrate the conformal predictor on a calibration set.
        
        Args:
            calibration_articles: List of articles used for calibration
            calibration_scores: Corresponding bias scores
        """
        if len(calibration_articles) < 5:
            print("Warning: Too few calibration samples. Using default intervals.")
            return
        
        # Extract features
        X = np.array([self.extract_features(art, score) 
                     for art, score in zip(calibration_articles, calibration_scores)])
        
        # Normalize features
        X = self.scaler.fit_transform(X)
        
        # For each dimension, compute nonconformity scores
        dimensions = ['ideological_stance', 'factual_grounding', 'framing_choices',
                     'emotional_tone', 'source_transparency']
        
        for dim in dimensions:
            y = np.array([score['scores'][dim] for score in calibration_scores])
            
            # Fit ridge regression for this dimension
            self.ridge_model.fit(X, y)
            y_pred = self.ridge_model.predict(X)
            
            # Compute nonconformity scores (absolute residuals)
            nonconformity = np.abs(y - y_pred)
            self.nonconformity_scores.extend(nonconformity)
        
        self.is_calibrated = True
        
    def get_quantile(self, q: float) -> float:
        """
        Get the q-th quantile of nonconformity scores.
        """
        if not self.nonconformity_scores:
            # Default conservative interval if not calibrated
            return 15.0
        
        return np.quantile(self.nonconformity_scores, q)
    
    def predict_interval(self, article: Dict, scores: Dict) -> Dict[str, Tuple[float, float]]:
        """
        Predict confidence intervals for each dimension.
        
        Returns:
            Dictionary mapping dimension -> (lower_bound, upper_bound)
        """
        intervals = {}
        
        if not self.is_calibrated:
            # Use default intervals based on ensemble variance
            default_width = 10.0
            for dim in scores['scores']:
                score = scores['scores'][dim]
                intervals[dim] = (
                    max(0, score - default_width),
                    min(100, score + default_width)
                )
        else:
            # Use calibrated conformal intervals
            quantile = self.get_quantile(1 - self.alpha)
            
            # Extract features for this article
            features = self.extract_features(article, scores)
            features = self.scaler.transform([features])[0]
            
            # Predict nonconformity for this article
            # Simplified: use average quantile for all dimensions
            for dim in scores['scores']:
                score = scores['scores'][dim]
                intervals[dim] = (
                    max(0, score - quantile),
                    min(100, score + quantile)
                )
        
        return intervals
    
    def compute_prediction_confidence(self, scores: Dict, intervals: Dict) -> float:
        """
        Compute overall confidence based on interval width and score consistency.
        """
        # Average interval width
        avg_width = np.mean([
            intervals[dim][1] - intervals[dim][0] 
            for dim in intervals
        ])
        
        # Score variance
        score_values = [scores['scores'][dim] for dim in scores['scores']]
        score_variance = np.std(score_values)
        
        # Confidence decreases with wider intervals and higher variance
        confidence = max(0.3, min(0.95, 1.0 - (avg_width / 100) - (score_variance / 200)))
        
        return confidence
    
    def add_conformal_bands(self, article: Dict, scores: Dict) -> Dict:
        """
        Add conformal prediction bands to scoring results.
        """
        # Compute intervals
        intervals = self.predict_interval(article, scores)
        
        # Compute overall confidence
        confidence = self.compute_prediction_confidence(scores, intervals)
        
        # Add to scores
        scores['confidence_bands'] = intervals
        scores['conformal_confidence'] = confidence
        
        # Update confidence interval with conformal prediction
        scores['confidence_interval'] = {
            'lower': confidence - 0.05,
            'upper': confidence + 0.05,
            'confidence': confidence,
            'method': 'conformal_prediction' if self.is_calibrated else 'default'
        }
        
        return scores
    
    def batch_add_conformal_bands(self, articles: List[Dict], scores_list: List[Dict]) -> List[Dict]:
        """
        Add conformal bands to multiple articles.
        
        Uses first half for calibration if not already calibrated.
        """
        if not self.is_calibrated and len(articles) > 10:
            # Use first half for calibration
            split_idx = len(articles) // 2
            self.calibrate(articles[:split_idx], scores_list[:split_idx])
        
        # Add bands to all articles
        results = []
        for article, scores in zip(articles, scores_list):
            results.append(self.add_conformal_bands(article, scores))
        
        return results
