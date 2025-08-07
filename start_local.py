#!/usr/bin/env python3
"""
Simple Local Development Server
Simplified startup for local development only
"""

import os
import sys
from pathlib import Path

def setup_local_environment():
    """Set up local development environment"""
    print("🏠 Setting up local development environment...")
    
    # Use local PostgreSQL database for learning PostgreSQL
    os.environ['DATABASE_URL'] = 'postgresql:///student_success_local'
    
    # Set development mode
    os.environ['DEVELOPMENT_MODE'] = 'true'
    os.environ['ENVIRONMENT'] = 'development'
    
    # Set a simple API key for local development
    if 'MVP_API_KEY' not in os.environ:
        os.environ['MVP_API_KEY'] = 'local-dev-key'
    
    print("✅ Local environment configured")
    print("   - Database: PostgreSQL (student_success_local)")
    print("   - Mode: Development")
    print("   - API Key: Local development key")

def start_server():
    """Start the local development server"""
    print("\n🚀 Starting local development server...")
    print("🌐 Open: http://localhost:8001")
    print("📋 API Docs: http://localhost:8001/docs")
    print("❌ Press Ctrl+C to stop\n")
    
    # Import and run the MVP server
    try:
        # Import the FastAPI app directly
        import uvicorn
        
        # First try the modular import path
        try:
            from src.mvp.mvp_api import app
        except ImportError:
            # Fallback to direct import after adding src to path
            import sys
            from pathlib import Path
            src_path = str(Path(__file__).parent / "src")
            if src_path not in sys.path:
                sys.path.insert(0, src_path)
            from mvp.mvp_api import app
        
        # Run with uvicorn
        uvicorn.run(app, host="127.0.0.1", port=8001, reload=False)
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except ImportError as e:
        print(f"❌ Failed to import server: {e}")
        print("💡 Make sure you're in the project directory")

if __name__ == "__main__":
    setup_local_environment()
    start_server()