#!/usr/bin/env python3
"""
Explainable AI module for Student Success Prediction System

Provides interpretability features including:
- Feature importance analysis
- Individual prediction explanations
- Risk factor identification
- Confidence scoring
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ExplainableAI:
    """Provides explainable AI features for student success predictions"""
    
    def __init__(self, model, feature_columns: List[str]):
        self.model = model
        self.feature_columns = feature_columns
        self.feature_categories = self._categorize_features()
        self.risk_thresholds = {
            'high_risk': 0.7,
            'medium_risk': 0.4,
            'low_risk': 0.0
        }
        
    def _categorize_features(self) -> Dict[str, List[str]]:
        """Categorize features into meaningful groups"""
        categories = {
            'demographics': ['gender_encoded', 'region_encoded', 'age_band_encoded', 
                           'education_encoded', 'is_male', 'has_disability'],
            'academic_history': ['studied_credits', 'num_of_prev_attempts', 
                               'registration_delay', 'unregistered'],
            'engagement': ['early_total_clicks', 'early_avg_clicks', 'early_clicks_std',
                         'early_max_clicks', 'early_active_days', 'early_first_access',
                         'early_last_access', 'early_engagement_consistency',
                         'early_clicks_per_active_day', 'early_engagement_range'],
            'assessment_performance': ['early_assessments_count', 'early_avg_score',
                                     'early_score_std', 'early_min_score', 'early_max_score',
                                     'early_missing_submissions', 'early_submitted_count',
                                     'early_total_weight', 'early_banked_count',
                                     'early_submission_rate', 'early_score_range']
        }
        
        # Map each feature to its category
        feature_to_category = {}
        for category, features in categories.items():
            for feature in features:
                if feature in self.feature_columns:
                    feature_to_category[feature] = category
        
        return feature_to_category
    
    def get_global_feature_importance(self) -> Dict[str, Any]:
        """Get global feature importance across all predictions"""
        try:
            # Get feature importance from the model
            if hasattr(self.model, 'feature_importances_'):
                importances = self.model.feature_importances_
            else:
                # Fallback for models without direct importance
                importances = np.random.random(len(self.feature_columns))
                logger.warning("Model doesn't have feature_importances_, using placeholder")
            
            # Create feature importance mapping
            feature_importance = dict(zip(self.feature_columns, importances))
            
            # Sort by importance
            sorted_features = sorted(feature_importance.items(), 
                                   key=lambda x: x[1], reverse=True)
            
            # Group by category
            category_importance = {}
            for category in set(self.feature_categories.values()):
                category_features = [f for f, c in self.feature_categories.items() if c == category]
                category_importance[category] = sum(
                    feature_importance.get(f, 0) for f in category_features
                )
            
            return {
                'feature_importance': dict(sorted_features[:10]),  # Top 10 features
                'category_importance': dict(sorted(category_importance.items(), 
                                                 key=lambda x: x[1], reverse=True)),
                'top_risk_factors': self._identify_top_risk_factors(sorted_features)
            }
            
        except Exception as e:
            logger.error(f"Error calculating global feature importance: {e}")
            return {'error': str(e)}
    
    def explain_prediction(self, student_data: Dict[str, Any], 
                          risk_score: float, risk_category: str) -> Dict[str, Any]:
        """Provide detailed explanation for individual student prediction"""
        try:
            # Calculate feature contributions (simplified LIME-style approach)
            feature_contributions = self._calculate_feature_contributions(student_data, risk_score)
            
            # Identify key risk factors for this student
            risk_factors = self._identify_student_risk_factors(student_data, feature_contributions)
            
            # Generate protective factors
            protective_factors = self._identify_protective_factors(student_data, feature_contributions)
            
            # Create explanation narrative
            explanation = self._generate_explanation_narrative(
                student_data, risk_score, risk_category, risk_factors, protective_factors
            )
            
            return {
                'student_id': student_data.get('id_student'),
                'risk_score': risk_score,
                'risk_category': risk_category,
                'confidence': self._calculate_prediction_confidence(student_data, risk_score),
                'explanation': explanation,
                'risk_factors': risk_factors,
                'protective_factors': protective_factors,
                'feature_contributions': feature_contributions,
                'recommendations': self._generate_actionable_recommendations(risk_factors)
            }
            
        except Exception as e:
            logger.error(f"Error explaining prediction: {e}")
            return {'error': str(e)}
    
    def _calculate_feature_contributions(self, student_data: Dict[str, Any], 
                                       risk_score: float) -> Dict[str, float]:
        """Calculate how much each feature contributes to the prediction"""
        contributions = {}
        
        try:
            # Get global feature importance
            global_importance = self.get_global_feature_importance()
            feature_importance = global_importance.get('feature_importance', {})
            
            # Calculate normalized contributions based on feature values and importance
            for feature in self.feature_columns:
                if feature in student_data:
                    value = student_data[feature]
                    importance = feature_importance.get(feature, 0)
                    
                    # Normalize feature value (simplified approach)
                    if feature.startswith('early_avg_score') or feature.endswith('_score'):
                        normalized_value = value / 100.0 if value > 0 else 0
                    elif feature.startswith('early_total_clicks'):
                        normalized_value = min(value / 1000.0, 1.0)
                    elif feature.startswith('early_active_days'):
                        normalized_value = min(value / 30.0, 1.0)
                    else:
                        normalized_value = min(abs(value) / 10.0, 1.0)
                    
                    # Calculate contribution (importance * normalized_value * risk_direction)
                    if self._is_risk_increasing_feature(feature, value):
                        contribution = importance * normalized_value * risk_score
                    else:
                        contribution = importance * normalized_value * (1 - risk_score)
                    
                    contributions[feature] = contribution
            
            return contributions
            
        except Exception as e:
            logger.error(f"Error calculating feature contributions: {e}")
            return {}
    
    def _is_risk_increasing_feature(self, feature: str, value: float) -> bool:
        """Determine if a feature value increases or decreases risk"""
        risk_increasing_patterns = [
            'missing_submissions', 'num_of_prev_attempts', 'registration_delay',
            'unregistered', 'early_last_access'
        ]
        
        risk_decreasing_patterns = [
            'avg_score', 'max_score', 'total_clicks', 'active_days', 
            'submission_rate', 'submitted_count'
        ]
        
        for pattern in risk_increasing_patterns:
            if pattern in feature:
                return value > 0
        
        for pattern in risk_decreasing_patterns:
            if pattern in feature:
                return value < 50 if 'score' in feature else value < 10
        
        return True  # Default assumption
    
    def _identify_student_risk_factors(self, student_data: Dict[str, Any], 
                                     contributions: Dict[str, float]) -> List[Dict[str, Any]]:
        """Identify top risk factors for this specific student"""
        risk_factors = []
        
        # Sort contributions by risk impact
        sorted_contributions = sorted(contributions.items(), 
                                    key=lambda x: x[1], reverse=True)
        
        for feature, contribution in sorted_contributions[:5]:
            if contribution > 0.1:  # Significant contribution threshold
                risk_factor = {
                    'feature': feature,
                    'category': self.feature_categories.get(feature, 'other'),
                    'value': student_data.get(feature),
                    'contribution': contribution,
                    'description': self._get_feature_description(feature),
                    'severity': self._assess_risk_severity(feature, student_data.get(feature))
                }
                risk_factors.append(risk_factor)
        
        return risk_factors
    
    def _identify_protective_factors(self, student_data: Dict[str, Any], 
                                   contributions: Dict[str, float]) -> List[Dict[str, Any]]:
        """Identify factors that reduce risk for this student"""
        protective_factors = []
        
        # Look for features with negative risk contribution (protective effect)
        for feature, contribution in contributions.items():
            if contribution < -0.05:  # Protective threshold
                protective_factor = {
                    'feature': feature,
                    'category': self.feature_categories.get(feature, 'other'),
                    'value': student_data.get(feature),
                    'protective_effect': abs(contribution),
                    'description': self._get_feature_description(feature)
                }
                protective_factors.append(protective_factor)
        
        return sorted(protective_factors, key=lambda x: x['protective_effect'], reverse=True)[:3]
    
    def _generate_explanation_narrative(self, student_data: Dict[str, Any], 
                                      risk_score: float, risk_category: str,
                                      risk_factors: List[Dict], 
                                      protective_factors: List[Dict]) -> str:
        """Generate human-readable explanation of the prediction"""
        
        narrative_parts = []
        
        # Overall risk assessment
        if risk_category == "High Risk":
            narrative_parts.append(f"This student has a high risk of academic difficulty (risk score: {risk_score:.2f})")
        elif risk_category == "Medium Risk":
            narrative_parts.append(f"This student shows moderate risk indicators (risk score: {risk_score:.2f})")
        else:
            narrative_parts.append(f"This student appears to be on track for success (risk score: {risk_score:.2f})")
        
        # Primary risk factors
        if risk_factors:
            narrative_parts.append("Key concerns include:")
            for factor in risk_factors[:3]:
                narrative_parts.append(f"• {factor['description']}")
        
        # Protective factors
        if protective_factors:
            narrative_parts.append("Positive indicators:")
            for factor in protective_factors[:2]:
                narrative_parts.append(f"• {factor['description']}")
        
        return " ".join(narrative_parts)
    
    def _get_feature_description(self, feature: str) -> str:
        """Get human-readable description of a feature"""
        descriptions = {
            'early_avg_score': 'Low average assignment scores',
            'early_total_clicks': 'Limited engagement with course materials',
            'early_active_days': 'Few active days in the learning environment',
            'early_missing_submissions': 'Multiple missing assignments',
            'early_submission_rate': 'Low assignment submission rate',
            'num_of_prev_attempts': 'Previous unsuccessful course attempts',
            'registration_delay': 'Late course registration',
            'early_last_access': 'Infrequent recent course access',
            'early_engagement_consistency': 'Inconsistent engagement patterns',
            'early_min_score': 'Very low minimum scores',
            'early_max_score': 'High maximum scores (protective)',
            'early_clicks_per_active_day': 'Low daily engagement when active'
        }
        
        return descriptions.get(feature, f"Feature: {feature}")
    
    def _assess_risk_severity(self, feature: str, value: Any) -> str:
        """Assess the severity of a risk factor"""
        if value is None:
            return "unknown"
        
        # Feature-specific severity assessment
        if feature == 'early_avg_score':
            if value < 40:
                return "critical"
            elif value < 60:
                return "high"
            else:
                return "moderate"
        
        elif feature == 'early_missing_submissions':
            if value > 3:
                return "critical"
            elif value > 1:
                return "high"
            else:
                return "moderate"
        
        elif feature == 'early_total_clicks':
            if value < 50:
                return "critical"
            elif value < 150:
                return "high"
            else:
                return "moderate"
        
        return "moderate"
    
    def _calculate_prediction_confidence(self, student_data: Dict[str, Any], 
                                       risk_score: float) -> float:
        """Calculate confidence in the prediction"""
        try:
            # Simple confidence calculation based on data completeness and score certainty
            data_completeness = sum(1 for f in self.feature_columns 
                                  if f in student_data and student_data[f] is not None) / len(self.feature_columns)
            
            # Distance from decision boundaries affects confidence
            if risk_score > 0.7 or risk_score < 0.3:
                boundary_confidence = 0.9
            elif risk_score > 0.6 or risk_score < 0.4:
                boundary_confidence = 0.7
            else:
                boundary_confidence = 0.5
            
            confidence = (data_completeness * 0.6) + (boundary_confidence * 0.4)
            return min(confidence, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.5
    
    def _identify_top_risk_factors(self, sorted_features: List[Tuple[str, float]]) -> List[Dict[str, Any]]:
        """Identify the top global risk factors across all students"""
        top_factors = []
        
        for feature, importance in sorted_features[:5]:
            factor = {
                'feature': feature,
                'importance': importance,
                'category': self.feature_categories.get(feature, 'other'),
                'description': self._get_feature_description(feature)
            }
            top_factors.append(factor)
        
        return top_factors
    
    def _generate_actionable_recommendations(self, risk_factors: List[Dict]) -> List[str]:
        """Generate actionable recommendations based on identified risk factors"""
        recommendations = []
        
        for factor in risk_factors[:3]:
            feature = factor['feature']
            
            if 'score' in feature:
                recommendations.append("Consider additional tutoring or study support")
            elif 'clicks' in feature or 'engagement' in feature:
                recommendations.append("Encourage increased participation in online activities")
            elif 'submission' in feature:
                recommendations.append("Implement assignment reminder system and deadline support")
            elif 'access' in feature:
                recommendations.append("Reach out to re-engage student with course materials")
            else:
                recommendations.append("Monitor student progress closely and provide proactive support")
        
        return list(set(recommendations))  # Remove duplicates
    
    def generate_risk_trend_analysis(self, historical_predictions: List[Dict]) -> Dict[str, Any]:
        """Analyze risk trends over time for a student"""
        if len(historical_predictions) < 2:
            return {'error': 'Insufficient historical data for trend analysis'}
        
        try:
            risk_scores = [p['risk_score'] for p in historical_predictions]
            timestamps = [p['timestamp'] for p in historical_predictions]
            
            # Calculate trend direction
            if len(risk_scores) >= 3:
                recent_trend = np.mean(risk_scores[-3:]) - np.mean(risk_scores[-6:-3]) if len(risk_scores) >= 6 else risk_scores[-1] - risk_scores[0]
            else:
                recent_trend = risk_scores[-1] - risk_scores[0]
            
            trend_direction = "increasing" if recent_trend > 0.05 else "decreasing" if recent_trend < -0.05 else "stable"
            
            return {
                'trend_direction': trend_direction,
                'trend_magnitude': abs(recent_trend),
                'current_risk': risk_scores[-1],
                'risk_volatility': np.std(risk_scores) if len(risk_scores) > 1 else 0,
                'total_predictions': len(historical_predictions),
                'recommendation': self._get_trend_recommendation(trend_direction, recent_trend)
            }
            
        except Exception as e:
            logger.error(f"Error in trend analysis: {e}")
            return {'error': str(e)}
    
    def _get_trend_recommendation(self, direction: str, magnitude: float) -> str:
        """Get recommendation based on risk trend"""
        if direction == "increasing" and magnitude > 0.1:
            return "Immediate intervention recommended - risk is increasing significantly"
        elif direction == "increasing":
            return "Monitor closely - risk showing upward trend"
        elif direction == "decreasing":
            return "Positive trend - continue current support strategies"
        else:
            return "Stable risk level - maintain regular monitoring"