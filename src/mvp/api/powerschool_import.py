"""
PowerSchool SIS Import API Endpoints
Handles PowerSchool student data import with database persistence
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
import json
import logging
from datetime import datetime

# Import authentication  
from src.mvp.security import auth_dependency

# Import mock data generator
from examples.mock_data.powerschool_mock_data import powerschool_data_generator

# Import database functionality
from src.mvp.database import get_db_session
from src.mvp.models import Student, Prediction, Institution

# Setup logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/powerschool-import", tags=["PowerSchool SIS"])

# Using standard authentication from security module

@router.get("/schools")
async def get_powerschool_schools(current_user: dict = Depends(auth_dependency)):
    """Get list of available PowerSchool schools"""
    try:
        schools = powerschool_data_generator.get_schools_summary()
        
        return JSONResponse({
            "success": True,
            "schools": schools,
            "total_schools": len(schools)
        })
        
    except Exception as e:
        logger.error(f"Error fetching PowerSchool schools: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch schools")

@router.post("/test-connection")
async def test_powerschool_connection(
    request: Request,
    current_user: dict = Depends(auth_dependency)
):
    """Test PowerSchool SIS connection with provided credentials"""
    try:
        body = await request.json()
        server_url = body.get('server_url', '')
        username = body.get('username', '')
        password = body.get('password', '')
        
        # Validate required fields
        if not all([server_url, username, password]):
            raise HTTPException(status_code=400, detail="Missing required connection parameters")
        
        # Mock connection test - in production, this would test actual PowerSchool API
        schools = powerschool_data_generator.get_schools_summary()
        
        return JSONResponse({
            "success": True,
            "message": "Connection successful",
            "server_info": {
                "server_url": server_url,
                "version": "PowerSchool 24.5.0",
                "district_name": "Sample School District"
            },
            "schools_found": len(schools),
            "schools": schools
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing PowerSchool connection: {e}")
        raise HTTPException(status_code=500, detail="Connection test failed")

@router.post("/import-schools")
async def import_powerschool_schools(
    request: Request,
    current_user: dict = Depends(auth_dependency)
):
    """Import student data from selected PowerSchool schools"""
    try:
        body = await request.json()
        selected_school_ids = body.get('school_ids', [])
        options = body.get('options', {})
        
        if not selected_school_ids:
            raise HTTPException(status_code=400, detail="No schools selected for import")
        
        logger.info(f"Starting PowerSchool import for schools: {selected_school_ids}")
        
        # Calculate total expected students for selected schools
        schools_info = powerschool_data_generator.get_schools_summary()
        total_expected = 0
        for school in schools_info:
            if school['id'] in selected_school_ids:
                total_expected += school['expected_students']
        
        # Generate the correct number of students to match UI expectations
        # Cap at reasonable limit for demo purposes
        students_to_generate = min(total_expected, 500)
        all_students = powerschool_data_generator.generate_powerschool_students(count=students_to_generate)
        
        # Filter students by selected schools
        filtered_students = [
            student for student in all_students 
            if student['school_id'] in selected_school_ids
        ]
        
        if not filtered_students:
            return JSONResponse({
                "success": True,
                "message": "No students found in selected schools",
                "summary": {
                    "schools_imported": 0,
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
            
            for ps_student in filtered_students:
                try:
                    # Convert PowerSchool format to database Student model
                    student = Student(
                        institution_id=demo_institution.id,
                        student_id=ps_student['student_id'],
                        sis_id=ps_student['student_id'],
                        name=ps_student['full_name'],
                        email=f"{ps_student['first_name'].lower()}.{ps_student['last_name'].lower()}@school.edu",
                        
                        # Demographics
                        gender=ps_student['gender'],
                        ethnicity=ps_student['ethnicity'],
                        grade_level=ps_student['grade_level'],
                        
                        # Academic data
                        current_gpa=ps_student['gpa'],
                        enrollment_status='active',
                        
                        # Attendance data
                        attendance_rate=ps_student['attendance_rate'],
                        
                        # Special populations
                        has_iep=(ps_student['special_population'] == 'IEP'),
                        is_ell=(ps_student['special_population'] == 'ELL'),
                        has_504=(ps_student['special_population'] == '504 Plan'),
                        
                        # Socioeconomic
                        is_economically_disadvantaged=(ps_student['socioeconomic_status'] in ['Free Lunch', 'Reduced Lunch', 'Low Income'])
                    )
                    
                    db.add(student)
                    students_imported += 1
                    
                    # Generate basic prediction if requested
                    if options.get('generate_predictions', True):
                        # Simple risk calculation based on multiple factors
                        risk_score = calculate_risk_score(ps_student)
                        
                        prediction = Prediction(
                            student_id=student.student_id,
                            institution_id=demo_institution.id,
                            model_version="powerschool_import_v1",
                            prediction_type="risk_assessment",
                            risk_score=risk_score,
                            success_probability=1.0 - risk_score,
                            risk_factors=json.dumps(get_risk_factors(ps_student)),
                            created_at=datetime.now()
                        )
                        db.add(prediction)
                        predictions_created += 1
                
                except Exception as student_error:
                    logger.error(f"Error processing student {ps_student.get('student_id', 'unknown')}: {student_error}")
                    continue
            
            db.commit()
        
        # Import summary
        summary = {
            "schools_imported": len(selected_school_ids),
            "students_imported": students_imported,
            "students_with_predictions": predictions_created,
            "data_source": "powerschool",
            "import_timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"PowerSchool import completed: {summary}")
        
        return JSONResponse({
            "success": True,
            "message": f"Successfully imported {students_imported} students from {len(selected_school_ids)} schools",
            "summary": summary
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing PowerSchool data: {e}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

@router.get("/import-status")
async def get_powerschool_import_status(current_user: dict = Depends(auth_dependency)):
    """Get current PowerSchool import status and statistics"""
    try:
        with get_db_session() as db:
            # Count PowerSchool students
            powerschool_students = db.query(Student).filter_by(data_source='powerschool').count()
            
            # Get recent imports
            recent_students = db.query(Student).filter_by(data_source='powerschool').order_by(Student.last_updated.desc()).limit(5).all()
            
            # School breakdown
            school_breakdown = {}
            if powerschool_students > 0:
                schools_data = db.query(Student.school_name).filter_by(data_source='powerschool').distinct().all()
                for (school_name,) in schools_data:
                    if school_name:
                        count = db.query(Student).filter_by(data_source='powerschool', school_name=school_name).count()
                        school_breakdown[school_name] = count
            
            return JSONResponse({
                "success": True,
                "total_powerschool_students": powerschool_students,
                "school_breakdown": school_breakdown,
                "recent_imports": [
                    {
                        "student_id": s.student_id,
                        "name": f"{s.first_name} {s.last_name}",
                        "school": s.school_name,
                        "grade": s.grade_level,
                        "imported_at": s.last_updated.isoformat() if s.last_updated else None
                    }
                    for s in recent_students
                ],
                "last_import": recent_students[0].last_updated.isoformat() if recent_students else None
            })
            
    except Exception as e:
        logger.error(f"Error getting PowerSchool import status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get import status")

def calculate_risk_score(student_data: Dict[str, Any]) -> float:
    """Calculate risk score based on PowerSchool student data"""
    risk_score = 0.0
    
    # Academic performance risk
    gpa = student_data.get('gpa', 4.0)
    if gpa < 2.0:
        risk_score += 0.3
    elif gpa < 2.5:
        risk_score += 0.2
    elif gpa < 3.0:
        risk_score += 0.1
    
    # Attendance risk
    attendance_rate = student_data.get('attendance_rate', 95.0)
    if attendance_rate < 85:
        risk_score += 0.25
    elif attendance_rate < 90:
        risk_score += 0.15
    elif attendance_rate < 95:
        risk_score += 0.05
    
    # Behavioral risk
    disciplinary_incidents = student_data.get('disciplinary_incidents', 0)
    if disciplinary_incidents > 2:
        risk_score += 0.2
    elif disciplinary_incidents > 0:
        risk_score += 0.1
    
    # Special population adjustments
    if student_data.get('special_population') in ['IEP', 'ELL']:
        risk_score += 0.1
    
    # Socioeconomic risk
    if student_data.get('socioeconomic_status') in ['Low Income', 'Free Lunch']:
        risk_score += 0.05
    
    # Grade level considerations (middle school transition risk)
    if student_data.get('grade_level') in ['6', '7']:
        risk_score += 0.05
    
    return min(1.0, max(0.0, risk_score))

def get_risk_factors(student_data: Dict[str, Any]) -> List[str]:
    """Identify specific risk factors for a student"""
    factors = []
    
    if student_data.get('gpa', 4.0) < 2.5:
        factors.append("Low Academic Performance")
    
    if student_data.get('attendance_rate', 95.0) < 90:
        factors.append("Poor Attendance")
    
    if student_data.get('disciplinary_incidents', 0) > 0:
        factors.append("Behavioral Issues")
    
    if student_data.get('special_population') == 'IEP':
        factors.append("Special Education Services")
    
    if student_data.get('special_population') == 'ELL':
        factors.append("English Language Learner")
    
    if student_data.get('socioeconomic_status') in ['Low Income', 'Free Lunch']:
        factors.append("Economic Disadvantage")
    
    if student_data.get('grade_level') in ['6', '7', '9']:
        factors.append("Grade Transition Period")
    
    return factors
