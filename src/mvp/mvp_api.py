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
from fastapi.middleware.trustedhost import TrustedHostMiddleware
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
from security import secure_validator, security_manager, rate_limiter
from security.auth import require_read_permission, require_write_permission
from api.canvas_endpoints import canvas_router

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

# Security middleware
allowed_hosts = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

# CORS middleware with secure defaults
allowed_origins = os.getenv('ALLOWED_ORIGINS', 'http://localhost:8001').split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=3600
)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'"
    
    # Remove server header
    response.headers.pop("server", None)
    
    return response

# Global variables
intervention_system = None
sample_data = None

# Include Canvas integration router
app.include_router(canvas_router)

# Static files and templates
app.mount("/static", StaticFiles(directory="src/mvp/static"), name="static")
templates = Jinja2Templates(directory="src/mvp/templates")

# Simple SQLite database for MVP
def init_sqlite():
    """Initialize simple SQLite database for MVP"""
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
    return db_path

def save_prediction_to_sqlite(student_id: int, risk_score: float, risk_category: str, session_id: str):
    """Save prediction to SQLite"""
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
        logger.warning(f"Failed to save prediction: {e}")

def detect_gradebook_format(df):
    """Automatically detect gradebook format from column patterns"""
    columns = [col.lower() for col in df.columns]
    
    # Canvas detection
    if any('student' in col for col in columns) and any('current score' in col for col in columns):
        return 'canvas'
    
    # Blackboard detection (often has "Last Name" and "First Name" separate)
    if any('last name' in col for col in columns) and any('first name' in col for col in columns):
        return 'blackboard'
    
    # Moodle detection (often has "email address" and specific format)
    if any('email address' in col for col in columns) and any('course total' in col for col in columns):
        return 'moodle'
    
    # Google Classroom (often has "Student" and "Grade" columns)
    if any('timestamp' in col for col in columns) and any('score' in col for col in columns):
        return 'google_classroom'
    
    # PowerSchool (common in K-12)
    if any('student number' in col for col in columns) and any('grade level' in col for col in columns):
        return 'powerschool'
    
    # Generic gradebook (has some form of ID and scores)
    if any('id' in col for col in columns) and len([col for col in columns if any(keyword in col for keyword in ['score', 'grade', 'points', 'percent'])]) >= 2:
        return 'generic'
    
    # Direct prediction format
    if 'id_student' in columns:
        return 'prediction_format'
    
    return 'unknown'

def extract_student_identifier(df, format_type):
    """Extract student ID from various formats"""
    columns = df.columns.tolist()
    
    if format_type == 'canvas':
        return df['ID'].astype(str)
    elif format_type == 'blackboard':
        # Blackboard often uses "Username" or combines last,first names
        if 'Username' in columns:
            return df['Username'].astype(str)
        elif 'Last Name' in columns and 'First Name' in columns:
            return (df['Last Name'] + '_' + df['First Name']).str.replace(' ', '')
    elif format_type in ['moodle', 'google_classroom']:
        if 'Email address' in columns:
            return df['Email address'].str.extract(r'^([^@]+)')[0]  # Extract username from email
    elif format_type == 'powerschool':
        return df['Student Number'].astype(str)
    elif format_type == 'generic':
        # Find the most likely ID column
        id_cols = [col for col in columns if 'id' in col.lower()]
        if id_cols:
            return df[id_cols[0]].astype(str)
    elif format_type == 'prediction_format':
        return df['id_student'].astype(str)
    
    # Fallback: use row index as ID
    return pd.Series(range(1000, 1000 + len(df)), index=df.index).astype(str)

def extract_assignment_scores(df, format_type):
    """Extract assignment scores and calculate statistics"""
    columns = df.columns.tolist()
    
    # Define patterns for assignment columns by platform
    score_patterns = {
        'canvas': ['Assignment', 'Quiz', 'Exam', 'Test', 'Discussion'],
        'blackboard': ['Item', 'Assignment', 'Quiz', 'Test', 'Exam'],
        'moodle': ['Quiz', 'Assignment', 'Forum', 'Workshop'],
        'google_classroom': ['Assignment', 'Quiz'],
        'powerschool': ['Assignment', 'Quiz', 'Test', 'Exam'],
        'generic': ['Assignment', 'Quiz', 'Test', 'Exam', 'Grade', 'Score', 'Points']
    }
    
    patterns = score_patterns.get(format_type, score_patterns['generic'])
    
    # Find score columns
    score_columns = []
    for col in columns:
        if any(pattern.lower() in col.lower() for pattern in patterns):
            # Exclude final/summative items for early prediction
            if not any(exclude in col.lower() for exclude in ['final', 'total', 'current', 'overall', 'summary']):
                score_columns.append(col)
    
    # Extract numeric scores from each column
    scores_data = []
    for _, row in df.iterrows():
        student_scores = []
        for col in score_columns:
            try:
                value = str(row[col]).strip()
                if value and value.lower() not in ['nan', '', 'null', 'n/a']:
                    # Handle different score formats
                    if '/' in value:  # Format: "85/100"
                        score, max_points = value.split('/')
                        percentage = (float(score) / float(max_points)) * 100
                        student_scores.append(percentage)
                    elif '%' in value:  # Format: "85%"
                        student_scores.append(float(value.replace('%', '')))
                    elif value.replace('.', '').isdigit():  # Pure number
                        score = float(value)
                        # If score seems to be out of 100, use as-is; otherwise assume it's a percentage
                        student_scores.append(score if score <= 100 else score)
            except (ValueError, AttributeError, IndexError):
                continue
        
        # Calculate statistics
        if student_scores:
            scores_data.append({
                'early_avg_score': np.mean(student_scores),
                'early_min_score': np.min(student_scores),
                'early_max_score': np.max(student_scores),
                'early_score_std': np.std(student_scores) if len(student_scores) > 1 else 0,
                'early_submitted_count': len(student_scores),
                'early_assessments_count': len(score_columns),
                'early_score_range': np.max(student_scores) - np.min(student_scores) if len(student_scores) > 1 else 0
            })
        else:
            scores_data.append({
                'early_avg_score': 50,  # Default for missing data
                'early_min_score': 0,
                'early_max_score': 50,
                'early_score_std': 0,
                'early_submitted_count': 0,
                'early_assessments_count': max(1, len(score_columns)),
                'early_score_range': 0
            })
    
    return pd.DataFrame(scores_data)

def extract_engagement_metrics(df, format_type):
    """Extract engagement metrics from various gradebook formats"""
    engagement_data = []
    
    # Look for engagement indicators by platform
    engagement_patterns = {
        'canvas': ['Activity Time', 'Last Activity', 'Participations', 'Page Views'],
        'blackboard': ['Last Access', 'Time in Course', 'Discussion Posts'],
        'moodle': ['Last access', 'Time spent', 'Forum posts'],
        'google_classroom': ['Last seen', 'Timestamp'],
        'generic': ['activity', 'access', 'time', 'participation', 'engagement']
    }
    
    patterns = engagement_patterns.get(format_type, engagement_patterns['generic'])
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
    return {"status": "healthy", "service": "mvp-api", "timestamp": datetime.now()}

@app.get("/")
async def root(request: Request):
    """Serve the main MVP page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/canvas")
async def canvas_integration_page(request: Request):
    """Serve the Canvas integration page"""
    return templates.TemplateResponse("canvas_integration.html", {"request": request})

@app.post("/api/mvp/analyze")
async def analyze_student_data(
    request: Request,
    file: UploadFile = File(...),
    current_user: dict = Depends(require_write_permission)
):
    """Analyze uploaded CSV file and return risk predictions"""
    try:
        # Rate limiting for file uploads
        rate_limiter.enforce_rate_limit(request, 'upload')
        
        # Secure file validation and processing
        contents = await file.read()
        df = secure_validator.secure_process_upload(contents, file.filename or "upload.csv")
        
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
        
        # Format results for frontend
        students = []
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
            
            # Save to SQLite
            save_prediction_to_sqlite(
                student_data['id_student'],
                student_data['risk_score'],
                student_data['risk_category'],
                f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
        
        # Calculate summary statistics
        risk_counts = risk_results['risk_category'].value_counts().to_dict()
        summary = {
            'total': len(students),
            'high_risk': risk_counts.get('High Risk', 0),
            'medium_risk': risk_counts.get('Medium Risk', 0),
            'low_risk': risk_counts.get('Low Risk', 0)
        }
        
        logger.info(f"Analysis complete: {summary}")
        
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
    current_user: dict = Depends(require_read_permission)
):
    """Return sample student data for demo purposes"""
    # Rate limiting for analysis requests
    rate_limiter.enforce_rate_limit(request, 'analysis')
    try:
        global sample_data
        if sample_data is None:
            # Create sample data
            students_data = create_sample_student_data()
            df = pd.DataFrame(students_data)
            
            # Get risk predictions
            risk_results = intervention_system.assess_student_risk(df)
            
            # Combine data with predictions
            students = []
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
                
                # Save to SQLite
                save_prediction_to_sqlite(
                    student_data['id_student'],
                    student_data['risk_score'],
                    student_data['risk_category'],
                    "sample_data"
                )
            
            # Calculate summary
            risk_counts = risk_results['risk_category'].value_counts().to_dict()
            summary = {
                'total': len(students),
                'high_risk': risk_counts.get('High Risk', 0),
                'medium_risk': risk_counts.get('Medium Risk', 0),
                'low_risk': risk_counts.get('Low Risk', 0)
            }
            
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

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize the MVP system on startup"""
    global intervention_system
    
    try:
        # Initialize SQLite database
        init_sqlite()
        logger.info("✅ SQLite database initialized")
        
        # Load intervention system
        intervention_system = InterventionRecommendationSystem()
        logger.info("✅ MVP Student Success Prediction API started")
        logger.info(f"✅ Model loaded with {len(intervention_system.feature_columns)} features")
        
    except Exception as e:
        logger.error(f"❌ Failed to start MVP API: {e}")
        raise

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")