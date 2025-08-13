#!/usr/bin/env python3
"""
Interventions API Endpoints
Student intervention tracking and management
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from datetime import datetime, timedelta
import logging
import time

from src.mvp.database import get_db_session
from src.mvp.models import Intervention, Student, User, Institution

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/interventions", tags=["Interventions"])

# Database dependency
def get_db() -> Session:
    with get_db_session() as session:
        yield session

class InterventionCreate(BaseModel):
    student_id: int
    intervention_type: str
    title: str
    description: Optional[str] = None
    priority: str = "medium"  # low, medium, high, critical
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None

class InterventionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None  # pending, in_progress, completed, cancelled
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    outcome: Optional[str] = None
    outcome_notes: Optional[str] = None
    actual_cost: Optional[float] = None
    time_spent_minutes: Optional[int] = None

class InterventionResponse(BaseModel):
    id: int
    student_id: int
    student_name: str
    intervention_type: str
    title: str
    description: Optional[str] = None
    priority: str
    status: str
    assigned_to: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    outcome: Optional[str] = None
    outcome_notes: Optional[str] = None
    created_at: datetime

# Bulk Operation Models
class BulkInterventionCreate(BaseModel):
    student_ids: List[int]
    intervention_type: str
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    
    @validator('student_ids')
    def validate_student_ids(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one student ID is required')
        if len(v) > 100:  # Reasonable limit
            raise ValueError('Cannot create interventions for more than 100 students at once')
        return v
    
    @validator('priority')
    def validate_priority(cls, v):
        if v not in ['low', 'medium', 'high', 'critical']:
            return 'medium'  # Default to medium if invalid
        return v

class BulkInterventionUpdate(BaseModel):
    intervention_ids: List[int]
    status: Optional[str] = None
    outcome: Optional[str] = None
    outcome_notes: Optional[str] = None
    assigned_to: Optional[str] = None
    priority: Optional[str] = None
    
    @validator('intervention_ids')
    def validate_intervention_ids(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one intervention ID is required')
        if len(v) > 200:  # Allow more for updates
            raise ValueError('Cannot update more than 200 interventions at once')
        return v

class BulkOperationItem(BaseModel):
    id: int
    success: bool
    error_message: Optional[str] = None
    item_data: Optional[Dict[str, Any]] = None

class BulkOperationResult(BaseModel):
    total_requested: int
    successful: int
    failed: int
    results: List[BulkOperationItem]
    execution_time: float
    operation_type: str

@router.get("/student/{student_id}", response_model=List[InterventionResponse])
async def get_student_interventions(
    student_id: str,  # Accept string to handle both IDs and student_id values
    db: Session = Depends(get_db),
    status: Optional[str] = None
):
    """Get all interventions for a specific student"""
    try:
        # Get student to verify they exist and get institution
        # Try to find by database ID first, then by student_id string
        student = None
        try:
            # Try as integer ID first
            student = db.query(Student).filter(Student.id == int(student_id)).first()
        except ValueError:
            pass
        
        if not student:
            # Try as student_id string (CSV upload case)
            student = db.query(Student).filter(Student.student_id == student_id).first()
            
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        # Build query using the database student.id
        query = db.query(Intervention).filter(
            Intervention.student_id == student.id
        )
        
        if status:
            query = query.filter(Intervention.status == status)
        
        interventions = query.order_by(Intervention.created_at.desc()).all()
        
        # Convert to response format
        results = []
        for intervention in interventions:
            results.append({
                "id": intervention.id,
                "student_id": intervention.student_id,
                "student_name": f"Student {student.student_id}",  # Will enhance this later
                "intervention_type": intervention.intervention_type,
                "title": intervention.title,
                "description": intervention.description,
                "priority": intervention.priority,
                "status": intervention.status,
                "assigned_to": intervention.assigned_to,
                "scheduled_date": intervention.scheduled_date,
                "due_date": intervention.due_date,
                "completed_date": intervention.completed_date,
                "outcome": intervention.outcome,
                "outcome_notes": intervention.outcome_notes,
                "created_at": intervention.created_at
            })
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting student interventions: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve interventions")

@router.get("/all", response_model=Dict[str, Any])
async def get_all_interventions(
    db: Session = Depends(get_db),
    page: int = 1,
    limit: int = 50,
    status: Optional[str] = None,
    intervention_type: Optional[str] = None,
    priority: Optional[str] = None,
    student_search: Optional[str] = None,
    assigned_to: Optional[str] = None
):
    """Get paginated list of all interventions with filtering"""
    try:
        # Validate pagination parameters
        if page < 1:
            page = 1
        if limit < 1 or limit > 100:
            limit = 50
            
        offset = (page - 1) * limit
        
        # Build query
        query = db.query(Intervention).join(Student)
        
        # Apply filters
        if status:
            query = query.filter(Intervention.status == status)
        if intervention_type:
            query = query.filter(Intervention.intervention_type == intervention_type)
        if priority:
            query = query.filter(Intervention.priority == priority)
        if assigned_to:
            query = query.filter(Intervention.assigned_to.ilike(f"%{assigned_to}%"))
        if student_search:
            query = query.filter(Student.student_id.ilike(f"%{student_search}%"))
        
        # Get total count for pagination
        total_count = query.count()
        
        # Get paginated results
        interventions = query.order_by(Intervention.created_at.desc()).offset(offset).limit(limit).all()
        
        # Format results
        results = []
        for intervention in interventions:
            student = db.query(Student).filter(Student.id == intervention.student_id).first()
            results.append({
                "id": intervention.id,
                "student_id": intervention.student_id,
                "student_name": f"Student {student.student_id}" if student else "Unknown Student",
                "intervention_type": intervention.intervention_type,
                "title": intervention.title,
                "description": intervention.description,
                "priority": intervention.priority,
                "status": intervention.status,
                "assigned_to": intervention.assigned_to,
                "due_date": intervention.due_date,
                "completed_date": intervention.completed_date,
                "outcome": intervention.outcome,
                "outcome_notes": intervention.outcome_notes,
                "created_at": intervention.created_at,
                "updated_at": intervention.updated_at
            })
        
        # Calculate pagination info
        total_pages = (total_count + limit - 1) // limit
        has_next = page < total_pages
        has_prev = page > 1
        
        return {
            "interventions": results,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_items": total_count,
                "items_per_page": limit,
                "has_next": has_next,
                "has_prev": has_prev
            },
            "filters_applied": {
                "status": status,
                "intervention_type": intervention_type,
                "priority": priority,
                "student_search": student_search,
                "assigned_to": assigned_to
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting all interventions: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve interventions")

@router.get("/{intervention_id}", response_model=InterventionResponse)
async def get_intervention(
    intervention_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific intervention by ID"""
    try:
        # Find intervention by ID
        intervention = db.query(Intervention).filter(
            Intervention.id == intervention_id
        ).first()
        
        if not intervention:
            raise HTTPException(status_code=404, detail="Intervention not found")
        
        # Get student info for response
        student = db.query(Student).filter(Student.id == intervention.student_id).first()
        student_name = f"Student {student.student_id}" if student else "Unknown Student"
        
        return {
            "id": intervention.id,
            "student_id": intervention.student_id,
            "student_name": student_name,
            "intervention_type": intervention.intervention_type,
            "title": intervention.title,
            "description": intervention.description,
            "priority": intervention.priority,
            "status": intervention.status,
            "assigned_to": intervention.assigned_to,
            "scheduled_date": intervention.scheduled_date,
            "due_date": intervention.due_date,
            "completed_date": intervention.completed_date,
            "outcome": intervention.outcome,
            "outcome_notes": intervention.outcome_notes,
            "created_at": intervention.created_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting intervention {intervention_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve intervention")

@router.post("/", response_model=InterventionResponse)
async def create_intervention(
    intervention_data: InterventionCreate,
    db: Session = Depends(get_db)
):
    """Create a new intervention for a student"""
    try:
        # Get student to verify they exist and get institution
        # Try to find by database ID first, then by student_id string
        student = db.query(Student).filter(Student.id == intervention_data.student_id).first()
        if not student:
            # Try finding by student_id string (CSV upload case)
            student = db.query(Student).filter(Student.student_id == str(intervention_data.student_id)).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        # Create intervention (no duplicate prevention needed - multiple interventions per student allowed)
        intervention = Intervention(
            institution_id=student.institution_id,
            student_id=student.id,  # Use the database ID
            intervention_type=intervention_data.intervention_type,
            title=intervention_data.title,
            description=intervention_data.description,
            priority=intervention_data.priority,
            status="pending",
            assigned_to=intervention_data.assigned_to,
            due_date=intervention_data.due_date,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.add(intervention)
        db.commit()
        db.refresh(intervention)
        
        logger.info(f"Created intervention {intervention.id} for student {student.student_id}")
        
        return {
            "id": intervention.id,
            "student_id": intervention.student_id,
            "student_name": f"Student {student.student_id}",
            "intervention_type": intervention.intervention_type,
            "title": intervention.title,
            "description": intervention.description,
            "priority": intervention.priority,
            "status": intervention.status,
            "assigned_to": intervention.assigned_to,
            "scheduled_date": intervention.scheduled_date,
            "due_date": intervention.due_date,
            "completed_date": intervention.completed_date,
            "outcome": intervention.outcome,
            "outcome_notes": intervention.outcome_notes,
            "created_at": intervention.created_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating intervention: {e}")
        raise HTTPException(status_code=500, detail="Failed to create intervention")

@router.put("/{intervention_id}", response_model=InterventionResponse)
async def update_intervention(
    intervention_id: int,
    intervention_data: InterventionUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing intervention"""
    try:
        intervention = db.query(Intervention).filter(Intervention.id == intervention_id).first()
        if not intervention:
            raise HTTPException(status_code=404, detail="Intervention not found")
        
        # Get student for response
        student = db.query(Student).filter(Student.id == intervention.student_id).first()
        
        # Update fields if provided
        update_data = intervention_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(intervention, field, value)
        
        # Set completion date if status changed to completed
        if intervention_data.status == "completed" and not intervention.completed_date:
            intervention.completed_date = datetime.now()
        
        intervention.updated_at = datetime.now()
        
        db.commit()
        db.refresh(intervention)
        
        logger.info(f"Updated intervention {intervention.id}")
        
        return {
            "id": intervention.id,
            "student_id": intervention.student_id,
            "student_name": f"Student {student.student_id}" if student else "Unknown",
            "intervention_type": intervention.intervention_type,
            "title": intervention.title,
            "description": intervention.description,
            "priority": intervention.priority,
            "status": intervention.status,
            "assigned_to": intervention.assigned_to,
            "scheduled_date": intervention.scheduled_date,
            "due_date": intervention.due_date,
            "completed_date": intervention.completed_date,
            "outcome": intervention.outcome,
            "outcome_notes": intervention.outcome_notes,
            "created_at": intervention.created_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating intervention: {e}")
        raise HTTPException(status_code=500, detail="Failed to update intervention")

@router.delete("/{intervention_id}")
async def delete_intervention(
    intervention_id: int,
    db: Session = Depends(get_db)
):
    """Delete an intervention"""
    try:
        intervention = db.query(Intervention).filter(Intervention.id == intervention_id).first()
        if not intervention:
            raise HTTPException(status_code=404, detail="Intervention not found")
        
        db.delete(intervention)
        db.commit()
        
        logger.info(f"Deleted intervention {intervention_id}")
        
        return JSONResponse({"message": "Intervention deleted successfully"})
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting intervention: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete intervention")

@router.get("/types")
async def get_intervention_types():
    """Get available intervention types"""
    types = [
        {"value": "academic_support", "label": "Academic Support", "description": "Tutoring, study groups, academic coaching"},
        {"value": "attendance_support", "label": "Attendance Support", "description": "Attendance monitoring, family engagement"},
        {"value": "behavioral_support", "label": "Behavioral Support", "description": "Counseling, behavior plans, conflict resolution"},
        {"value": "engagement_support", "label": "Engagement Support", "description": "Extracurricular activities, peer mentoring"},
        {"value": "family_engagement", "label": "Family Engagement", "description": "Parent conferences, home visits, family support"},
        {"value": "college_career", "label": "College & Career", "description": "College prep, career counseling, internships"},
        {"value": "health_wellness", "label": "Health & Wellness", "description": "Mental health support, wellness programs"},
        {"value": "technology_support", "label": "Technology Support", "description": "Device access, digital literacy support"}
    ]
    return types

@router.get("/dashboard")
async def get_interventions_dashboard(
    db: Session = Depends(get_db),
    institution_id: Optional[int] = None
):
    """Get intervention dashboard statistics"""
    try:
        # For now, get all interventions (later filter by institution/user access)
        query = db.query(Intervention)
        if institution_id:
            query = query.filter(Intervention.institution_id == institution_id)
        
        interventions = query.all()
        
        # Calculate statistics
        total = len(interventions)
        pending = len([i for i in interventions if i.status == "pending"])
        in_progress = len([i for i in interventions if i.status == "in_progress"])
        completed = len([i for i in interventions if i.status == "completed"])
        
        # Priority breakdown
        high_priority = len([i for i in interventions if i.priority in ["high", "critical"]])
        overdue = len([i for i in interventions if i.due_date and i.due_date < datetime.now() and i.status not in ["completed", "cancelled"]])
        
        return {
            "total": total,
            "pending": pending,
            "in_progress": in_progress,
            "completed": completed,
            "high_priority": high_priority,
            "overdue": overdue,
            "completion_rate": round((completed / total * 100) if total > 0 else 0, 1)
        }
        
    except Exception as e:
        logger.error(f"Error getting interventions dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard data")

# ========== BULK OPERATION ENDPOINTS ==========

@router.post("/bulk/validate", response_model=Dict[str, Any])
async def validate_bulk_operation(
    operation_data: BulkInterventionCreate,
    db: Session = Depends(get_db)
):
    """Pre-validate bulk intervention creation"""
    try:
        validation_results = []
        valid_student_ids = []
        
        for student_id in operation_data.student_ids:
            # Check if student exists - try database ID first, then student_id string
            student = None
            
            # Try database ID lookup
            try:
                if isinstance(student_id, int) or str(student_id).isdigit():
                    student = db.query(Student).filter(Student.id == int(student_id)).first()
            except (ValueError, TypeError):
                pass
            
            # If not found by database ID, try student_id string lookup
            if not student:
                student = db.query(Student).filter(Student.student_id == str(student_id)).first()
            
            if not student:
                validation_results.append({
                    "student_id": student_id,
                    "valid": False,
                    "error": f"Student not found (searched by ID {student_id})"
                })
            else:
                validation_results.append({
                    "student_id": student_id,
                    "student_name": f"Student {student.student_id}",
                    "valid": True,
                    "error": None
                })
                valid_student_ids.append(student_id)
        
        return {
            "total_students": len(operation_data.student_ids),
            "valid_students": len(valid_student_ids),
            "invalid_students": len(operation_data.student_ids) - len(valid_student_ids),
            "can_proceed": len(valid_student_ids) > 0,
            "validation_details": validation_results
        }
        
    except Exception as e:
        logger.error(f"Error validating bulk operation: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate bulk operation")

@router.post("/bulk/create", response_model=BulkOperationResult)
async def create_bulk_interventions(
    bulk_data: BulkInterventionCreate,
    db: Session = Depends(get_db)
):
    """Create interventions for multiple students"""
    start_time = time.time()
    results = []
    successful_count = 0
    
    try:
        logger.info(f"Starting bulk intervention creation for {len(bulk_data.student_ids)} students")
        
        for student_id in bulk_data.student_ids:
            try:
                # Get student to verify they exist and get institution
                # Try to find by database ID first, then by student_id string
                student = None
                
                # If it's a valid integer, try database ID lookup
                try:
                    if isinstance(student_id, int) or str(student_id).isdigit():
                        student = db.query(Student).filter(Student.id == int(student_id)).first()
                except (ValueError, TypeError):
                    pass
                
                # If not found by database ID, try student_id string lookup
                if not student:
                    student = db.query(Student).filter(Student.student_id == str(student_id)).first()
                
                if not student:
                    results.append(BulkOperationItem(
                        id=student_id,
                        success=False,
                        error_message=f"Student not found (searched by ID {student_id})"
                    ))
                    continue
                
                # Create intervention
                intervention = Intervention(
                    institution_id=student.institution_id,
                    student_id=student.id,
                    intervention_type=bulk_data.intervention_type,
                    title=bulk_data.title,
                    description=bulk_data.description,
                    priority=bulk_data.priority,
                    status="pending",
                    assigned_to=bulk_data.assigned_to,
                    due_date=bulk_data.due_date,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                db.add(intervention)
                db.flush()  # Get the ID without committing
                
                results.append(BulkOperationItem(
                    id=student_id,
                    success=True,
                    error_message=None,
                    item_data={
                        "intervention_id": intervention.id,
                        "student_name": f"Student {student.student_id}",
                        "intervention_title": intervention.title
                    }
                ))
                successful_count += 1
                
            except Exception as item_error:
                logger.error(f"Error creating intervention for student {student_id}: {item_error}")
                results.append(BulkOperationItem(
                    id=student_id,
                    success=False,
                    error_message=str(item_error)
                ))
        
        # Commit all successful operations
        if successful_count > 0:
            db.commit()
            logger.info(f"Successfully created {successful_count} interventions")
        else:
            db.rollback()
            logger.warning("No interventions were created - rolling back transaction")
        
        execution_time = time.time() - start_time
        
        return BulkOperationResult(
            total_requested=len(bulk_data.student_ids),
            successful=successful_count,
            failed=len(bulk_data.student_ids) - successful_count,
            results=results,
            execution_time=round(execution_time, 3),
            operation_type="bulk_create"
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error in bulk intervention creation: {e}")
        raise HTTPException(status_code=500, detail=f"Bulk operation failed: {str(e)}")

@router.put("/bulk/update", response_model=BulkOperationResult)
async def update_bulk_interventions(
    bulk_data: BulkInterventionUpdate,
    db: Session = Depends(get_db)
):
    """Update multiple interventions"""
    start_time = time.time()
    results = []
    successful_count = 0
    
    try:
        logger.info(f"Starting bulk intervention update for {len(bulk_data.intervention_ids)} interventions")
        
        for intervention_id in bulk_data.intervention_ids:
            try:
                # Get intervention
                intervention = db.query(Intervention).filter(
                    Intervention.id == intervention_id
                ).first()
                
                if not intervention:
                    results.append(BulkOperationItem(
                        id=intervention_id,
                        success=False,
                        error_message="Intervention not found"
                    ))
                    continue
                
                # Update fields if provided
                updated_fields = []
                intervention_deleted = False
                
                if bulk_data.status is not None:
                    # Handle cancellation by deleting the intervention
                    if bulk_data.status == "cancelled":
                        # Store intervention title before deletion
                        intervention_title = intervention.title
                        # Delete the intervention instead of updating status
                        db.delete(intervention)
                        updated_fields.append("deleted (cancelled)")
                        intervention_deleted = True
                        logger.info(f"Deleted intervention {intervention_id} due to cancellation")
                    else:
                        intervention.status = bulk_data.status
                        updated_fields.append("status")
                        if bulk_data.status == "completed":
                            intervention.completed_date = datetime.now()
                            updated_fields.append("completed_date")
                
                # Only update other fields if intervention wasn't deleted
                if not intervention_deleted:
                    if bulk_data.outcome is not None:
                        intervention.outcome = bulk_data.outcome
                        updated_fields.append("outcome")
                        
                    if bulk_data.outcome_notes is not None:
                        intervention.outcome_notes = bulk_data.outcome_notes
                        updated_fields.append("outcome_notes")
                        
                    if bulk_data.assigned_to is not None:
                        intervention.assigned_to = bulk_data.assigned_to
                        updated_fields.append("assigned_to")
                        
                    if bulk_data.priority is not None:
                        intervention.priority = bulk_data.priority
                        updated_fields.append("priority")
                    
                    intervention.updated_at = datetime.now()
                    updated_fields.append("updated_at")
                    intervention_title = intervention.title
                else:
                    # For deleted interventions, use the stored title
                    pass
                
                results.append(BulkOperationItem(
                    id=intervention_id,
                    success=True,
                    error_message=None,
                    item_data={
                        "intervention_title": intervention_title,
                        "updated_fields": updated_fields
                    }
                ))
                successful_count += 1
                
            except Exception as item_error:
                logger.error(f"Error updating intervention {intervention_id}: {item_error}")
                results.append(BulkOperationItem(
                    id=intervention_id,
                    success=False,
                    error_message=str(item_error)
                ))
        
        # Commit all successful operations
        if successful_count > 0:
            db.commit()
            logger.info(f"Successfully updated {successful_count} interventions")
        else:
            db.rollback()
            logger.warning("No interventions were updated - rolling back transaction")
        
        execution_time = time.time() - start_time
        
        return BulkOperationResult(
            total_requested=len(bulk_data.intervention_ids),
            successful=successful_count,
            failed=len(bulk_data.intervention_ids) - successful_count,
            results=results,
            execution_time=round(execution_time, 3),
            operation_type="bulk_update"
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error in bulk intervention update: {e}")
        raise HTTPException(status_code=500, detail=f"Bulk update failed: {str(e)}")

@router.delete("/bulk/delete")
async def delete_bulk_interventions(
    intervention_ids: List[int],
    db: Session = Depends(get_db)
):
    """Delete multiple interventions"""
    start_time = time.time()
    results = []
    successful_count = 0
    
    try:
        if not intervention_ids or len(intervention_ids) == 0:
            raise HTTPException(status_code=400, detail="At least one intervention ID is required")
        
        if len(intervention_ids) > 200:
            raise HTTPException(status_code=400, detail="Cannot delete more than 200 interventions at once")
        
        logger.info(f"Starting bulk intervention deletion for {len(intervention_ids)} interventions")
        
        for intervention_id in intervention_ids:
            try:
                # Get intervention
                intervention = db.query(Intervention).filter(
                    Intervention.id == intervention_id
                ).first()
                
                if not intervention:
                    results.append(BulkOperationItem(
                        id=intervention_id,
                        success=False,
                        error_message="Intervention not found"
                    ))
                    continue
                
                # Store info before deletion
                intervention_title = intervention.title
                
                # Delete intervention
                db.delete(intervention)
                
                results.append(BulkOperationItem(
                    id=intervention_id,
                    success=True,
                    error_message=None,
                    item_data={
                        "intervention_title": intervention_title
                    }
                ))
                successful_count += 1
                
            except Exception as item_error:
                logger.error(f"Error deleting intervention {intervention_id}: {item_error}")
                results.append(BulkOperationItem(
                    id=intervention_id,
                    success=False,
                    error_message=str(item_error)
                ))
        
        # Commit all successful operations
        if successful_count > 0:
            db.commit()
            logger.info(f"Successfully deleted {successful_count} interventions")
        else:
            db.rollback()
            logger.warning("No interventions were deleted - rolling back transaction")
        
        execution_time = time.time() - start_time
        
        return BulkOperationResult(
            total_requested=len(intervention_ids),
            successful=successful_count,
            failed=len(intervention_ids) - successful_count,
            results=results,
            execution_time=round(execution_time, 3),
            operation_type="bulk_delete"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error in bulk intervention deletion: {e}")
        raise HTTPException(status_code=500, detail=f"Bulk deletion failed: {str(e)}")