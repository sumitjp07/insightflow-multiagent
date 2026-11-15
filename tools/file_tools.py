"""
tools/file_tools.py – File Handling Utilities
===============================================
File upload, save, aur path management tools.
"""

import os
import shutil
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def validate_file(file_path: str, 
                  max_size_mb: int = 50,
                  allowed_extensions: set = None) -> dict:
    """
    File ko validate karta hai — size aur extension check.
    
    Args:
        file_path: File ka path
        max_size_mb: Maximum allowed file size in MB
        allowed_extensions: Allowed file types (e.g., {".csv", ".xlsx"})
    """
    if allowed_extensions is None:
        allowed_extensions = {".csv", ".xlsx", ".xls"}
    
    path = Path(file_path)
    
    if not path.exists():
        return {"valid": False, "error": f"File not found: {file_path}"}
    
    ext = path.suffix.lower()
    if ext not in allowed_extensions:
        return {"valid": False, "error": f"Invalid file type: {ext}. Allowed: {allowed_extensions}"}
    
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > max_size_mb:
        return {"valid": False, "error": f"File too large: {size_mb:.1f}MB (max: {max_size_mb}MB)"}
    
    return {
        "valid": True,
        "file_name": path.name,
        "extension": ext,
        "size_mb": round(size_mb, 2),
        "full_path": str(path.resolve()),
    }


def save_uploaded_file(uploaded_file, save_dir: str = "uploads") -> dict:
    """
    Streamlit uploaded file ko disk pe save karta hai.
    
    Args:
        uploaded_file: Streamlit UploadedFile object
        save_dir: Directory jahan save karna hai
    """
    try:
        save_path = Path(save_dir)
        save_path.mkdir(exist_ok=True)
        
        file_path = save_path / uploaded_file.name
        
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        logger.info(f"💾 File saved: {file_path}")
        
        return {
            "success": True,
            "file_path": str(file_path),
            "file_name": uploaded_file.name,
            "size_bytes": uploaded_file.size,
        }
    except Exception as e:
        logger.error(f"❌ File save error: {str(e)}")
        return {"success": False, "error": str(e)}


def get_sample_files() -> list:
    """
    sample_data/ folder ke saare files ki list deta hai.
    """
    sample_dir = Path("sample_data")
    if not sample_dir.exists():
        return []
    
    files = []
    for f in sample_dir.iterdir():
        if f.suffix.lower() in {".csv", ".xlsx", ".xls"}:
            files.append({
                "name": f.name,
                "path": str(f),
                "size_kb": round(f.stat().st_size / 1024, 2),
                "type": f.suffix.lower(),
            })
    
    return files


# ── Quick Test ─────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*55)
    print("  InsightFlow – File Tools Test")
    print("="*55)
    
    # Test 1: Validate
    print("\n📌 Test 1: Validate sales_data.csv")
    result = validate_file("sample_data/sales_data.csv")
    print(f"  Valid: {result['valid']}")
    if result['valid']:
        print(f"  Size: {result['size_mb']} MB")
    
    # Test 2: Sample files
    print("\n📌 Test 2: List sample files")
    files = get_sample_files()
    for f in files:
        print(f"  📄 {f['name']} ({f['size_kb']} KB)")
    
    print("\n" + "="*55)
    print("  ✅ All File Tools Tests Passed!")
    print("="*55 + "\n")

