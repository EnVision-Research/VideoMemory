from pydantic import BaseModel
from typing import List

from langchain.tools import tool, ToolRuntime
from langchain.agents import create_agent
from langchain.agents.middleware import ToolRetryMiddleware
from langchain_core.messages import ToolMessage, HumanMessage
from langgraph.types import Command

from src.state import KeyframeRecord, VideoClip, VideoMemoryContext

from .nano_banana_tool import nano_banana_replicate_tool
from .sora2_tool import sora2_tool
from .mock_image_tool import mock_image_tool
from .mock_video_tool import mock_video_tool

import os
import logging
logger = logging.getLogger(__name__)


class Keyframe(BaseModel):
    keyframes: List[KeyframeRecord]

@tool
def keyframe_generation(request: str, runtime: ToolRuntime) -> Command:
    """
    Generate a keyframe using the keyframe generation tool.
    """

    ctx = runtime.context

    thread_id = runtime.config.get("configurable", {}).get("thread_id")
    if not thread_id:
        raise ValueError("thread_id is required in config.configurable.thread_id")
    
    storyboard_json = runtime.state["storyboard"]
    memory_bank_json = runtime.state["memory_bank"]

    query_messages = f"""
        The request from visualization agent is:\n{request}\n
        The base_path is: output/{thread_id}
        Storyboard is:\n{storyboard_json}\n
        Memory bank is:\n{memory_bank_json}\n
    """

    # Create Keyframe sub-agent
    keyframe_agent = create_agent(
        name="keyframe_agent",
        model=ctx.keyframe_model,
        tools=[nano_banana_replicate_tool],
        system_prompt=ctx.keyframe_prompt,
        response_format=Keyframe,
        context_schema=VideoMemoryContext,
        middleware=[
            ToolRetryMiddleware(
                max_retries=5,
                backoff_factor=2.0,
                initial_delay=1.0,
            ),
        ],
    )

    result = keyframe_agent.invoke(
        {"messages": [HumanMessage(content=query_messages, name="keyframe_subagent")]},
        context=ctx,
    )

    keyframe_json = result['structured_response'].model_dump_json(indent=2)
    # save the visualization to a file
    os.makedirs(f"output/{thread_id}", exist_ok=True)
    with open(f"output/{thread_id}/keyframe.json", "w") as f:
        f.write(keyframe_json)

    return Command(
        update={
            "messages": [ToolMessage(content="The new keyframe is saved at output/{thread_id}/keyframe.json", tool_call_id=runtime.tool_call_id)],
            "keyframe": keyframe_json,
        }
    )


class Video(BaseModel):
    video_clips: List[VideoClip]

@tool
def video_generation(request: str, runtime: ToolRuntime) -> Command:
    """
    Generate a video using the video generation tool.
    """
    ctx = runtime.context
    thread_id = runtime.config.get("configurable", {}).get("thread_id")
    if not thread_id:
        raise ValueError("thread_id is required in config.configurable.thread_id")
    
    storyboard_json = runtime.state["storyboard"]
    logger.info(f"storyboard_json: \n{storyboard_json}")
    keyframe_json = runtime.state["keyframe"]
    logger.info(f"keyframe_json: \n{keyframe_json}")

    human_message = f"""
        The request from visualization agent is:\n{request}\n
        The base_path is: output/{thread_id}
        Storyboard is:\n{storyboard_json}\n
        Keyframe is:\n{keyframe_json}\n
    """

    # Create Video sub-agent
    video_agent = create_agent(
        name="video_agent",
        model=ctx.video_model,
        tools=[sora2_tool],
        system_prompt=ctx.video_prompt,
        response_format=Video,
        context_schema=VideoMemoryContext,
        middleware=[
            ToolRetryMiddleware(
                max_retries=5,
                backoff_factor=2.0,
                initial_delay=1.0,
            ),
        ],
    )

    result = video_agent.invoke(
        {"messages": [HumanMessage(content=human_message, name="video_subagent")]},
        context=ctx,
    )

    video_clips = result['structured_response'].model_dump_json(indent=2)
    # save the video clips to a file
    os.makedirs(f"output/{thread_id}", exist_ok=True)
    with open(f"output/{thread_id}/video_clips.json", "w") as f:
        f.write(video_clips)

    return Command(
        update={
            "messages": [ToolMessage(content="The new video clips are saved at output/{thread_id}/video_clips.json", tool_call_id=runtime.tool_call_id)],
            "video_clips": video_clips,
        }
    )