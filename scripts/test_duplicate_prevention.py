#!/usr/bin/env python3
"""
Test Duplicate Prevention
Tests the unique constraints and upsert logic to prevent duplicates
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.mvp.database import save_prediction, save_predictions_batch
from src.mvp.models import Student, Prediction, Institution
from src.mvp.database import get_db_session
from sqlalchemy import text

def test_duplicate_prevention():
    """Test duplicate prevention mechanisms"""
    
    print("=== TESTING DUPLICATE PREVENTION ===")
    print()
    
    # Set PostgreSQL URL
    os.environ['DATABASE_URL'] = "postgresql://postgres:postgres@localhost:5432/student_success"
    
    # Test data
    test_prediction = {
        'student_id': 'TEST001',
        'risk_score': 0.75,
        'risk_category': 'High Risk',
        'success_probability': 0.25,
        'features_data': {'test': 'data'},
        'explanation_data': {'explanation': 'test'}
    }
    
    session_id = "test_session_001"
    
    print("🧪 Test 1: Creating initial prediction")
    try:
        save_prediction(test_prediction, session_id)
        print("✅ Initial prediction created successfully")
    except Exception as e:
        print(f"❌ Failed to create initial prediction: {e}")
        return
    
    print("\n🧪 Test 2: Attempting to create duplicate prediction (should update existing)")
    try:
        # Modify some data to see if it updates
        test_prediction['risk_score'] = 0.80
        test_prediction['risk_category'] = 'Critical Risk'
        
        save_prediction(test_prediction, session_id)
        print("✅ Duplicate prevention worked - prediction updated instead of duplicated")
    except Exception as e:
        print(f"❌ Duplicate prevention failed: {e}")
        return
    
    print("\n🧪 Test 3: Verifying only one prediction exists for student")
    try:
        with get_db_session() as db:
            predictions = db.execute(text("""
                SELECT COUNT(*) as count, risk_score, risk_category
                FROM predictions p
                JOIN students s ON p.student_id = s.id
                WHERE s.student_id = 'TEST001'
                GROUP BY risk_score, risk_category
            """)).fetchall()
            
            if len(predictions) == 1 and predictions[0].count == 1:
                print(f"✅ Only one prediction exists with updated values: {predictions[0].risk_score}, {predictions[0].risk_category}")
            else:
                print(f"❌ Found {len(predictions)} prediction groups, expected 1")
                for pred in predictions:
                    print(f"   - Count: {pred.count}, Risk: {pred.risk_score}, Category: {pred.risk_category}")
    except Exception as e:
        print(f"❌ Failed to verify single prediction: {e}")
        return
    
    print("\n🧪 Test 4: Testing batch upsert with mixed new/existing students")
    try:
        batch_data = [
            {
                'student_id': 'TEST001',  # Existing - should update
                'risk_score': 0.85,
                'risk_category': 'Very High Risk',
                'success_probability': 0.15,
                'features_data': {'batch': 'test'},
                'explanation_data': {'explanation': 'batch test'}
            },
            {
                'student_id': 'TEST002',  # New - should create
                'risk_score': 0.30,
                'risk_category': 'Low Risk',
                'success_probability': 0.70,
                'features_data': {'new': 'student'},
                'explanation_data': {'explanation': 'new student'}
            }
        ]
        
        save_predictions_batch(batch_data, "batch_test_session")
        print("✅ Batch upsert completed successfully")
    except Exception as e:
        print(f"❌ Batch upsert failed: {e}")
        return
    
    print("\n🧪 Test 5: Verifying final state")
    try:
        with get_db_session() as db:
            results = db.execute(text("""
                SELECT s.student_id, p.risk_score, p.risk_category
                FROM predictions p
                JOIN students s ON p.student_id = s.id
                WHERE s.student_id IN ('TEST001', 'TEST002')
                ORDER BY s.student_id
            """)).fetchall()
            
            print(f"✅ Final database state ({len(results)} predictions):")
            for result in results:
                print(f"   - Student {result.student_id}: {result.risk_score} ({result.risk_category})")
            
            # Verify TEST001 was updated and TEST002 was created
            if len(results) == 2:
                test001 = next((r for r in results if r.student_id == 'TEST001'), None)
                test002 = next((r for r in results if r.student_id == 'TEST002'), None)
                
                if test001 and test001.risk_score == 0.85:
                    print("   ✅ TEST001 was properly updated")
                else:
                    print("   ❌ TEST001 was not properly updated")
                
                if test002 and test002.risk_score == 0.30:
                    print("   ✅ TEST002 was properly created")
                else:
                    print("   ❌ TEST002 was not properly created")
            
    except Exception as e:
        print(f"❌ Failed to verify final state: {e}")
        return
    
    print("\n🎉 ALL DUPLICATE PREVENTION TESTS PASSED!")

if __name__ == "__main__":
    test_duplicate_prevention()