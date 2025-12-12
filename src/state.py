from dataclasses import dataclass
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage

from typing import TypedDict, Annotated, List, Optional
from pydantic import BaseModel

from src.prompts import STORYBOARD, MEMORY, VISUALIZATION, KEYFRAME, VIDEO

# ===== STATE DEFINITIONS =====
class VideoMemoryState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    script: str
    storyboard: str
    memory_bank: dict
    keyframe: str
    video_clips: str

# ===== CONTEXT DEFINITIONS =====
@dataclass
class VideoMemoryContext:
    """Context configuration for VideoMemory pipeline."""
    
    # prompts for agent 
    storyboard_prompt: str = STORYBOARD
    memory_prompt: str = MEMORY
    visualization_prompt: str = VISUALIZATION
    keyframe_prompt: str = KEYFRAME
    video_prompt: str = VIDEO

    # models for agent 
    storyboard_model: str = "gpt-5.2"
    memory_model: str = "gpt-5.2"
    visualization_model: str = "gpt-5.2"
    keyframe_model: str = "gpt-5.2"
    video_model: str = "gpt-5.2"

    # config for image and video tools
    aspect_ratio: str = "16:9"
    total_shot_number: int = 8
    sora2_seconds: int = 8
    sora2_model: str = "sora-2"
    sora2_size: str = "1280x720"

# ===== SCHEMA DEFINITIONS =====
# Storyboard
class StoryboardShot(BaseModel):
    shot: int 
    act: int 
    narrative_function: str
    shot_pattern: str
    visual_chain: str
    plot: str 
    scene: str 
    characters: List[str] 
    key_props: List[str] 
    keyframe_design: str 
    video_shot_design: str 


class Storyboard(BaseModel):
    title: str 
    logline: str 
    global_visual_style: str
    shots: List[StoryboardShot]

# Memory Bank
class Asset(BaseModel):
    """Asset with generation prompt and path (for batch generation later)"""
    name: str 
    generation_prompt: str 
    image_path: str
    reference_image_list: Optional[List[str]] 

class ShotRecord(BaseModel):
    """Complete record for one shot"""
    shot: int 
    act: int
    characters: List[Asset] 
    props: List[Asset] 
    scene: Asset 
    reference_image_list: List[str] 

class MemoryBank(BaseModel):
    """Complete memory bank with all shots"""
    shots: List[ShotRecord]

# Visualization
class KeyframeRecord(BaseModel):
    """Record for a generated keyframe"""
    shot: int
    generation_prompt: str
    reference_image_list: List[str] 
    keyframe_path: str


class VideoClip(BaseModel):
    """Record for a generated video clip"""
    shot: int
    generation_prompt: str
    keyframe_path: str
    video_path: str

class Visualization(BaseModel):
    """Complete visualization with keyframes and video clips"""
    keyframes: List[KeyframeRecord]
    video_clips: List[VideoClip]
