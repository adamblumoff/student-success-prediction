#!/usr/bin/env python3
"""
Download Open University Learning Analytics Dataset (OULAD)
"""
import os
import requests
import zipfile
from pathlib import Path

def download_oulad():
    """Download and extract OULAD dataset"""
    data_dir = Path("data/raw")
    data_dir.mkdir(exist_ok=True)

    print("OULAD Dataset Download Instructions:")
    print("=" * 50)
    print("1. Visit: https://analyse.kmi.open.ac.uk/open_dataset")
    print("2. Download the following CSV files to data/raw/:")
    print("   - studentInfo.csv")
    print("   - courses.csv") 
    print("   - assessments.csv")
    print("   - studentAssessment.csv")
    print("   - vle.csv")
    print("   - studentVle.csv")
    print("   - studentRegistration.csv")
    print("\n3. After downloading, run the data exploration notebook:")
    print("   jupyter notebook notebooks/01_data_exploration.ipynb")
    print("\nNote: The dataset is approximately 200MB total")
    
    # Check if files already exist
    expected_files = [
        "studentInfo.csv", "courses.csv", "assessments.csv",
        "studentAssessment.csv", "vle.csv", "studentVle.csv", 
        "studentRegistration.csv"
    ]
    
    existing_files = []
    for file in expected_files:
        if (data_dir / file).exists():
            existing_files.append(file)
    
    if existing_files:
        print(f"\nFound existing files: {', '.join(existing_files)}")
    else:
        print("\nNo dataset files found in data/raw/")
    
    return len(existing_files) == len(expected_files)

if __name__ == "__main__":
    download_oulad()