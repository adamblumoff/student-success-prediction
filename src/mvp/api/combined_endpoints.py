#!/usr/bin/env python3
"""
Combined Canvas + PowerSchool Integration API Endpoints

Handles the ultimate integration combining Canvas LMS real-time gradebook data
with PowerSchool SIS comprehensive student records for supreme prediction accuracy.
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from pathlib import Path
import sys
import logging
from datetime import datetime

# Add src directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))
from mvp.api.core import get_current_user
from mvp.database import save_predictions_batch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/integration/combined", tags=["Combined Integration"])

@router.post("/connect")
async def connect_combined_systems(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Connect to both Canvas LMS and PowerSchool SIS for combined analysis"""
    try:
        body = await request.json()
        
        # Canvas credentials
        canvas_url = body.get('canvas_url', '').strip()
        canvas_token = body.get('canvas_token', '').strip()
        
        # PowerSchool credentials
        powerschool_url = body.get('powerschool_url', '').strip()
        powerschool_client_id = body.get('powerschool_client_id', '').strip()
        powerschool_client_secret = body.get('powerschool_client_secret', '').strip()
        
        if not all([canvas_url, canvas_token, powerschool_url, powerschool_client_id, powerschool_client_secret]):
            raise HTTPException(status_code=400, detail="All Canvas and PowerSchool credentials are required")
        
        # Import combined integration
        from integrations.combined_integration import create_combined_integration
        
        # Create combined integration
        combined = create_combined_integration(
            canvas_url, canvas_token,
            powerschool_url, powerschool_client_id, powerschool_client_secret
        )
        
        # Test connections to both systems
        connection_result = combined.test_connections()
        
        if connection_result['status'] in ['success', 'partial']:
            return JSONResponse({
                'status': connection_result['status'],
                'message': 'Combined integration connection test complete',
                'canvas_status': connection_result['canvas']['status'],
                'powerschool_status': connection_result['powerschool']['status'],
                'integration_ready': connection_result['integration_ready'],
                'canvas_info': connection_result['canvas'],
                'powerschool_info': connection_result['powerschool']
            })
        else:
            raise HTTPException(status_code=400, detail=f"Combined connection failed: {connection_result.get('error')}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error with combined connection: {e}")
        raise HTTPException(status_code=500, detail=f"Combined connection error: {str(e)}")

@router.post("/matches")
async def get_combined_matches(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Get suggested matches between Canvas courses and PowerSchool schools"""
    try:
        body = await request.json()
        
        # Canvas credentials
        canvas_url = body.get('canvas_url', '').strip()
        canvas_token = body.get('canvas_token', '').strip()
        
        # PowerSchool credentials
        powerschool_url = body.get('powerschool_url', '').strip()
        powerschool_client_id = body.get('powerschool_client_id', '').strip()
        powerschool_client_secret = body.get('powerschool_client_secret', '').strip()
        
        if not all([canvas_url, canvas_token, powerschool_url, powerschool_client_id, powerschool_client_secret]):
            raise HTTPException(status_code=400, detail="All credentials required")
        
        from integrations.combined_integration import create_combined_integration
        combined = create_combined_integration(
            canvas_url, canvas_token,
            powerschool_url, powerschool_client_id, powerschool_client_secret
        )
        
        # Get matching suggestions
        matches_result = combined.get_matching_courses_and_schools()
        
        if matches_result['status'] == 'success':
            return JSONResponse(matches_result)
        else:
            raise HTTPException(status_code=400, detail=f"Failed to get matches: {matches_result.get('error')}")
            
    except Exception as e:
        logger.error(f"Error getting combined matches: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting matches: {str(e)}")

@router.post("/sync")
async def sync_combined_data(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Perform ultimate combined Canvas + PowerSchool data sync and analysis"""
    try:
        body = await request.json()
        
        # Credentials
        canvas_url = body.get('canvas_url', '').strip()
        canvas_token = body.get('canvas_token', '').strip()
        powerschool_url = body.get('powerschool_url', '').strip()
        powerschool_client_id = body.get('powerschool_client_id', '').strip()
        powerschool_client_secret = body.get('powerschool_client_secret', '').strip()
        
        # Selection
        canvas_course_id = body.get('canvas_course_id', '').strip()
        powerschool_school_id = body.get('powerschool_school_id', '').strip()
        grade_levels = body.get('grade_levels', [])
        
        if not all([canvas_url, canvas_token, powerschool_url, powerschool_client_id, 
                   powerschool_client_secret, canvas_course_id, powerschool_school_id]):
            raise HTTPException(status_code=400, detail="All credentials and selection parameters required")
        
        from integrations.combined_integration import create_combined_integration
        combined = create_combined_integration(
            canvas_url, canvas_token,
            powerschool_url, powerschool_client_id, powerschool_client_secret
        )
        
        # Perform combined sync
        sync_result = combined.sync_combined_data(
            canvas_course_id, powerschool_school_id, 
            grade_levels if grade_levels else None
        )
        
        if sync_result['status'] == 'success':
            # Save combined predictions to database
            try:
                session_id = f"combined_{canvas_course_id}_{powerschool_school_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                if sync_result['predictions']:
                    save_predictions_batch(sync_result['predictions'], session_id)
                    logger.info(f"Saved {len(sync_result['predictions'])} combined predictions to database")
            except Exception as db_error:
                logger.warning(f"Could not save combined predictions to database: {db_error}")
            
            # Generate enhanced summary statistics
            predictions = sync_result['predictions']
            if predictions:
                total_students = len(predictions)
                critical_priority = sync_result['analysis']['risk_analysis']['critical_priority']
                high_priority = sync_result['analysis']['risk_analysis']['high_priority']
                medium_priority = sync_result['analysis']['risk_analysis']['medium_priority']
                low_priority = sync_result['analysis']['risk_analysis']['low_priority']
                
                # Traditional risk categories
                high_risk = sum(1 for p in predictions if p.get('risk_level') == 'danger')
                moderate_risk = sum(1 for p in predictions if p.get('risk_level') == 'warning') 
                low_risk = sum(1 for p in predictions if p.get('risk_level') == 'success')
                
                avg_gpa = sum(p.get('current_gpa', 0) for p in predictions) / total_students if total_students > 0 else 0
                avg_attendance = sum(p.get('attendance_rate', 0) for p in predictions) / total_students if total_students > 0 else 0
                
                sync_result['enhanced_summary'] = {
                    'total_students': total_students,
                    'traditional_risk_distribution': {
                        'high_risk': high_risk,
                        'moderate_risk': moderate_risk,
                        'low_risk': low_risk
                    },
                    'intervention_priority_distribution': {
                        'critical': critical_priority,
                        'high': high_priority,
                        'medium': medium_priority,
                        'low': low_priority
                    },
                    'class_averages': {
                        'gpa': round(avg_gpa, 2),
                        'attendance': round(avg_attendance * 100, 1)
                    },
                    'data_integration_quality': {
                        'match_rate': sync_result['match_rate'],
                        'canvas_coverage': sync_result['canvas_students'],
                        'powerschool_coverage': sync_result['powerschool_students'],
                        'combined_profiles': sync_result['matched_students'],
                        'data_completeness': sync_result['data_quality']['data_completeness_score']
                    }
                }
            
            return JSONResponse(sync_result)
        else:
            raise HTTPException(status_code=400, detail=f"Combined sync failed: {sync_result.get('error')}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error with combined sync: {e}")
        raise HTTPException(status_code=500, detail=f"Combined sync error: {str(e)}")