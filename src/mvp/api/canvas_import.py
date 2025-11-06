#!/usr/bin/env python3
"""
Canvas Import API Endpoints
Handles importing Canvas mock data into the database
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.mvp.security import auth_dependency
from mvp.database import get_db_session
from mvp.models import Student, Institution, Prediction
from examples.mock_data.canvas_mock_data import CanvasMockDataGenerator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/canvas-import", tags=["Canvas Import"])

@router.post("/import-courses")
async def import_canvas_courses(
    request: Request,
    current_user: dict = Depends(auth_dependency)
):
    """Import selected Canvas courses as mock student data"""
    
    try:
        body = await request.json()
        selected_course_ids = body.get('course_ids', [])
        import_options = body.get('options', {})
        
        logger.info(f"Starting Canvas import for courses: {selected_course_ids}")
        
        # Generate Canvas mock data
        generator = CanvasMockDataGenerator()
        canvas_students = generator.generate_all_canvas_students(selected_course_ids)
        
        # Get import summary for reporting
        summary = generator.get_import_summary(selected_course_ids)
        
        # Import into database
        imported_count = 0
        predictions_generated = 0
        
        with get_db_session() as db:
            # Get or create default institution
            institution = db.query(Institution).first()
            if not institution:
                institution = Institution(
                    name="Canvas Demo School",
                    code="CANVAS_DEMO",
                    type="K12",
                    active=True
                )
                db.add(institution)
                db.flush()
            
            # Process each Canvas student
            for student_data in canvas_students:
                try:
                    # Check if student already exists
                    existing_student = db.query(Student).filter(
                        Student.student_id == student_data['student_id'],
                        Student.institution_id == institution.id
                    ).first()
                    
                    if existing_student:
                        logger.info(f"Student {student_data['student_id']} already exists, skipping")
                        continue
                    
                    # Create new student record
                    student = Student(
                        institution_id=institution.id,
                        student_id=student_data['student_id'],
                        sis_id=student_data['sis_id'],
                        name=student_data['name'],
                        grade_level=student_data['grade_level'],
                        birth_date=student_data['birth_date'],
                        gender=student_data['gender'],
                        ethnicity=student_data['ethnicity'],
                        current_gpa=student_data['current_gpa'],
                        previous_gpa=student_data['previous_gpa'],
                        attendance_rate=student_data['attendance_rate'],
                        study_hours_week=student_data['study_hours_week'],
                        extracurricular=student_data['extracurricular'],
                        parent_education=student_data['parent_education'],
                        socioeconomic_status=student_data['socioeconomic_status'],
                        enrollment_status=student_data['enrollment_status'],
                        enrollment_date=student_data['enrollment_date'],
                        is_ell=student_data['is_ell'],
                        has_iep=student_data['has_iep'],
                        has_504=student_data['has_504'],
                        is_economically_disadvantaged=student_data['is_economically_disadvantaged'],
                        email=student_data['email'],
                        parent_email=student_data['parent_email'],
                        phone=student_data['phone'],
                        parent_phone=student_data['parent_phone'],
                        last_activity=student_data['last_activity']
                    )
                    
                    db.add(student)
                    db.flush()  # Get the student ID
                    
                    imported_count += 1
                    
                    # Generate ML predictions if requested
                    if import_options.get('generate_predictions', True):
                        try:
                            # Create a simplified student record for ML prediction
                            student_features = {
                                'current_gpa': student_data['current_gpa'],
                                'attendance_rate': student_data['attendance_rate'],
                                'study_hours_week': student_data['study_hours_week'],
                                'parent_education': student_data['parent_education'],
                                'socioeconomic_status': student_data['socioeconomic_status'],
                                'extracurricular': student_data['extracurricular'],
                                'is_ell': student_data['is_ell'],
                                'has_iep': student_data['has_iep'],
                                'is_economically_disadvantaged': student_data['is_economically_disadvantaged']
                            }
                            
                            # Generate risk prediction using simple rules (since we don't have full ML features)
                            risk_score = calculate_risk_score(student_features)
                            success_probability = 1.0 - risk_score
                            
                            # Determine risk category
                            if risk_score > 0.7:
                                risk_category = "High Risk"
                                needs_intervention = True
                            elif risk_score > 0.4:
                                risk_category = "Moderate Risk" 
                                needs_intervention = True
                            else:
                                risk_category = "Low Risk"
                                needs_intervention = False
                            
                            # Create prediction record
                            prediction = Prediction(
                                institution_id=institution.id,
                                student_id=student.id,
                                model_name="canvas_import_risk_assessment",
                                risk_score=risk_score,
                                success_probability=success_probability,
                                risk_category=risk_category,
                                needs_intervention=needs_intervention,
                                confidence_score=0.85,  # Fixed confidence for demo
                                prediction_date=datetime.now(),
                                model_version="1.0"
                            )
                            
                            db.add(prediction)
                            predictions_generated += 1
                            
                        except Exception as e:
                            logger.warning(f"Could not generate prediction for {student_data['student_id']}: {e}")
                    
                except Exception as e:
                    logger.error(f"Error importing student {student_data['student_id']}: {e}")
                    continue
            
            # Commit all changes
            db.commit()
            
            logger.info(f"Canvas import completed: {imported_count} students, {predictions_generated} predictions")
            
            return JSONResponse({
                "status": "success",
                "message": "Canvas courses imported successfully",
                "summary": {
                    "students_imported": imported_count,
                    "predictions_generated": predictions_generated,
                    "courses_imported": summary['total_courses'],
                    "grade_levels": summary['grade_levels'],
                    "subjects": summary['subjects']
                },
                "details": summary
            })
            
    except Exception as e:
        logger.error(f"Canvas import failed: {e}")
        raise HTTPException(status_code=500, detail=f"Canvas import failed: {str(e)}")

@router.get("/import-status")
async def get_import_status(
    current_user: dict = Depends(auth_dependency)
):
    """Get status of Canvas imports"""
    
    try:
        with get_db_session() as db:
            # Get Canvas students (those with CVS_ prefix in student_id)
            canvas_students = db.query(Student).filter(
                Student.student_id.like('CVS_%')
            ).all()
            
            if not canvas_students:
                return JSONResponse({
                    "status": "no_imports",
                    "message": "No Canvas imports found",
                    "student_count": 0
                })
            
            # Group by course (extracted from student_id)
            courses_data = {}
            total_students = len(canvas_students)
            
            for student in canvas_students:
                # Extract course code from student ID (CVS_MATH-ALG1-P1_001)
                parts = student.student_id.split('_')
                if len(parts) >= 2:
                    course_code = parts[1]
                    if course_code not in courses_data:
                        courses_data[course_code] = {
                            'course_code': course_code,
                            'student_count': 0,
                            'grade_levels': set(),
                            'last_import': None
                        }
                    
                    courses_data[course_code]['student_count'] += 1
                    if student.grade_level:
                        courses_data[course_code]['grade_levels'].add(student.grade_level)
                    
                    # Update last import time
                    if (courses_data[course_code]['last_import'] is None or 
                        student.created_at > courses_data[course_code]['last_import']):
                        courses_data[course_code]['last_import'] = student.created_at
            
            # Convert sets to lists for JSON serialization
            for course in courses_data.values():
                course['grade_levels'] = list(course['grade_levels'])
                if course['last_import']:
                    course['last_import'] = course['last_import'].isoformat()
            
            return JSONResponse({
                "status": "success",
                "total_canvas_students": total_students,
                "courses_imported": len(courses_data),
                "courses": list(courses_data.values())
            })
            
    except Exception as e:
        logger.error(f"Error getting import status: {e}")
        raise HTTPException(status_code=500, detail=f"Could not get import status: {str(e)}")

@router.delete("/clear-canvas-data")
async def clear_canvas_data(
    current_user: dict = Depends(auth_dependency)
):
    """Clear all Canvas imported data"""
    
    try:
        with get_db_session() as db:
            # Delete predictions for Canvas students
            canvas_students = db.query(Student).filter(
                Student.student_id.like('CVS_%')
            ).all()
            
            canvas_student_ids = [s.id for s in canvas_students]
            
            if canvas_student_ids:
                # Delete predictions
                predictions_deleted = db.query(Prediction).filter(
                    Prediction.student_id.in_(canvas_student_ids)
                ).delete(synchronize_session=False)
                
                # Delete students
                students_deleted = db.query(Student).filter(
                    Student.student_id.like('CVS_%')
                ).delete(synchronize_session=False)
                
                db.commit()
                
                logger.info(f"Cleared Canvas data: {students_deleted} students, {predictions_deleted} predictions")
                
                return JSONResponse({
                    "status": "success",
                    "message": "Canvas data cleared successfully",
                    "students_deleted": students_deleted,
                    "predictions_deleted": predictions_deleted
                })
            else:
                return JSONResponse({
                    "status": "no_data",
                    "message": "No Canvas data found to clear"
                })
                
    except Exception as e:
        logger.error(f"Error clearing Canvas data: {e}")
        raise HTTPException(status_code=500, detail=f"Could not clear Canvas data: {str(e)}")

def calculate_risk_score(student_features: Dict[str, Any]) -> float:
    """Calculate a simple risk score based on key student features"""
    
    risk_score = 0.0
    
    # GPA factor (0.4 weight)
    gpa = student_features.get('current_gpa', 3.0)
    if gpa < 2.0:
        risk_score += 0.4
    elif gpa < 2.5:
        risk_score += 0.3
    elif gpa < 3.0:
        risk_score += 0.15
    
    # Attendance factor (0.3 weight)
    attendance = student_features.get('attendance_rate', 0.9)
    if attendance < 0.7:
        risk_score += 0.3
    elif attendance < 0.8:
        risk_score += 0.2
    elif attendance < 0.9:
        risk_score += 0.1
    
    # Socioeconomic factors (0.2 weight)
    if student_features.get('is_economically_disadvantaged', False):
        risk_score += 0.1
    
    parent_education = student_features.get('parent_education', 3)
    if parent_education <= 2:
        risk_score += 0.1
    
    # Special populations (0.1 weight)
    if student_features.get('has_iep', False):
        risk_score += 0.05
    if student_features.get('is_ell', False):
        risk_score += 0.05
    
    # Protective factors (negative risk)
    study_hours = student_features.get('study_hours_week', 8)
    if study_hours > 12:
        risk_score -= 0.1
    
    extracurricular = student_features.get('extracurricular', 1)
    if extracurricular >= 2:
        risk_score -= 0.05
    
    # Clamp between 0 and 1
    return max(0.0, min(1.0, risk_score))
