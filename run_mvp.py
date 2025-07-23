#!/usr/bin/env python3
"""
Simple startup script for MVP Student Success Prediction System
"""

import sys
import uvicorn
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

if __name__ == "__main__":
    # Import the MVP API
    from mvp.mvp_api import app
    
    print("🚀 Starting MVP Student Success Prediction System")
    print("📊 Web interface will be available at: http://localhost:8001")
    print("📋 API documentation at: http://localhost:8001/docs")
    print("❌ Press Ctrl+C to stop")
    
    # Run the server
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8001, 
        log_level="info",
        reload=False
    )