from dotenv import load_dotenv
load_dotenv()

import replicate
import os
import httpx
import time
from pydantic import BaseModel, Field
from typing import List, Optional
from langchain.tools import tool


class NanoBananaReplicateInput(BaseModel):
    prompt: str = Field(..., description="The text prompt to guide image generation")
    aspect_ratio: str = Field(
        default="16:9", 
        description="The aspect ratio of the image")
    images: Optional[List[str]] = Field(
        default=None,
        description="Optional list of local image file paths to include in contents; length can vary",
    )    
    save_path: str = Field(
        ..., description="The local path to store the generated image file"
    )


@tool(args_schema=NanoBananaReplicateInput)
def nano_banana_replicate_tool(
    prompt: str, aspect_ratio: str, save_path: str, images: Optional[List[str]] = None
) -> str:
    """
    Generate an image using "nano-banana", supporting a variable number of input images, and save the result to the specified local path.

    Args:
        prompt (str): The text prompt to guide image generation.
        save_path (str): The local path to save the generated image (including filename and extension, e.g., .png).
        images (List[str], optional): List of local image file paths to include in the contents; can be empty or any number.

    Returns:
        str: The local path where the generated image is saved.
    """

    inputs = {
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "output_format": "png",
    }
    # Create a Replicate client with extended timeout
    client = replicate.Client(
        api_token=os.environ.get("REPLICATE_API_TOKEN"),
        timeout=300  # Increase timeout to 300 seconds (5 minutes)
    )
    
    if images:
        # Upload local files to Replicate and get URLs
        image_urls = []
        for img_path in images:
            with open(img_path, "rb") as img_file:
                # Upload file to Replicate and get URL
                file_obj = client.files.create(img_file)
                # Use the URL from the file object's urls attribute
                image_urls.append(file_obj.urls["get"])
        inputs["image_input"] = image_urls
    
    output = client.run(
        "google/nano-banana",
        input=inputs,
    )
    
    # Save the generated image to the specified path
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    # Download with retry logic
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            # Handle different output formats
            if isinstance(output, list):
                # If output is a list of URLs, download the first one
                with httpx.Client(timeout=120.0) as http_client:
                    response = http_client.get(output[0])
                    response.raise_for_status()
                    with open(save_path, "wb") as file:
                        file.write(response.content)
            elif hasattr(output, 'read'):
                # If output is a file-like object
                with open(save_path, "wb") as file:
                    file.write(output.read())
            else:
                # If output is a URL string
                with httpx.Client(timeout=120.0) as http_client:
                    response = http_client.get(str(output))
                    response.raise_for_status()
                    with open(save_path, "wb") as file:
                        file.write(response.content)
            
            # Success - break retry loop
            break
            
        except (httpx.RemoteProtocolError, httpx.TimeoutException, httpx.HTTPError) as e:
            if attempt < max_retries - 1:
                print(f"⚠️  Download attempt {attempt + 1} failed: {e}")
                print(f"   Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                print(f"❌ Download failed after {max_retries} attempts")
                raise

    return save_path


if __name__ == "__main__":
    nano_banana_replicate_tool.invoke(
        {
            "prompt": "Create a new image by combining the elements from the provided images. Take the characters Maverick and Rooster from the reference images and place them in the flight briefing room environment. Add the tactical screen and mission schematics props. The final image should show: Maverick standing before a glowing tactical screen displaying mission schematics, Rooster watching him from the front row with clear resentment, tense atmosphere, high-contrast sterile lighting dominated by blue glow, cool color palette of blues, greys, and blacks, wide shot establishing the room and positions of all pilots, cinematic film style, professional military aesthetic",
            "save_path": "output/TopGunMaverick/keyframes/1.png",
            "aspect_ratio": "16:9",
            "images": ['output/TopGunMaverick/memory_bank/characters/MAVERICK.png', 'output/TopGunMaverick/memory_bank/characters/ROOSTER.png', 'output/TopGunMaverick/memory_bank/scenes/FLIGHT_BRIEFING_ROOM.png', 'output/TopGunMaverick/memory_bank/props/TACTICAL_SCREEN.png', 'output/TopGunMaverick/memory_bank/props/MISSION_SCHEMATICS.png']
        }
    )