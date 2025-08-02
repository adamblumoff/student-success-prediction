#!/usr/bin/env python3
"""
Simple startup script for MVP Student Success Prediction System
"""

import sys
import uvicorn
import os
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env file")
except ImportError:
    # Manual .env loading if python-dotenv not available
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        print("✅ Manually loaded environment variables from .env file")
    else:
        print("⚠️  No .env file found, using system environment variables")

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

if __name__ == "__main__":
    print("🚀 Starting MVP Student Success Prediction System")
    
    # Validate security configuration before starting
    try:
        from mvp.simple_auth import validate_security_configuration_on_startup
        security_config = validate_security_configuration_on_startup()
        print(f"🔒 Security configuration validated successfully")
    except ValueError as e:
        print(f"\n{e}")
        print("\n💡 To fix this:")
        print("   export MVP_API_KEY='your-secure-api-key-here'")
        print("   export DEVELOPMENT_MODE=false  # For production")
        print("   # Or set DEVELOPMENT_MODE=true for development")
        sys.exit(1)
    except Exception as e:
        print(f"⚠️  Warning during security validation: {e}")
    
    # Import the MVP API
    from mvp.mvp_api import app
    
    print("📊 Web interface will be available at: http://localhost:8001")
    print("📋 API documentation at: http://localhost:8001/docs")
    print("❌ Press Ctrl+C to stop")
    
    # Get port from environment or default to 8001
    port = int(os.getenv("PORT", 8001))
    
    # Run the server
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port, 
        log_level="info",
        reload=False
    )