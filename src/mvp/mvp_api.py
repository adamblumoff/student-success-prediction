"""
Modular MVP API - Entry point that combines all specialized routers
"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import all modular routers
from src.mvp.api.core import router as core_router
from src.mvp.api.canvas_endpoints import router as canvas_router
from src.mvp.api.powerschool_endpoints import router as powerschool_router
from src.mvp.api.combined_endpoints import router as combined_router

# Create FastAPI app
app = FastAPI(
    title="Student Success Prediction MVP",
    description="Modular API for student success prediction with Canvas LMS and PowerSchool SIS integration",
    version="2.0.0"
)

# Static files and templates
app.mount("/static", StaticFiles(directory="src/mvp/static"), name="static")
templates = Jinja2Templates(directory="src/mvp/templates")

# Include all routers
app.include_router(core_router, prefix="/api/mvp", tags=["Core MVP"])
app.include_router(canvas_router, prefix="/api/lms", tags=["Canvas LMS"])
app.include_router(powerschool_router, prefix="/api/sis", tags=["PowerSchool SIS"])
app.include_router(combined_router, prefix="/api/integration", tags=["Combined Integration"])

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Main web interface"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "2.0.0", "architecture": "modular"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)