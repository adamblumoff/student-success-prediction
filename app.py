#!/usr/bin/env python3
"""
Deployment-optimized entry point for Student Success Prediction System
Works with Render, Railway, Heroku, and other cloud platforms
"""

import os
import sys
from pathlib import Path

# Setup paths for deployment
current_dir = Path(__file__).parent
src_dir = current_dir / "src"

# Add both current directory and src to Python path
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(src_dir))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Set default environment variables for deployment
if not os.getenv("MVP_API_KEY"):
    os.environ["MVP_API_KEY"] = "0dUHi4QroC1GfgnbibLbqowUnv2YFWIe"

if not os.getenv("ENVIRONMENT"):
    os.environ["ENVIRONMENT"] = "production"

if not os.getenv("DEVELOPMENT_MODE"):
    os.environ["DEVELOPMENT_MODE"] = "false"

# Import and configure the app
try:
    from mvp.mvp_api import app
    
    # Add a startup event to validate configuration
    @app.on_event("startup")
    async def startup_event():
        print("✅ Student Success Prediction System started successfully")
        print(f"🔒 Environment: {os.getenv('ENVIRONMENT', 'unknown')}")
        print(f"🌐 Port: {os.getenv('PORT', '8001')}")
    
except ImportError as e:
    print(f"❌ Failed to import app: {e}")
    print("📁 Current directory:", os.getcwd())
    print("🐍 Python path:", sys.path)
    raise

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8001))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"🚀 Starting server on {host}:{port}")
    
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        log_level="info",
        reload=False,
        access_log=True
    )