#!/usr/bin/env python3
"""
Deployment Validation Script
Validates that all components are ready for production deployment
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def check_file_exists(filepath, description="File"):
    """Check if a file exists and return status"""
    exists = Path(filepath).exists()
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {filepath}")
    return exists

def check_environment_setup():
    """Check environment file configuration"""
    print("\n🔧 Environment Configuration Check")
    print("=" * 40)
    
    env_files = [".env.production", ".env.development"]
    for env_file in env_files:
        check_file_exists(env_file, f"Environment template")
        
    # Check if .env exists for production
    if check_file_exists(".env", "Active environment file"):
        with open(".env", "r") as f:
            content = f.read()
            has_db_url = "DATABASE_URL=" in content and "postgresql://" in content
            has_api_key = "MVP_API_KEY=" in content and "dev-key-change-me" not in content
            
            print(f"{'✅' if has_db_url else '❌'} Database URL configured")
            print(f"{'✅' if has_api_key else '⚠️'} API key configured (change default for production)")
    
def check_docker_files():
    """Check Docker configuration files"""
    print("\n🐳 Docker Configuration Check")
    print("=" * 35)
    
    docker_files = [
        ("Dockerfile", "Multi-stage production Dockerfile"),
        ("docker-compose.prod.yml", "Production compose configuration"),
        ("docker-compose.dev.yml", "Development compose configuration"),
        ("deploy.sh", "Automated deployment script"),
        (".dockerignore", "Docker ignore file")
    ]
    
    all_present = True
    for file_path, description in docker_files:
        if not check_file_exists(file_path, description):
            all_present = False
            
    return all_present

def check_application_files():
    """Check core application files"""
    print("\n📁 Application Files Check")
    print("=" * 30)
    
    core_files = [
        ("run_mvp.py", "Application entry point"),
        ("src/mvp/mvp_api.py", "Main API module"),
        ("src/mvp/notifications.py", "Notification system"),
        ("src/mvp/database.py", "Database module"),
        ("requirements.txt", "Python dependencies"),
        ("alembic.ini", "Database migration config"),
        ("alembic/env.py", "Alembic environment")
    ]
    
    all_present = True
    for file_path, description in core_files:
        if not check_file_exists(file_path, description):
            all_present = False
            
    return all_present

def check_model_files():
    """Check machine learning model files"""
    print("\n🤖 Machine Learning Models Check")
    print("=" * 35)
    
    model_dir = Path("results/models")
    if not model_dir.exists():
        print("❌ Models directory not found")
        return False
        
    model_files = list(model_dir.glob("*.pkl"))
    metadata_file = model_dir / "model_metadata.json"
    
    print(f"{'✅' if len(model_files) > 0 else '❌'} Model files found: {len(model_files)}")
    print(f"{'✅' if metadata_file.exists() else '❌'} Model metadata: {metadata_file}")
    
    if metadata_file.exists():
        try:
            with open(metadata_file, "r") as f:
                metadata = json.load(f)
                print(f"   📊 Models available: {', '.join(metadata.keys())}")
        except Exception as e:
            print(f"   ⚠️ Error reading metadata: {e}")
    
    return len(model_files) > 0 and metadata_file.exists()

def check_dependencies():
    """Check Python dependencies"""
    print("\n📦 Dependencies Check")
    print("=" * 22)
    
    if not check_file_exists("requirements.txt", "Requirements file"):
        return False
        
    try:
        # Read requirements
        with open("requirements.txt", "r") as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            
        print(f"✅ Requirements found: {len(requirements)} packages")
        
        # Check critical dependencies
        critical_deps = [
            "fastapi", "uvicorn", "pandas", "scikit-learn", 
            "asyncpg", "alembic", "websockets"
        ]
        
        req_text = "\n".join(requirements).lower()
        for dep in critical_deps:
            found = dep in req_text
            print(f"{'✅' if found else '❌'} {dep}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error checking requirements: {e}")
        return False

def check_database_migration():
    """Check database migration setup"""
    print("\n🗄️ Database Migration Check")
    print("=" * 28)
    
    migration_files = [
        "alembic.ini",
        "alembic/env.py", 
        "alembic/script.py.mako"
    ]
    
    all_present = True
    for file_path in migration_files:
        if not check_file_exists(file_path, f"Migration file"):
            all_present = False
            
    # Check for migration versions
    versions_dir = Path("alembic/versions")
    if versions_dir.exists():
        versions = list(versions_dir.glob("*.py"))
        print(f"✅ Migration versions: {len(versions)}")
    else:
        print("❌ No migration versions directory")
        all_present = False
        
    return all_present

def check_security_setup():
    """Check security configuration"""
    print("\n🔒 Security Configuration Check")
    print("=" * 32)
    
    security_checks = []
    
    # Check for non-root user in Dockerfile
    if Path("Dockerfile").exists():
        with open("Dockerfile", "r") as f:
            dockerfile_content = f.read()
            has_nonroot = "useradd" in dockerfile_content and "USER appuser" in dockerfile_content
            security_checks.append(("Non-root user in Docker", has_nonroot))
    
    # Check for environment variable usage
    if Path(".env.production").exists():
        with open(".env.production", "r") as f:
            env_content = f.read()
            has_secure_key = "your-secure-production-api-key-here" in env_content
            security_checks.append(("Secure API key template", has_secure_key))
    
    # Check for SSL configuration
    if Path("docker-compose.prod.yml").exists():
        with open("docker-compose.prod.yml", "r") as f:
            compose_content = f.read()
            has_ssl = "tls=true" in compose_content
            security_checks.append(("SSL/TLS configuration", has_ssl))
    
    for check_name, passed in security_checks:
        print(f"{'✅' if passed else '❌'} {check_name}")
    
    return all(passed for _, passed in security_checks)

def generate_deployment_report():
    """Generate overall deployment readiness report"""
    print("\n📋 Deployment Readiness Report")
    print("=" * 35)
    
    checks = [
        ("Environment Setup", check_environment_setup),
        ("Docker Configuration", check_docker_files),
        ("Application Files", check_application_files),
        ("ML Models", check_model_files),
        ("Dependencies", check_dependencies),
        ("Database Migrations", check_database_migration),
        ("Security Setup", check_security_setup)
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ Error in {check_name}: {e}")
            results.append((check_name, False))
    
    print("\n📊 Summary")
    print("=" * 12)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {check_name}")
    
    print(f"\n🎯 Overall Score: {passed}/{total} ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("🚀 Ready for production deployment!")
        return True
    else:
        print("⚠️ Some issues need to be resolved before production deployment")
        return False

def show_deployment_commands():
    """Show deployment commands"""
    print("\n🚀 Deployment Commands")
    print("=" * 22)
    print("Development:")
    print("  ./deploy.sh --environment development")
    print("\nProduction:")
    print("  ./deploy.sh --environment production")
    print("\nManual Docker:")
    print("  docker compose -f docker-compose.prod.yml up -d --build")
    print("\nHealth Check:")
    print("  curl http://localhost:8001/health")

if __name__ == "__main__":
    print("🔍 Student Success Prediction - Deployment Validation")
    print("=" * 58)
    
    # Change to project root directory if needed
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)
    
    print(f"📂 Project directory: {os.getcwd()}")
    
    # Run validation
    ready = generate_deployment_report()
    show_deployment_commands()
    
    # Exit with appropriate code
    sys.exit(0 if ready else 1)