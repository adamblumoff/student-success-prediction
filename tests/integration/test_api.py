#!/usr/bin/env python3
"""
API Test Client for Student Success Prediction System
"""

import requests
import json
import time

# API Configuration
API_BASE_URL = "http://localhost:8000"
API_KEY = "demo-api-key"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def test_health_check():
    """Test API health check"""
    print("🔍 Testing Health Check...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health Check: {data['status']}")
            return True
        else:
            print(f"❌ Health Check Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health Check Error: {e}")
        return False

def test_single_prediction():
    """Test single student prediction"""
    print("\n🔍 Testing Single Student Prediction...")
    
    # Sample student data (high-risk profile)
    student_data = {
        "id_student": 12345,
        "code_module": "AAA",
        "code_presentation": "2013J",
        "gender_encoded": 1,
        "age_band_encoded": 0,
        "education_encoded": 1,
        "studied_credits": 60,
        "num_of_prev_attempts": 1,
        "registration_delay": 15.0,
        "early_total_clicks": 150,
        "early_avg_clicks": 5.0,
        "early_active_days": 8,
        "early_engagement_consistency": 0.25,
        "early_assessments_count": 2,
        "early_avg_score": 35.0,
        "early_min_score": 20.0,
        "early_max_score": 50.0,
        "early_submission_rate": 0.6,
        "early_missing_submissions": 2
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{API_BASE_URL}/predict/single",
            headers=HEADERS,
            json=student_data
        )
        response_time = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Single Prediction Success:")
            print(f"   Student ID: {data['student_id']}")
            print(f"   Risk Score: {data['risk_score']:.3f}")
            print(f"   Risk Category: {data['risk_category']}")
            print(f"   Needs Intervention: {data['needs_intervention']}")
            print(f"   Response Time: {response_time:.1f}ms")
            return True
        else:
            print(f"❌ Single Prediction Failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Single Prediction Error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 TESTING STUDENT SUCCESS PREDICTION API")
    print("=" * 50)
    
    # Wait for API to be ready
    time.sleep(1)
    
    # Run tests
    health_ok = test_health_check()
    prediction_ok = test_single_prediction()
    
    print(f"\n📋 RESULTS: {'✅ API WORKING' if health_ok and prediction_ok else '❌ ISSUES FOUND'}")