#!/usr/bin/env python3
"""
Student Success Prediction API

Production-ready API for the student success prediction system.
Provides endpoints for risk assessment, intervention recommendations, and monitoring.
"""

from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import pandas as pd
import numpy as np
from pathlib import Path
import joblib
import json
import logging
import time
from datetime import datetime
import sys
from sqlalchemy.orm import Session

# Add src directory to path
sys.path.append(str(Path(__file__).parent.parent))
from models.intervention_system import InterventionRecommendationSystem
from database import get_db, Student, RiskPrediction, Intervention, get_student_features_for_ml, init_db, test_db_connection
from database.models import create_student_with_features

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Student Success Prediction API",
    description="AI-powered early warning system for student retention",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Global variables
intervention_system = None
feature_columns = None
db_available = False

# Pydantic models for request/response
class StudentData(BaseModel):
    id_student: int
    code_module: str = Field(..., description="Course module code")
    code_presentation: str = Field(..., description="Course presentation code")
    
    # Demographic features
    gender_encoded: int = Field(0, ge=0, le=1)
    region_encoded: int = Field(0, ge=0, le=12)
    age_band_encoded: int = Field(0, ge=0, le=2)
    education_encoded: int = Field(0, ge=0, le=4)
    is_male: int = Field(0, ge=0, le=1)
    has_disability: int = Field(0, ge=0, le=1)
    studied_credits: int = Field(0, ge=0, le=600)
    num_of_prev_attempts: int = Field(0, ge=0, le=6)
    registration_delay: float = Field(0.0)
    unregistered: int = Field(0, ge=0, le=1)
    
    # Early VLE features
    early_total_clicks: float = Field(0.0, ge=0)
    early_avg_clicks: float = Field(0.0, ge=0)
    early_clicks_std: float = Field(0.0, ge=0)
    early_max_clicks: float = Field(0.0, ge=0)
    early_active_days: int = Field(0, ge=0, le=300)
    early_first_access: int = Field(0, ge=-50)
    early_last_access: int = Field(0, ge=-50)
    early_engagement_consistency: float = Field(0.0, ge=0, le=10)
    early_clicks_per_active_day: float = Field(0.0, ge=0)
    early_engagement_range: int = Field(0, ge=0)
    
    # Early assessment features
    early_assessments_count: int = Field(0, ge=0)
    early_avg_score: float = Field(0.0, ge=0, le=100)
    early_score_std: float = Field(0.0, ge=0)
    early_min_score: float = Field(0.0, ge=0, le=100)
    early_max_score: float = Field(0.0, ge=0, le=100)
    early_missing_submissions: int = Field(0, ge=0)
    early_submitted_count: int = Field(0, ge=0)
    early_total_weight: float = Field(0.0, ge=0)
    early_banked_count: int = Field(0, ge=0)
    early_submission_rate: float = Field(0.0, ge=0, le=1)
    early_score_range: float = Field(0.0, ge=0)

class RiskAssessment(BaseModel):
    student_id: int
    success_probability: float = Field(..., ge=0, le=1)
    risk_score: float = Field(..., ge=0, le=1)
    risk_category: str = Field(..., pattern="^(Low Risk|Medium Risk|High Risk)$")
    needs_intervention: bool
    timestamp: datetime

class Intervention(BaseModel):
    type: str
    category: str
    title: str
    description: str
    timeline: str
    resources: List[str]
    cost: str

class InterventionRecommendation(BaseModel):
    student_id: int
    risk_level: str
    risk_score: float
    interventions: List[Intervention]
    priority: str
    timestamp: datetime

class BatchStudentData(BaseModel):
    students: List[StudentData]

class BatchRiskAssessment(BaseModel):
    assessments: List[RiskAssessment]
    total_students: int
    high_risk_count: int
    processing_time_ms: float

# API Health and Status
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "version": "1.0.0",
        "system_ready": intervention_system is not None
    }

@app.get("/status")
async def system_status():
    """Detailed system status"""
    db_stats = {}
    if db_available:
        try:
            from database import get_db_stats
            with next(get_db()) as db_session:
                db_stats = get_db_stats(db_session)
        except Exception:
            db_stats = {"error": "Failed to get database stats"}
    
    return {
        "system": "Student Success Prediction API",
        "database_available": db_available,
        "database_stats": db_stats,
        "version": "1.0.0",
        "status": "operational",
        "model_loaded": intervention_system is not None,
        "features_available": len(feature_columns) if feature_columns else 0,
        "timestamp": datetime.now(),
        "uptime": "N/A"  # Would track actual uptime in production
    }

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Validate API key (simplified for demo)"""
    # In production, implement proper JWT token validation
    if credentials.credentials != "demo-api-key":
        raise HTTPException(status_code=401, detail="Invalid API key")
    return {"user": "demo_user"}

# Core API endpoints
@app.post("/predict/single", response_model=RiskAssessment)
async def predict_single_student(
    student: StudentData,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Predict risk for a single student"""
    try:
        start_time = time.time()
        
        # Convert to DataFrame
        student_df = pd.DataFrame([student.dict()])
        
        # Get risk assessment
        risk_result = intervention_system.assess_student_risk(student_df)
        
        # Format response
        result = RiskAssessment(
            student_id=student.id_student,
            success_probability=float(risk_result.iloc[0]['success_probability']),
            risk_score=float(risk_result.iloc[0]['risk_score']),
            risk_category=risk_result.iloc[0]['risk_category'],
            needs_intervention=bool(risk_result.iloc[0]['needs_intervention']),
            timestamp=datetime.now()
        )
        
        # Save prediction to database if available
        if db_available:
            try:
                # Check if student exists, if not create them
                existing_student = db.query(Student).filter(Student.id_student == student.id_student).first()
                if not existing_student:
                    new_student = create_student_with_features(db, student.dict())
                    student_db_id = new_student.id
                else:
                    student_db_id = existing_student.id
                
                # Save prediction
                prediction = RiskPrediction(
                    student_id=student_db_id,
                    risk_score=result.risk_score,
                    risk_category=result.risk_category,
                    needs_intervention=result.needs_intervention,
                    model_version="gradient_boosting_v1.0",
                    confidence_score=result.success_probability
                )
                db.add(prediction)
                db.commit()
                
            except Exception as db_e:
                logger.warning(f"Failed to save prediction to database: {db_e}")
                db.rollback()
        
        # Log request
        processing_time = (time.time() - start_time) * 1000
        logger.info(f"Single prediction: student_id={student.id_student}, "
                   f"risk_score={result.risk_score:.3f}, "
                   f"processing_time={processing_time:.1f}ms")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in single prediction: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.post("/predict/batch", response_model=BatchRiskAssessment)
async def predict_batch_students(
    batch: BatchStudentData,
    current_user: dict = Depends(get_current_user)
):
    """Predict risk for multiple students"""
    try:
        start_time = time.time()
        
        if len(batch.students) > 1000:
            raise HTTPException(status_code=400, detail="Batch size limited to 1000 students")
        
        # Convert to DataFrame
        students_data = [student.dict() for student in batch.students]
        students_df = pd.DataFrame(students_data)
        
        # Get risk assessments
        risk_results = intervention_system.assess_student_risk(students_df)
        
        # Format response
        assessments = []
        for i, (_, row) in enumerate(risk_results.iterrows()):
            assessment = RiskAssessment(
                student_id=batch.students[i].id_student,
                success_probability=float(row['success_probability']),
                risk_score=float(row['risk_score']),
                risk_category=row['risk_category'],
                needs_intervention=bool(row['needs_intervention']),
                timestamp=datetime.now()
            )
            assessments.append(assessment)
        
        # Calculate summary statistics
        high_risk_count = sum(1 for a in assessments if a.risk_category == "High Risk")
        processing_time = (time.time() - start_time) * 1000
        
        result = BatchRiskAssessment(
            assessments=assessments,
            total_students=len(assessments),
            high_risk_count=high_risk_count,
            processing_time_ms=processing_time
        )
        
        # Log request
        logger.info(f"Batch prediction: students={len(batch.students)}, "
                   f"high_risk={high_risk_count}, "
                   f"processing_time={processing_time:.1f}ms")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in batch prediction: {e}")
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")

@app.post("/interventions/recommend", response_model=List[InterventionRecommendation])
async def recommend_interventions(
    batch: BatchStudentData,
    current_user: dict = Depends(get_current_user)
):
    """Get intervention recommendations for students"""
    try:
        start_time = time.time()
        
        if len(batch.students) > 100:
            raise HTTPException(status_code=400, detail="Intervention recommendations limited to 100 students")
        
        # Convert to DataFrame
        students_data = [student.dict() for student in batch.students]
        students_df = pd.DataFrame(students_data)
        
        # Get intervention recommendations
        recommendations = intervention_system.get_intervention_recommendations(students_df)
        
        # Format response
        result = []
        for rec in recommendations:
            interventions = [
                Intervention(
                    type=intervention['type'],
                    category=intervention['category'],
                    title=intervention['title'],
                    description=intervention['description'],
                    timeline=intervention['timeline'],
                    resources=intervention['resources'],
                    cost=intervention['cost']
                )
                for intervention in rec['interventions']
            ]
            
            recommendation = InterventionRecommendation(
                student_id=rec['student_id'],
                risk_level=rec['risk_level'],
                risk_score=rec['risk_score'],
                interventions=interventions,
                priority=rec['priority'],
                timestamp=datetime.now()
            )
            result.append(recommendation)
        
        # Log request
        processing_time = (time.time() - start_time) * 1000
        logger.info(f"Intervention recommendations: students={len(batch.students)}, "
                   f"processing_time={processing_time:.1f}ms")
        
        return result
        
    except Exception as e:
        logger.error(f"Error generating interventions: {e}")
        raise HTTPException(status_code=500, detail=f"Intervention generation failed: {str(e)}")

@app.get("/models/info")
async def model_info(current_user: dict = Depends(get_current_user)):
    """Get information about the loaded models"""
    try:
        # Load model metadata
        with open("results/models/model_metadata.json", 'r') as f:
            metadata = json.load(f)
        
        return {
            "model_info": metadata,
            "feature_count": len(feature_columns),
            "deployment_ready": True,
            "last_updated": datetime.now(),
            "performance_metrics": {
                "binary_auc": metadata['best_binary_model']['metrics']['auc'],
                "multiclass_f1": metadata['best_multi_model']['metrics']['f1'],
                "prediction_speed": "<100ms"
            }
        }
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize the system on startup"""
    global intervention_system, feature_columns, db_available
    
    try:
        # Test database connection
        db_available = test_db_connection()
        if db_available:
            logger.info("✅ Database connection established")
            init_db()  # Initialize database tables
        else:
            logger.warning("⚠️ Database not available, using file-based mode")
        
        # Load intervention system
        intervention_system = InterventionRecommendationSystem()
        feature_columns = intervention_system.feature_columns
        logger.info("✅ Student Success Prediction API started successfully")
        logger.info(f"✅ Model loaded with {len(feature_columns)} features")
        
    except Exception as e:
        logger.error(f"❌ Failed to start API: {e}")
        raise

# Database-specific endpoints
@app.get("/students/{student_id}/predictions")
async def get_student_predictions(
    student_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all predictions for a student"""
    if not db_available:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        student = db.query(Student).filter(Student.id_student == student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        predictions = db.query(RiskPrediction).filter(
            RiskPrediction.student_id == student.id
        ).order_by(RiskPrediction.prediction_date.desc()).all()
        
        return {
            "student_id": student_id,
            "total_predictions": len(predictions),
            "predictions": [
                {
                    "id": p.id,
                    "risk_score": p.risk_score,
                    "risk_category": p.risk_category,
                    "needs_intervention": p.needs_intervention,
                    "prediction_date": p.prediction_date,
                    "model_version": p.model_version,
                    "confidence_score": p.confidence_score
                } for p in predictions
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching student predictions: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch predictions")

@app.get("/analytics/risk-distribution")
async def get_risk_distribution(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get distribution of risk categories"""
    if not db_available:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        from sqlalchemy import func
        
        risk_counts = db.query(
            RiskPrediction.risk_category,
            func.count(RiskPrediction.id).label('count')
        ).group_by(RiskPrediction.risk_category).all()
        
        total_predictions = sum(count for _, count in risk_counts)
        
        distribution = {
            "total_predictions": total_predictions,
            "risk_distribution": {
                category: {
                    "count": count,
                    "percentage": round((count / total_predictions) * 100, 2) if total_predictions > 0 else 0
                } for category, count in risk_counts
            }
        }
        
        return distribution
        
    except Exception as e:
        logger.error(f"Error fetching risk distribution: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch analytics")

@app.post("/students/create")
async def create_student(
    student: StudentData,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new student record"""
    if not db_available:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        # Check if student already exists
        existing = db.query(Student).filter(Student.id_student == student.id_student).first()
        if existing:
            raise HTTPException(status_code=400, detail="Student already exists")
        
        # Create new student
        new_student = create_student_with_features(db, student.dict())
        
        return {
            "message": "Student created successfully",
            "student_id": student.id_student,
            "database_id": new_student.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating student: {e}")
        raise HTTPException(status_code=500, detail="Failed to create student")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")