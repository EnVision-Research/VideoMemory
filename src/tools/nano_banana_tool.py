from dotenv import load_dotenv
load_dotenv()

import replicate
import os
import httpx
from pydantic import BaseModel, Field
from typing import List, Optional

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

import logging
logger = logging.getLogger(__name__)

# Create a Replicate client with extended timeout
client = replicate.Client(
    api_token=os.environ.get("REPLICATE_API_TOKEN"),
    timeout=300  # Increase timeout to 300 seconds (5 minutes)
)

class NanoBananaReplicateInput(BaseModel):
    prompt: str = Field(..., description="The text prompt to guide image generation")
    reference_image_list: Optional[List[str]] = Field(default=[], description="The reference images to include in the contents")    
    save_path: str = Field(..., description="The local path to store the generated image file")


@tool(args_schema=NanoBananaReplicateInput)
def nano_banana_replicate_tool(
    prompt: str, 
    save_path: str, 
    runtime: ToolRuntime,
    reference_image_list: Optional[List[str]] = None, 
) -> Command:
    """
    Generate an image using "nano-banana", supporting a variable number of input reference_image_list, and save the result to the specified local path.

    Args:
        prompt (str): The text prompt to guide image generation.
        save_path (str): The local path to save the generated image 
        reference_image_list (List[str]): The reference images to include in the contents

    Returns:
        save_path (str): The local path where the generated image is saved.
    """
    ctx = runtime.context

    inputs = {
        "prompt": prompt,
        "aspect_ratio": ctx.aspect_ratio,
        "output_format": "png",
    }
    
    if reference_image_list:
        # Upload local files to Replicate and get URLs
        image_urls = []
        for img_path in reference_image_list:
            with open(img_path, "rb") as img_file:
                # Upload file to Replicate and get URL
                file_obj = client.files.create(img_file)
                # Use the URL from the file object's urls attribute
                image_urls.append(file_obj.urls["get"])
        inputs["image_input"] = image_urls
    
    
    output = client.run("google/nano-banana", input=inputs)

    # Save the generated image to the specified path
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    # Download the output image
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
                
    logger.info(f"Generated image saved at {save_path}")
    
    return Command(
        update={
            "messages": [
                ToolMessage(f"The new image is saved at {save_path}", tool_call_id=runtime.tool_call_id)
            ],
        }
    )


if __name__ == "__main__":
    nano_banana_replicate_tool.invoke(
        {
            "prompt": "Create a new image by combining the elements from the provided reference_image_list. Take the characters Maverick and Rooster from the reference reference_image_list and place them in the flight briefing room environment. Add the tactical screen and mission schematics props. The final image should show: Maverick standing before a glowing tactical screen displaying mission schematics, Rooster watching him from the front row with clear resentment, tense atmosphere, high-contrast sterile lighting dominated by blue glow, cool color palette of blues, greys, and blacks, wide shot establishing the room and positions of all pilots, cinematic film style, professional military aesthetic",
            "save_path": "output/keyframes/1.png",
        }
    )
