from dotenv import load_dotenv
load_dotenv()

import os
import time
import tempfile
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import Optional, Literal, Tuple
from PIL import Image

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

import logging
logger = logging.getLogger(__name__)

# Create OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def parse_size(size: str) -> Tuple[int, int]:
    """Parse size string like '1920x1080' into (width, height) tuple."""
    parts = size.lower().split('x')
    if len(parts) != 2:
        raise ValueError(f"Invalid size format: {size}. Expected 'WIDTHxHEIGHT'")
    return int(parts[0]), int(parts[1])


def resize_image_to_match(image_path: str, target_width: int, target_height: int) -> str:
    """
    Resize image to match target dimensions and save to a temp file.
    
    Args:
        image_path: Path to the input image.
        target_width: Target width in pixels.
        target_height: Target height in pixels.
        
    Returns:
        Path to the resized image (temp file).
    """
    with Image.open(image_path) as img:
        original_size = img.size
        target_size = (target_width, target_height)
        
        if original_size == target_size:
            logger.info(f"Image already matches target size: {target_size}")
            return image_path
        
        logger.info(f"Resizing image from {original_size} to {target_size}")
        
        # Use LANCZOS for high-quality downsampling
        resized_img = img.resize(target_size, Image.LANCZOS)
        
        # Preserve image format
        img_format = img.format or "PNG"
        suffix = f".{img_format.lower()}"
        
        # Save to temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        resized_img.save(temp_file.name, format=img_format)
        temp_file.close()
        
        logger.info(f"Resized image saved to: {temp_file.name}")
        return temp_file.name


class Sora2Input(BaseModel):
    prompt: str = Field(..., description="Text prompt that describes the video to generate")
    save_path: str = Field(..., description="Local path to save the generated video file")
    input_image: Optional[str] = Field(
        default=None, 
        description="Optional path to input image file that guides generation"
    )

@tool(args_schema=Sora2Input)
def sora2_tool(
    prompt: str,
    save_path: str,
    runtime: ToolRuntime,
    input_image: Optional[str] = None,
) -> Command:
    """
    Generate a video using OpenAI Sora 2 API and save to the specified path.

    Args:
        prompt: Text prompt that describes the video to generate.
        save_path: Local path to save the generated video.
        input_image: Optional path to input image for image-to-video generation.

    Returns:
        Command with the path where the video is saved.
    """
    ctx = runtime.context
    model = ctx.sora2_model
    seconds = ctx.sora2_seconds
    size = ctx.sora2_size

    logger.info(f"Creating video: model={model}, seconds={seconds}, size={size}")
    
    # Build request kwargs
    create_kwargs = {
        "model": model,
        "prompt": prompt,
        "seconds": seconds,
        "size": size,
    }
    
    # Track temp file for cleanup
    temp_image_path = None
    
    # Add input image if provided
    if input_image:
        # Parse target size and resize image if needed
        target_width, target_height = parse_size(size)
        resized_path = resize_image_to_match(input_image, target_width, target_height)
        
        # Track if we created a temp file
        if resized_path != input_image:
            temp_image_path = resized_path
        
        create_kwargs["input_reference"] = open(resized_path, "rb")
        logger.info(f"Using input image: {resized_path}")
    
    try:
        # Create video generation job
        video_job = client.videos.create(**create_kwargs)
        job_id = video_job.id
        logger.info(f"Video job created: {job_id}")
        
        # Poll for completion
        max_wait = 600  # 10 minutes
        poll_interval = 5
        elapsed = 0
        
        while elapsed < max_wait:
            video_job = client.videos.retrieve(job_id)
            status = video_job.status
            progress = getattr(video_job, 'progress', 0)
            
            logger.info(f"Status: {status}, Progress: {progress}%")
            
            if status == "completed":
                break
            elif status == "failed":
                error = getattr(video_job, 'error', {})
                raise RuntimeError(f"Video generation failed: {error}")
            
            time.sleep(poll_interval)
            elapsed += poll_interval
        else:
            raise TimeoutError(f"Video generation timed out after {max_wait}s")
        
        # Download video content
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        response = client.videos.download_content(job_id)
        content = response.read()
        
        with open(save_path, "wb") as f:
            f.write(content)
        
        logger.info(f"Video saved: {save_path}")
        
    finally:
        # Close file handle if opened
        if input_image and "input_reference" in create_kwargs:
            create_kwargs["input_reference"].close()
        
        # Clean up temp file if created
        if temp_image_path and os.path.exists(temp_image_path):
            try:
                os.remove(temp_image_path)
                logger.info(f"Cleaned up temp file: {temp_image_path}")
            except OSError as e:
                logger.warning(f"Failed to clean up temp file: {e}")
    
    return Command(
        update={
            "messages": [
                ToolMessage(f"Video saved at {save_path}", tool_call_id=runtime.tool_call_id)
            ],
        }
    )