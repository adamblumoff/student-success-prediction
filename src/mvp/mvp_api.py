"""
Modular MVP API - Entry point that combines all specialized routers
"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import os
import sys
import time
import pathlib

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Initialize structured logging first
from src.mvp.logging_config import get_logger, log_request, log_error
logger = get_logger(__name__)

# Request Logging Middleware
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests with timing and user context"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Extract user context if available
        user_id = getattr(request.state, 'user', {}).get('user', 'anonymous')
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log successful requests
            log_request(
                endpoint=str(request.url.path),
                method=request.method,
                user_id=user_id,
                processing_time=round(process_time * 1000, 2)  # Convert to ms
            )
            
            # Add timing header
            response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            
            # Log failed requests
            log_error(
                error=e,
                context=f"{request.method} {request.url.path}",
                user_id=user_id
            )
            
            raise

# Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add comprehensive security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Comprehensive security headers
        security_headers = {
            # Prevent clickjacking attacks
            "X-Frame-Options": "DENY",
            
            # Prevent MIME type sniffing
            "X-Content-Type-Options": "nosniff",
            
            # Enable XSS protection
            "X-XSS-Protection": "1; mode=block",
            
            # Referrer policy for privacy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Content Security Policy (restrictive for security)
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' cdnjs.cloudflare.com cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' cdnjs.cloudflare.com cdn.jsdelivr.net fonts.googleapis.com; "
                "font-src 'self' fonts.gstatic.com cdnjs.cloudflare.com; "
                "img-src 'self' data: blob:; "
                "connect-src 'self'; "
                "base-uri 'self'; "
                "form-action 'self'"
            ),
            
            # Permissions policy (restrict sensitive APIs)
            "Permissions-Policy": (
                "geolocation=(), "
                "microphone=(), "
                "camera=(), "
                "payment=(), "
                "usb=(), "
                "magnetometer=(), "
                "gyroscope=(), "
                "accelerometer=()"
            ),
            
            # HSTS for HTTPS enforcement (only in production)
            **({"Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload"} 
               if os.getenv('ENVIRONMENT', '').lower() in ['production', 'prod'] 
               else {}),
            
            # Server identification (minimal)
            "Server": "StudentSuccessAPI/2.0"
        }
        
        # Apply all security headers
        for header, value in security_headers.items():
            response.headers[header] = value
            
        return response

# Import all modular routers
from src.mvp.api.core import router as core_router
from src.mvp.api.canvas_endpoints import router as canvas_router
from src.mvp.api.powerschool_endpoints import router as powerschool_router
from src.mvp.api.google_classroom_endpoints import router as google_classroom_router
from src.mvp.api.combined_endpoints import router as combined_router
from src.mvp.api.notifications_endpoints import router as notifications_router
from src.mvp.api.health import router as health_router

# Create FastAPI app
app = FastAPI(
    title="Student Success Prediction MVP",
    description="Modular API for student success prediction with Canvas LMS, PowerSchool SIS, and Google Classroom integration",
    version="2.0.0"
)

# Add middleware in correct order (last added = first executed)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# Add trusted host middleware for production
if os.getenv('ENVIRONMENT', '').lower() in ['production', 'prod']:
    # Allow common deployment platforms
    default_hosts = 'localhost,127.0.0.1,*.onrender.com,*.railway.app,*.vercel.app,*.herokuapp.com'
    allowed_hosts = os.getenv('ALLOWED_HOSTS', default_hosts).split(',')
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

# Static files and templates with absolute paths
import pathlib
base_dir = pathlib.Path(__file__).parent.parent.parent  # Go up to project root
static_dir = base_dir / "src" / "mvp" / "static" 
templates_dir = base_dir / "src" / "mvp" / "templates"

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
templates = Jinja2Templates(directory=str(templates_dir))

# Include all routers
app.include_router(core_router, prefix="/api/mvp", tags=["Core MVP"])
app.include_router(canvas_router, prefix="/api/lms", tags=["Canvas LMS"])
app.include_router(powerschool_router, prefix="/api/sis", tags=["PowerSchool SIS"])
app.include_router(google_classroom_router, prefix="/api/google", tags=["Google Classroom"])
app.include_router(combined_router, prefix="/api/integration", tags=["Combined Integration"])
app.include_router(notifications_router, prefix="/api", tags=["Real-time Notifications"])
app.include_router(health_router, prefix="", tags=["Health & Monitoring"])

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Main web interface"""
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        # Fallback HTML if template fails
        return HTMLResponse(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Student Success Predictor</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; text-align: center; }}
                .container {{ max-width: 800px; margin: 0 auto; }}
                .error {{ background: #f8f9fa; padding: 20px; border-radius: 8px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 Student Success Predictor</h1>
                <div class="error">
                    <h3>System Initializing...</h3>
                    <p>Web interface is loading. Please check:</p>
                    <ul style="text-align: left;">
                        <li><a href="/health">Health Check</a></li>
                        <li><a href="/docs">API Documentation</a></li>
                    </ul>
                    <p><small>Template error: {str(e)}</small></p>
                </div>
            </div>
        </body>
        </html>
        """)

@app.get("/favicon.ico")
async def favicon():
    """Favicon to prevent 404 errors"""
    return Response(content="", media_type="image/x-icon")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "2.0.0", "architecture": "modular"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)