#!/usr/bin/env python3
"""
Simple test server to verify MVP functionality
"""

import sys
from pathlib import Path
sys.path.append('src')

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Create simple FastAPI app
app = FastAPI(title="Student Success MVP Test")

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="src/mvp/static"), name="static")
except Exception as e:
    print(f"Warning: Could not mount static files: {e}")

@app.get("/")
async def root():
    """Serve simple test page"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Student Success MVP Test</title>
    </head>
    <body>
        <h1>🎉 Student Success MVP is Working!</h1>
        <p>The server is running successfully.</p>
        <button onclick="testAPI()">Test API</button>
        <div id="result"></div>
        
        <script>
        async function testAPI() {
            try {
                const response = await fetch('/test');
                const data = await response.json();
                document.getElementById('result').innerHTML = 
                    '<p>✅ API Test: ' + data.message + '</p>';
            } catch (error) {
                document.getElementById('result').innerHTML = 
                    '<p>❌ API Error: ' + error + '</p>';
            }
        }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {"message": "API is working!", "status": "success"}

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "message": "Test server running"}

if __name__ == "__main__":
    print("🚀 Starting simple test server...")
    print("📱 Open: http://localhost:8001")
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")