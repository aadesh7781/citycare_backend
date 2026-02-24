import os
import uuid
from werkzeug.utils import secure_filename
from PIL import Image
import io

UPLOAD_FOLDER = "uploads/complaints"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_IMAGE_SIZE = (1920, 1920)  # Max width/height

def allowed_file(filename):
    """Check if file extension is allowed"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_image(file):
    """
    Save and compress image file

    Args:
        file: FileStorage object from Flask request

    Returns:
        str: URL path to saved image

    Raises:
        ValueError: If file is invalid or too large
    """
    if not file:
        return None

    if not allowed_file(file.filename):
        raise ValueError(f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")

    # Check file size
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Reset to beginning

    if size > MAX_FILE_SIZE:
        raise ValueError(f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024}MB")

    try:
        # Open image with PIL
        img = Image.open(file)

        # Resize if too large
        img.thumbnail(MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)

        # Convert RGBA/P to RGB for JPEG
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        # Generate unique filename
        ext = file.filename.rsplit(".", 1)[1].lower()
        # Use JPEG for better compression
        if ext in ['jpg', 'jpeg']:
            ext = 'jpg'
        else:
            ext = 'jpg'  # Convert all to JPEG for consistency

        filename = f"{uuid.uuid4()}.{ext}"
        filename = secure_filename(filename)

        # Create upload directory if it doesn't exist
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        # Save with compression
        img.save(file_path, quality=85, optimize=True)

        return f"/{UPLOAD_FOLDER}/{filename}"

    except Exception as e:
        raise ValueError(f"Failed to process image: {str(e)}")


def delete_image(image_url):
    """
    Delete an image file

    Args:
        image_url: URL path to image (e.g., /uploads/complaints/abc.jpg)
    """
    if not image_url:
        return

    try:
        # Remove leading slash and construct file path
        file_path = image_url.lstrip('/')

        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Error deleting image {image_url}: {e}")