#!/usr/bin/env python3
"""
GPT-Enhanced API Endpoints

New API endpoints that leverage GPT-OSS 20B model for enhanced AI analysis,
narrative reports, and comprehensive educational insights.
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Query, Path
from fastapi.responses import JSONResponse
from typing import Optional, Dict, List, Any
import sys
from pathlib import Path as PathLib
from datetime import datetime
import logging

# Add project root to path
project_root = PathLib(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.mvp.logging_config import get_logger, log_prediction
from src.mvp.services.gpt_enhanced_predictor import GPTEnhancedPredictor
from src.mvp.services.gpt_oss_service import GPTOSSService
from src.mvp.services.metrics_aggregator import MetricsAggregator
from src.mvp.services.context_builder import ContextBuilder
from src.mvp.database import get_db_session
from src.mvp.models import Student, Prediction, Intervention, Institution
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel, Field

logger = get_logger(__name__)

# Create router
router = APIRouter()

# Request/Response Models
class GPTAnalysisRequest(BaseModel):
    """Request model for GPT analysis."""
    student_id: int = Field(..., description="Database ID of the student")
    analysis_depth: str = Field("detailed", description="Analysis depth: basic, detailed, comprehensive")
    include_peer_context: bool = Field(True, description="Include peer comparison data")
    include_intervention_history: bool = Field(True, description="Include intervention history")
    format_for_display: str = Field("web", description="Display format: web, report, email, mobile")

class CohortAnalysisRequest(BaseModel):
    """Request model for cohort analysis."""
    institution_id: int = Field(..., description="Institution ID")
    grade_level: Optional[str] = Field(None, description="Grade level filter")
    analysis_focus: str = Field("patterns", description="Analysis focus: patterns, interventions, equity")
    limit_students: int = Field(50, description="Maximum students to include")

class InterventionPlanRequest(BaseModel):
    """Request model for intervention planning."""
    student_id: int = Field(..., description="Database ID of the student")
    available_resources: Optional[Dict[str, Any]] = Field(None, description="Available school resources")
    timeline_preference: str = Field("standard", description="Timeline: immediate, standard, extended")

class QuickInsightRequest(BaseModel):
    """Request model for quick student insights."""
    student_data: Dict[str, Any] = Field(..., description="Student data from CSV or form input")
    question: str = Field(..., description="Specific question about the student")

# Service dependencies
def get_gpt_enhanced_predictor():
    """Dependency to get GPT-enhanced predictor."""
    predictor = GPTEnhancedPredictor()
    if not predictor.is_initialized:
        predictor.initialize_components()
    return predictor

def get_gpt_service():
    """Dependency to get GPT service."""
    service = GPTOSSService()
    if not service.is_initialized:
        service.initialize_model()
    return service

def get_context_builder():
    """Dependency to get context builder."""
    return ContextBuilder()

def get_metrics_aggregator():
    """Dependency to get metrics aggregator.""" 
    return MetricsAggregator()

# Database dependency
def get_db():
    """Database session dependency."""
    from mvp.database import get_session_factory
    session_factory = get_session_factory()
    session = session_factory()
    try:
        yield session
    finally:
        session.close()

@router.post("/analyze-student/{student_id}", response_model=Dict[str, Any])
async def analyze_student_comprehensive(
    student_id: int = Path(..., description="Database ID of the student"),
    request: Request = None,
    analysis_depth: str = Query("detailed", description="Analysis depth: basic, detailed, comprehensive"),
    include_gpt_analysis: bool = Query(True, description="Include GPT-OSS natural language analysis"),
    format_for_display: str = Query("web", description="Display format: web, report, email, mobile"),
    predictor: GPTEnhancedPredictor = Depends(get_gpt_enhanced_predictor),
    context_builder: ContextBuilder = Depends(get_context_builder),
    db: Session = Depends(get_db)
):
    """
    Generate comprehensive AI-enhanced analysis for a specific student.
    
    This endpoint combines ML prediction, intervention recommendations, and GPT-OSS
    natural language analysis to provide rich, actionable insights for educators.
    """
    try:
        start_time = datetime.now()
        logger.info(f"🧠 Starting comprehensive analysis for student {student_id}")
        
        # Verify student exists
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail=f"Student {student_id} not found")
        
        # Get comprehensive student data
        metrics_aggregator = MetricsAggregator()
        comprehensive_data = metrics_aggregator.get_comprehensive_student_data(student_id)
        
        if comprehensive_data.get("error"):
            raise HTTPException(status_code=500, detail=f"Failed to aggregate student data: {comprehensive_data['error']}")
        
        # Extract student data for prediction
        student_data = {
            "student_id": student_id,
            "grade_level": student.grade_level,
            "current_gpa": comprehensive_data.get("academic_performance", {}).get("academic_features", {}).get("current_gpa", 2.5),
            "attendance_rate": comprehensive_data.get("academic_performance", {}).get("academic_features", {}).get("attendance_rate", 0.85),
            "assignment_completion": comprehensive_data.get("academic_performance", {}).get("academic_features", {}).get("assignment_completion", 0.75),
            "discipline_incidents": comprehensive_data.get("academic_performance", {}).get("academic_features", {}).get("discipline_incidents", 0),
            "is_ell": student.is_ell,
            "has_iep": student.has_iep,
            "has_504": student.has_504,
            "is_economically_disadvantaged": student.is_economically_disadvantaged
        }
        
        # Generate enhanced prediction
        prediction_result = predictor.predict_student_success(
            student_data=student_data,
            include_gpt_analysis=include_gpt_analysis,
            analysis_depth=analysis_depth
        )
        
        if not prediction_result.get("success"):
            raise HTTPException(status_code=500, detail=f"Prediction failed: {prediction_result.get('error')}")
        
        # Format GPT analysis for display if available
        if prediction_result.get("gpt_analysis") and prediction_result["gpt_analysis"].get("narrative_analysis"):
            formatted_analysis = context_builder.format_for_display(
                prediction_result["gpt_analysis"]["narrative_analysis"],
                format_for_display
            )
            prediction_result["gpt_analysis"]["formatted_analysis"] = formatted_analysis
        
        # Add student context
        prediction_result["student_context"] = {
            "student_id": student_id,
            "grade_level": student.grade_level,
            "institution_id": student.institution_id,
            "analysis_timestamp": start_time.isoformat(),
            "comprehensive_data_available": not comprehensive_data.get("error")
        }
        
        # Log the analysis
        processing_time = (datetime.now() - start_time).total_seconds()
        log_prediction(
            student_id=str(student_id),
            prediction_type="gpt_enhanced_comprehensive",
            risk_score=prediction_result.get("ml_prediction", {}).get("risk_score", 0),
            processing_time=processing_time
        )
        
        logger.info(f"✅ Comprehensive analysis completed for student {student_id} in {processing_time:.2f}s")
        return prediction_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Comprehensive analysis failed for student {student_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/analyze-cohort", response_model=Dict[str, Any])
async def analyze_cohort_patterns(
    request_data: CohortAnalysisRequest,
    request: Request = None,
    predictor: GPTEnhancedPredictor = Depends(get_gpt_enhanced_predictor),
    db: Session = Depends(get_db)
):
    """
    Generate cohort-level analysis with GPT-OSS insights for district leadership.
    
    Analyzes patterns across student populations to identify systemic issues,
    intervention opportunities, and equity considerations.
    """
    try:
        start_time = datetime.now()
        logger.info(f"🏫 Starting cohort analysis for institution {request_data.institution_id}")
        
        # Verify institution exists
        institution = db.query(Institution).filter(Institution.id == request_data.institution_id).first()
        if not institution:
            raise HTTPException(status_code=404, detail=f"Institution {request_data.institution_id} not found")
        
        # Generate cohort analysis
        cohort_result = predictor.predict_cohort_patterns(
            institution_id=request_data.institution_id,
            grade_level=request_data.grade_level
        )
        
        if not cohort_result.get("success"):
            raise HTTPException(status_code=500, detail=f"Cohort analysis failed: {cohort_result.get('error')}")
        
        # Add request context
        cohort_result["analysis_parameters"] = {
            "institution_id": request_data.institution_id,
            "grade_level_filter": request_data.grade_level,
            "analysis_focus": request_data.analysis_focus,
            "student_limit": request_data.limit_students,
            "analysis_timestamp": start_time.isoformat()
        }
        
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Cohort analysis completed for institution {request_data.institution_id} in {processing_time:.2f}s")
        
        return cohort_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Cohort analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Cohort analysis failed: {str(e)}")

@router.post("/intervention-planning", response_model=Dict[str, Any])
async def generate_intervention_plan(
    request_data: InterventionPlanRequest,
    request: Request = None,
    gpt_service: GPTOSSService = Depends(get_gpt_service),
    context_builder: ContextBuilder = Depends(get_context_builder),
    db: Session = Depends(get_db)
):
    """
    Generate comprehensive, GPT-enhanced intervention plan for a student.
    
    Creates detailed, actionable intervention strategies based on student data,
    historical interventions, and available resources.
    """
    try:
        start_time = datetime.now()
        logger.info(f"🎯 Generating intervention plan for student {request_data.student_id}")
        
        # Get student and intervention history
        student = db.query(Student).filter(Student.id == request_data.student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail=f"Student {request_data.student_id} not found")
        
        # Get intervention history
        interventions = db.query(Intervention).filter(
            Intervention.student_id == request_data.student_id
        ).order_by(desc(Intervention.created_at)).limit(10).all()
        
        intervention_history = []
        for intervention in interventions:
            intervention_history.append({
                "type": intervention.intervention_type,
                "status": intervention.status,
                "outcome": intervention.outcome,
                "created_date": intervention.created_at.isoformat() if intervention.created_at else None,
                "time_spent_minutes": intervention.time_spent_minutes
            })
        
        # Get comprehensive student data
        metrics_aggregator = MetricsAggregator()
        comprehensive_data = metrics_aggregator.get_comprehensive_student_data(request_data.student_id)
        
        # Build student data for intervention planning
        student_data = {
            "student_id": request_data.student_id,
            "grade_level": student.grade_level,
            "risk_category": comprehensive_data.get("risk_assessment", {}).get("risk_category", "Medium")
        }
        
        # Generate intervention planning context
        planning_context = context_builder.build_intervention_planning_context(
            student_data=student_data,
            intervention_history=intervention_history,
            available_resources=request_data.available_resources
        )
        
        # Generate GPT-powered intervention plan
        if gpt_service and gpt_service.is_initialized:
            gpt_plan = gpt_service.generate_analysis(
                planning_context,
                "intervention_planning",
                max_tokens=1536
            )
            
            intervention_plan = {
                "success": True,
                "student_id": request_data.student_id,
                "gpt_intervention_plan": gpt_plan,
                "intervention_history_summary": {
                    "total_previous_interventions": len(intervention_history),
                    "recent_intervention_types": list(set([i["type"] for i in intervention_history[:5]])),
                    "success_rate": len([i for i in intervention_history if i["outcome"] == "successful"]) / len(intervention_history) if intervention_history else 0
                },
                "planning_parameters": {
                    "timeline_preference": request_data.timeline_preference,
                    "resources_considered": request_data.available_resources is not None,
                    "historical_data_points": len(intervention_history)
                },
                "generated_timestamp": start_time.isoformat()
            }
        else:
            intervention_plan = {
                "success": False,
                "error": "GPT service not available",
                "fallback_plan": "Please consult with intervention specialist for comprehensive planning"
            }
        
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Intervention plan generated for student {request_data.student_id} in {processing_time:.2f}s")
        
        return intervention_plan
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Intervention planning failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Intervention planning failed: {str(e)}")

@router.post("/quick-insight", response_model=Dict[str, Any])
async def get_quick_student_insight(
    request_data: QuickInsightRequest,
    request: Request = None,
    gpt_service: GPTOSSService = Depends(get_gpt_service)
):
    """
    Get quick GPT-powered insight about a student based on specific question.
    
    Provides immediate answers to specific questions about student data,
    useful for quick consultations during meetings or planning sessions.
    """
    try:
        start_time = datetime.now()
        logger.info(f"🔍 DEBUG: /api/gpt/quick-insight endpoint called!")
        logger.info(f"❓ Generating quick insight for student question")
        
        if not gpt_service or not gpt_service.is_initialized:
            logger.error(f"🔍 DEBUG: GPT service not initialized! gpt_service exists: {gpt_service is not None}, is_initialized: {gpt_service.is_initialized if gpt_service else 'N/A'}")
            return {
                "success": False,
                "error": "GPT service not available",
                "fallback_response": "Please consult with educational specialist for detailed insights"
            }
        
        # Build focused prompt for the specific question
        prompt_parts = [
            "STUDENT INSIGHT REQUEST",
            f"Question: {request_data.question}",
            "",
            "Student Data:"
        ]
        
        # Add relevant student data
        logger.info(f"🔍 DEBUG: Student data received: {request_data.student_data}")
        for key, value in request_data.student_data.items():
            if value is not None:
                prompt_parts.append(f"• {key.replace('_', ' ').title()}: {value}")
        
        prompt_parts.extend([
            "",
            "Format each recommendation as:",
            "1) [Action title]",
            "- What to do: [One specific action]", 
            "- Why it's needed for THIS student: [Brief explanation using their data]",
            "- How to implement: [1 concrete step]",
            "- Timeline: [When to start/complete]"
        ])
        
        insight_prompt = "\n".join(prompt_parts)
        logger.info(f"🔍 DEBUG: Full prompt being sent to GPT:\n{insight_prompt}")
        
        # Generate insight
        gpt_response = gpt_service.generate_analysis(
            insight_prompt,
            "student_analysis", 
            max_tokens=512
        )
        logger.info(f"🔍 DEBUG: GPT response: {gpt_response}")
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        result = {
            "success": gpt_response.get("success", False),
            "question": request_data.question,
            "insight": gpt_response.get("analysis", "Unable to generate insight"),
            "student_data_used": list(request_data.student_data.keys()),
            "response_metadata": gpt_response.get("metadata", {}),
            "processing_time_seconds": processing_time,
            "timestamp": start_time.isoformat()
        }
        
        if not gpt_response.get("success"):
            result["error"] = gpt_response.get("error", "Unknown error")
        
        logger.info(f"✅ Quick insight generated in {processing_time:.2f}s")
        return result
        
    except Exception as e:
        logger.error(f"❌ Quick insight generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Quick insight failed: {str(e)}")

@router.post("/narrative-report/{student_id}", response_model=Dict[str, Any])
async def generate_narrative_report(
    student_id: int = Path(..., description="Database ID of the student"),
    request: Request = None,
    report_type: str = Query("comprehensive", description="Report type: summary, detailed, comprehensive"),
    include_recommendations: bool = Query(True, description="Include specific recommendations"),
    audience: str = Query("educator", description="Target audience: educator, administrator, family"),
    predictor: GPTEnhancedPredictor = Depends(get_gpt_enhanced_predictor),
    context_builder: ContextBuilder = Depends(get_context_builder),
    db: Session = Depends(get_db)
):
    """
    Generate comprehensive narrative report about a student for different audiences.
    
    Creates detailed, natural language reports suitable for sharing with educators,
    administrators, or families (with appropriate privacy considerations).
    """
    try:
        start_time = datetime.now()
        logger.info(f"📋 Generating {report_type} narrative report for student {student_id}")
        
        # Verify student exists
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail=f"Student {student_id} not found")
        
        # Get comprehensive analysis first
        metrics_aggregator = MetricsAggregator()
        comprehensive_data = metrics_aggregator.get_comprehensive_student_data(student_id)
        
        # Generate enhanced prediction for the report
        student_data = {
            "student_id": student_id,
            "grade_level": student.grade_level
        }
        
        prediction_result = predictor.predict_student_success(
            student_data=student_data,
            include_gpt_analysis=True,
            analysis_depth="comprehensive" if report_type == "comprehensive" else "detailed"
        )
        
        # Format report based on audience
        if audience == "family":
            report_format = "email"  # Family-friendly formatting
        elif audience == "administrator":
            report_format = "report"  # Formal report formatting  
        else:
            report_format = "web"  # Educator web formatting
        
        # Build narrative report
        report_sections = []
        
        # Report header
        report_sections.append(f"STUDENT SUCCESS REPORT - {report_type.upper()}")
        report_sections.append(f"Grade: {student.grade_level}")
        report_sections.append(f"Report Date: {start_time.strftime('%B %d, %Y')}")
        report_sections.append(f"Prepared for: {audience.title()}")
        
        # Include ML prediction summary
        if prediction_result.get("success") and prediction_result.get("ml_prediction"):
            ml_pred = prediction_result["ml_prediction"]
            risk_category = ml_pred.get("risk_category", "Unknown")
            success_prob = ml_pred.get("success_probability", 0)
            
            report_sections.append(f"\nOVERALL ASSESSMENT:")
            report_sections.append(f"Current Risk Level: {risk_category}")
            report_sections.append(f"Success Probability: {success_prob:.1%}")
        
        # Include GPT narrative analysis
        if prediction_result.get("gpt_analysis") and prediction_result["gpt_analysis"].get("narrative_analysis"):
            narrative = prediction_result["gpt_analysis"]["narrative_analysis"]
            formatted_narrative = context_builder.format_for_display(narrative, report_format)
            report_sections.append(f"\nDETAILED ANALYSIS:")
            report_sections.append(formatted_narrative)
        
        # Include intervention recommendations if requested
        if include_recommendations and prediction_result.get("interventions"):
            interventions = prediction_result["interventions"]
            if interventions.get("success") and interventions.get("recommended_interventions"):
                report_sections.append(f"\nRECOMMENDATIONS:")
                for i, intervention in enumerate(interventions["recommended_interventions"][:5], 1):
                    intervention_name = intervention.get("name", "Unnamed intervention")
                    report_sections.append(f"{i}. {intervention_name}")
        
        # Compile final report
        full_report = "\n".join(report_sections)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        result = {
            "success": True,
            "student_id": student_id,
            "report_type": report_type,
            "audience": audience,
            "narrative_report": full_report,
            "report_metadata": {
                "word_count": len(full_report.split()),
                "generation_time_seconds": processing_time,
                "ml_prediction_included": prediction_result.get("success", False),
                "gpt_analysis_included": prediction_result.get("gpt_analysis") is not None,
                "recommendations_included": include_recommendations
            },
            "generated_timestamp": start_time.isoformat()
        }
        
        logger.info(f"✅ Narrative report generated for student {student_id} in {processing_time:.2f}s")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Narrative report generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Narrative report failed: {str(e)}")

@router.get("/health", response_model=Dict[str, Any])
async def health_check_gpt_services():
    """
    Health check endpoint for all GPT-enhanced services.
    
    Returns the status of GPT-OSS model, enhanced predictor, and related services.
    """
    try:
        health_status = {
            "service": "GPT-Enhanced Endpoints",
            "timestamp": datetime.now().isoformat(),
            "status": "operational",
            "components": {}
        }
        
        # Check GPT Enhanced Predictor
        try:
            predictor = GPTEnhancedPredictor()
            predictor_health = predictor.health_check()
            health_status["components"]["gpt_enhanced_predictor"] = predictor_health
        except Exception as e:
            health_status["components"]["gpt_enhanced_predictor"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Check GPT-OSS Service directly
        try:
            gpt_service = GPTOSSService()
            gpt_health = gpt_service.health_check()
            health_status["components"]["gpt_oss_service"] = gpt_health
        except Exception as e:
            health_status["components"]["gpt_oss_service"] = {
                "status": "error", 
                "error": str(e)
            }
        
        # Check Context Builder
        try:
            context_builder = ContextBuilder()
            health_status["components"]["context_builder"] = {
                "status": "operational",
                "grade_contexts_available": len(context_builder.grade_contexts),
                "risk_contexts_available": len(context_builder.risk_contexts)
            }
        except Exception as e:
            health_status["components"]["context_builder"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Check Metrics Aggregator
        try:
            metrics_aggregator = MetricsAggregator()
            health_status["components"]["metrics_aggregator"] = {
                "status": "operational"
            }
        except Exception as e:
            health_status["components"]["metrics_aggregator"] = {
                "status": "error",
                "error": str(e)
            }
        
        return health_status
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {str(e)}")
        return {
            "service": "GPT-Enhanced Endpoints",
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }