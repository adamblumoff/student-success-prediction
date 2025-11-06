"""
Google Classroom Import API Endpoints
Handles Google Classroom student data import with database persistence
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
import json
import logging
import os
from datetime import datetime

# Import authentication  
from src.mvp.security import auth_dependency

# Import mock data generator
from src.mvp.services.google_classroom_mock_data import google_classroom_data_generator

# Import database functionality
from src.mvp.database import get_db_session
from src.mvp.models import Student, Prediction, Institution

# Setup logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/google-classroom-import", tags=["Google Classroom"])

# Using standard authentication from security module

@router.get("/classrooms")
async def get_google_classrooms(current_user: dict = Depends(auth_dependency)):
    """Get list of available Google Classrooms"""
    try:
        classrooms = google_classroom_data_generator.get_classrooms_summary()
        
        return JSONResponse({
            "success": True,
            "classrooms": classrooms,
            "total_classrooms": len(classrooms)
        })
        
    except Exception as e:
        logger.error(f"Error fetching Google Classrooms: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch classrooms")

@router.post("/test-connection")
async def test_google_classroom_connection(
    request: Request,
    current_user: dict = Depends(auth_dependency)
):
    """Test Google Classroom connection with provided credentials"""
    try:
        body = await request.json()
        service_account_key = body.get('service_account_key', '')
        domain = body.get('domain', '')
        admin_email = body.get('admin_email', '')
        
        # Validate required fields
        if not all([service_account_key, domain, admin_email]):
            raise HTTPException(status_code=400, detail="Missing required connection parameters")
        
        # Mock connection test - in production, this would test actual Google Classroom API
        classrooms = google_classroom_data_generator.get_classrooms_summary()
        
        return JSONResponse({
            "success": True,
            "message": "Connection successful",
            "service_info": {
                "domain": domain,
                "admin_email": admin_email,
                "api_version": "Google Classroom API v1",
                "district_name": "Demo Educational District"
            },
            "classrooms_found": len(classrooms),
            "classrooms": classrooms
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing Google Classroom connection: {e}")
        raise HTTPException(status_code=500, detail="Connection test failed")

@router.post("/import-classrooms")
async def import_google_classrooms(
    request: Request,
    current_user: dict = Depends(auth_dependency)
):
    """Import student data from selected Google Classrooms"""
    try:
        body = await request.json()
        selected_classroom_ids = body.get('classroom_ids', [])
        options = body.get('options', {})
        
        if not selected_classroom_ids:
            raise HTTPException(status_code=400, detail="No classrooms selected for import")
        
        logger.info(f"Starting Google Classroom import for classrooms: {selected_classroom_ids}")
        
        # Calculate total expected students for selected classrooms
        classrooms_info = google_classroom_data_generator.get_classrooms_summary()
        total_expected = 0
        for classroom in classrooms_info:
            if classroom['id'] in selected_classroom_ids:
                total_expected += classroom['expected_students']
        
        # Generate the correct number of students to match UI expectations
        # Cap at reasonable limit for demo purposes
        students_to_generate = min(total_expected, 500)
        all_students = google_classroom_data_generator.generate_google_classroom_students(count=students_to_generate)
        
        # Filter students by selected classrooms
        filtered_students = [
            student for student in all_students 
            if student['classroom_id'] in selected_classroom_ids
        ]
        
        if not filtered_students:
            return JSONResponse({
                "success": True,
                "message": "No students found in selected classrooms",
                "summary": {
                    "classrooms_imported": 0,
                    "students_imported": 0,
                    "students_with_predictions": 0
                }
            })
        
        # Convert to database format and save
        students_imported = 0
        predictions_created = 0
        
        with get_db_session() as db:
            # Use the same demo institution as Canvas integration
            demo_institution = db.query(Institution).filter(
                Institution.code == "MVP_DEMO"
            ).first()
            
            if not demo_institution:
                demo_institution = Institution(
                    name="Demo Educational District",
                    code="MVP_DEMO",
                    type="K12_District",
                    timezone="America/New_York",
                    active=True
                )
                db.add(demo_institution)
                db.flush()
            
            for gc_student in filtered_students:
                try:
                    # Convert Google Classroom format to database Student model
                    student = Student(
                        institution_id=demo_institution.id,
                        student_id=gc_student['student_id'],
                        sis_id=gc_student['student_id'],
                        name=gc_student['full_name'],
                        email=gc_student['email'],
                        
                        # Demographics
                        gender=gc_student['gender'],
                        ethnicity=gc_student['ethnicity'],
                        grade_level=gc_student['grade_level'],
                        
                        # Academic data (convert percentage to GPA scale)
                        current_gpa=round(gc_student['overall_grade'] / 25, 2),  # Convert 0-100 to 0-4 scale
                        enrollment_status='active',
                        
                        # Google Classroom specific fields can be stored as additional data
                        # Using available Student model fields
                        parent_email=gc_student['guardian_email']
                    )
                    
                    db.add(student)
                    students_imported += 1
                    
                    # Generate basic prediction if requested
                    if options.get('generate_predictions', True):
                        # Simple risk calculation based on Google Classroom data
                        risk_score = calculate_risk_score(gc_student)
                        
                        # Note: Prediction model needs to be updated to handle the new fields
                        # For now, skip prediction creation to avoid the 'prediction_type' error
                        # prediction = Prediction(
                        #     student_id=student.student_id,
                        #     institution_id=demo_institution.id,
                        #     model_version="google_classroom_import_v1",
                        #     risk_score=risk_score,
                        #     success_probability=1.0 - risk_score,
                        #     risk_factors=json.dumps(get_risk_factors(gc_student)),
                        #     created_at=datetime.now()
                        # )
                        # db.add(prediction)
                        # predictions_created += 1
                
                except Exception as student_error:
                    logger.error(f"Error processing student {gc_student.get('student_id', 'unknown')}: {student_error}")
                    continue
            
            db.commit()
        
        # Import summary
        summary = {
            "classrooms_imported": len(selected_classroom_ids),
            "students_imported": students_imported,
            "students_with_predictions": predictions_created,
            "data_source": "google_classroom",
            "import_timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Google Classroom import completed: {summary}")
        
        return JSONResponse({
            "success": True,
            "message": f"Successfully imported {students_imported} students from {len(selected_classroom_ids)} classrooms",
            "summary": summary
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing Google Classroom data: {e}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

@router.get("/import-status")
async def get_google_classroom_import_status(current_user: dict = Depends(auth_dependency)):
    """Get current Google Classroom import status and statistics"""
    try:
        with get_db_session() as db:
            # Count Google Classroom students (we'll identify them by email domain or other means)
            # For now, count all students since we're using the same institution
            total_students = db.query(Student).filter_by(institution_id=1).count()
            
            # Get recent imports
            recent_students = db.query(Student).filter_by(institution_id=1).order_by(Student.created_at.desc()).limit(5).all()
            
            return JSONResponse({
                "success": True,
                "total_students": total_students,
                "recent_imports": [
                    {
                        "student_id": s.student_id,
                        "name": s.name,
                        "email": s.email,
                        "grade": s.grade_level,
                        "imported_at": s.created_at.isoformat() if s.created_at else None
                    }
                    for s in recent_students
                ],
                "last_import": recent_students[0].created_at.isoformat() if recent_students else None
            })
            
    except Exception as e:
        logger.error(f"Error getting Google Classroom import status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get import status")

def calculate_risk_score(student_data: Dict[str, Any]) -> float:
    """Calculate risk score based on Google Classroom student data"""
    risk_score = 0.0
    
    # Academic performance risk (based on overall grade)
    overall_grade = student_data.get('overall_grade', 85.0)
    if overall_grade < 60:
        risk_score += 0.3
    elif overall_grade < 70:
        risk_score += 0.2
    elif overall_grade < 80:
        risk_score += 0.1
    
    # Participation risk
    participation = student_data.get('participation_level', 'Medium')
    if participation == 'Low':
        risk_score += 0.25
    elif participation == 'Medium':
        risk_score += 0.1
    
    # Submission pattern risk
    submission_pattern = student_data.get('submission_pattern', 'Usually On Time')
    if submission_pattern == 'Often Late':
        risk_score += 0.2
    elif submission_pattern == 'Sometimes Late':
        risk_score += 0.1
    
    # Assignment completion risk
    assignment_count = student_data.get('assignment_count', 15)
    assignments_submitted = student_data.get('assignments_submitted', 15)
    if assignment_count > 0:
        completion_rate = assignments_submitted / assignment_count
        if completion_rate < 0.7:
            risk_score += 0.15
        elif completion_rate < 0.85:
            risk_score += 0.05
    
    return min(1.0, max(0.0, risk_score))

def get_risk_factors(student_data: Dict[str, Any]) -> List[str]:
    """Identify specific risk factors for a student"""
    factors = []
    
    if student_data.get('overall_grade', 85.0) < 70:
        factors.append("Low Academic Performance")
    
    if student_data.get('participation_level', 'Medium') == 'Low':
        factors.append("Low Class Participation")
    
    if student_data.get('submission_pattern', 'Usually On Time') in ['Often Late', 'Sometimes Late']:
        factors.append("Late Assignment Submissions")
    
    assignment_count = student_data.get('assignment_count', 15)
    assignments_submitted = student_data.get('assignments_submitted', 15)
    if assignment_count > 0 and (assignments_submitted / assignment_count) < 0.8:
        factors.append("Incomplete Assignments")
    
    on_time_rate = student_data.get('on_time_submissions', 15) / max(assignment_count, 1)
    if on_time_rate < 0.7:
        factors.append("Frequent Late Submissions")
    
    return factors
