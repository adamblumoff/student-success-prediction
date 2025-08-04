#!/usr/bin/env python3
"""
Temporary debugging script to diagnose model loading issues in production.
Run this to see what's actually happening with paths and files.
"""

import os
import sys
from pathlib import Path

print("🔍 PRODUCTION MODEL DEBUGGING")
print("=" * 50)

# Check environment variables
print(f"🌍 MODELS_DIR env var: {os.getenv('MODELS_DIR', 'NOT SET')}")
print(f"🌍 K12_MODELS_DIR env var: {os.getenv('K12_MODELS_DIR', 'NOT SET')}")

# Check current working directory
print(f"📁 Current working directory: {os.getcwd()}")

# Check if we're in the expected production paths
production_paths = [
    "/opt/render/project/results/models",
    "/opt/render/project/src/results/models", 
    "/opt/render/project",
    str(Path(os.getcwd()) / "results" / "models"),
    str(Path(os.getcwd()) / "src" / "results" / "models"),
]

print("\n🔍 CHECKING PRODUCTION PATHS:")
for path in production_paths:
    path_obj = Path(path)
    exists = path_obj.exists()
    print(f"📂 {path}: {'✅ EXISTS' if exists else '❌ MISSING'}")
    if exists and path_obj.is_dir():
        try:
            files = list(path_obj.glob("*.pkl"))[:5]  # First 5 pkl files
            print(f"   🗂️  PKL files: {[f.name for f in files]}")
        except Exception as e:
            print(f"   ❌ Error listing files: {e}")

# Check the specific model file that's failing
problem_file = "/opt/render/project/results/models/best_binary_model.pkl"
print(f"\n🎯 SPECIFIC FILE CHECK:")
print(f"📄 {problem_file}: {'✅ EXISTS' if Path(problem_file).exists() else '❌ MISSING'}")

# Try to find the file anywhere in the project
print(f"\n🕵️ SEARCHING FOR best_binary_model.pkl:")
try:
    import subprocess
    result = subprocess.run(['find', '/opt/render/project', '-name', 'best_binary_model.pkl'], 
                          capture_output=True, text=True, timeout=10)
    if result.stdout.strip():
        print(f"📍 Found at: {result.stdout.strip()}")
    else:
        print("❌ File not found anywhere in project")
except Exception as e:
    print(f"❌ Search failed: {e}")

# Show what's actually in the directories
key_dirs = ["/opt/render/project", "/opt/render/project/results"]
for dir_path in key_dirs:
    if Path(dir_path).exists():
        print(f"\n📋 CONTENTS OF {dir_path}:")
        try:
            for item in Path(dir_path).iterdir():
                item_type = "📁" if item.is_dir() else "📄"
                print(f"  {item_type} {item.name}")
        except Exception as e:
            print(f"  ❌ Error listing: {e}")

print("\n" + "=" * 50)
print("🔚 Debug complete - check output above for issues")