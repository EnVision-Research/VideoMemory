from pydantic import BaseModel, Field
from typing import List, Optional

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

import logging
logger = logging.getLogger(__name__)


class MockImageInput(BaseModel):
    prompt: str = Field(..., description="The text prompt to guide image generation")
    aspect_ratio: str = Field(default="16:9", description="The aspect ratio of the image")
    images: Optional[List[str]] = Field(default=None, description="Optional list of local image file paths to include in contents; length can vary")    
    save_path: str = Field(..., description="The local path to store the generated image file")


@tool(args_schema=MockImageInput)
def mock_image_tool(
    prompt: str, 
    aspect_ratio: str, 
    save_path: str, 
    runtime: ToolRuntime,
    images: Optional[List[str]] = None, 
) -> Command:
    """
    Generate an image using "nano-banana", supporting a variable number of input images, and save the result to the specified local path.

    Args:
        prompt (str): The text prompt to guide image generation.
        save_path (str): The local path to save the generated image (including filename and extension, e.g., .png).
        images (List[str], optional): List of local image file paths to include in the contents; can be empty or any number.

    Returns:
        save_path (str): The local path where the generated image is saved.
    """

    inputs = {
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "output_format": "png",
    }
    
    if images:
        inputs["image_input"] = images
    
    logger.info("Inputs: ", inputs)
    logger.info(f"Generated image saved at {save_path}")
    
    return Command(
        update={
            "messages": [
                ToolMessage(f"The new image is saved at {save_path}", tool_call_id=runtime.tool_call_id)
            ],
        }
    )


if __name__ == "__main__":
    mock_image_tool.invoke(
        {
            "prompt": "Create a new image by combining the elements from the provided images. Take the characters Maverick and Rooster from the reference images and place them in the flight briefing room environment. Add the tactical screen and mission schematics props. The final image should show: Maverick standing before a glowing tactical screen displaying mission schematics, Rooster watching him from the front row with clear resentment, tense atmosphere, high-contrast sterile lighting dominated by blue glow, cool color palette of blues, greys, and blacks, wide shot establishing the room and positions of all pilots, cinematic film style, professional military aesthetic",
            "save_path": "output/keyframes/1.png",
            "aspect_ratio": "16:9",
        }
    )
