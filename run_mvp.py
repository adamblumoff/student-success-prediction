#!/usr/bin/env python3
"""
Production-ready startup script for MVP Student Success Prediction System
Handles common deployment issues across different platforms
"""

import sys
import os
import logging
from pathlib import Path

def setup_logging():
    """Configure logging for deployment"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def load_environment():
    """Load environment variables with fallbacks"""
    # Try python-dotenv first
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Loaded environment variables from .env file")
    except ImportError:
        # Manual .env loading if python-dotenv not available
        env_file = Path(__file__).parent / ".env"
        if env_file.exists():
            try:
                with open(env_file) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            os.environ[key] = value
                print("✅ Manually loaded environment variables from .env file")
            except Exception as e:
                print(f"⚠️  Could not load .env file: {e}")
        else:
            print("⚠️  No .env file found, using system environment variables")

def setup_paths():
    """Setup Python paths for imports"""
    # Add src directory to path for local development
    src_path = str(Path(__file__).parent / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    
    # Also try current directory (for some deployment platforms)
    current_path = str(Path(__file__).parent)
    if current_path not in sys.path:
        sys.path.insert(0, current_path)

def validate_dependencies():
    """Check that required dependencies are available"""
    required_modules = [
        ('fastapi', 'FastAPI web framework'),
        ('uvicorn', 'ASGI server'),
        ('pandas', 'Data processing'),
        ('numpy', 'Numerical computing'),
        ('sklearn', 'Machine learning')
    ]
    
    missing = []
    for module, description in required_modules:
        try:
            __import__(module)
            print(f"✅ {description} available")
        except ImportError:
            missing.append(f"{module} ({description})")
            print(f"❌ {description} missing")
    
    if missing:
        print(f"\n❌ Missing dependencies: {', '.join(missing)}")
        print("💡 Run: pip install -r requirements.txt")
        return False
    
    return True

def validate_security():
    """Validate security configuration"""
    try:
        from mvp.simple_auth import validate_security_configuration_on_startup
        security_config = validate_security_configuration_on_startup()
        print("🔒 Security configuration validated successfully")
        return security_config
    except ValueError as e:
        print(f"\n❌ Security validation failed: {e}")
        print("\n💡 Fix by setting environment variables:")
        print("   MVP_API_KEY=your-secure-api-key-here")
        print("   ENVIRONMENT=production")
        print("   DEVELOPMENT_MODE=false")
        sys.exit(1)
    except Exception as e:
        print(f"⚠️  Warning during security validation: {e}")
        return {}

def get_app():
    """Import and return the FastAPI app with error handling"""
    try:
        from mvp.mvp_api import app
        print("✅ MVP API loaded successfully")
        return app
    except ImportError as e:
        print(f"❌ Failed to import MVP API: {e}")
        print("💡 Check that all files are in the correct locations")
        sys.exit(1)

if __name__ == "__main__":
    logger = setup_logging()
    
    print("🚀 Starting MVP Student Success Prediction System")
    print(f"🐍 Python {sys.version}")
    print(f"📁 Working directory: {os.getcwd()}")
    
    # Setup environment
    load_environment()
    setup_paths()
    
    # Validate system
    if not validate_dependencies():
        sys.exit(1)
    
    security_config = validate_security()
    app = get_app()
    
    # Get configuration
    port = int(os.getenv("PORT", 8001))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"📊 Starting server on {host}:{port}")
    print(f"🌐 Web interface: http://localhost:{port}")
    print(f"📋 API docs: http://localhost:{port}/docs")
    print("❌ Press Ctrl+C to stop")
    
    # Import uvicorn here to ensure it's available
    try:
        import uvicorn
        
        # Run the server with deployment-friendly settings
        uvicorn.run(
            app, 
            host=host, 
            port=port, 
            log_level="info",
            reload=False,
            access_log=True
        )
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        print("💡 Check that the port is available and dependencies are installed")
        sys.exit(1)