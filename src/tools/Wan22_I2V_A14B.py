from dotenv import load_dotenv
load_dotenv()

import requests
import os
import time
import base64
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from langchain.tools import tool

import logging
logger = logging.getLogger(__name__)

# ============ Helper Functions ============

def _submit_video_generation(
    api_key: str,
    prompt: str, 
    image_path: str, 
    image_size: str = "1280x720",
    seed: int = 42,
    negative_prompt: Optional[str] = None,
) -> str:
    """
    Submit a video generation request using Wan2.2-I2V-A14B model.
    
    API Reference: https://docs.siliconflow.cn/cn/api-reference/videos/videos_submit

    Args:
        api_key (str): SiliconFlow API key.
        prompt (str): The text prompt to guide video generation.
        image_path (str): The local path of the input image file.
        image_size (str): The aspect ratio of the video. Default is "1280x720".
        negative_prompt (str, optional): Negative prompt to guide what should not appear.
        seed (int, optional): Seed for reproducible results.

    Returns:
        str: The requestId for polling video generation status.
    """
    
    # Read and encode the image to base64
    with open(image_path, "rb") as img_file:
        img_data = img_file.read()
        img_base64 = base64.b64encode(img_data).decode('utf-8')
        # Determine image format from file extension
        ext = os.path.splitext(image_path)[1].lower()
        mime_type = "image/png" if ext == ".png" else "image/jpeg"
        image_data_uri = f"data:{mime_type};base64,{img_base64}"
    
    # Submit video generation request
    submit_url = "https://api.siliconflow.cn/v1/video/submit"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "Wan-AI/Wan2.2-I2V-A14B",
        "prompt": prompt,
        "image_size": image_size,
        "image": image_data_uri
    }
    
    if negative_prompt:
        data["negative_prompt"] = negative_prompt
    if seed is not None:
        data["seed"] = seed
    
    logger.info("Submitting video generation request...")
    response = requests.post(submit_url, headers=headers, json=data)
    
    if response.status_code != 200:
        raise Exception(f"Failed to submit video generation request: {response.status_code}, {response.text}")
    
    request_id = response.json().get("requestId")
    logger.info(f"Request submitted successfully. Request ID: {request_id}")
    
    return request_id


def _get_video_status(api_key: str, request_id: str) -> Dict[str, Any]:
    """
    Get the status of a video generation request.
    
    API Reference: https://docs.siliconflow.cn/cn/api-reference/videos/get_videos_status

    Args:
        api_key (str): SiliconFlow API key.
        request_id (str): The requestId returned from submit_video_generation.

    Returns:
        dict: A dictionary containing:
            - status (str): "Succeed", "InQueue", "InProgress", or "Failed"
            - reason (str): Reason for the operation
            - results (dict): Contains video URLs and metadata (only when status is "Succeed")
    """
    
    status_url = "https://api.siliconflow.cn/v1/video/status"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        status_url,
        headers=headers,
        json={"requestId": request_id}
    )
    
    if response.status_code != 200:
        raise Exception(f"Failed to get video status: {response.status_code}, {response.text}")
    
    return response.json()


# ============ Main Tool ============

class Wan22I2VAToolInput(BaseModel):
    prompt: str = Field(..., description="The text prompt to guide video generation")
    image_path: str = Field(..., description="The local path of the input image file")
    image_size: str = Field(
        default="1280x720", 
        description="The aspect ratio of the video. Options: 1280x720, 720x1280, 960x960"
    )
    negative_prompt: Optional[str] = Field(
        default=None,
        description="Optional negative prompt to guide what should not appear in the video"
    )
    seed: Optional[int] = Field(
        default=None,
        description="Optional seed for reproducible results"
    )
    save_path: str = Field(
        ..., description="The local path to store the generated video file"
    )


@tool(args_schema=Wan22I2VAToolInput)
def wan22_i2v_tool(
    prompt: str, 
    image_path: str, 
    save_path: str,
    image_size: str = "1280x720",
    seed: int = 42,
    negative_prompt: Optional[str] = None,
) -> str:
    """
    Generate a video from an input image using Wan2.2-I2V-A14B model, and save the result to the specified local path.
    
    This tool internally uses two key functions:
    1. _submit_video_generation: Submit the video generation request
    2. _get_video_status: Poll for video generation status

    Args:
        prompt (str): The text prompt to guide video generation.
        image_path (str): The local path of the input image file.
        save_path (str): The local path to save the generated video (including filename and extension, e.g., .mp4).
        image_size (str): The aspect ratio of the video. Default is "1280x720".
        negative_prompt (str, optional): Negative prompt to guide what should not appear.
        seed (int, optional): Seed for reproducible results.

    Returns:
        str: The local path where the generated video is saved.
    """
    
    api_key = os.environ.get("SILICONFLOW_API_KEY")
    if not api_key:
        raise ValueError("SILICONFLOW_API_KEY environment variable is not set")
    
    # Step 1: Submit video generation request
    request_id = _submit_video_generation(
        api_key=api_key,
        prompt=prompt,
        image_path=image_path,
        image_size=image_size,
        negative_prompt=negative_prompt,
        seed=seed
    )
    
    # Step 2: Poll for video result
    max_attempts = 60  # Maximum 10 minutes (60 attempts * 10 seconds)
    attempt = 0
    
    logger.info("Waiting for video generation to complete...")
    while attempt < max_attempts:
        time.sleep(10)  # Wait 10 seconds between polls
        attempt += 1
        
        result_data = _get_video_status(api_key, request_id)
        status = result_data.get("status")
        
        logger.info(f"Request ID: {request_id}. Status: {status}. Attempt {attempt}/{max_attempts}...")
        
        if status == "Succeed":
            # Extract video URL from results
            results = result_data.get("results", {})
            videos = results.get("videos", [])
            
            if videos and len(videos) > 0:
                video_url = videos[0].get("url")
                
                if video_url:
                    logger.info("Video generated successfully! Downloading...")
                    # Download the video with retry logic
                    max_download_attempts = 5
                    download_attempt = 0
                    
                    while download_attempt < max_download_attempts:
                        try:
                            download_attempt += 1
                            logger.info(f"Download attempt {download_attempt}/{max_download_attempts}...")
                            
                            # Add timeout and stream for large files
                            video_response = requests.get(
                                video_url, 
                                timeout=(30, 300),  # (connect timeout, read timeout)
                                stream=True
                            )
                            video_response.raise_for_status()
                            
                            # Ensure directory exists
                            os.makedirs(os.path.dirname(save_path), exist_ok=True)
                            
                            # Save the video to the specified path (streaming)
                            with open(save_path, "wb") as video_file:
                                for chunk in video_response.iter_content(chunk_size=8192):
                                    if chunk:
                                        video_file.write(chunk)
                            
                            logger.info(f"Video saved to: {save_path}")
                            return save_path
                            
                        except (requests.exceptions.SSLError, 
                                requests.exceptions.ConnectionError,
                                requests.exceptions.Timeout,
                                requests.exceptions.ChunkedEncodingError) as e:
                            logger.warning(f"Download attempt {download_attempt} failed: {str(e)}")
                            # Delete incomplete file if exists
                            if os.path.exists(save_path):
                                try:
                                    os.remove(save_path)
                                    logger.info(f"Removed incomplete file: {save_path}")
                                except Exception as remove_error:
                                    logger.warning(f"Failed to remove incomplete file: {remove_error}")
                            
                            if download_attempt >= max_download_attempts:
                                raise Exception(f"Failed to download video after {max_download_attempts} attempts: {str(e)}")
                            # Wait before retry (exponential backoff)
                            wait_time = 2 ** download_attempt
                            logger.info(f"Waiting {wait_time}s before retry...")
                            time.sleep(wait_time)
            
            raise Exception("Video generation succeeded but no video URL found in response")
            
        elif status == "Failed":
            reason = result_data.get("reason", "Unknown error")
            raise Exception(f"Video generation failed: {reason}")
        
        # Status is "InQueue" or "InProgress", continue polling
    
    raise TimeoutError(f"Video generation timed out after {max_attempts} attempts")


if __name__ == "__main__":
    # Example usage
    wan22_i2v_tool.invoke(
        {
            "prompt": "A cinematic shot of Elsa using her ice magic, camera slowly zooms in",
            "image_path": "output/FronzenII/keyframes/shot_1.png",
            "image_size": "1280x720",
            "save_path": "output/FronzenII/videos/shot_1.mp4"
        }
    )

