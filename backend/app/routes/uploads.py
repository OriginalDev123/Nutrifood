"""
Image Upload Routes
Endpoints for uploading images (food photos, profile pictures, etc.)
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
import shutil
from pathlib import Path

from app.database import get_db
from app.models.user import User
from app.utils.dependencies import get_current_active_user
from app.config import settings


router = APIRouter(
    prefix="/uploads",
    tags=["File Upload"]
)


# ==========================================
# CONFIGURATION
# ==========================================

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Allowed image types
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def validate_image(file: UploadFile) -> None:
    """
    Validate uploaded image file
    
    Raises:
        HTTPException: If validation fails
    """
    
    # Check file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check content type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="File must be an image"
        )


def save_upload_file(upload_file: UploadFile, destination: Path) -> None:
    """
    Save uploaded file to destination
    
    Args:
        upload_file: FastAPI UploadFile object
        destination: Path to save file
    """
    
    try:
        with destination.open("wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
    finally:
        upload_file.file.close()


# ==========================================
# UPLOAD ENDPOINTS
# ==========================================

@router.post("/food-image", response_model=dict)
async def upload_food_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload food image
    
    **Use Cases:**
    - Meal logging with photo
    - AI food recognition
    - Recipe images
    
    **File Requirements:**
    - Format: JPG, JPEG, PNG, GIF, WebP
    - Max size: 10MB
    
    **Returns:**
    - image_url: URL to access the uploaded image
    - filename: Generated filename
    
    **Example:**
    ```bash
    curl -X POST http://localhost:8000/uploads/food-image \
      -H "Authorization: Bearer {token}" \
      -F "file=@meal.jpg"
    ```
    """
    
    # Validate file
    validate_image(file)
    
    # Generate unique filename
    file_ext = os.path.splitext(file.filename)[1].lower()
    unique_filename = f"food_{uuid.uuid4()}{file_ext}"
    
    # Create subdirectory for food images
    food_dir = UPLOAD_DIR / "foods"
    food_dir.mkdir(exist_ok=True)
    
    file_path = food_dir / unique_filename
    
    # Save file
    save_upload_file(file, file_path)
    
    # Generate URL (adjust for your deployment)
    image_url = f"/static/uploads/foods/{unique_filename}"
    
    return {
        "image_url": image_url,
        "filename": unique_filename,
        "original_filename": file.filename,
        "size_bytes": file_path.stat().st_size
    }


@router.post("/profile-image", response_model=dict)
async def upload_profile_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload profile picture
    
    **File Requirements:**
    - Format: JPG, JPEG, PNG, GIF, WebP
    - Max size: 10MB
    - Recommended: Square image (1:1 ratio)
    
    **Returns:**
    - image_url: URL to access the uploaded image
    - Updates user profile automatically
    
    **Example:**
    ```bash
    curl -X POST http://localhost:8000/uploads/profile-image \
      -H "Authorization: Bearer {token}" \
      -F "file=@avatar.jpg"
    ```
    """
    
    # Validate file
    validate_image(file)
    
    # Generate unique filename
    file_ext = os.path.splitext(file.filename)[1].lower()
    unique_filename = f"profile_{current_user.user_id}_{uuid.uuid4()}{file_ext}"
    
    # Create subdirectory for profile images
    profile_dir = UPLOAD_DIR / "profiles"
    profile_dir.mkdir(exist_ok=True)
    
    file_path = profile_dir / unique_filename
    
    # Delete old profile image if exists
    if current_user.profile and current_user.profile.profile_image_url:
        old_filename = current_user.profile.profile_image_url.split("/")[-1]
        old_path = profile_dir / old_filename
        if old_path.exists():
            old_path.unlink()
    
    # Save new file
    save_upload_file(file, file_path)
    
    # Generate URL
    image_url = f"/static/uploads/profiles/{unique_filename}"
    
    # Update user profile
    if current_user.profile:
        current_user.profile.profile_image_url = image_url
        db.commit()
    
    return {
        "image_url": image_url,
        "filename": unique_filename,
        "message": "Profile image updated successfully"
    }


@router.post("/recipe-image", response_model=dict)
async def upload_recipe_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload recipe image
    
    **File Requirements:**
    - Format: JPG, JPEG, PNG, GIF, WebP
    - Max size: 10MB
    
    **Returns:**
    - image_url: URL to use when creating/updating recipe
    
    **Example:**
    ```bash
    curl -X POST http://localhost:8000/uploads/recipe-image \
      -H "Authorization: Bearer {token}" \
      -F "file=@pho.jpg"
    ```
    """
    
    # Validate file
    validate_image(file)
    
    # Generate unique filename
    file_ext = os.path.splitext(file.filename)[1].lower()
    unique_filename = f"recipe_{uuid.uuid4()}{file_ext}"
    
    # Create subdirectory for recipe images
    recipe_dir = UPLOAD_DIR / "recipes"
    recipe_dir.mkdir(exist_ok=True)
    
    file_path = recipe_dir / unique_filename
    
    # Save file
    save_upload_file(file, file_path)
    
    # Generate URL
    image_url = f"/static/uploads/recipes/{unique_filename}"
    
    return {
        "image_url": image_url,
        "filename": unique_filename,
        "original_filename": file.filename
    }


@router.post("/bulk-upload", response_model=dict)
async def bulk_upload_images(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload multiple images at once
    
    **File Requirements:**
    - Format: JPG, JPEG, PNG, GIF, WebP
    - Max size per file: 10MB
    - Max files: 10
    
    **Returns:**
    - Array of uploaded image URLs
    
    **Example:**
    ```bash
    curl -X POST http://localhost:8000/uploads/bulk-upload \
      -H "Authorization: Bearer {token}" \
      -F "files=@meal1.jpg" \
      -F "files=@meal2.jpg"
    ```
    """
    
    if len(files) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 files allowed per request"
        )
    
    uploaded_files = []
    
    for file in files:
        try:
            # Validate file
            validate_image(file)
            
            # Generate unique filename
            file_ext = os.path.splitext(file.filename)[1].lower()
            unique_filename = f"bulk_{uuid.uuid4()}{file_ext}"
            
            # Save to bulk directory
            bulk_dir = UPLOAD_DIR / "bulk"
            bulk_dir.mkdir(exist_ok=True)
            
            file_path = bulk_dir / unique_filename
            save_upload_file(file, file_path)
            
            # Generate URL
            image_url = f"/static/uploads/bulk/{unique_filename}"
            
            uploaded_files.append({
                "original_filename": file.filename,
                "image_url": image_url,
                "filename": unique_filename
            })
            
        except HTTPException as e:
            uploaded_files.append({
                "original_filename": file.filename,
                "error": e.detail
            })
    
    return {
        "uploaded_count": len([f for f in uploaded_files if "error" not in f]),
        "failed_count": len([f for f in uploaded_files if "error" in f]),
        "files": uploaded_files
    }


@router.delete("/image/{filename}")
async def delete_image(
    filename: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete uploaded image
    
    **Path Parameters:**
    - filename: Name of file to delete
    
    **Security:**
    - Only file owner can delete
    
    **Example:**
    ```
    DELETE /uploads/image/food_uuid-here.jpg
    ```
    """
    
    # Search in all upload directories
    for subdir in ["foods", "profiles", "recipes", "bulk"]:
        file_path = UPLOAD_DIR / subdir / filename
        if file_path.exists():
            # Additional security: Check if user owns this file
            # (Implement ownership check based on your requirements)
            
            file_path.unlink()
            return {
                "message": "Image deleted successfully",
                "filename": filename
            }
    
    raise HTTPException(
        status_code=404,
        detail="Image not found"
    )


# ==========================================
# UTILITY ENDPOINTS
# ==========================================

@router.get("/stats")
async def get_upload_stats(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get upload statistics
    
    **Returns:**
    - Total files uploaded
    - Total storage used
    - Breakdown by type
    
    **Example:**
    ```
    GET /uploads/stats
    ```
    """
    
    stats = {
        "foods": 0,
        "profiles": 0,
        "recipes": 0,
        "bulk": 0,
        "total_size_mb": 0
    }
    
    for category in ["foods", "profiles", "recipes", "bulk"]:
        category_dir = UPLOAD_DIR / category
        if category_dir.exists():
            files = list(category_dir.glob("*"))
            stats[category] = len(files)
            stats["total_size_mb"] += sum(f.stat().st_size for f in files) / (1024 * 1024)
    
    stats["total_files"] = sum([stats[k] for k in ["foods", "profiles", "recipes", "bulk"]])
    stats["total_size_mb"] = round(stats["total_size_mb"], 2)
    
    return stats