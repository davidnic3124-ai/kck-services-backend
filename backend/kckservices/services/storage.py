import uuid
from fastapi import UploadFile, HTTPException
from kckservices.clients import supabase_admin
from kckservices.config import settings

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024

async def upload_car_image(file: UploadFile, car_id: str) -> str:
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Only JPG, PNG, and WebP images are supported.")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Image exceeds the 5 MB limit.")

    ext = file.filename.split(".")[-1].lower() if file.filename and "." in file.filename else "jpg"
    unique_path = f"cars/{car_id}/{uuid.uuid4().hex}.{ext}"

    try:
        supabase_admin.storage.from_(settings.storage_bucket).upload(
            path=unique_path,
            file=content,
            file_options={"content-type": file.content_type}
        )
        return supabase_admin.storage.from_(settings.storage_bucket).get_public_url(unique_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload image to storage: {str(e)}")
