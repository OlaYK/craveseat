import cloudinary
import cloudinary.uploader
import cloudinary.api 
from cloudinary.utils import cloudinary_url
from fastapi import UploadFile
from dotenv import load_dotenv
import os   
import asyncio
import io
from concurrent.futures import ThreadPoolExecutor

load_dotenv()  # take environment variables from .env file       
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
    )

async def upload_image(image_file: UploadFile, folder: str = "user_profiles"):
    try:
        # Read the file content safely
        file_content = await image_file.read()

        # Check that file isn't empty
        if not file_content:
            raise Exception("Empty file — ensure a valid image is selected")

        # Upload to Cloudinary using the binary content
        upload_result = cloudinary.uploader.upload(
            file_content,
            folder=folder,
            resource_type="image"
        )

        # Return the secure URL
        return upload_result.get("secure_url")

    except Exception as e:
        raise Exception(f"Image upload failed: {str(e)}")    
    #file_bytes = await image_file.read()
    #upload_result = cloudinary.uploader.upload(image_file, folder=folder)
    #return upload_result.get("secure_url")
    #upload_result =  cloudinary.uploader.upload(file_bytes, folder=folder)
    #return upload_result.get("secure_url")

