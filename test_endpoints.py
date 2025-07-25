#\!/usr/bin/env python3
"""
Test script to debug the explain endpoint issue
"""

import sys
import pandas as pd
sys.path.append('src')

def test_explain_endpoint():
    """Test the explain endpoint functionality directly"""
    
    print("🧪 Testing Explain Endpoint Components")
    print("="*50)
    
    # Test 1: Test intervention system initialization
    print("\n1. Testing Intervention System Initialization:")
    try:
        from models.intervention_system import InterventionRecommendationSystem
        system = InterventionRecommendationSystem()
        print(f"✅ Intervention system loaded with {len(system.feature_columns)} features")
    except Exception as e:
        print(f"❌ Failed to load intervention system: {e}")
        return False
    
    # Test 2: Test explainable AI functionality
    print("\n2. Testing Explainable AI:")
    try:
        # Create sample student data (same as in the API)
        sample_data = pd.DataFrame([{
            'id_student': 1001,
            'early_avg_score': 65,
            'early_total_clicks': 120,
            'early_active_days': 8,
            'early_missing_submissions': 2,
            'early_submission_rate': 0.6,
            'studied_credits': 120,
            'num_of_prev_attempts': 0,
            'registration_delay': 0,
            'early_engagement_consistency': 1.5
        }])
        
        print(f"✅ Sample data created: {sample_data.shape}")
        
        # Test explainable predictions
        explanations = system.get_explainable_predictions(sample_data)
        
        if explanations:
            explanation = explanations[0]
            print(f"✅ Explanation generated for student {explanation.get('student_id')}")
            print(f"   Risk category: {explanation.get('risk_category')}")
            print(f"   Risk score: {explanation.get('risk_score'):.2f}")
            print(f"   Has explanation text: {'explanation' in explanation}")
            print(f"   Has risk factors: {'risk_factors' in explanation}")
            
        else:
            print("❌ No explanations generated")
            return False
            
    except Exception as e:
        print(f"❌ Error in explainable AI: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_authentication():
    """Test if the authentication is working"""
    print("\n🔐 Testing Authentication:")
    try:
        from mvp.simple_auth import simple_auth
        
        # Create mock credentials
        class MockCredentials:
            def __init__(self, token):
                self.credentials = token
        
        # Test valid auth
        valid_creds = MockCredentials("dev-key-change-me")
        result = simple_auth(valid_creds)
        print(f"✅ Valid auth works: {result}")
        
    except Exception as e:
        print(f"❌ Auth test failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting Explain Endpoint Debug Tests")
    
    # Test authentication
    test_authentication()
    
    # Test explain functionality
    success = test_explain_endpoint()
    
    if success:
        print("\n✅ ALL TESTS PASSED - The explain endpoint should work\!")
    else:
        print("\n❌ TESTS FAILED - There are issues with the explain endpoint")
EOF < /dev/null
