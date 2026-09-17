import os
import hashlib
from uuid import UUID
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from pathlib import Path

from app.models import Document, User
from app.core.config import settings

def calculate_file_hash(file_path: str) -> str:
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        buf = f.read(65536)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(65536)
    return hasher.hexdigest()

def save_upload_file(upload_file: UploadFile, user: User) -> Document:
    # Validate extension
    allowed_extensions = {".pdf", ".jpg", ".jpeg", ".png"}
    ext = Path(upload_file.filename).suffix.lower()
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="INVALID_FILE_TYPE")
    
    # Validate size (simple check by reading bytes or depending on framework)
    file_bytes = upload_file.file.read()
    if len(file_bytes) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail="FILE_TOO_LARGE")

    # Generate safe filename
    import uuid
    safe_filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(settings.STORAGE_PATH, safe_filename)

    os.makedirs(settings.STORAGE_PATH, exist_ok=True)

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    file_hash = calculate_file_hash(file_path)

    # Determine mime type
    mime_type = "application/pdf"
    if ext in [".jpg", ".jpeg"]:
        mime_type = "image/jpeg"
    elif ext == ".png":
        mime_type = "image/png"

    # Create document record
    doc = Document(
        company_id=user.company_id,
        file_name=upload_file.filename,
        file_path=file_path,
        file_type=mime_type,
        file_size=len(file_bytes),
        status="UPLOADED",
        file_hash=file_hash,
        uploaded_by=user.id
    )

    return doc
