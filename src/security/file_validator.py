#!/usr/bin/env python3
"""
Secure file validation and processing utilities
"""

try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    import warnings
    warnings.warn("python-magic not installed. MIME type detection will use filename only.")

import hashlib
import csv
import io
from typing import Optional, List, Dict, Any
import pandas as pd
from fastapi import HTTPException
import re
import logging

logger = logging.getLogger(__name__)

class SecureFileValidator:
    """Secure file validation and processing"""
    
    # Maximum file size (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    # Allowed MIME types
    ALLOWED_MIME_TYPES = {
        'text/csv',
        'application/csv',
        'text/plain'
    }
    
    # CSV injection patterns to detect
    CSV_INJECTION_PATTERNS = [
        r'^=',  # Formula starting with =
        r'^\+',  # Formula starting with +
        r'^-',   # Formula starting with -
        r'^@',   # Formula starting with @
        r'^\s*=', # Formula with leading whitespace
        r'cmd\|',  # Command injection
        r'powershell',  # PowerShell injection
        r'<script',  # XSS in CSV
        r'javascript:',  # JavaScript execution
    ]
    
    def __init__(self):
        self.injection_regex = re.compile('|'.join(self.CSV_INJECTION_PATTERNS), re.IGNORECASE)
    
    def validate_file_size(self, content: bytes) -> None:
        """Validate file size"""
        if len(content) > self.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size allowed: {self.MAX_FILE_SIZE / (1024*1024):.1f}MB"
            )
    
    def validate_mime_type(self, content: bytes, filename: str) -> None:
        """Validate MIME type using python-magic"""
        if MAGIC_AVAILABLE:
            try:
                mime_type = magic.from_buffer(content, mime=True)
                if mime_type not in self.ALLOWED_MIME_TYPES:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid file type. Expected CSV file, got: {mime_type}"
                    )
                return
            except Exception as e:
                logger.warning(f"MIME type detection failed for {filename}: {e}")
        
        # Fallback to extension validation if magic not available or fails
        if not filename.lower().endswith('.csv'):
            raise HTTPException(
                status_code=400,
                detail="Invalid file extension. Only CSV files are allowed."
            )
        
        # Basic content validation for CSV
        try:
            content_str = content.decode('utf-8')[:1000]  # Check first 1KB
            if not any(char in content_str for char in ',;\t'):  # Look for common delimiters
                raise HTTPException(
                    status_code=400,
                    detail="File does not appear to be a valid CSV format."
                )
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=400,
                detail="File encoding not supported. Please use UTF-8."
            )
    
    def validate_filename(self, filename: str) -> str:
        """Validate and sanitize filename"""
        if not filename:
            raise HTTPException(status_code=400, detail="Filename cannot be empty")
        
        # Remove path traversal attempts
        sanitized = filename.replace('..', '').replace('/', '').replace('\\', '')
        
        # Only allow alphanumeric, dots, hyphens, underscores
        sanitized = re.sub(r'[^a-zA-Z0-9.\-_]', '_', sanitized)
        
        # Ensure it's a CSV file
        if not sanitized.lower().endswith('.csv'):
            sanitized += '.csv'
        
        return sanitized[:100]  # Limit length
    
    def detect_csv_injection(self, content: str) -> List[str]:
        """Detect potential CSV injection attempts"""
        threats = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines[:100], 1):  # Check first 100 lines
            cells = next(csv.reader([line]), [])
            for cell_num, cell in enumerate(cells):
                if self.injection_regex.search(str(cell)):
                    threats.append(f"Line {line_num}, Cell {cell_num + 1}: Potential injection pattern")
        
        return threats
    
    def sanitize_csv_content(self, content: str) -> str:
        """Sanitize CSV content to prevent injection"""
        lines = []
        csv_reader = csv.reader(io.StringIO(content))
        
        for row in csv_reader:
            sanitized_row = []
            for cell in row:
                cell_str = str(cell).strip()
                
                # Escape cells that start with formula characters
                if cell_str and cell_str[0] in '=+-@':
                    cell_str = "'" + cell_str  # Prefix with single quote to escape
                
                # Remove or escape potentially dangerous content
                cell_str = re.sub(r'cmd\|.*', '[REMOVED]', cell_str, flags=re.IGNORECASE)
                cell_str = re.sub(r'powershell.*', '[REMOVED]', cell_str, flags=re.IGNORECASE)
                cell_str = re.sub(r'<script.*?</script>', '[REMOVED]', cell_str, flags=re.IGNORECASE)
                cell_str = re.sub(r'javascript:.*', '[REMOVED]', cell_str, flags=re.IGNORECASE)
                
                sanitized_row.append(cell_str)
            
            lines.append(sanitized_row)
        
        # Convert back to CSV string
        output = io.StringIO()
        csv_writer = csv.writer(output)
        csv_writer.writerows(lines)
        return output.getvalue()
    
    def calculate_file_hash(self, content: bytes) -> str:
        """Calculate SHA-256 hash of file content"""
        return hashlib.sha256(content).hexdigest()
    
    def validate_csv_structure(self, df: pd.DataFrame) -> None:
        """Validate CSV structure and content"""
        # Check if DataFrame is not empty
        if df.empty:
            raise HTTPException(status_code=400, detail="CSV file is empty")
        
        # Check maximum number of rows (prevent DoS)
        if len(df) > 10000:
            raise HTTPException(
                status_code=400,
                detail="CSV file has too many rows. Maximum allowed: 10,000"
            )
        
        # Check maximum number of columns
        if len(df.columns) > 100:
            raise HTTPException(
                status_code=400,
                detail="CSV file has too many columns. Maximum allowed: 100"
            )
        
        # Check for suspiciously large cells
        for col in df.columns:
            if df[col].astype(str).str.len().max() > 1000:
                raise HTTPException(
                    status_code=400,
                    detail=f"Column '{col}' contains cells that are too large"
                )
    
    def secure_process_upload(self, content: bytes, filename: str) -> pd.DataFrame:
        """Securely process uploaded file"""
        try:
            # Validate file size
            self.validate_file_size(content)
            
            # Validate filename
            safe_filename = self.validate_filename(filename)
            
            # Validate MIME type
            self.validate_mime_type(content, safe_filename)
            
            # Calculate file hash for logging
            file_hash = self.calculate_file_hash(content)
            
            # Decode content
            try:
                content_str = content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    content_str = content.decode('latin-1')
                except UnicodeDecodeError:
                    raise HTTPException(
                        status_code=400,
                        detail="File encoding not supported. Please use UTF-8 or Latin-1."
                    )
            
            # Detect CSV injection attempts
            injection_threats = self.detect_csv_injection(content_str)
            if injection_threats:
                logger.warning(f"CSV injection detected in {safe_filename}: {injection_threats}")
                # Sanitize content instead of rejecting
                content_str = self.sanitize_csv_content(content_str)
            
            # Parse CSV safely
            try:
                df = pd.read_csv(io.StringIO(content_str))
            except pd.errors.EmptyDataError:
                raise HTTPException(status_code=400, detail="The uploaded file is empty")
            except pd.errors.ParserError as e:
                raise HTTPException(status_code=400, detail=f"Invalid CSV format: {str(e)}")
            
            # Validate CSV structure
            self.validate_csv_structure(df)
            
            # Log successful processing (without sensitive data)
            logger.info(f"Secure file upload processed: filename={safe_filename}, "
                       f"hash={file_hash[:8]}..., rows={len(df)}, cols={len(df.columns)}")
            
            return df
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in secure file processing: {e}")
            raise HTTPException(
                status_code=500,
                detail="An error occurred while processing the file"
            )

# Global instance
secure_validator = SecureFileValidator()