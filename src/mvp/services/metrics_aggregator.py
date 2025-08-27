#!/usr/bin/env python3
"""
Metrics Aggregation Service

Collects and formats comprehensive student metrics from database
for GPT-OSS analysis, including risk scores, interventions, academic performance,
and peer context data.
"""

import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text, desc, and_, func

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.mvp.models import Student, Prediction, Intervention, Institution, AuditLog
from src.mvp.database import get_db_session
from src.mvp.logging_config import get_logger

logger = get_logger(__name__)

class MetricsAggregator:
    """Service for aggregating comprehensive student metrics for AI analysis."""
    
    def __init__(self):
        """Initialize metrics aggregator."""
        self.session_factory = get_db_session
        
    def get_comprehensive_student_data(self, student_id: int, 
                                     institution_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Aggregate all available data for a student.
        
        Args:
            student_id: Database ID of the student
            institution_id: Optional institution filter
            
        Returns:
            Comprehensive student data dictionary
        """
        try:
            with self.session_factory() as db:
                # Get student record
                query = db.query(Student).filter(Student.id == student_id)
                if institution_id:
                    query = query.filter(Student.institution_id == institution_id)
                
                student = query.first()
                if not student:
                    return {"error": f"Student {student_id} not found"}
                
                # Build comprehensive profile
                profile = {
                    "student_info": self._get_student_demographics(student),
                    "academic_performance": self._get_academic_metrics(db, student_id),
                    "risk_assessment": self._get_latest_risk_assessment(db, student_id),
                    "intervention_history": self._get_intervention_history(db, student_id),
                    "engagement_metrics": self._get_engagement_metrics(db, student_id),
                    "peer_context": self._get_peer_context(db, student),
                    "temporal_trends": self._get_temporal_trends(db, student_id),
                    "support_factors": self._get_support_factors(db, student_id)
                }
                
                return profile
                
        except Exception as e:
            logger.error(f"❌ Error aggregating student data: {str(e)}")
            return {"error": f"Data aggregation failed: {str(e)}"}
    
    def _get_student_demographics(self, student: Student) -> Dict[str, Any]:
        """Extract student demographic information (FERPA-compliant)."""
        return {
            "grade_level": student.grade_level,
            "enrollment_status": student.enrollment_status,
            "enrollment_duration_months": self._calculate_enrollment_duration(student),
            "special_populations": {
                "is_ell": student.is_ell,
                "has_iep": student.has_iep,
                "has_504": student.has_504,
                "economically_disadvantaged": student.is_economically_disadvantaged
            },
            "anonymized_id": f"student_{student.id}"  # For GPT analysis
        }
    
    def _calculate_enrollment_duration(self, student: Student) -> Optional[int]:
        """Calculate months enrolled."""
        if student.enrollment_date:
            end_date = student.graduation_date or datetime.now()
            delta = end_date - student.enrollment_date
            return int(delta.days / 30)  # Approximate months
        return None
    
    def _get_academic_metrics(self, db: Session, student_id: int) -> Dict[str, Any]:
        """Get academic performance metrics from predictions."""
        try:
            # Get latest prediction
            latest_prediction = db.query(Prediction).filter(
                Prediction.student_id == student_id
            ).order_by(desc(Prediction.prediction_date)).first()
            
            if not latest_prediction:
                return {"no_predictions": True}
            
            # Extract features if available
            features = {}
            if latest_prediction.features_used:
                import json
                try:
                    features = json.loads(latest_prediction.features_used)
                except:
                    pass
            
            return {
                "current_risk_score": latest_prediction.risk_score,
                "risk_category": latest_prediction.risk_category,
                "success_probability": latest_prediction.success_probability,
                "confidence_score": latest_prediction.confidence_score,
                "model_version": latest_prediction.model_version,
                "prediction_date": latest_prediction.prediction_date.isoformat() if latest_prediction.prediction_date else None,
                "academic_features": self._extract_academic_features(features)
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting academic metrics: {str(e)}")
            return {"error": "Academic metrics unavailable"}
    
    def _extract_academic_features(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Extract academic-related features from prediction features."""
        academic_keys = [
            'gpa', 'current_gpa', 'attendance_rate', 'assignment_completion',
            'course_failures', 'grade_level', 'math_performance', 'reading_performance',
            'homework_quality', 'study_skills_rating'
        ]
        
        academic_features = {}
        for key in academic_keys:
            if key in features:
                academic_features[key] = features[key]
        
        return academic_features
    
    def _get_latest_risk_assessment(self, db: Session, student_id: int) -> Dict[str, Any]:
        """Get the most recent risk assessment details."""
        try:
            latest_prediction = db.query(Prediction).filter(
                Prediction.student_id == student_id
            ).order_by(desc(Prediction.prediction_date)).first()
            
            if not latest_prediction:
                return {"no_assessment": True}
            
            # Parse explanation data if available
            risk_factors = []
            protective_factors = []
            
            if latest_prediction.risk_factors:
                try:
                    import json
                    risk_factors = json.loads(latest_prediction.risk_factors)
                except:
                    pass
            
            if latest_prediction.protective_factors:
                try:
                    import json
                    protective_factors = json.loads(latest_prediction.protective_factors)
                except:
                    pass
            
            return {
                "risk_score": latest_prediction.risk_score,
                "risk_category": latest_prediction.risk_category,
                "risk_factors": risk_factors,
                "protective_factors": protective_factors,
                "assessment_date": latest_prediction.prediction_date.isoformat() if latest_prediction.prediction_date else None,
                "explanation": latest_prediction.explanation
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting risk assessment: {str(e)}")
            return {"error": "Risk assessment unavailable"}
    
    def _get_intervention_history(self, db: Session, student_id: int) -> List[Dict[str, Any]]:
        """Get student's intervention history with outcomes."""
        try:
            interventions = db.query(Intervention).filter(
                Intervention.student_id == student_id
            ).order_by(desc(Intervention.created_at)).limit(10).all()
            
            history = []
            for intervention in interventions:
                history.append({
                    "type": intervention.intervention_type,
                    "title": intervention.title,
                    "priority": intervention.priority,
                    "status": intervention.status,
                    "outcome": intervention.outcome,
                    "created_date": intervention.created_at.isoformat() if intervention.created_at else None,
                    "completed_date": intervention.completed_date.isoformat() if intervention.completed_date else None,
                    "time_spent_minutes": intervention.time_spent_minutes,
                    "follow_up_needed": intervention.follow_up_needed,
                    "assigned_to": intervention.assigned_to
                })
            
            return history
            
        except Exception as e:
            logger.error(f"❌ Error getting intervention history: {str(e)}")
            return []
    
    def _get_engagement_metrics(self, db: Session, student_id: int) -> Dict[str, Any]:
        """Calculate engagement metrics from intervention and prediction data."""
        try:
            # Count interventions by type and outcome
            intervention_stats = db.query(
                Intervention.intervention_type,
                Intervention.outcome,
                func.count(Intervention.id).label('count')
            ).filter(
                Intervention.student_id == student_id
            ).group_by(Intervention.intervention_type, Intervention.outcome).all()
            
            engagement_summary = {
                "total_interventions": len(intervention_stats),
                "successful_interventions": sum(1 for stat in intervention_stats if stat.outcome == 'successful'),
                "intervention_types": list(set(stat.intervention_type for stat in intervention_stats)),
                "response_rate": 0.0
            }
            
            # Calculate response rate
            total = len(intervention_stats)
            successful = engagement_summary["successful_interventions"]
            if total > 0:
                engagement_summary["response_rate"] = successful / total
            
            return engagement_summary
            
        except Exception as e:
            logger.error(f"❌ Error getting engagement metrics: {str(e)}")
            return {"error": "Engagement metrics unavailable"}
    
    def _get_peer_context(self, db: Session, student: Student) -> Dict[str, Any]:
        """Get peer comparison context for same grade level and institution."""
        try:
            # Get grade-level statistics
            grade_stats = db.query(
                func.avg(Prediction.risk_score).label('avg_risk_score'),
                func.count(distinct(Prediction.student_id)).label('total_students')
            ).join(Student).filter(
                and_(
                    Student.institution_id == student.institution_id,
                    Student.grade_level == student.grade_level,
                    Student.enrollment_status == 'active'
                )
            ).first()
            
            # Calculate percentile rank for student
            student_risk = db.query(Prediction.risk_score).filter(
                Prediction.student_id == student.id
            ).order_by(desc(Prediction.prediction_date)).first()
            
            percentile_rank = None
            if student_risk and student_risk[0] is not None:
                # Count students with lower risk scores
                lower_risk_count = db.query(func.count(distinct(Prediction.student_id))).join(Student).filter(
                    and_(
                        Student.institution_id == student.institution_id,
                        Student.grade_level == student.grade_level,
                        Student.enrollment_status == 'active',
                        Prediction.risk_score < student_risk[0]
                    )
                ).scalar()
                
                if grade_stats.total_students and grade_stats.total_students > 0:
                    percentile_rank = (lower_risk_count / grade_stats.total_students) * 100
            
            return {
                "grade_level": student.grade_level,
                "institution_peer_count": grade_stats.total_students or 0,
                "grade_average_risk_score": float(grade_stats.avg_risk_score) if grade_stats.avg_risk_score else None,
                "student_percentile_rank": round(percentile_rank, 1) if percentile_rank is not None else None,
                "comparison_context": self._generate_peer_comparison_text(percentile_rank)
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting peer context: {str(e)}")
            return {"error": "Peer context unavailable"}
    
    def _generate_peer_comparison_text(self, percentile_rank: Optional[float]) -> str:
        """Generate human-readable peer comparison context."""
        if percentile_rank is None:
            return "Insufficient peer data for comparison"
        
        if percentile_rank >= 75:
            return f"Student performs better than {percentile_rank:.0f}% of grade-level peers"
        elif percentile_rank >= 50:
            return f"Student performs above average compared to grade-level peers"
        elif percentile_rank >= 25:
            return f"Student performs below average compared to grade-level peers"
        else:
            return f"Student requires significant support compared to grade-level peers"
    
    def _get_temporal_trends(self, db: Session, student_id: int) -> Dict[str, Any]:
        """Analyze trends in risk scores and interventions over time."""
        try:
            # Get predictions over last 6 months
            six_months_ago = datetime.now() - timedelta(days=180)
            predictions = db.query(Prediction).filter(
                and_(
                    Prediction.student_id == student_id,
                    Prediction.prediction_date >= six_months_ago
                )
            ).order_by(Prediction.prediction_date).all()
            
            if len(predictions) < 2:
                return {"insufficient_data": True}
            
            # Calculate trend
            risk_scores = [p.risk_score for p in predictions if p.risk_score is not None]
            dates = [p.prediction_date for p in predictions if p.risk_score is not None]
            
            trend_analysis = {
                "data_points": len(risk_scores),
                "date_range_months": (dates[-1] - dates[0]).days / 30 if len(dates) > 1 else 0,
                "initial_risk_score": risk_scores[0] if risk_scores else None,
                "latest_risk_score": risk_scores[-1] if risk_scores else None,
                "risk_score_change": None,
                "trend_direction": "stable"
            }
            
            if len(risk_scores) >= 2:
                change = risk_scores[-1] - risk_scores[0]
                trend_analysis["risk_score_change"] = change
                
                if abs(change) < 0.1:
                    trend_analysis["trend_direction"] = "stable"
                elif change > 0:
                    trend_analysis["trend_direction"] = "increasing_risk"
                else:
                    trend_analysis["trend_direction"] = "improving"
            
            return trend_analysis
            
        except Exception as e:
            logger.error(f"❌ Error getting temporal trends: {str(e)}")
            return {"error": "Temporal analysis unavailable"}
    
    def _get_support_factors(self, db: Session, student_id: int) -> Dict[str, Any]:
        """Identify support factors and resources available to student."""
        try:
            # Analyze successful interventions
            successful_interventions = db.query(Intervention).filter(
                and_(
                    Intervention.student_id == student_id,
                    Intervention.outcome == 'successful'
                )
            ).all()
            
            # Identify what works for this student
            effective_strategies = {}
            for intervention in successful_interventions:
                strategy = intervention.intervention_type
                if strategy in effective_strategies:
                    effective_strategies[strategy] += 1
                else:
                    effective_strategies[strategy] = 1
            
            # Sort by effectiveness
            effective_strategies = dict(sorted(effective_strategies.items(), 
                                             key=lambda x: x[1], reverse=True))
            
            return {
                "successful_intervention_count": len(successful_interventions),
                "most_effective_strategies": list(effective_strategies.keys())[:3],
                "strategy_success_rates": effective_strategies,
                "has_consistent_support": len(effective_strategies) > 0,
                "support_recommendation": self._generate_support_recommendation(effective_strategies)
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting support factors: {str(e)}")
            return {"error": "Support factor analysis unavailable"}
    
    def _generate_support_recommendation(self, effective_strategies: Dict[str, int]) -> str:
        """Generate support strategy recommendation based on historical success."""
        if not effective_strategies:
            return "Limited intervention history - consider comprehensive assessment"
        
        top_strategy = list(effective_strategies.keys())[0]
        success_count = effective_strategies[top_strategy]
        
        if success_count >= 3:
            return f"Strong response to {top_strategy} - continue similar approaches"
        elif success_count >= 2:
            return f"Moderate response to {top_strategy} - expand with complementary strategies"
        else:
            return "Mixed intervention history - may need individualized approach"
    
    def get_cohort_analysis(self, institution_id: int, grade_level: str = None, 
                          limit_students: int = 100) -> Dict[str, Any]:
        """
        Aggregate cohort-level data for pattern analysis.
        
        Args:
            institution_id: Institution to analyze
            grade_level: Optional grade level filter
            limit_students: Maximum students to include
            
        Returns:
            Cohort analysis data
        """
        try:
            with self.session_factory() as db:
                # Base query for students
                student_query = db.query(Student).filter(
                    and_(
                        Student.institution_id == institution_id,
                        Student.enrollment_status == 'active'
                    )
                )
                
                if grade_level:
                    student_query = student_query.filter(Student.grade_level == grade_level)
                
                students = student_query.limit(limit_students).all()
                
                # Aggregate cohort metrics
                cohort_data = {
                    "institution_id": institution_id,
                    "grade_level_filter": grade_level,
                    "total_students": len(students),
                    "demographics": self._analyze_cohort_demographics(students),
                    "risk_distribution": self._analyze_risk_distribution(db, [s.id for s in students]),
                    "intervention_patterns": self._analyze_intervention_patterns(db, [s.id for s in students]),
                    "success_factors": self._identify_cohort_success_factors(db, [s.id for s in students])
                }
                
                return cohort_data
                
        except Exception as e:
            logger.error(f"❌ Error in cohort analysis: {str(e)}")
            return {"error": f"Cohort analysis failed: {str(e)}"}
    
    def _analyze_cohort_demographics(self, students: List[Student]) -> Dict[str, Any]:
        """Analyze demographic distribution of cohort."""
        demographics = {
            "total_count": len(students),
            "grade_levels": {},
            "special_populations": {
                "ell_count": 0,
                "iep_count": 0,
                "section_504_count": 0,
                "economically_disadvantaged_count": 0
            }
        }
        
        for student in students:
            # Grade level distribution
            grade = student.grade_level or "unknown"
            demographics["grade_levels"][grade] = demographics["grade_levels"].get(grade, 0) + 1
            
            # Special populations
            if student.is_ell:
                demographics["special_populations"]["ell_count"] += 1
            if student.has_iep:
                demographics["special_populations"]["iep_count"] += 1
            if student.has_504:
                demographics["special_populations"]["section_504_count"] += 1
            if student.is_economically_disadvantaged:
                demographics["special_populations"]["economically_disadvantaged_count"] += 1
        
        return demographics
    
    def _analyze_risk_distribution(self, db: Session, student_ids: List[int]) -> Dict[str, Any]:
        """Analyze risk score distribution across cohort."""
        try:
            # Get latest predictions for each student
            subquery = db.query(
                Prediction.student_id,
                func.max(Prediction.prediction_date).label('max_date')
            ).filter(
                Prediction.student_id.in_(student_ids)
            ).group_by(Prediction.student_id).subquery()
            
            predictions = db.query(Prediction).join(
                subquery,
                and_(
                    Prediction.student_id == subquery.c.student_id,
                    Prediction.prediction_date == subquery.c.max_date
                )
            ).all()
            
            risk_categories = {"High": 0, "Medium": 0, "Low": 0}
            risk_scores = []
            
            for prediction in predictions:
                if prediction.risk_category:
                    risk_categories[prediction.risk_category] = risk_categories.get(prediction.risk_category, 0) + 1
                if prediction.risk_score is not None:
                    risk_scores.append(prediction.risk_score)
            
            return {
                "total_with_predictions": len(predictions),
                "category_distribution": risk_categories,
                "average_risk_score": sum(risk_scores) / len(risk_scores) if risk_scores else None,
                "high_risk_percentage": (risk_categories["High"] / len(predictions) * 100) if predictions else 0
            }
            
        except Exception as e:
            logger.error(f"❌ Error analyzing risk distribution: {str(e)}")
            return {"error": "Risk distribution analysis failed"}
    
    def _analyze_intervention_patterns(self, db: Session, student_ids: List[int]) -> Dict[str, Any]:
        """Analyze intervention patterns across cohort."""
        try:
            interventions = db.query(Intervention).filter(
                Intervention.student_id.in_(student_ids)
            ).all()
            
            patterns = {
                "total_interventions": len(interventions),
                "intervention_types": {},
                "success_rates": {},
                "students_with_interventions": len(set(i.student_id for i in interventions))
            }
            
            # Analyze by type
            for intervention in interventions:
                int_type = intervention.intervention_type
                outcome = intervention.outcome
                
                # Count by type
                patterns["intervention_types"][int_type] = patterns["intervention_types"].get(int_type, 0) + 1
                
                # Track success rates
                if int_type not in patterns["success_rates"]:
                    patterns["success_rates"][int_type] = {"total": 0, "successful": 0}
                
                patterns["success_rates"][int_type]["total"] += 1
                if outcome == "successful":
                    patterns["success_rates"][int_type]["successful"] += 1
            
            # Calculate success percentages
            for int_type in patterns["success_rates"]:
                total = patterns["success_rates"][int_type]["total"]
                successful = patterns["success_rates"][int_type]["successful"]
                patterns["success_rates"][int_type]["percentage"] = (successful / total * 100) if total > 0 else 0
            
            return patterns
            
        except Exception as e:
            logger.error(f"❌ Error analyzing intervention patterns: {str(e)}")
            return {"error": "Intervention pattern analysis failed"}
    
    def _identify_cohort_success_factors(self, db: Session, student_ids: List[int]) -> Dict[str, Any]:
        """Identify factors associated with successful outcomes."""
        try:
            # This is a simplified analysis - in production, would use more sophisticated methods
            success_factors = {
                "high_performing_students": [],
                "common_success_patterns": [],
                "protective_factors": []
            }
            
            # Find students with consistently low risk or improving trends
            improving_students = []
            
            for student_id in student_ids[:20]:  # Sample for performance
                predictions = db.query(Prediction).filter(
                    Prediction.student_id == student_id
                ).order_by(Prediction.prediction_date).limit(5).all()
                
                if len(predictions) >= 2:
                    first_risk = predictions[0].risk_score
                    last_risk = predictions[-1].risk_score
                    
                    if first_risk and last_risk and last_risk < first_risk:
                        improving_students.append(student_id)
            
            success_factors["improving_student_count"] = len(improving_students)
            success_factors["improvement_rate"] = len(improving_students) / min(len(student_ids), 20) * 100
            
            return success_factors
            
        except Exception as e:
            logger.error(f"❌ Error identifying success factors: {str(e)}")
            return {"error": "Success factor analysis failed"}