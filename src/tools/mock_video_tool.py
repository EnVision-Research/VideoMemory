from pydantic import BaseModel, Field
from typing import Optional

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

import logging
logger = logging.getLogger(__name__)


class MockVideoInput(BaseModel):
    prompt: str = Field(..., description="The text prompt to guide video generation")
    keyframe_path: str = Field(..., description="The path to the keyframe image to use as the first frame")
    duration: float = Field(default=8.0, description="The duration of the video in seconds")
    save_path: str = Field(..., description="The local path to store the generated video file")


@tool(args_schema=MockVideoInput)
def mock_video_tool(
    prompt: str, 
    keyframe_path: str,
    duration: float,
    save_path: str, 
    runtime: ToolRuntime,
) -> Command:
    """
    Generate a video clip based on a keyframe image and prompt.
    This is a mock tool that simulates video generation without actually creating a video.

    Args:
        prompt (str): The text prompt to guide video generation (e.g., camera movements, actions).
        keyframe_path (str): The path to the keyframe image to use as the first frame.
        duration (float): The duration of the video in seconds (default: 8.0).
        save_path (str): The local path to save the generated video (including filename and extension, e.g., .mp4).

    Returns:
        save_path (str): The local path where the generated video would be saved.
    """

    inputs = {
        "prompt": prompt,
        "keyframe_path": keyframe_path,
        "duration": duration,
        "output_format": "mp4",
    }
    
    logger.info(f"Mock video generation inputs: {inputs}")
    logger.info(f"Mock video would be saved at {save_path}")
    
    return Command(
        update={
            "messages": [
                ToolMessage(f"The new video is saved at {save_path}", tool_call_id=runtime.tool_call_id)
            ],
        }
    )


if __name__ == "__main__":
    mock_video_tool.invoke(
        {
            "prompt": "0-2s: Eye-level medium shot, character raises hand; 2-6s: Cut to POV close-up; 6-8s: Cut to low-angle reaction shot",
            "keyframe_path": "output/keyframes/1.png",
            "duration": 8.0,
            "save_path": "output/videos/1.mp4",
        }
    )
