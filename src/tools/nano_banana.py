from dotenv import load_dotenv
load_dotenv()

import replicate
import os
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
                file_url = client.files.create(img_file)
                image_urls.append(file_url.urls['get'])
        inputs["image_input"] = image_urls
    
    output = client.run(
        "google/nano-banana",
        input=inputs,
    )
    # Save the first image to the normalized path
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, "wb") as file:
        # Ensure directory exists
        file.write(output.read())

    return save_path


if __name__ == "__main__":
    nano_banana_replicate_tool.invoke(
        {
            "prompt": "Cinematic keyframe from Frozen 2: ELSA (age 21, wearing signature ice-blue gown) stands troubled on Arendelle Castle balcony, hearing mysterious ethereal voice calling her. ANNA (age 19, in green dress) approaches with concerned expression. Wind carries ethereal whispers through the air, visible in Elsa's flowing hair and gown. Cool blue color palette with ethereal lighting, soft focus on Elsa's troubled expression. Medium close-up composition showing both sisters, camera slowly pushing in as voice calls. Mysterious atmosphere with wind effects, ancient powerful presence felt. Emotional tone: mysterious and troubled. Visual style: cinematic animation with soft lighting and wind movement.",
            "aspect_ratio": "16:9",
            "save_path": "output/FronzenII/keyframes/shot_1.png",
            "images": ['output/FronzenII/memory_bank/characters/ELSA.png', 'output/FronzenII/memory_bank/characters/ANNA.png', 'output/FronzenII/memory_bank/scenes/Arendelle_Castle_balcony.png']
        }
    )