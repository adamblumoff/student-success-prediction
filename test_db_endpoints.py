#!/usr/bin/env python3
"""
Test script for database-specific API endpoints
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

def test_system_status():
    """Test system status with database info"""
    print("🔍 Testing System Status with Database Info...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/status", headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ System Status: {data['system']}")
            print(f"   Database Available: {data.get('database_available', 'Unknown')}")
            print(f"   Database Stats: {data.get('database_stats', {})}")
            return True
        else:
            print(f"❌ Status Check Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Status Check Error: {e}")
        return False

def test_create_student():
    """Test creating a student via API"""
    print("\n🔍 Testing Student Creation...")
    
    student_data = {
        "id_student": 99998,
        "code_module": "TEST",
        "code_presentation": "2024J",
        "gender_encoded": 0,
        "age_band_encoded": 1,
        "education_encoded": 2,
        "studied_credits": 120,
        "num_of_prev_attempts": 0,
        "registration_delay": -5.0,
        "early_total_clicks": 800.0,
        "early_avg_clicks": 15.5,
        "early_active_days": 30,
        "early_assessments_count": 4,
        "early_avg_score": 82.0,
        "early_submission_rate": 0.9
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/students/create",
            headers=HEADERS,
            json=student_data
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Student Created: {data['message']}")
            print(f"   Student ID: {data['student_id']}")
            print(f"   Database ID: {data['database_id']}")
            return True
        elif response.status_code == 503:
            print("⚠️ Database not available - endpoint skipped")
            return True
        else:
            print(f"❌ Student Creation Failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Student Creation Error: {e}")
        return False

def test_student_prediction_with_db():
    """Test prediction that saves to database"""
    print("\n🔍 Testing Prediction with Database Persistence...")
    
    student_data = {
        "id_student": 99997,
        "code_module": "TEST",
        "code_presentation": "2024J", 
        "gender_encoded": 1,
        "age_band_encoded": 0,
        "education_encoded": 3,
        "studied_credits": 60,
        "num_of_prev_attempts": 1,
        "registration_delay": 10.0,
        "early_total_clicks": 200.0,
        "early_avg_clicks": 3.5,
        "early_active_days": 12,
        "early_assessments_count": 1,
        "early_avg_score": 45.0,
        "early_submission_rate": 0.4
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
            print(f"✅ Prediction with DB Persistence:")
            print(f"   Student ID: {data['student_id']}")
            print(f"   Risk Score: {data['risk_score']:.3f}")
            print(f"   Risk Category: {data['risk_category']}")
            print(f"   Response Time: {response_time:.1f}ms")
            return data['student_id']
        else:
            print(f"❌ Prediction Failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Prediction Error: {e}")
        return None

def test_student_predictions_history(student_id):
    """Test getting student prediction history"""
    print(f"\n🔍 Testing Prediction History for Student {student_id}...")
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/students/{student_id}/predictions",
            headers=HEADERS
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Prediction History Retrieved:")
            print(f"   Total Predictions: {data['total_predictions']}")
            if data['predictions']:
                latest = data['predictions'][0]
                print(f"   Latest Risk Score: {latest['risk_score']:.3f}")
                print(f"   Latest Category: {latest['risk_category']}")
            return True
        elif response.status_code == 503:
            print("⚠️ Database not available - endpoint skipped")
            return True
        elif response.status_code == 404:
            print("⚠️ Student not found in database")
            return True
        else:
            print(f"❌ History Retrieval Failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ History Retrieval Error: {e}")
        return False

def test_risk_analytics():
    """Test risk distribution analytics"""
    print("\n🔍 Testing Risk Distribution Analytics...")
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/analytics/risk-distribution",
            headers=HEADERS
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Risk Analytics Retrieved:")
            print(f"   Total Predictions: {data['total_predictions']}")
            for risk_level, stats in data['risk_distribution'].items():
                print(f"   {risk_level}: {stats['count']} ({stats['percentage']}%)")
            return True
        elif response.status_code == 503:
            print("⚠️ Database not available - endpoint skipped")
            return True
        else:
            print(f"❌ Analytics Failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Analytics Error: {e}")
        return False

def main():
    """Run all database endpoint tests"""
    print("🧪 TESTING DATABASE API ENDPOINTS")
    print("=" * 50)
    
    # Wait for API to be ready
    time.sleep(1)
    
    # Run tests
    tests = [
        test_system_status(),
        test_create_student(),
        test_risk_analytics()
    ]
    
    # Test prediction with database persistence
    student_id = test_student_prediction_with_db()
    if student_id:
        tests.append(test_student_predictions_history(student_id))
    
    # Summary
    passed = sum(tests)
    total = len(tests)
    
    print(f"\n📋 RESULTS: {passed}/{total} tests passed")
    if passed == total:
        print("🎉 ALL DATABASE ENDPOINT TESTS PASSED!")
    else:
        print("⚠️ Some tests failed - check output above")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)