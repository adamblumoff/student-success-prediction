#!/usr/bin/env python3
"""
PowerSchool SIS Integration API Endpoints

Handles PowerSchool SIS connection, school management, and comprehensive
student data synchronization for enhanced predictions.
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from pathlib import Path
import sys
import logging
from datetime import datetime

# Add src directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))
from mvp.security import get_current_user_secure as get_current_user
from mvp.database import save_predictions_batch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/powerschool", tags=["PowerSchool SIS"])

@router.get("/health")
async def powerschool_health():
    return JSONResponse({
        'status': 'healthy',
        'service': 'PowerSchool SIS Integration'
    })
@router.post("/connect")
async def connect_powerschool_sis(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Connect to PowerSchool SIS and test authentication"""
    try:
        body = await request.json()
        base_url = body.get('base_url', '').strip()
        client_id = body.get('client_id', '').strip()
        client_secret = body.get('client_secret', '').strip()
        
        if not all([base_url, client_id, client_secret]):
            raise HTTPException(status_code=400, detail="PowerSchool URL, client ID, and client secret are required")
        
        # Import PowerSchool integration
        from integrations.powerschool_sis import create_powerschool_integration
        
        # Create PowerSchool integration
        ps = create_powerschool_integration(base_url, client_id, client_secret)
        
        # Test connection
        connection_result = ps.test_connection()
        
        if connection_result['status'] == 'success':
            return JSONResponse({
                'status': 'success',
                'message': 'Successfully connected to PowerSchool SIS',
                'district_info': {
                    'name': connection_result.get('district_name'),
                    'id': connection_result.get('district_id'),
                    'accessible_students': connection_result.get('accessible_students', False),
                    'rate_limit_remaining': connection_result.get('rate_limit_remaining', 0),
                    'token_expires_in': connection_result.get('token_expires_in', 0)
                },
                'permissions': connection_result.get('permissions', {})
            })
        else:
            raise HTTPException(status_code=400, detail=f"PowerSchool connection failed: {connection_result.get('error')}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error connecting to PowerSchool: {e}")
        raise HTTPException(status_code=500, detail=f"PowerSchool connection error: {str(e)}")

@router.post("/schools")
async def get_powerschool_schools(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Get list of schools from PowerSchool SIS"""
    try:
        body = await request.json()
        base_url = body.get('base_url', '').strip()
        client_id = body.get('client_id', '').strip()
        client_secret = body.get('client_secret', '').strip()
        
        if not all([base_url, client_id, client_secret]):
            raise HTTPException(status_code=400, detail="PowerSchool credentials required")
        
        from integrations.powerschool_sis import create_powerschool_integration
        ps = create_powerschool_integration(base_url, client_id, client_secret)
        
        # Get schools
        schools = ps.get_schools()
        
        return JSONResponse({
            'status': 'success',
            'schools': schools,
            'total_schools': len(schools)
        })
        
    except Exception as e:
        logger.error(f"Error fetching PowerSchool schools: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching schools: {str(e)}")

@router.post("/sync")
async def sync_powerschool_school(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Sync PowerSchool school data and generate enhanced predictions"""
    try:
        body = await request.json()
        base_url = body.get('base_url', '').strip()
        client_id = body.get('client_id', '').strip()
        client_secret = body.get('client_secret', '').strip()
        school_id = body.get('school_id', '').strip()
        grade_levels = body.get('grade_levels', [])
        
        if not all([base_url, client_id, client_secret, school_id]):
            raise HTTPException(status_code=400, detail="PowerSchool credentials and school ID are required")
        
        from integrations.powerschool_sis import create_powerschool_integration
        ps = create_powerschool_integration(base_url, client_id, client_secret)
        
        # Sync school data and generate predictions
        sync_result = ps.sync_school_data(school_id, grade_levels if grade_levels else None)
        
        if sync_result['status'] == 'success':
            # Save predictions to database if available
            try:
                session_id = f"powerschool_{school_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                if sync_result['predictions']:
                    save_predictions_batch(sync_result['predictions'], session_id)
                    logger.info(f"Saved {len(sync_result['predictions'])} PowerSchool predictions to database")
            except Exception as db_error:
                logger.warning(f"Could not save PowerSchool predictions to database: {db_error}")
            
            # Generate summary statistics
            predictions = sync_result['predictions']
            if predictions:
                total_students = len(predictions)
                high_risk = sum(1 for p in predictions if p.get('risk_level') == 'danger')
                moderate_risk = sum(1 for p in predictions if p.get('risk_level') == 'warning') 
                low_risk = sum(1 for p in predictions if p.get('risk_level') == 'success')
                
                avg_gpa = sum(p.get('current_gpa', 0) for p in predictions) / total_students if total_students > 0 else 0
                avg_attendance = sum(p.get('attendance_rate', 0) for p in predictions) / total_students if total_students > 0 else 0
                
                sync_result['summary'] = {
                    'total_students': total_students,
                    'risk_distribution': {
                        'high_risk': high_risk,
                        'moderate_risk': moderate_risk,
                        'low_risk': low_risk
                    },
                    'class_averages': {
                        'gpa': round(avg_gpa, 2),
                        'attendance': round(avg_attendance * 100, 1)
                    },
                    'enhanced_data_coverage': {
                        'attendance_data': sync_result['data_quality']['has_attendance'],
                        'discipline_data': sync_result['data_quality']['has_discipline'],
                        'demographics_data': sync_result['data_quality']['has_demographics'],
                        'special_programs_data': sync_result['data_quality']['has_special_programs']
                    }
                }
            
            return JSONResponse(sync_result)
        else:
            raise HTTPException(status_code=400, detail=f"PowerSchool sync failed: {sync_result.get('error')}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing PowerSchool school: {e}")
        raise HTTPException(status_code=500, detail=f"PowerSchool sync error: {str(e)}")

@router.get("/student/{student_id}")
async def get_powerschool_student_details(
    student_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Get detailed PowerSchool student information"""
    try:
        # Get PowerSchool credentials from request headers
        base_url = request.headers.get('X-PowerSchool-URL')
        client_id = request.headers.get('X-PowerSchool-Client-ID')
        client_secret = request.headers.get('X-PowerSchool-Client-Secret')
        
        if not all([base_url, client_id, client_secret]):
            raise HTTPException(status_code=400, detail="PowerSchool credentials required in headers")
        
        from integrations.powerschool_sis import create_powerschool_integration
        ps = create_powerschool_integration(base_url, client_id, client_secret)
        
        # Get comprehensive student data
        student_data = ps.get_student_comprehensive_data(student_id)
        
        # Convert to JSON-serializable format
        student_dict = {
            'id': student_data.id,
            'state_id': student_data.state_id,
            'local_id': student_data.local_id,
            'name': f"{student_data.first_name} {student_data.last_name}",
            'grade_level': student_data.grade_level,
            'school_id': student_data.school_id,
            'enrollment_status': student_data.enrollment_status,
            'academic_data': {
                'gpa_current': student_data.gpa_current,
                'gpa_cumulative': student_data.gpa_cumulative,
                'credits_earned': student_data.credits_earned,
                'credits_attempted': student_data.credits_attempted
            },
            'attendance_data': {
                'attendance_rate': student_data.attendance_rate,
                'absences_excused': student_data.absences_excused,
                'absences_unexcused': student_data.absences_unexcused,
                'tardies': student_data.tardies
            },
            'behavioral_data': {
                'discipline_incidents': student_data.discipline_incidents,
                'office_referrals': student_data.office_referrals,
                'suspensions': student_data.suspensions
            },
            'demographics': {
                'birth_date': student_data.birth_date,
                'gender': student_data.gender,
                'ethnicity': student_data.ethnicity,
                'economic_disadvantaged': student_data.economic_disadvantaged
            },
            'special_programs': {
                'iep_status': student_data.iep_status,
                'section_504': student_data.section_504,
                'ell_status': student_data.ell_status,
                'gifted_status': student_data.gifted_status
            }
        }
        
        return JSONResponse({
            'status': 'success',
            'student_data': student_dict
        })
        
    except Exception as e:
        logger.error(f"Error fetching PowerSchool student details: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching student details: {str(e)}")