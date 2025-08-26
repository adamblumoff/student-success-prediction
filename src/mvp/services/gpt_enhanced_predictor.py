#!/usr/bin/env python3
"""
GPT-Enhanced Predictor

Combines the existing K12UltraPredictor (81.5% AUC) with GPT-OSS natural language
analysis to provide comprehensive student success predictions with rich explanations.
"""

import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.models.k12_ultra_predictor import K12UltraPredictor
from src.models.k12_intervention_system import K12InterventionSystem
from src.mvp.services.gpt_oss_service import GPTOSSService
from src.mvp.services.metrics_aggregator import MetricsAggregator
from src.mvp.logging_config import get_logger

logger = get_logger(__name__)

class GPTEnhancedPredictor:
    """Enhanced predictor combining ML models with GPT-OSS natural language analysis."""
    
    def __init__(self):
        """Initialize the enhanced predictor with all components."""
        self.k12_predictor = None
        self.intervention_system = None
        self.gpt_service = None
        self.metrics_aggregator = None
        self.is_initialized = False
        
        # Configuration
        self.config = {
            "use_gpt_enhancement": True,
            "fallback_to_ml_only": True,
            "gpt_analysis_timeout": 30,  # seconds
            "include_peer_context": True,
            "include_intervention_history": True
        }
    
    def initialize_components(self) -> Dict[str, bool]:
        """Initialize all predictor components."""
        initialization_status = {
            "k12_predictor": False,
            "intervention_system": False, 
            "gpt_service": False,
            "metrics_aggregator": False
        }
        
        try:
            # Initialize K-12 Ultra Predictor
            logger.info("🎓 Initializing K-12 Ultra Predictor...")
            self.k12_predictor = K12UltraPredictor()
            initialization_status["k12_predictor"] = True
            logger.info("✅ K-12 Ultra Predictor initialized")
            
            # Initialize Intervention System
            logger.info("🔧 Initializing K-12 Intervention System...")
            self.intervention_system = K12InterventionSystem()
            initialization_status["intervention_system"] = True
            logger.info("✅ K-12 Intervention System initialized")
            
            # Initialize Metrics Aggregator
            logger.info("📊 Initializing Metrics Aggregator...")
            self.metrics_aggregator = MetricsAggregator()
            initialization_status["metrics_aggregator"] = True
            logger.info("✅ Metrics Aggregator initialized")
            
            # Initialize GPT-OSS Service (optional)
            try:
                logger.info("🤖 Initializing GPT-OSS Service...")
                self.gpt_service = GPTOSSService()
                if self.gpt_service.initialize_model():
                    initialization_status["gpt_service"] = True
                    logger.info("✅ GPT-OSS Service initialized")
                else:
                    logger.warning("⚠️ GPT-OSS Service initialization failed - continuing with ML-only mode")
            except Exception as e:
                logger.warning(f"⚠️ GPT-OSS Service unavailable: {str(e)} - continuing with ML-only mode")
            
            # Check overall initialization
            core_components = ["k12_predictor", "intervention_system", "metrics_aggregator"]
            self.is_initialized = all(initialization_status[comp] for comp in core_components)
            
            if self.is_initialized:
                logger.info("✅ GPT-Enhanced Predictor fully initialized")
            else:
                logger.error("❌ Critical components failed to initialize")
            
            return initialization_status
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize GPT-Enhanced Predictor: {str(e)}")
            return initialization_status
    
    def predict_student_success(self, student_data: Dict[str, Any], 
                              include_gpt_analysis: bool = True,
                              analysis_depth: str = "comprehensive") -> Dict[str, Any]:
        """
        Generate enhanced student success prediction with optional GPT analysis.
        
        Args:
            student_data: Student data dictionary (can be from CSV or database)
            include_gpt_analysis: Whether to include GPT-OSS natural language analysis
            analysis_depth: Level of analysis ("basic", "detailed", "comprehensive")
            
        Returns:
            Enhanced prediction results with ML scores and GPT insights
        """
        if not self.is_initialized:
            initialization_status = self.initialize_components()
            if not self.is_initialized:
                return {
                    "success": False,
                    "error": "Predictor initialization failed",
                    "initialization_status": initialization_status
                }
        
        try:
            prediction_start = datetime.now()
            
            # Step 1: Generate ML-based prediction using K-12 Ultra Predictor
            logger.info("🔍 Generating ML-based prediction...")
            ml_results = self._generate_ml_prediction(student_data)
            
            if not ml_results.get("success", False):
                return {
                    "success": False,
                    "error": "ML prediction failed",
                    "details": ml_results
                }
            
            # Step 2: Generate intervention recommendations
            logger.info("🎯 Generating intervention recommendations...")
            intervention_results = self._generate_intervention_recommendations(student_data, ml_results)
            
            # Step 3: Aggregate comprehensive metrics if student has database ID
            comprehensive_data = None
            if student_data.get("student_id") and isinstance(student_data["student_id"], int):
                logger.info("📊 Aggregating comprehensive student metrics...")
                comprehensive_data = self.metrics_aggregator.get_comprehensive_student_data(
                    student_data["student_id"]
                )
            
            # Step 4: Generate GPT analysis if requested and available
            gpt_analysis = None
            if include_gpt_analysis and self.gpt_service and self.config["use_gpt_enhancement"]:
                logger.info("🧠 Generating GPT-OSS enhanced analysis...")
                gpt_analysis = self._generate_gpt_analysis(
                    student_data, ml_results, intervention_results, comprehensive_data, analysis_depth
                )
            
            # Step 5: Combine all results
            enhanced_prediction = self._combine_prediction_results(
                ml_results, intervention_results, gpt_analysis, comprehensive_data,
                prediction_start
            )
            
            logger.info("✅ Enhanced prediction completed successfully")
            return enhanced_prediction
            
        except Exception as e:
            logger.error(f"❌ Enhanced prediction failed: {str(e)}")
            return {
                "success": False,
                "error": f"Prediction generation failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def _generate_ml_prediction(self, student_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate base ML prediction using K-12 Ultra Predictor."""
        try:
            # Convert student data to DataFrame format expected by K-12 predictor
            student_df = self._format_student_data_for_ml(student_data)
            
            # Generate prediction using K-12 Ultra Predictor
            predictions = self.k12_predictor.predict_gradebook_risks(student_df)
            
            if predictions.empty:
                return {"success": False, "error": "No predictions generated"}
            
            # Extract first prediction (assuming single student)
            prediction = predictions.iloc[0]
            
            return {
                "success": True,
                "risk_score": float(prediction.get("risk_score", 0)),
                "risk_category": str(prediction.get("risk_category", "Unknown")),
                "success_probability": float(prediction.get("success_probability", 0.5)),
                "confidence_score": float(prediction.get("confidence_score", 0.5)),
                "needs_intervention": bool(prediction.get("needs_intervention", False)),
                "model_version": "K12UltraPredictor",
                "features_used": prediction.to_dict(),
                "prediction_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ ML prediction generation failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _format_student_data_for_ml(self, student_data: Dict[str, Any]) -> pd.DataFrame:
        """Format student data for ML model consumption."""
        # Create DataFrame with single student record
        formatted_data = {}
        
        # Map common fields to ML model expected fields
        field_mappings = {
            "student_id": "student_id",
            "grade_level": "grade_level", 
            "current_gpa": ["current_gpa", "gpa", "grade_avg"],
            "attendance_rate": ["attendance_rate", "attendance"],
            "assignment_completion": ["assignment_completion", "homework_completion"],
            "discipline_incidents": ["discipline_incidents", "behavior_incidents"],
            "parent_engagement": ["parent_engagement", "family_engagement"]
        }
        
        # Apply mappings
        for ml_field, source_fields in field_mappings.items():
            if isinstance(source_fields, list):
                # Try multiple possible source fields
                for source_field in source_fields:
                    if source_field in student_data and student_data[source_field] is not None:
                        formatted_data[ml_field] = student_data[source_field]
                        break
                else:
                    # Set default value if none found
                    formatted_data[ml_field] = self._get_default_value(ml_field)
            else:
                # Single field mapping
                formatted_data[ml_field] = student_data.get(source_fields, self._get_default_value(ml_field))
        
        # Ensure student_id is properly formatted
        if "student_id" not in formatted_data or formatted_data["student_id"] is None:
            formatted_data["student_id"] = f"temp_student_{hash(str(student_data)) % 10000}"
        
        return pd.DataFrame([formatted_data])
    
    def _get_default_value(self, field: str) -> Any:
        """Get default values for missing fields."""
        defaults = {
            "student_id": "unknown_student",
            "grade_level": "9",  # Default to high school
            "current_gpa": 2.5,  # Neutral GPA
            "attendance_rate": 0.85,  # Typical attendance
            "assignment_completion": 0.75,  # Typical completion rate
            "discipline_incidents": 0,  # No incidents by default
            "parent_engagement": 0.5  # Moderate engagement
        }
        return defaults.get(field, 0)
    
    def _generate_intervention_recommendations(self, student_data: Dict[str, Any], 
                                             ml_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate intervention recommendations using K-12 Intervention System."""
        try:
            # Use intervention system to generate recommendations
            risk_category = ml_results.get("risk_category", "Medium")
            grade_level = student_data.get("grade_level", "9")
            
            # Generate grade-appropriate interventions
            intervention_plan = self.intervention_system.recommend_interventions_by_risk(
                risk_category, grade_level
            )
            
            return {
                "success": True,
                "recommended_interventions": intervention_plan,
                "priority_level": self._determine_intervention_priority(ml_results),
                "timeline_recommendation": self._determine_timeline(risk_category, grade_level),
                "resource_requirements": self._estimate_resource_requirements(intervention_plan)
            }
            
        except Exception as e:
            logger.error(f"❌ Intervention recommendation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "fallback_recommendations": self._get_generic_interventions(ml_results.get("risk_category"))
            }
    
    def _determine_intervention_priority(self, ml_results: Dict[str, Any]) -> str:
        """Determine intervention priority based on ML results."""
        risk_score = ml_results.get("risk_score", 0.5)
        risk_category = ml_results.get("risk_category", "Medium")
        
        if risk_category == "High" or risk_score > 0.8:
            return "Critical"
        elif risk_category == "Medium" or risk_score > 0.5:
            return "High"
        else:
            return "Moderate"
    
    def _determine_timeline(self, risk_category: str, grade_level: str) -> str:
        """Determine recommended intervention timeline."""
        if risk_category == "High":
            return "Immediate (within 1 week)"
        elif risk_category == "Medium":
            return "Short-term (within 2-3 weeks)"
        else:
            return "Long-term (within 4-6 weeks)"
    
    def _estimate_resource_requirements(self, intervention_plan: List[Dict]) -> Dict[str, Any]:
        """Estimate resource requirements for intervention plan."""
        if not intervention_plan:
            return {"error": "No intervention plan available"}
        
        total_interventions = len(intervention_plan)
        estimated_hours = sum(
            intervention.get("estimated_duration_hours", 2) for intervention in intervention_plan
        )
        
        return {
            "total_interventions": total_interventions,
            "estimated_total_hours": estimated_hours,
            "staff_types_needed": list(set(
                intervention.get("staff_required", "teacher") for intervention in intervention_plan
            )),
            "estimated_cost_range": f"${estimated_hours * 50}-{estimated_hours * 100}"  # Rough estimate
        }
    
    def _get_generic_interventions(self, risk_category: str) -> List[str]:
        """Provide generic intervention suggestions as fallback."""
        generic_interventions = {
            "High": [
                "Immediate academic support tutoring",
                "Intensive progress monitoring",
                "Family conference and support plan",
                "Behavioral intervention if needed"
            ],
            "Medium": [
                "Regular academic check-ins",
                "Study skills training", 
                "Peer tutoring program",
                "Parent communication enhancement"
            ],
            "Low": [
                "Continue current supports",
                "Periodic progress monitoring",
                "Enrichment opportunities",
                "Leadership development"
            ]
        }
        return generic_interventions.get(risk_category, generic_interventions["Medium"])
    
    def _generate_gpt_analysis(self, student_data: Dict[str, Any], ml_results: Dict[str, Any],
                              intervention_results: Dict[str, Any], comprehensive_data: Optional[Dict],
                              analysis_depth: str) -> Optional[Dict[str, Any]]:
        """Generate GPT-OSS natural language analysis."""
        try:
            if not self.gpt_service or not self.gpt_service.is_initialized:
                return None
            
            # Build comprehensive prompt for GPT analysis
            analysis_prompt = self._build_gpt_analysis_prompt(
                student_data, ml_results, intervention_results, comprehensive_data, analysis_depth
            )
            
            # Generate GPT analysis
            gpt_response = self.gpt_service.generate_analysis(
                analysis_prompt, 
                "student_analysis",
                max_tokens=1024 if analysis_depth == "basic" else 1536
            )
            
            if gpt_response.get("success"):
                return {
                    "success": True,
                    "narrative_analysis": gpt_response["analysis"],
                    "gpt_metadata": gpt_response["metadata"],
                    "analysis_depth": analysis_depth
                }
            else:
                logger.warning(f"⚠️ GPT analysis failed: {gpt_response.get('error')}")
                return None
                
        except Exception as e:
            logger.error(f"❌ GPT analysis generation failed: {str(e)}")
            return None
    
    def _build_gpt_analysis_prompt(self, student_data: Dict[str, Any], ml_results: Dict[str, Any],
                                 intervention_results: Dict[str, Any], comprehensive_data: Optional[Dict],
                                 analysis_depth: str) -> str:
        """Build comprehensive prompt for GPT analysis."""
        prompt_parts = []
        
        # Basic student information
        grade = student_data.get("grade_level", "Unknown")
        prompt_parts.append(f"STUDENT ANALYSIS REQUEST - Grade {grade} Student")
        
        # ML Prediction Results
        risk_score = ml_results.get("risk_score", 0)
        risk_category = ml_results.get("risk_category", "Unknown")
        success_prob = ml_results.get("success_probability", 0)
        
        prompt_parts.append(f"""
ML MODEL RESULTS:
- Risk Score: {risk_score:.2f}/1.0
- Risk Category: {risk_category}
- Success Probability: {success_prob:.2f}
- Confidence: {ml_results.get('confidence_score', 0):.2f}""")
        
        # Key metrics
        if student_data:
            metrics = []
            for key in ["current_gpa", "attendance_rate", "assignment_completion", "discipline_incidents"]:
                if key in student_data and student_data[key] is not None:
                    metrics.append(f"- {key.replace('_', ' ').title()}: {student_data[key]}")
            
            if metrics:
                prompt_parts.append(f"\nKEY METRICS:\n" + "\n".join(metrics))
        
        # Intervention recommendations
        if intervention_results.get("success") and intervention_results.get("recommended_interventions"):
            interventions = intervention_results["recommended_interventions"][:3]  # Top 3
            intervention_names = [interv.get("name", "Unknown intervention") for interv in interventions]
            prompt_parts.append(f"\nRECOMMENDED INTERVENTIONS:\n- " + "\n- ".join(intervention_names))
        
        # Comprehensive data if available
        if comprehensive_data and not comprehensive_data.get("error"):
            if comprehensive_data.get("intervention_history"):
                history = comprehensive_data["intervention_history"][:3]  # Recent 3
                history_summary = [f"{h['type']} ({h['status']})" for h in history]
                prompt_parts.append(f"\nRECENT INTERVENTION HISTORY:\n- " + "\n- ".join(history_summary))
            
            if comprehensive_data.get("peer_context", {}).get("comparison_context"):
                prompt_parts.append(f"\nPEER CONTEXT:\n{comprehensive_data['peer_context']['comparison_context']}")
        
        # Analysis request based on depth
        if analysis_depth == "basic":
            request = """
Please provide a concise analysis focusing on:
1. Primary risk factors and protective factors
2. Top 2-3 intervention priorities
3. Expected timeline for improvement"""
        elif analysis_depth == "detailed":
            request = """
Please provide a detailed analysis including:
1. Comprehensive risk and protective factor analysis
2. Specific intervention strategies with rationale
3. Timeline and milestone expectations
4. Family engagement recommendations
5. Progress monitoring suggestions"""
        else:  # comprehensive
            request = """
Please provide a comprehensive educational analysis including:
1. Holistic student profile with academic, behavioral, and social-emotional factors
2. Detailed intervention strategy with multiple approaches
3. Implementation timeline with specific milestones
4. Resource requirements and staff coordination
5. Family partnership strategies
6. Short-term and long-term success indicators
7. Risk mitigation strategies
8. Peer and classroom context considerations"""
        
        prompt_parts.append(request)
        prompt_parts.append("\nFocus on actionable, evidence-based recommendations appropriate for K-12 educational settings.")
        
        return "\n".join(prompt_parts)
    
    def _combine_prediction_results(self, ml_results: Dict[str, Any], 
                                  intervention_results: Dict[str, Any],
                                  gpt_analysis: Optional[Dict[str, Any]],
                                  comprehensive_data: Optional[Dict[str, Any]],
                                  prediction_start: datetime) -> Dict[str, Any]:
        """Combine all prediction results into unified response."""
        
        processing_time = (datetime.now() - prediction_start).total_seconds()
        
        combined_results = {
            "success": True,
            "prediction_id": f"gpt_enhanced_{int(datetime.now().timestamp())}",
            "timestamp": datetime.now().isoformat(),
            "processing_time_seconds": processing_time,
            
            # Core ML Results
            "ml_prediction": ml_results,
            
            # Intervention Recommendations
            "interventions": intervention_results,
            
            # GPT Analysis (if available)
            "gpt_analysis": gpt_analysis,
            
            # Comprehensive Data (if available)
            "comprehensive_context": comprehensive_data,
            
            # Summary
            "summary": {
                "risk_level": ml_results.get("risk_category", "Unknown"),
                "intervention_priority": intervention_results.get("priority_level", "Unknown"),
                "gpt_enhanced": gpt_analysis is not None,
                "has_historical_data": comprehensive_data is not None and not comprehensive_data.get("error")
            },
            
            # System Information
            "system_info": {
                "predictor_version": "GPT-Enhanced v1.0",
                "ml_model": "K12UltraPredictor",
                "gpt_model": self.gpt_service.model_name if self.gpt_service else None,
                "components_used": {
                    "ml_prediction": True,
                    "intervention_system": True,
                    "gpt_analysis": gpt_analysis is not None,
                    "comprehensive_metrics": comprehensive_data is not None
                }
            }
        }
        
        return combined_results
    
    def predict_cohort_patterns(self, institution_id: int, grade_level: str = None) -> Dict[str, Any]:
        """Generate cohort-level analysis using GPT-OSS insights."""
        try:
            if not self.is_initialized:
                self.initialize_components()
            
            # Get cohort data
            cohort_data = self.metrics_aggregator.get_cohort_analysis(
                institution_id, grade_level, limit_students=50
            )
            
            if cohort_data.get("error"):
                return cohort_data
            
            # Generate GPT cohort analysis if available
            gpt_cohort_analysis = None
            if self.gpt_service and self.gpt_service.is_initialized:
                cohort_prompt = self._build_cohort_analysis_prompt(cohort_data)
                gpt_cohort_analysis = self.gpt_service.generate_analysis(
                    cohort_prompt, "cohort_analysis", max_tokens=1024
                )
            
            return {
                "success": True,
                "cohort_data": cohort_data,
                "gpt_insights": gpt_cohort_analysis,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Cohort pattern analysis failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _build_cohort_analysis_prompt(self, cohort_data: Dict[str, Any]) -> str:
        """Build prompt for cohort-level GPT analysis."""
        prompt_parts = []
        
        prompt_parts.append("COHORT ANALYSIS REQUEST")
        prompt_parts.append(f"Institution ID: {cohort_data.get('institution_id')}")
        prompt_parts.append(f"Grade Level: {cohort_data.get('grade_level_filter', 'All grades')}")
        prompt_parts.append(f"Total Students: {cohort_data.get('total_students', 0)}")
        
        # Demographics
        if cohort_data.get("demographics"):
            demo = cohort_data["demographics"]
            special_pop = demo.get("special_populations", {})
            prompt_parts.append(f"""
DEMOGRAPHICS:
- ELL Students: {special_pop.get('ell_count', 0)}
- IEP Students: {special_pop.get('iep_count', 0)}
- Section 504: {special_pop.get('section_504_count', 0)}
- Economically Disadvantaged: {special_pop.get('economically_disadvantaged_count', 0)}""")
        
        # Risk distribution
        if cohort_data.get("risk_distribution"):
            risk_dist = cohort_data["risk_distribution"]
            categories = risk_dist.get("category_distribution", {})
            prompt_parts.append(f"""
RISK DISTRIBUTION:
- High Risk: {categories.get('High', 0)} students
- Medium Risk: {categories.get('Medium', 0)} students
- Low Risk: {categories.get('Low', 0)} students
- High Risk Percentage: {risk_dist.get('high_risk_percentage', 0):.1f}%""")
        
        prompt_parts.append("""
Please analyze this cohort data and provide:
1. Key patterns and trends in the student population
2. Systemic risk factors that may need district-level attention
3. Recommended district-wide intervention strategies
4. Resource allocation priorities
5. Equity considerations and recommendations
6. Success indicators to track progress

Focus on actionable insights for school administrators and district leadership.""")
        
        return "\n".join(prompt_parts)
    
    def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check of all components."""
        health_status = {
            "service": "GPT-Enhanced Predictor",
            "initialized": self.is_initialized,
            "timestamp": datetime.now().isoformat(),
            "components": {}
        }
        
        # Check each component
        if self.k12_predictor:
            health_status["components"]["k12_predictor"] = {"status": "available"}
        else:
            health_status["components"]["k12_predictor"] = {"status": "unavailable"}
        
        if self.intervention_system:
            health_status["components"]["intervention_system"] = {"status": "available"}
        else:
            health_status["components"]["intervention_system"] = {"status": "unavailable"}
        
        if self.gpt_service:
            gpt_health = self.gpt_service.health_check()
            health_status["components"]["gpt_service"] = gpt_health
        else:
            health_status["components"]["gpt_service"] = {"status": "unavailable"}
        
        if self.metrics_aggregator:
            health_status["components"]["metrics_aggregator"] = {"status": "available"}
        else:
            health_status["components"]["metrics_aggregator"] = {"status": "unavailable"}
        
        return health_status