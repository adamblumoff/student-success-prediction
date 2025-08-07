# 🏠 Local Development Guide

Simple guide for local development of the Student Success Prediction System.

## 🚀 Quick Start

### Start the Server
```bash
# Simple one-command startup
python3 start_local.py

# Or traditional method
python3 run_mvp.py
```

### Access the Application
- **Web Interface**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs
- **Sample Data**: Click "Load Sample Data" on the web interface

## 📊 Database

### PostgreSQL (Default - Learning PostgreSQL)
- **Database**: `student_success_local` (local PostgreSQL)
- **Connection**: `postgresql:///student_success_local`
- **Setup**: Already configured in start_local.py
- **View data**: `psql student_success_local` then `\dt` and `SELECT * FROM predictions;`
- **Row counts**: `SELECT COUNT(*) FROM predictions;`

### Create Tables (First Time Only)
```bash
# Create database tables using Alembic migrations
alembic upgrade head
```

## 🧪 Testing

### Test the API
```bash
# Load sample data
curl http://localhost:8001/api/mvp/sample

# Upload CSV
curl -X POST -F "file=@test.csv" http://localhost:8001/api/mvp/analyze
```

### Run Tests
```bash
python3 scripts/run_tests.py
```

## 🔧 Configuration

### Environment Variables
- `DEVELOPMENT_MODE=true` (automatically set)
- `MVP_API_KEY=local-dev-key` (automatically set)
- `DATABASE_URL` (optional, defaults to SQLite)

### Files
- `student_success_local` - PostgreSQL database
- `.env` - Environment variables (optional)

## 📁 Key Directories

```
src/
├── mvp/           # Main application
│   ├── api/       # API endpoints
│   ├── templates/ # Web interface
│   └── static/    # CSS/JS files
├── models/        # ML models
└── integrations/  # LMS/SIS integrations

results/models/    # Trained ML models
tests/             # Test files
```

## 🛠️ Development Workflow

1. **Make changes** to code files
2. **Restart server** (Ctrl+C then `python3 start_local.py`)
3. **Test changes** at http://localhost:8001
4. **Debug with print statements** (they show in terminal)
5. **Commit when working**: `git add . && git commit -m "Your changes"`

## 💡 Tips

- **Database**: Uses PostgreSQL for learning database skills
- **Debugging**: Add `print()` statements - they show immediately in terminal
- **Hot Reload**: Server doesn't auto-reload, restart manually after changes
- **API Testing**: Use the web interface or curl commands
- **Database**: All data stays in local PostgreSQL (student_success_local)

## 🔍 Troubleshooting

### Server Won't Start
```bash
# Check if port is in use
lsof -i :8001
pkill -f python  # Kill any running Python processes
```

### Database Issues
```bash
# View PostgreSQL database
psql student_success_local

# Reset database (if needed)
psql -c "DROP DATABASE IF EXISTS student_success_local;"
psql -c "CREATE DATABASE student_success_local;"
alembic upgrade head  # Recreate tables
```

### Import Errors
```bash
# Make sure you're in the project directory
cd /path/to/student-success-prediction
python3 start_local.py
```

---

**That's it!** Everything else is just for local development and testing. 🎉