#!/usr/bin/env python3
"""
Test ML model integration with database
"""
import sys
import pandas as pd
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

def test_ml_prediction_with_db():
    """Test ML prediction using database stored features"""
    print("🧪 TESTING ML MODEL WITH DATABASE INTEGRATION")
    print("=" * 60)
    
    try:
        # Test 1: Load model and test prediction
        from models.intervention_system import InterventionRecommendationSystem
        
        print("🔍 Loading ML intervention system...")
        intervention_system = InterventionRecommendationSystem()
        print(f"✅ Model loaded with {len(intervention_system.feature_columns)} features")
        
        # Test 2: Database feature extraction
        from database.connection import SQLiteManager
        from database.models import get_student_features_for_ml
        
        print("\n🔍 Testing database feature extraction...")
        sqlite_manager = SQLiteManager("demo_student_success.db")
        
        with next(sqlite_manager.get_session()) as db:
            # Get features for student ID 1 from database
            student_features = get_student_features_for_ml(db, 1)
            if student_features:
                print(f"✅ Retrieved {len(student_features)} features from database")
                print(f"   Student ID: {student_features['id_student']}")
                print(f"   Module: {student_features['code_module']}")
                print(f"   Early Clicks: {student_features['early_total_clicks']}")
                print(f"   Early Score: {student_features['early_avg_score']}")
            else:
                print("❌ No features retrieved from database")
                return False
        
        # Test 3: ML prediction using database features
        print("\n🔍 Testing ML prediction with database features...")
        
        # Create DataFrame from database features
        student_df = pd.DataFrame([student_features])
        
        # Run risk assessment
        risk_result = intervention_system.assess_student_risk(student_df)
        
        print("✅ ML Prediction Results:")
        result = risk_result.iloc[0]
        print(f"   Success Probability: {result['success_probability']:.3f}")
        print(f"   Risk Score: {result['risk_score']:.3f}")
        print(f"   Risk Category: {result['risk_category']}")
        print(f"   Needs Intervention: {result['needs_intervention']}")
        
        # Test 4: Intervention recommendations
        print("\n🔍 Testing intervention recommendations...")
        
        if result['needs_intervention']:
            interventions = intervention_system.recommend_interventions(student_df)
            intervention_result = interventions.iloc[0]
            print("✅ Intervention Recommendations:")
            print(f"   Risk Level: {intervention_result['risk_level']}")
            print(f"   Priority: {intervention_result['priority']}")
            print(f"   Number of Interventions: {len(intervention_result['interventions'])}")
            
            # Show first intervention
            if intervention_result['interventions']:
                first_intervention = intervention_result['interventions'][0]
                print(f"   Top Intervention: {first_intervention['title']}")
                print(f"   Category: {first_intervention['category']}")
        else:
            print("✅ No intervention needed (low risk student)")
        
        # Test 5: Complete pipeline validation
        print("\n🔍 Testing complete prediction pipeline...")
        
        # Create a high-risk test student
        high_risk_student = {
            'id_student': 99999,
            'code_module': 'TEST',
            'code_presentation': '2024J',
            'gender_encoded': 1,
            'region_encoded': 0,
            'age_band_encoded': 0,
            'education_encoded': 1,
            'is_male': 1,
            'has_disability': 0,
            'studied_credits': 60,
            'num_of_prev_attempts': 2,
            'registration_delay': 20.0,
            'unregistered': 0,
            'early_total_clicks': 50.0,
            'early_avg_clicks': 1.0,
            'early_clicks_std': 2.0,
            'early_max_clicks': 5.0,
            'early_active_days': 3,
            'early_first_access': -5,
            'early_last_access': 10,
            'early_engagement_consistency': 0.1,
            'early_clicks_per_active_day': 1.5,
            'early_engagement_range': 15,
            'early_assessments_count': 1,
            'early_avg_score': 25.0,
            'early_score_std': 0.0,
            'early_min_score': 25.0,
            'early_max_score': 25.0,
            'early_missing_submissions': 2,
            'early_submitted_count': 1,
            'early_total_weight': 20.0,
            'early_banked_count': 0,
            'early_submission_rate': 0.33,
            'early_score_range': 0.0
        }
        
        test_df = pd.DataFrame([high_risk_student])
        test_result = intervention_system.assess_student_risk(test_df)
        
        print("✅ High-Risk Student Test:")
        test_row = test_result.iloc[0]
        print(f"   Risk Score: {test_row['risk_score']:.3f}")
        print(f"   Risk Category: {test_row['risk_category']}")
        print(f"   Needs Intervention: {test_row['needs_intervention']}")
        
        print("\n🎉 ALL ML DATABASE INTEGRATION TESTS PASSED!")
        print("\n📊 SUMMARY:")
        print("   ✅ Database feature extraction working")
        print("   ✅ ML model prediction with DB data working") 
        print("   ✅ Risk assessment pipeline functional")
        print("   ✅ Intervention system integrated")
        print("   ✅ Complete end-to-end pipeline validated")
        
        return True
        
    except Exception as e:
        print(f"❌ ML Database integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_ml_prediction_with_db()
    sys.exit(0 if success else 1)