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

    # OULAD dataset URL
    url = "https://analyse.kmi.open.ac.uk/open_dataset/download"

    print("Downloading OULAD dataset...")
    # Implementation details for downloading the dataset
    print("Please visit: https://analyse.kmi.open.ac.uk/open_dataset")
    print("Download the CSV files manually to data/raw/")

if __name__ == "__main__":
    download_oulad()