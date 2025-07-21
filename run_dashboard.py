#!/usr/bin/env python3
"""
Launch the Student Success Prediction Dashboard

This script launches the Streamlit dashboard for teachers to monitor
student progress and get intervention recommendations.
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Launch the dashboard"""
    
    print("🚀 Starting Student Success Prediction Dashboard...")
    print("=" * 60)
    
    # Path to the dashboard script
    dashboard_path = Path("src/dashboard/teacher_dashboard.py")
    
    if not dashboard_path.exists():
        print(f"❌ Dashboard script not found at {dashboard_path}")
        sys.exit(1)
    
    try:
        # Launch Streamlit
        print("📊 Launching Streamlit dashboard...")
        print("🌐 Dashboard will be available at: http://localhost:8010")
        print("⏹️  Press Ctrl+C to stop the dashboard")
        print("=" * 60)
        
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(dashboard_path),
            "--server.port=8010",
            "--server.address=localhost",
            "--server.headless=true",
            "--browser.serverAddress=localhost"
        ])
        
    except KeyboardInterrupt:
        print("\\n\\n⏹️  Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Error launching dashboard: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()