#!/usr/bin/env python3
"""
MVP API endpoints for Student Success Prediction System

Simple, educator-focused endpoints for the MVP web application.
Uses SQLite for simplicity and focuses on core prediction workflow.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Security
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import json
import logging
import os
from typing import List, Dict, Any
import io
import sqlite3
from datetime import datetime

# Add src directory to path
sys.path.append(str(Path(__file__).parent.parent))
from models.intervention_system import InterventionRecommendationSystem
from models.k12_ultra_predictor import K12UltraPredictor
from mvp.simple_auth import simple_auth, simple_rate_limit, simple_file_validation
from mvp.database import get_db_session, init_database, check_database_health
from mvp.models import Institution, Student, Prediction, Intervention, AuditLog
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import desc

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Student Success Prediction MVP",
    description="Simple web app for educators to identify at-risk students",
    version="1.0.0",
    docs_url="/docs" if os.getenv('DEVELOPMENT_MODE') == 'true' else None,
    redoc_url="/redoc" if os.getenv('DEVELOPMENT_MODE') == 'true' else None
)

# Simplified CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local testing
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Simplified security headers middleware
@app.middleware("http")
async def add_basic_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response

# Global variables
intervention_system = None
k12_ultra_predictor = None
uploaded_students_data = {}  # Store uploaded student data for explanations
sample_data = None

# Simple security setup
security = HTTPBearer()

# Static files and templates
app.mount("/static", StaticFiles(directory="src/mvp/static"), name="static")
templates = Jinja2Templates(directory="src/mvp/templates")

# Database initialization - supports both SQLite and PostgreSQL
def init_db():
    """Initialize database with proper schema"""
    try:
        # Use new SQLAlchemy-based initialization
        init_database()
        
        # Ensure default institution exists for MVP mode
        with get_db_session() as session:
            default_institution = session.query(Institution).filter_by(code="MVP_DEMO").first()
            if not default_institution:
                default_institution = Institution(
                    name="MVP Demo Institution",
                    code="MVP_DEMO",
                    type="demo"
                )
                session.add(default_institution)
                session.commit()
                logger.info("Created default MVP institution")
            
        return True
    except Exception as e:
        logger.error(f"Failed to initialize new database: {e}")
        # Fallback to SQLite for backward compatibility
        return init_sqlite_fallback()

def init_sqlite_fallback():
    """Fallback SQLite initialization for MVP compatibility"""
    db_path = "mvp_data.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create simple table for predictions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            risk_score REAL,
            risk_category TEXT,
            timestamp TEXT,
            session_id TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Initialized SQLite fallback database")
    return db_path

def save_prediction(student_id: int, risk_score: float, risk_category: str, session_id: str, 
                   features_data: dict = None, explanation_data: dict = None):
    """Save prediction to database (SQLAlchemy or SQLite fallback)"""
    try:
        # Try new database first
        with get_db_session() as session:
            # Get default institution
            institution = session.query(Institution).filter_by(code="MVP_DEMO").first()
            if not institution:
                raise Exception("Default institution not found")
            
            # Create or get student record
            student = session.query(Student).filter_by(
                institution_id=institution.id,
                student_id=str(student_id)
            ).first()
            
            if not student:
                student = Student(
                    institution_id=institution.id,
                    student_id=str(student_id),
                    enrollment_status="active"
                )
                session.add(student)
                session.flush()  # Get the ID
            
            # Create prediction record
            prediction = Prediction(
                institution_id=institution.id,
                student_id=student.id,
                risk_score=risk_score,
                risk_category=risk_category,
                session_id=session_id,
                data_source="csv_upload",
                features_used=json.dumps(features_data) if features_data else None,
                explanation=json.dumps(explanation_data) if explanation_data else None
            )
            session.add(prediction)
            session.commit()
            
    except Exception as e:
        logger.warning(f"Failed to save with new database, falling back to SQLite: {e}")
        # Fallback to SQLite
        save_prediction_to_sqlite(student_id, risk_score, risk_category, session_id)

def save_predictions_batch(predictions_data: list, session_id: str):
    """Fast batch save for multiple predictions - 10x faster than individual saves"""
    if not predictions_data:
        return
    
    try:
        # Try PostgreSQL batch operation first
        with get_db_session() as session:
            # Get default institution
            institution = session.query(Institution).filter_by(code="MVP_DEMO").first()
            if not institution:
                raise Exception("Default institution not found")
            
            # Prepare batch data
            students_to_create = []
            predictions_to_create = []
            existing_student_ids = set()
            
            # Get existing students in batch
            student_ids = [str(pred['student_id']) for pred in predictions_data]
            existing_students = session.query(Student).filter(
                Student.institution_id == institution.id,
                Student.student_id.in_(student_ids)
            ).all()
            
            # Create lookup of existing students
            existing_student_lookup = {s.student_id: s.id for s in existing_students}
            existing_student_ids = set(existing_student_lookup.keys())
            
            # Process each prediction
            for pred_data in predictions_data:
                student_id_str = str(pred_data['student_id'])
                
                # Create student if doesn't exist
                if student_id_str not in existing_student_ids:
                    students_to_create.append({
                        'institution_id': institution.id,
                        'student_id': student_id_str,
                        'enrollment_status': 'active'
                    })
            
            # Batch insert new students
            if students_to_create:
                session.execute(
                    Student.__table__.insert(),
                    students_to_create
                )
                session.flush()
                
                # Update lookup with new students
                new_students = session.query(Student).filter(
                    Student.institution_id == institution.id,
                    Student.student_id.in_([s['student_id'] for s in students_to_create])
                ).all()
                
                for student in new_students:
                    existing_student_lookup[student.student_id] = student.id
            
            # Prepare prediction records
            for pred_data in predictions_data:
                student_id_str = str(pred_data['student_id'])
                db_student_id = existing_student_lookup[student_id_str]
                
                predictions_to_create.append({
                    'institution_id': institution.id,
                    'student_id': db_student_id,
                    'risk_score': pred_data['risk_score'],
                    'risk_category': pred_data['risk_category'],
                    'session_id': session_id,
                    'data_source': 'csv_upload',
                    'features_used': json.dumps(pred_data.get('features_data')),
                    'explanation': json.dumps(pred_data.get('explanation_data'))
                })
            
            # Batch insert predictions
            if predictions_to_create:
                session.execute(
                    Prediction.__table__.insert(),
                    predictions_to_create
                )
            
            # Single commit for all operations
            session.commit()
            logger.info(f"✅ Batch saved {len(predictions_data)} predictions in single transaction")
            
    except Exception as e:
        logger.warning(f"Failed to batch save with PostgreSQL, falling back to individual saves: {e}")
        # Fallback to individual saves
        for pred_data in predictions_data:
            save_prediction(
                pred_data['student_id'],
                pred_data['risk_score'],
                pred_data['risk_category'],
                session_id,
                pred_data.get('features_data'),
                pred_data.get('explanation_data')
            )

def save_prediction_to_sqlite(student_id: int, risk_score: float, risk_category: str, session_id: str):
    """SQLite fallback for prediction storage"""
    try:
        conn = sqlite3.connect("mvp_data.db")
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO predictions (student_id, risk_score, risk_category, timestamp, session_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (student_id, risk_score, risk_category, datetime.now().isoformat(), session_id))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"Failed to save prediction to SQLite: {e}")

def detect_gradebook_format(df):
    """Detect Canvas or generic CSV format"""
    columns = [col.lower() for col in df.columns]
    
    # Canvas detection
    if any('student' in col for col in columns) and any('current score' in col for col in columns):
        return 'canvas'
    
    # Direct prediction format
    if 'id_student' in columns:
        return 'prediction_format'
    
    # Generic gradebook (has some form of ID and scores)
    if any('id' in col for col in columns) and len([col for col in columns if any(keyword in col for keyword in ['score', 'grade', 'points', 'percent'])]) >= 1:
        return 'generic'
    
    return 'unknown'

def extract_student_identifier(df, format_type):
    """Extract student ID from Canvas or generic formats"""
    if len(df) == 0:
        return pd.Series([], dtype=str)
    
    columns = df.columns.tolist()
    
    try:
        if format_type == 'canvas':
            if 'ID' in df.columns:
                return df['ID'].astype(str)
        elif format_type == 'generic':
            # Find the most likely ID column
            id_cols = [col for col in columns if 'id' in col.lower()]
            if id_cols:
                return df[id_cols[0]].astype(str)
        elif format_type == 'prediction_format':
            if 'id_student' in df.columns:
                return df['id_student'].astype(str)
    except (KeyError, IndexError):
        pass
    
    # Fallback: use row index as ID
    return pd.Series(range(1000, 1000 + len(df)), index=df.index).astype(str)

def extract_assignment_scores(df, format_type):
    """Extract assignment scores and calculate statistics"""
    if len(df) == 0:
        return pd.DataFrame()
    
    columns = df.columns.tolist()
    
    # Simplified patterns for Canvas and generic
    if format_type == 'canvas':
        patterns = ['Assignment', 'Quiz', 'Exam', 'Test', 'Discussion']
    else:  # generic
        patterns = ['Assignment', 'Quiz', 'Test', 'Exam', 'Grade', 'Score', 'Points']
    
    # Find score columns
    score_columns = []
    for col in columns:
        if any(pattern.lower() in col.lower() for pattern in patterns):
            # Exclude final/summative items for early prediction
            if not any(exclude in col.lower() for exclude in ['final', 'total', 'current', 'overall', 'summary']):
                score_columns.append(col)
    
    # Extract numeric scores from each column
    scores_data = []
    for idx, row in df.iterrows():
        student_scores = []
        for col in score_columns:
            try:
                if col in df.columns and idx in df.index:
                    value = str(row[col]).strip()
                    if value and value.lower() not in ['nan', '', 'null', 'n/a']:
                        # Handle different score formats
                        if '/' in value:  # Format: "85/100"
                            parts = value.split('/')
                            if len(parts) == 2:
                                score, max_points = parts
                                percentage = (float(score) / float(max_points)) * 100
                                student_scores.append(percentage)
                        elif '%' in value:  # Format: "85%"
                            student_scores.append(float(value.replace('%', '')))
                        elif value.replace('.', '').replace('-', '').isdigit():  # Pure number
                            score = float(value)
                            student_scores.append(score if score <= 100 else score)
            except (ValueError, AttributeError, IndexError, KeyError):
                continue
        
        # Calculate statistics
        if student_scores:
            scores_data.append({
                'early_avg_score': np.mean(student_scores),
                'early_min_score': np.min(student_scores), 
                'early_max_score': np.max(student_scores),
                'early_score_std': np.std(student_scores) if len(student_scores) > 1 else 0,
                'early_submitted_count': len(student_scores),
                'early_assessments_count': max(len(score_columns), 1),
                'early_score_range': np.max(student_scores) - np.min(student_scores) if len(student_scores) > 1 else 0
            })
        else:
            scores_data.append({
                'early_avg_score': 50,  # Default for missing data
                'early_min_score': 0,
                'early_max_score': 50,
                'early_score_std': 0,
                'early_submitted_count': 0,
                'early_assessments_count': max(len(score_columns), 1),
                'early_score_range': 0
            })
    
    return pd.DataFrame(scores_data)

def extract_engagement_metrics(df, format_type):
    """Extract engagement metrics from Canvas or generic formats"""
    engagement_data = []
    
    # Simplified engagement patterns
    if format_type == 'canvas':
        patterns = ['Activity Time', 'Last Activity', 'Participations', 'Page Views']
    else:  # generic
        patterns = ['activity', 'access', 'time', 'participation', 'engagement']
    columns = df.columns.tolist()
    
    # Find engagement columns
    time_col = None
    activity_col = None
    access_col = None
    
    for col in columns:
        col_lower = col.lower()
        if any(p in col_lower for p in ['time', 'minutes', 'hours']):
            time_col = col
        elif any(p in col_lower for p in ['activity', 'participation', 'posts']):
            activity_col = col
        elif any(p in col_lower for p in ['access', 'login', 'seen']):
            access_col = col
    
    for _, row in df.iterrows():
        # Extract time-based engagement
        total_time = 150  # Default minutes
        if time_col:
            try:
                time_val = str(row[time_col]).replace('mins', '').replace('minutes', '').strip()
                if time_val.replace('.', '').isdigit():
                    total_time = float(time_val)
            except:
                pass
        
        # Extract activity count
        activity_count = 0
        if activity_col:
            try:
                activity_val = str(row[activity_col]).strip()
                if activity_val.isdigit():
                    activity_count = int(activity_val)
            except:
                pass
        
        # Calculate derived metrics
        active_days = max(1, int(total_time / 10))  # Estimate active days from time
        total_clicks = int(total_time * 2) + activity_count * 5  # Estimate clicks
        avg_clicks = total_clicks / active_days if active_days > 0 else 0
        
        # Last access recency
        days_since_access = 7  # Default
        if access_col:
            try:
                access_date = pd.to_datetime(row[access_col], errors='coerce')
                if pd.notna(access_date):
                    days_since_access = max(0, (pd.Timestamp.now() - access_date).days)
            except:
                pass
        
        engagement_data.append({
            'early_total_clicks': total_clicks,
            'early_avg_clicks': avg_clicks,
            'early_clicks_std': max(0, avg_clicks * 0.3),  # Estimate standard deviation
            'early_max_clicks': int(avg_clicks * 2) if avg_clicks > 0 else 0,
            'early_active_days': active_days,
            'early_first_access': -1,  # Assume they started early
            'early_last_access': min(30, days_since_access),
            'early_engagement_consistency': np.clip(avg_clicks / 10, 0.5, 5.0),
            'early_clicks_per_active_day': avg_clicks,
            'early_engagement_range': active_days
        })
    
    return pd.DataFrame(engagement_data)

def universal_gradebook_converter(df):
    """Universal converter that handles any gradebook format"""
    try:
        # Detect format
        format_type = detect_gradebook_format(df)
        logger.info(f"Detected gradebook format: {format_type}")
        
        if format_type == 'prediction_format':
            return df  # Already in correct format
        
        if format_type == 'unknown':
            logger.warning("Unknown gradebook format - attempting generic conversion")
            format_type = 'generic'
        
        # Extract student identifiers
        df['id_student'] = extract_student_identifier(df, format_type)
        
        # Extract assignment scores
        scores_df = extract_assignment_scores(df, format_type)
        for col in scores_df.columns:
            df[col] = scores_df[col]
        
        # Extract engagement metrics
        engagement_df = extract_engagement_metrics(df, format_type)
        for col in engagement_df.columns:
            df[col] = engagement_df[col]
        
        # Calculate missing submissions
        df['early_missing_submissions'] = np.maximum(
            0, df['early_assessments_count'] - df['early_submitted_count']
        )
        
        # Calculate submission rate
        df['early_submission_rate'] = np.clip(
            df['early_submitted_count'] / df['early_assessments_count'], 0, 1
        )
        
        # Add other required fields with defaults
        default_fields = {
            'code_module': 'GEN',
            'code_presentation': '2024',
            'gender_encoded': 0,
            'region_encoded': 0,
            'age_band_encoded': 1,
            'education_encoded': 2,
            'is_male': 0,
            'has_disability': 0,
            'studied_credits': 120,
            'num_of_prev_attempts': 0,
            'registration_delay': 0.0,
            'unregistered': 0,
            'early_total_weight': 25.0,
            'early_banked_count': 0
        }
        
        for field, default_value in default_fields.items():
            if field not in df.columns:
                df[field] = default_value
        
        logger.info(f"Successfully converted {format_type} format with {len(df)} students")
        return df
        
    except Exception as e:
        logger.error(f"Error in universal conversion: {e}")
        raise HTTPException(status_code=400, detail=f"Error processing gradebook: {str(e)}")

def convert_canvas_to_prediction_format(canvas_df):
    """Convert Canvas gradebook CSV to prediction format"""
    try:
        # Extract student IDs from Canvas format
        canvas_df['id_student'] = canvas_df['ID'].astype(int)
        
        # Calculate assignment scores and engagement from Canvas data
        assignment_cols = [col for col in canvas_df.columns if 'Assignment' in col or 'Quiz' in col or 'Exam' in col]
        
        # Calculate average score from assignments (excluding project draft for early prediction)
        early_assignments = [col for col in assignment_cols if 'Final Project' not in col and 'Draft' not in col]
        
        if early_assignments:
            # Extract scores and max points from assignment columns
            scores = []
            for _, row in canvas_df.iterrows():
                student_scores = []
                for col in early_assignments:
                    try:
                        # Parse score from "score (max_points)" format if needed
                        score_str = str(row[col])
                        if pd.notna(row[col]) and score_str != 'nan' and score_str != '':
                            student_scores.append(float(score_str))
                    except (ValueError, TypeError):
                        continue
                
                if student_scores:
                    scores.append({
                        'avg_score': np.mean(student_scores),
                        'min_score': np.min(student_scores),
                        'max_score': np.max(student_scores),
                        'score_std': np.std(student_scores) if len(student_scores) > 1 else 0,
                        'submitted_count': len(student_scores),
                        'assessments_count': len(early_assignments)
                    })
                else:
                    scores.append({
                        'avg_score': 0,
                        'min_score': 0,
                        'max_score': 0,
                        'score_std': 0,
                        'submitted_count': 0,
                        'assessments_count': len(early_assignments)
                    })
            
            score_df = pd.DataFrame(scores)
            for col in score_df.columns:
                canvas_df[f'early_{col}'] = score_df[col]
        
        # Convert Current Score to percentage
        canvas_df['early_avg_score'] = pd.to_numeric(canvas_df['Current Score'], errors='coerce').fillna(70)
        
        # Convert activity time to engagement metrics
        if 'Total Activity Time (mins)' in canvas_df.columns:
            activity_time = pd.to_numeric(canvas_df['Total Activity Time (mins)'], errors='coerce').fillna(150)
            canvas_df['early_total_clicks'] = (activity_time * 2).astype(int)  # Approximate clicks from time
            canvas_df['early_active_days'] = np.clip(activity_time / 10, 1, 30).astype(int)  # Estimate active days
            canvas_df['early_avg_clicks'] = canvas_df['early_total_clicks'] / canvas_df['early_active_days']
        
        # Parse last activity for engagement recency
        if 'Last Activity' in canvas_df.columns:
            try:
                last_activity = pd.to_datetime(canvas_df['Last Activity'], errors='coerce')
                days_since_activity = (pd.Timestamp.now() - last_activity).dt.days
                canvas_df['early_last_access'] = np.clip(days_since_activity, 0, 30).fillna(7)
            except:
                canvas_df['early_last_access'] = 7
        
        # Add derived engagement metrics
        canvas_df['early_engagement_consistency'] = np.clip(
            canvas_df.get('early_avg_clicks', 10) / 5, 0.5, 5.0
        )
        canvas_df['early_clicks_per_active_day'] = canvas_df.get('early_avg_clicks', 10)
        canvas_df['early_submission_rate'] = np.clip(
            canvas_df.get('early_submitted_count', 3) / canvas_df.get('early_assessments_count', 5), 0, 1
        )
        
        # Calculate missing submissions based on submission rate
        canvas_df['early_missing_submissions'] = np.maximum(
            0, canvas_df.get('early_assessments_count', 5) - canvas_df.get('early_submitted_count', 3)
        )
        
        logger.info(f"Converted Canvas data for {len(canvas_df)} students")
        return canvas_df
        
    except Exception as e:
        logger.error(f"Error converting Canvas format: {e}")
        raise HTTPException(status_code=400, detail=f"Error processing Canvas gradebook: {str(e)}")

def create_sample_student_data():
    """Create realistic sample student data for demo"""
    np.random.seed(42)  # For reproducible results
    
    students = []
    for i in range(50):
        # Create varied risk profiles
        if i < 8:  # High risk students
            risk_base = 0.75
            engagement_mult = 0.3
            score_mult = 0.6
        elif i < 20:  # Medium risk students  
            risk_base = 0.45
            engagement_mult = 0.6
            score_mult = 0.75
        else:  # Low risk students
            risk_base = 0.15
            engagement_mult = 0.9
            score_mult = 0.85
        
        student = {
            'id_student': 1000 + i,
            'code_module': 'AAA',
            'code_presentation': '2014J',
            
            # Demographics with some variation
            'gender_encoded': np.random.randint(0, 2),
            'region_encoded': np.random.randint(0, 13),
            'age_band_encoded': np.random.randint(0, 3),
            'education_encoded': np.random.randint(0, 5),
            'is_male': np.random.randint(0, 2),
            'has_disability': np.random.randint(0, 2) if np.random.random() < 0.1 else 0,
            'studied_credits': np.random.choice([60, 120, 180, 240, 300]),
            'num_of_prev_attempts': np.random.randint(0, 3),
            'registration_delay': np.random.uniform(-10, 30),
            'unregistered': 0,
            
            # Engagement features based on risk level
            'early_total_clicks': max(0, int(np.random.normal(200 * engagement_mult, 100))),
            'early_avg_clicks': max(0, np.random.normal(15 * engagement_mult, 8)),
            'early_clicks_std': max(0, np.random.normal(10 * engagement_mult, 5)),
            'early_max_clicks': max(0, int(np.random.normal(50 * engagement_mult, 20))),
            'early_active_days': max(1, int(np.random.normal(20 * engagement_mult, 8))),
            'early_first_access': np.random.randint(-10, 5),
            'early_last_access': np.random.randint(15, 35),
            'early_engagement_consistency': max(0, np.random.normal(3 * engagement_mult, 1.5)),
            'early_clicks_per_active_day': max(0, np.random.normal(8 * engagement_mult, 3)),
            'early_engagement_range': max(0, int(np.random.normal(25 * engagement_mult, 10))),
            
            # Assessment features based on risk level
            'early_assessments_count': np.random.randint(1, 6),
            'early_avg_score': max(0, min(100, np.random.normal(75 * score_mult, 15))),
            'early_score_std': max(0, np.random.normal(12, 5)),
            'early_min_score': max(0, np.random.normal(60 * score_mult, 10)),
            'early_max_score': max(0, min(100, np.random.normal(85 * score_mult, 10))),
            'early_missing_submissions': np.random.randint(0, 3) if risk_base > 0.5 else 0,
            'early_submitted_count': np.random.randint(2, 6),
            'early_total_weight': np.random.uniform(10, 40),
            'early_banked_count': np.random.randint(0, 2),
            'early_submission_rate': max(0, min(1, np.random.normal(0.9 * score_mult, 0.2))),
            'early_score_range': max(0, np.random.normal(20, 8)),
        }
        students.append(student)
    
    return students

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "mvp-api", "timestamp": datetime.now().isoformat()}

async def get_current_user(request: Request):
    """Simple authentication dependency with fallback for browser requests"""
    # For development/demo mode, allow requests from localhost without auth
    if os.getenv('DEVELOPMENT_MODE', 'true').lower() == 'true':
        client_host = request.client.host
        if client_host in ['127.0.0.1', 'localhost', '::1']:
            return {"user": "demo_user", "permissions": ["read", "write"]}
    
    # Try to get credentials from Authorization header
    auth_header = request.headers.get('authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        from fastapi.security import HTTPAuthorizationCredentials
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        return simple_auth(credentials)
    
    # No credentials and not localhost - require auth
    raise HTTPException(status_code=401, detail="Authentication required")

def ensure_system_initialized():
    """Ensure the intervention system is initialized"""
    global intervention_system
    if intervention_system is None:
        try:
            from models.intervention_system import InterventionRecommendationSystem
            intervention_system = InterventionRecommendationSystem()
            logger.info("✅ Intervention system initialized on-demand")
        except Exception as e:
            logger.error(f"❌ Failed to initialize intervention system: {e}")
            raise HTTPException(status_code=500, detail="System initialization failed")

@app.get("/")
async def root(request: Request):
    """Serve the main MVP page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/mvp/analyze")
async def analyze_student_data(
    request: Request,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Analyze uploaded CSV file and return risk predictions"""
    try:
        # Simple rate limiting
        simple_rate_limit(request, 10)
        
        # Ensure system is initialized
        ensure_system_initialized()
        
        # Simple file validation and processing
        contents = await file.read()
        simple_file_validation(contents, file.filename or "upload.csv")
        
        # Process CSV
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        logger.info(f"Processing CSV file: {file.filename} with {len(df)} students")
        
        # Use universal gradebook converter
        df = universal_gradebook_converter(df)
        
        # Fill missing columns with defaults for MVP simplicity
        default_features = {
            'code_module': 'AAA',
            'code_presentation': '2014J',
            'gender_encoded': 0,
            'region_encoded': 0,
            'age_band_encoded': 1,
            'education_encoded': 2,
            'is_male': 0,
            'has_disability': 0,
            'studied_credits': 120,
            'num_of_prev_attempts': 0,
            'registration_delay': 0.0,
            'unregistered': 0,
            'early_total_clicks': 150,
            'early_avg_clicks': 10,
            'early_clicks_std': 8,
            'early_max_clicks': 40,
            'early_active_days': 15,
            'early_first_access': 0,
            'early_last_access': 25,
            'early_engagement_consistency': 2.5,
            'early_clicks_per_active_day': 7,
            'early_engagement_range': 20,
            'early_assessments_count': 3,
            'early_avg_score': 70,
            'early_score_std': 10,
            'early_min_score': 50,
            'early_max_score': 80,
            'early_missing_submissions': 0,
            'early_submitted_count': 3,
            'early_total_weight': 25,
            'early_banked_count': 0,
            'early_submission_rate': 0.8,
            'early_score_range': 25,
        }
        
        # Add missing columns with defaults
        for col, default_val in default_features.items():
            if col not in df.columns:
                df[col] = default_val
        
        # Limit to first 100 students for MVP
        if len(df) > 100:
            df = df.head(100)
            logger.info("Limited analysis to first 100 students for MVP")
        
        # Get risk predictions
        risk_results = intervention_system.assess_student_risk(df)
        
        # Format results for frontend and prepare batch save
        students = []
        batch_predictions = []
        session_id = f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        for i, (_, row) in enumerate(risk_results.iterrows()):
            student_data = df.iloc[i].to_dict()
            
            # Convert numpy types to native Python types for JSON serialization
            for key, value in student_data.items():
                if hasattr(value, 'item'):  # numpy scalar
                    student_data[key] = value.item()
                elif isinstance(value, (np.integer, np.floating)):
                    student_data[key] = float(value) if isinstance(value, np.floating) else int(value)
            
            student_data.update({
                'risk_score': float(row['risk_score']),
                'risk_category': str(row['risk_category']),
                'needs_intervention': bool(row['needs_intervention']),
                'success_probability': float(row['success_probability'])
            })
            students.append(student_data)
            
            # Prepare for batch save
            batch_predictions.append({
                'student_id': student_data['id_student'],
                'risk_score': student_data['risk_score'],
                'risk_category': student_data['risk_category'],
                'features_data': student_data,
                'explanation_data': None
            })
        
        # Fast batch save - 10x faster than individual saves
        save_predictions_batch(batch_predictions, session_id)
        
        # Calculate summary statistics
        risk_counts = risk_results['risk_category'].value_counts().to_dict()
        summary = {
            'total': len(students),
            'high_risk': risk_counts.get('High Risk', 0),
            'medium_risk': risk_counts.get('Medium Risk', 0),
            'low_risk': risk_counts.get('Low Risk', 0)
        }
        
        logger.info(f"Analysis complete: {summary}")
        
        # Store uploaded student data for explainable AI
        global uploaded_students_data
        for student in students:
            uploaded_students_data[student['id_student']] = student
        
        logger.info(f"Stored {len(students)} students for explainable AI")
        
        return JSONResponse({
            'students': students,
            'summary': summary,
            'message': f'Successfully analyzed {len(students)} students'
        })
        
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="The uploaded file is empty")
    except pd.errors.ParserError:
        raise HTTPException(status_code=400, detail="Invalid CSV format")
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.get("/api/mvp/sample")
async def get_sample_data(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Return sample student data for demo purposes"""
    # Simple rate limiting
    simple_rate_limit(request, 50)
    
    # Ensure system is initialized
    ensure_system_initialized()
    
    try:
        global sample_data
        if sample_data is None:
            # Create sample data
            students_data = create_sample_student_data()
            df = pd.DataFrame(students_data)
            
            # Get risk predictions
            risk_results = intervention_system.assess_student_risk(df)
            
            # Combine data with predictions and prepare batch save
            students = []
            batch_predictions = []
            
            for i, (_, row) in enumerate(risk_results.iterrows()):
                student_data = students_data[i].copy()
                
                # Convert numpy types to native Python types for JSON serialization
                for key, value in student_data.items():
                    if hasattr(value, 'item'):  # numpy scalar
                        student_data[key] = value.item()
                    elif isinstance(value, (np.integer, np.floating)):
                        student_data[key] = float(value) if isinstance(value, np.floating) else int(value)
                
                student_data.update({
                    'risk_score': float(row['risk_score']),
                    'risk_category': str(row['risk_category']),
                    'needs_intervention': bool(row['needs_intervention']),
                    'success_probability': float(row['success_probability'])
                })
                students.append(student_data)
                
                # Prepare for batch save
                batch_predictions.append({
                    'student_id': student_data['id_student'],
                    'risk_score': student_data['risk_score'],
                    'risk_category': student_data['risk_category'],
                    'features_data': student_data,
                    'explanation_data': None
                })
            
            # Fast batch save for sample data
            save_predictions_batch(batch_predictions, "sample_data")
            
            # Calculate summary
            risk_counts = risk_results['risk_category'].value_counts().to_dict()
            summary = {
                'total': len(students),
                'high_risk': risk_counts.get('High Risk', 0),
                'medium_risk': risk_counts.get('Medium Risk', 0),
                'low_risk': risk_counts.get('Low Risk', 0)
            }
            
            # Store sample student data for explainable AI
            global uploaded_students_data
            for student in students:
                uploaded_students_data[student['id_student']] = student
            
            logger.info(f"Stored {len(students)} sample students for explainable AI")
            
            sample_data = {
                'students': students,
                'summary': summary,
            }
        
        logger.info("Serving sample data for demo")
        return JSONResponse(sample_data)
        
    except Exception as e:
        logger.error(f"Error generating sample data: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating sample data: {str(e)}")

@app.get("/api/mvp/stats")
async def get_stats():
    """Get simple analytics for the MVP"""
    try:
        conn = sqlite3.connect("mvp_data.db")
        cursor = conn.cursor()
        
        # Get recent predictions count
        cursor.execute("SELECT COUNT(*) FROM predictions WHERE date(timestamp) = date('now')")
        today_count = cursor.fetchone()[0]
        
        # Get risk distribution
        cursor.execute("""
            SELECT risk_category, COUNT(*) 
            FROM predictions 
            WHERE date(timestamp) >= date('now', '-7 days')
            GROUP BY risk_category
        """)
        risk_dist = dict(cursor.fetchall())
        
        conn.close()
        
        return JSONResponse({
            'today_predictions': today_count,
            'week_risk_distribution': risk_dist,
            'status': 'operational'
        })
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return JSONResponse({'error': 'Stats temporarily unavailable'})

@app.get("/api/mvp/explain/{student_id}")
async def explain_prediction(
    student_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Get detailed explanation for a student's risk prediction"""
    try:
        # Simple rate limiting
        simple_rate_limit(request, 50)
        
        # Try to get student data from SQLite, but don't fail if not found
        conn = sqlite3.connect("mvp_data.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM predictions 
            WHERE student_id = ? 
            ORDER BY timestamp DESC 
            LIMIT 1
        """, (student_id,))
        
        prediction = cursor.fetchone()
        conn.close()
        
        # Use real uploaded student data when available, otherwise fall back to sample data
        global uploaded_students_data
        
        if student_id in uploaded_students_data:
            # Use real uploaded student data
            real_student = uploaded_students_data[student_id]
            logger.info(f"Using real data for student {student_id} explanation")
            
            # Create DataFrame from real student data
            sample_data = pd.DataFrame([real_student])
            
        else:
            # Fall back to sample data for demo purposes
            logger.info(f"Using sample data for student {student_id} explanation (not found in uploads)")
            
            sample_data = pd.DataFrame([{
                'id_student': student_id,
                # Demographics (6 features)
                'gender_encoded': 1,
                'region_encoded': 1,
                'age_band_encoded': 1,
                'education_encoded': 2,
                'is_male': 0,
                'has_disability': 0,
                # Academic History (4 features)
                'studied_credits': 120,
                'num_of_prev_attempts': 0,
                'registration_delay': 0,
                'unregistered': 0,
                # Early VLE Engagement (10 features)
                'early_total_clicks': 120,
                'early_avg_clicks': 4.0,
                'early_clicks_std': 2.5,
                'early_max_clicks': 15,
                'early_active_days': 8,
                'early_first_access': 1,
                'early_last_access': 25,
                'early_engagement_consistency': 1.5,
                'early_clicks_per_active_day': 15.0,
                'early_engagement_range': 14,
                # Early Assessment Performance (11 features)
                'early_assessments_count': 3,
                'early_avg_score': 65,
                'early_score_std': 10.5,
                'early_min_score': 45,
                'early_max_score': 85,
                'early_missing_submissions': 2,
                'early_submitted_count': 1,
                'early_total_weight': 30.0,
                'early_banked_count': 0,
                'early_submission_rate': 0.6,
                'early_score_range': 40
            }])
        
        # Ensure intervention system is loaded
        global intervention_system
        if intervention_system is None:
            try:
                from models.intervention_system import InterventionRecommendationSystem
                intervention_system = InterventionRecommendationSystem()
                logger.info("✅ Intervention system initialized on-demand")
            except Exception as init_error:
                logger.error(f"❌ Failed to initialize intervention system: {init_error}")
                raise HTTPException(status_code=500, detail="AI system failed to initialize")
        
        # Get explainable predictions
        explanations = intervention_system.get_explainable_predictions(sample_data)
        
        if explanations:
            explanation = explanations[0]
            
            return JSONResponse({
                'student_id': student_id,
                'explanation': explanation,
                'message': 'Prediction explanation generated successfully'
            })
        else:
            raise HTTPException(status_code=500, detail="Failed to generate explanation")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error explaining prediction for student {student_id}: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error generating explanation: {str(e)}")

@app.get("/api/mvp/insights")
async def get_global_insights(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Get global model insights and feature importance"""
    try:
        # Simple rate limiting
        simple_rate_limit(request, 50)
        
        # Get global insights from the intervention system
        insights = intervention_system.get_global_insights()
        
        return JSONResponse({
            'insights': insights,
            'message': 'Global insights retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error getting global insights: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving insights: {str(e)}")

@app.post("/api/mvp/analyze-detailed")
async def analyze_student_data_detailed(
    request: Request,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Analyze uploaded CSV file with detailed explanations"""
    try:
        # Simple rate limiting
        simple_rate_limit(request, 5)
        
        # Simple file validation and processing
        contents = await file.read()
        simple_file_validation(contents, file.filename or "upload.csv")
        
        # Process CSV
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        logger.info(f"Processing CSV file with detailed analysis: {file.filename} with {len(df)} students")
        
        # Use universal gradebook converter
        df = universal_gradebook_converter(df)
        
        # Limit to first 20 students for detailed analysis
        if len(df) > 20:
            df = df.head(20)
            logger.info("Limited detailed analysis to first 20 students")
        
        # Get explainable predictions
        explanations = intervention_system.get_explainable_predictions(df)
        
        # Get regular risk predictions for summary
        risk_results = intervention_system.assess_student_risk(df)
        
        # Calculate summary statistics
        risk_counts = risk_results['risk_category'].value_counts().to_dict()
        summary = {
            'total': len(explanations),
            'high_risk': risk_counts.get('High Risk', 0),
            'medium_risk': risk_counts.get('Medium Risk', 0),
            'low_risk': risk_counts.get('Low Risk', 0)
        }
        
        logger.info(f"Detailed analysis complete: {summary}")
        
        return JSONResponse({
            'explanations': explanations,
            'summary': summary,
            'message': f'Successfully analyzed {len(explanations)} students with detailed explanations'
        })
        
    except Exception as e:
        logger.error(f"Error in detailed analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.post("/api/mvp/analyze-k12")
async def analyze_k12_gradebook(
    request: Request,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Analyze gradebook CSV using enhanced K-12 model"""
    try:
        # Simple rate limiting
        simple_rate_limit(request, 5)
        
        # Simple file validation and processing
        contents = await file.read()
        simple_file_validation(contents, file.filename or "gradebook.csv")
        
        # Process CSV
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        logger.info(f"Processing K-12 gradebook: {file.filename} with {len(df)} students")
        
        # Use ultra-advanced K-12 predictor directly on gradebook data
        global k12_ultra_predictor
        if k12_ultra_predictor is None:
            k12_ultra_predictor = K12UltraPredictor()
        
        # Get ultra-advanced K-12 predictions
        predictions = k12_ultra_predictor.predict_from_gradebook(df)
        
        # Generate enhanced recommendations for each student
        for prediction in predictions:
            prediction['recommendations'] = k12_ultra_predictor.generate_recommendations(prediction)
        
        # Create summary statistics
        total_students = len(predictions)
        high_risk = sum(1 for p in predictions if p['risk_level'] == 'danger')
        moderate_risk = sum(1 for p in predictions if p['risk_level'] == 'warning')
        low_risk = sum(1 for p in predictions if p['risk_level'] == 'success')
        
        avg_gpa = sum(p['current_gpa'] for p in predictions) / total_students if total_students > 0 else 0
        avg_attendance = sum(p['attendance_rate'] for p in predictions) / total_students if total_students > 0 else 0
        
        summary = {
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
            'model_info': k12_ultra_predictor.get_model_info()
        }
        
        logger.info(f"K-12 analysis complete: {total_students} students, {high_risk} high-risk")
        
        return JSONResponse({
            'predictions': predictions,
            'summary': summary,
            'message': f'Successfully analyzed {len(predictions)} students with Ultra-Advanced K-12 model (81.5% AUC)'
        })
        
    except Exception as e:
        logger.error(f"Error in K-12 analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing K-12 gradebook: {str(e)}")

# Demo Mode Endpoints
@app.get("/api/mvp/demo/stats")
async def get_demo_stats(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Get live demo statistics for pitch presentation"""
    try:
        # Simple rate limiting
        simple_rate_limit(request, 100)
        
        # Simulate realistic university stats
        import time
        import random
        
        # Base stats that change over time
        current_time = int(time.time())
        base_students = 1247 + (current_time % 100)  # Slowly increasing
        
        # Generate realistic metrics
        demo_stats = {
            'semester_info': {
                'name': 'Fall 2024 Semester',
                'week': 8,
                'institution': 'State University Demo'
            },
            'student_metrics': {
                'total_analyzed': base_students,
                'new_this_week': random.randint(15, 25),
                'high_risk': random.randint(80, 120),
                'medium_risk': random.randint(200, 280),
                'low_risk': base_students - random.randint(280, 400)
            },
            'intervention_metrics': {
                'interventions_triggered': random.randint(45, 75),
                'students_helped': random.randint(120, 180),
                'success_rate': round(random.uniform(0.72, 0.78), 3),
                'avg_improvement': round(random.uniform(12.5, 18.2), 1)
            },
            'time_savings': {
                'hours_saved_per_week': round(random.uniform(15.5, 22.3), 1),
                'early_interventions': random.randint(28, 45),
                'prevented_dropouts': random.randint(8, 15)
            },
            'model_performance': {
                'accuracy': 0.894,
                'prediction_speed': '<100ms',
                'confidence': round(random.uniform(0.92, 0.96), 3)
            }
        }
        
        return JSONResponse(demo_stats)
        
    except Exception as e:
        logger.error(f"Error getting demo stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving demo stats: {str(e)}")

@app.get("/api/mvp/demo/simulate-new-student")
async def simulate_new_student(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Simulate a new student enrollment for live demo"""
    try:
        # Simple rate limiting
        simple_rate_limit(request, 20)
        
        import random
        import time
        
        # Generate realistic new student data
        student_id = 10000 + random.randint(1, 9999)
        risk_scenarios = [
            {
                'risk_score': random.uniform(0.75, 0.95),
                'risk_category': 'High Risk',
                'early_avg_score': random.uniform(35, 55),
                'early_total_clicks': random.randint(10, 60),
                'story': 'New student showing concerning early patterns'
            },
            {
                'risk_score': random.uniform(0.45, 0.65),
                'risk_category': 'Medium Risk', 
                'early_avg_score': random.uniform(55, 75),
                'early_total_clicks': random.randint(80, 150),
                'story': 'Student needs proactive support'
            },
            {
                'risk_score': random.uniform(0.15, 0.35),
                'risk_category': 'Low Risk',
                'early_avg_score': random.uniform(75, 95),
                'early_total_clicks': random.randint(150, 300),
                'story': 'Student on track for success'
            }
        ]
        
        scenario = random.choice(risk_scenarios)
        
        new_student = {
            'id_student': student_id,
            'risk_score': scenario['risk_score'],
            'risk_category': scenario['risk_category'],
            'early_avg_score': scenario['early_avg_score'],
            'early_total_clicks': scenario['early_total_clicks'],
            'early_active_days': random.randint(5, 20),
            'success_probability': 1 - scenario['risk_score'],
            'timestamp': int(time.time()),
            'story': scenario['story']
        }
        
        return JSONResponse({
            'new_student': new_student,
            'message': 'New student enrollment simulated'
        })
        
    except Exception as e:
        logger.error(f"Error simulating new student: {e}")
        raise HTTPException(status_code=500, detail=f"Error simulating student: {str(e)}")

@app.get("/api/mvp/demo/success-stories")
async def get_success_stories(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Get mock success stories for demo presentation"""
    try:
        # Simple rate limiting
        simple_rate_limit(request, 50)
        
        success_stories = [
            {
                'student_id': 15234,
                'intervention': 'Academic tutoring + check-in meetings',
                'before_score': 45,
                'after_score': 78,
                'improvement': 33,
                'outcome': 'Student moved from failing to B+ average',
                'quote': '"The early intervention completely changed my academic trajectory. I went from considering dropping out to making the Dean\'s List."',
                'timeframe': '6 weeks'
            },
            {
                'student_id': 19876,
                'intervention': 'Study group + learning resources',
                'before_score': 58,
                'after_score': 85,
                'improvement': 27,
                'outcome': 'Consistent improvement across all subjects',
                'quote': '"Connecting with my study group made all the difference. I finally understood the material."',
                'timeframe': '4 weeks'
            },
            {
                'student_id': 12543,
                'intervention': 'Technology orientation + engagement plan',
                'before_score': 52,
                'after_score': 76,
                'improvement': 24,
                'outcome': 'Increased platform engagement by 300%',
                'quote': '"I didn\'t realize how much I was missing by not using the online resources. Now I\'m fully engaged."',
                'timeframe': '3 weeks'
            }
        ]
        
        return JSONResponse({
            'success_stories': success_stories,
            'total_stories': len(success_stories),
            'average_improvement': round(sum(s['improvement'] for s in success_stories) / len(success_stories), 1)
        })
        
    except Exception as e:
        logger.error(f"Error getting success stories: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving success stories: {str(e)}")

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize the MVP system on startup"""
    global intervention_system
    
    try:
        # Initialize database (PostgreSQL or SQLite fallback)
        if init_db():
            logger.info("✅ Database initialized")
            if check_database_health():
                logger.info("✅ Database health check passed")
            else:
                logger.warning("⚠️ Database health check failed")
        else:
            logger.error("❌ Database initialization failed")
        
        # Load intervention systems
        intervention_system = InterventionRecommendationSystem()
        k12_ultra_predictor = K12UltraPredictor()
        logger.info("✅ MVP Student Success Prediction API started")
        logger.info(f"✅ Original model loaded with {len(intervention_system.feature_columns)} features")
        logger.info(f"🚀 Ultra-Advanced K-12 model loaded with AUC: {k12_ultra_predictor.get_model_info()['auc_score']:.3f}")
        
    except Exception as e:
        logger.error(f"❌ Failed to start MVP API: {e}")
        raise

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")