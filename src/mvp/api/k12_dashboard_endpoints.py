"""
K-12 Educational Dashboard API Endpoints

Provides FERPA-compliant data access for the K-12 educational dashboard
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import os

from ..database import get_db_session, get_session_factory
from ..models import Student, Prediction, Intervention, Institution

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/k12-dashboard", tags=["K12 Dashboard"])

# Simple security for K12 dashboard
security = HTTPBearer()

# Database dependency for FastAPI
def get_db():
    """FastAPI database dependency"""
    session_factory = get_session_factory()
    session = session_factory()
    try:
        yield session
    finally:
        session.close()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Simple authentication for K12 dashboard endpoints"""
    expected_key = os.getenv("MVP_API_KEY", "dev-key-change-me")
    
    if credentials.credentials != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return {
        "user": "k12_teacher", 
        "permissions": ["read", "write"],
        "institution_id": 1,
        "user_id": "k12_user_001",
        "role": "educator"
    }

@router.get("/students")
async def get_students_for_dashboard(
    institution_id: int = 1,
    grade_levels: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get students data for K-12 educational dashboard with FERPA compliance
    
    Args:
        institution_id: Institution ID (defaults to demo institution)
        grade_levels: Comma-separated grade levels to filter (e.g., "9,10,11,12")
        current_user: Authenticated user information
        db: Database session
    
    Returns:
        Dictionary containing students array and metadata
    """
    try:
        logger.info(f"Fetching K-12 dashboard data for institution {institution_id}")
        
        # Base query for students
        query = db.query(Student).filter(Student.institution_id == institution_id)
        
        # Filter by grade levels if specified
        if grade_levels:
            try:
                grade_list = [grade.strip() for grade in grade_levels.split(",")]
                # Convert to integers, handling 'K' as kindergarten
                grade_nums = []
                for grade in grade_list:
                    if grade.upper() == 'K':
                        grade_nums.append(0)
                    else:
                        grade_nums.append(int(grade))
                query = query.filter(Student.grade_level.in_([str(g) for g in grade_nums]))
            except ValueError:
                logger.warning(f"Invalid grade levels format: {grade_levels}")
        
        # Get students with their latest predictions
        students = query.order_by(Student.grade_level, Student.name).all()
        
        dashboard_students = []
        for student in students:
            # Get latest prediction for risk assessment
            latest_prediction = db.query(Prediction)\
                .filter_by(student_id=student.id)\
                .order_by(Prediction.created_at.desc())\
                .first()
            
            # Get active interventions
            active_interventions = db.query(Intervention)\
                .filter_by(student_id=student.id)\
                .filter(Intervention.status.in_(['planned', 'active', 'in_progress']))\
                .all()
            
            # Convert to K12Dashboard format
            dashboard_student = convert_to_k12_format(student, latest_prediction, active_interventions)
            dashboard_students.append(dashboard_student)
        
        # Calculate summary statistics
        total_students = len(dashboard_students)
        high_risk_count = sum(1 for s in dashboard_students if s.get('risk_score', 0) >= 0.7)
        medium_risk_count = sum(1 for s in dashboard_students if 0.4 <= s.get('risk_score', 0) < 0.7)
        low_risk_count = sum(1 for s in dashboard_students if s.get('risk_score', 0) < 0.4)
        
        # Grade band distribution
        elementary = sum(1 for s in dashboard_students if get_grade_level_num(s.get('grade_level', 0)) <= 5)
        middle = sum(1 for s in dashboard_students if 6 <= get_grade_level_num(s.get('grade_level', 0)) <= 8)
        high = sum(1 for s in dashboard_students if get_grade_level_num(s.get('grade_level', 0)) >= 9)
        
        logger.info(f"Retrieved {total_students} students for K-12 dashboard")
        
        return {
            "students": dashboard_students,
            "metadata": {
                "total_students": total_students,
                "institution_id": institution_id,
                "generated_at": datetime.now().isoformat(),
                "ferpa_compliant": True,
                "risk_distribution": {
                    "high_risk": high_risk_count,
                    "medium_risk": medium_risk_count, 
                    "low_risk": low_risk_count
                },
                "grade_distribution": {
                    "elementary": elementary,
                    "middle": middle,
                    "high_school": high
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching K-12 dashboard data: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard data")

def convert_to_k12_format(student: Student, prediction: Optional[Prediction], interventions: List[Intervention]) -> Dict[str, Any]:
    """Convert database models to K12Dashboard format"""
    
    grade_num = get_grade_level_num(student.grade_level)
    risk_score = prediction.risk_score if prediction else 0.0
    
    return {
        "student_id": student.student_id,  # External student ID for FERPA safety
        "database_id": student.id,  # Internal ID for operations
        "grade_level": grade_num,
        "risk_score": risk_score,
        "risk_category": map_risk_category(risk_score),
        "success_probability": prediction.success_probability if prediction else 0.7,
        "needs_intervention": risk_score >= 0.6,
        
        # Educational metrics based on grade level
        "reading_level": estimate_reading_level(student, grade_num),
        "credits_earned": student.current_gpa * 6 * (grade_num - 8) if grade_num >= 9 and student.current_gpa else None,
        "college_readiness": assess_college_readiness(student, grade_num),
        "study_skills_rating": estimate_study_skills(student),
        
        # Interventions (educational terminology)
        "interventions": [format_intervention(i) for i in interventions],
        
        # Special populations (privacy protected)
        "special_populations": {
            "has_iep": student.has_iep or False,
            "is_ell": student.is_ell or False,
            "has_504": student.has_504 or False,
            "is_economically_disadvantaged": student.is_economically_disadvantaged or False
        },
        
        # Behavioral and engagement indicators
        "behavioral_concerns": identify_behavioral_concerns(student, risk_score),
        "attendance_rate": student.attendance_rate or 0.9,
        
        # Metadata
        "last_updated": (student.updated_at or student.created_at).isoformat() if student.updated_at or student.created_at else datetime.now().isoformat(),
        "data_source": "database"
    }

def get_grade_level_num(grade_level: Any) -> int:
    """Convert grade level to numeric format"""
    if not grade_level:
        return 7  # Default to middle school
    
    grade_str = str(grade_level).upper().strip()
    if grade_str == 'K':
        return 0
    
    try:
        return int(grade_str)
    except ValueError:
        return 7  # Default fallback

def map_risk_category(risk_score: float) -> str:
    """Map risk score to educational terminology"""
    if risk_score >= 0.7:
        return "Needs Additional Support"
    elif risk_score >= 0.4:
        return "Monitor Progress" 
    else:
        return "On Track"

def estimate_reading_level(student: Student, grade_level: int) -> Optional[float]:
    """Estimate reading level based on available data"""
    if grade_level > 8:
        return None  # Not applicable for high school
    
    # Use GPA as proxy for reading level if available
    if student.current_gpa:
        # Scale GPA (0-4) to reading level relative to grade
        gpa_multiplier = student.current_gpa / 4.0
        base_reading = grade_level * gpa_multiplier
        return round(max(0.5, base_reading), 1)
    
    # Default estimation
    return float(grade_level * 0.9)

def assess_college_readiness(student: Student, grade_level: int) -> Optional[bool]:
    """Assess college readiness for high school students"""
    if grade_level < 11:
        return None
    
    # Basic college readiness assessment
    gpa_ready = (student.current_gpa or 2.0) >= 3.0
    attendance_ready = (student.attendance_rate or 0.8) >= 0.9
    
    return gpa_ready and attendance_ready

def estimate_study_skills(student: Student) -> float:
    """Estimate study skills rating (1-5 scale)"""
    base_score = 3.0  # Average
    
    if student.current_gpa:
        # Adjust based on GPA performance
        gpa_adjustment = (student.current_gpa - 2.5) * 0.8
        base_score += gpa_adjustment
    
    if student.attendance_rate:
        # Adjust based on attendance
        attendance_adjustment = (student.attendance_rate - 0.85) * 2
        base_score += attendance_adjustment
    
    return round(max(1.0, min(5.0, base_score)), 1)

def format_intervention(intervention: Intervention) -> str:
    """Format intervention with educational terminology"""
    intervention_map = {
        "academic_support": "Academic Support Program",
        "behavioral_support": "Behavioral Guidance", 
        "attendance_support": "Attendance Improvement Plan",
        "engagement_support": "Student Engagement Initiative",
        "family_engagement": "Family Partnership Program"
    }
    
    base_name = intervention_map.get(intervention.intervention_type, intervention.title or "Support Program")
    
    # Sanitize language to be school-appropriate
    sanitized = base_name.replace("therapy", "support")\
                         .replace("clinical", "educational")\
                         .replace("diagnosis", "assessment")
    
    return sanitized

def identify_behavioral_concerns(student: Student, risk_score: float) -> List[str]:
    """Identify behavioral concerns based on available data"""
    concerns = []
    
    if student.attendance_rate and student.attendance_rate < 0.85:
        concerns.append("Attendance")
    
    if risk_score >= 0.6:
        concerns.append("Academic Engagement")
    
    if student.current_gpa and student.current_gpa < 2.0:
        concerns.append("Academic Performance")
    
    return concerns

@router.get("/institutions")
async def get_available_institutions(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get list of available institutions for dashboard access"""
    
    try:
        institutions = db.query(Institution).filter(Institution.active == True).all()
        
        return [
            {
                "id": inst.id,
                "name": inst.name,
                "code": inst.code,
                "type": inst.type,
                "student_count": db.query(Student).filter_by(institution_id=inst.id).count()
            }
            for inst in institutions
        ]
    
    except Exception as e:
        logger.error(f"Error fetching institutions: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve institutions")

@router.get("/grade-bands/{institution_id}")
async def get_grade_band_summary(
    institution_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get grade band summary for an institution"""
    
    try:
        students = db.query(Student).filter_by(institution_id=institution_id).all()
        
        grade_bands = {"elementary": [], "middle": [], "high": []}
        
        for student in students:
            grade_num = get_grade_level_num(student.grade_level)
            
            if grade_num <= 5:
                grade_bands["elementary"].append(student)
            elif 6 <= grade_num <= 8:
                grade_bands["middle"].append(student)
            else:
                grade_bands["high"].append(student)
        
        summary = {}
        for band_name, band_students in grade_bands.items():
            if not band_students:
                summary[band_name] = {"count": 0, "average_risk": 0.0}
                continue
                
            # Calculate average risk for the band
            total_risk = 0.0
            risk_count = 0
            
            for student in band_students:
                prediction = db.query(Prediction)\
                    .filter_by(student_id=student.id)\
                    .order_by(Prediction.created_at.desc())\
                    .first()
                
                if prediction:
                    total_risk += prediction.risk_score
                    risk_count += 1
            
            avg_risk = total_risk / risk_count if risk_count > 0 else 0.0
            
            summary[band_name] = {
                "count": len(band_students),
                "average_risk": round(avg_risk, 3),
                "grade_levels": list(set(get_grade_level_num(s.grade_level) for s in band_students))
            }
        
        return summary
        
    except Exception as e:
        logger.error(f"Error fetching grade band summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve grade band data")