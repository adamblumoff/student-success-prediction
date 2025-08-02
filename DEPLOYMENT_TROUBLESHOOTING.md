# 🔧 Deployment Troubleshooting Guide

## 🚨 Common Issues & Solutions

### **Issue 1: Build Fails - Dependencies Missing**
```bash
# Error: "Could not find a version that satisfies the requirement..."
# Solution: Use compatible Python version
```
**Fix:**
- Use Python 3.8-3.11 (avoid 3.12+ for compatibility)
- Update `runtime.txt` to: `python-3.11.9`

### **Issue 2: Import Errors**
```bash
# Error: "ModuleNotFoundError: No module named 'mvp'"
# Solution: Use app.py instead of run_mvp.py
```
**Fix:**
- Use `python app.py` as start command
- Ensure Procfile contains: `web: python app.py`

### **Issue 3: Environment Variables Not Set**
```bash
# Error: "Security validation failed"
# Solution: Set required environment variables
```
**Fix - Render.com:**
```
MVP_API_KEY = 0dUHi4QroC1GfgnbibLbqowUnv2YFWIe
ENVIRONMENT = production
DEVELOPMENT_MODE = false
PORT = 10000
```

### **Issue 4: Port Binding Problems**
```bash
# Error: "Address already in use"
# Solution: Use correct port from environment
```
**Fix:**
- Render uses PORT=10000
- Railway uses dynamic PORT
- Check platform documentation

### **Issue 5: Model Files Missing**
```bash
# Error: "Model file not found"
# Solution: Models are included in repository
```
**Fix:**
- Models are in `results/models/` directory
- Check `.gitignore` doesn't exclude them
- Models should load automatically

---

## ✅ **Platform-Specific Deployment**

### **Render.com (Recommended)**
```yaml
# render.yaml (optional)
services:
  - type: web
    name: student-success-prediction
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python app.py
    envVars:
      - key: MVP_API_KEY
        value: 0dUHi4QroC1GfgnbibLbqowUnv2YFWIe
      - key: ENVIRONMENT
        value: production
      - key: DEVELOPMENT_MODE
        value: false
```

**Manual Setup:**
1. New Web Service → GitHub repo
2. Build Command: `pip install -r requirements.txt`
3. Start Command: `python app.py`
4. Add environment variables above

### **Railway.app**
```bash
# Works with Procfile automatically
# Just add environment variables in dashboard
```

### **Vercel (Serverless)**
```json
// vercel.json
{
  "builds": [
    {
      "src": "app.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "app.py"
    }
  ]
}
```

### **Google Cloud Run**
```dockerfile
# Dockerfile (if needed)
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

---

## 🧪 **Testing Deployment Locally**

### **Test 1: Basic Startup**
```bash
python app.py
# Should show: "✅ Student Success Prediction System started successfully"
```

### **Test 2: Health Check**
```bash
curl http://localhost:8001/health
# Should return: {"status":"healthy","version":"2.0.0"}
```

### **Test 3: API Documentation**
```bash
# Visit: http://localhost:8001/docs
# Should show FastAPI interactive documentation
```

### **Test 4: CSV Upload**
```bash
# Create test CSV
echo "student_id,score" > test.csv
echo "1001,85" >> test.csv

# Test upload (requires API key)
curl -X POST http://localhost:8001/api/mvp/analyze \
  -H "Authorization: Bearer 0dUHi4QroC1GfgnbibLbqowUnv2YFWIe" \
  -F "file=@test.csv"
```

---

## 🔍 **Debug Information**

### **Check System Status**
```python
# Run this to debug deployment issues
python3 -c "
import sys, os
print(f'Python: {sys.version}')
print(f'Working Dir: {os.getcwd()}')
print(f'Python Path: {sys.path[:3]}')

# Test imports
try:
    import fastapi, uvicorn, pandas
    print('✅ Core dependencies available')
except ImportError as e:
    print(f'❌ Missing dependency: {e}')

# Test app import
sys.path.insert(0, 'src')
try:
    from mvp.mvp_api import app
    print('✅ App imports successfully')
except Exception as e:
    print(f'❌ App import failed: {e}')
"
```

### **Environment Variables Check**
```bash
# Check if environment variables are set
echo "MVP_API_KEY: ${MVP_API_KEY:0:8}***"
echo "ENVIRONMENT: $ENVIRONMENT"
echo "DEVELOPMENT_MODE: $DEVELOPMENT_MODE"
echo "PORT: $PORT"
```

---

## 🆘 **Still Not Working?**

### **Quick Fixes to Try:**

1. **Use app.py instead of run_mvp.py**
   ```bash
   # In Procfile or start command
   python app.py
   ```

2. **Set Python version**
   ```bash
   # In runtime.txt
   python-3.11.9
   ```

3. **Check file structure**
   ```
   ✅ app.py (in root)
   ✅ requirements.txt (in root)
   ✅ src/mvp/mvp_api.py (API code)
   ✅ results/models/*.pkl (ML models)
   ```

4. **Verify environment variables**
   ```bash
   MVP_API_KEY=0dUHi4QroC1GfgnbibLbqowUnv2YFWIe
   ENVIRONMENT=production
   DEVELOPMENT_MODE=false
   ```

### **Platform Support:**
- ✅ **Render.com** - Fully supported
- ✅ **Railway.app** - Fully supported  
- ✅ **Google Cloud Run** - Supported with Docker
- ⚠️ **Vercel** - Serverless (may need modifications)
- ⚠️ **Heroku** - Free tier discontinued

---

## 🎯 **Expected Behavior**

When deployment succeeds, you should see:
1. **Build logs** showing dependency installation
2. **Startup logs** with "✅ Student Success Prediction System started successfully"
3. **Health endpoint** responding at `/health`
4. **Web interface** accessible at your deployment URL
5. **API docs** at `/docs`

**Your app is working when:**
- Health check returns `{"status":"healthy"}`
- Web interface loads without errors
- CSV upload and analysis works
- Predictions are generated correctly