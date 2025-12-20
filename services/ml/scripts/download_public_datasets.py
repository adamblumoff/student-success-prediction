#!/usr/bin/env python3
"""
Download public datasets used by the ML pipeline (OULAD + UCI Student Performance).
"""

import argparse
from pathlib import Path
import sys
import urllib.request


DEFAULT_OULAD_URL = "https://analyse.kmi.open.ac.uk/open-dataset/download"
DEFAULT_UCI_URL = "https://cdn.uci-ics-mlr-prod.aws.uci.edu/320/student%2Bperformance.zip"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download public datasets.")
    parser.add_argument(
        "--dest-dir",
        default="data",
        help="Directory to save downloads (default: data).",
    )
    parser.add_argument(
        "--oulad-url",
        default=DEFAULT_OULAD_URL,
        help="OULAD download URL.",
    )
    parser.add_argument(
        "--uci-url",
        default=DEFAULT_UCI_URL,
        help="UCI Student Performance download URL.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download files even if they already exist.",
    )
    return parser.parse_args()


def download(url: str, dest_path: Path, force: bool) -> None:
    if dest_path.exists() and not force:
        print(f"Skip (exists): {dest_path}")
        return
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {url} -> {dest_path}")
    urllib.request.urlretrieve(url, dest_path)


def main() -> int:
    args = parse_args()
    dest_dir = Path(args.dest_dir)

    oulad_path = dest_dir / "oulad.zip"
    uci_path = dest_dir / "student-performance.zip"

    try:
        download(args.oulad_url, oulad_path, args.force)
        download(args.uci_url, uci_path, args.force)
    except Exception as exc:
        print(f"Download failed: {exc}")
        return 1

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
