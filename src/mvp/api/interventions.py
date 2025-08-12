#!/usr/bin/env python3
"""
Interventions API Endpoints
Student intervention tracking and management
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from datetime import datetime, timedelta
import logging

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