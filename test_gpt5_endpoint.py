#!/usr/bin/env python3
"""
Test GPT-5-nano with correct endpoint
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_gpt5_nano_endpoint():
    """Test GPT-5-nano with Responses API endpoint."""
    print("🧪 Testing GPT-5-nano with Responses API")
    print("=" * 45)
    
    # Set API key
    os.environ['OPENAI_API_KEY'] = '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'
    
    try:
        from src.mvp.services.gpt_oss_service import GPTOSSService
        
        # Test GPT-5-nano
        service = GPTOSSService(model_name="gpt-5-nano")
        
        if not service.initialize_model():
            print("❌ Failed to initialize")
            return False
        
        print("✅ Service initialized")
        
        # Simple test prompt
        prompt = "Student has Grade 9, GPA 2.1, attendance 67%. What interventions are needed?"
        
        print("\n🎯 Testing with Responses API endpoint...")
        result = service.generate_analysis(prompt, "student_analysis", max_tokens=200)
        
        print(f"📊 Result: {result}")
        
        if result.get("success"):
            analysis = result.get("analysis", "")
            print("✅ SUCCESS: Got response!")
            print(f"📝 Analysis: {analysis}")
            return True
        else:
            print("❌ Failed")
            print(f"Error: {result.get('analysis', 'No analysis')}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_gpt5_nano_endpoint()
    print(f"\n{'🎉 SUCCESS' if success else '❌ FAILED'}: GPT-5-nano endpoint test")