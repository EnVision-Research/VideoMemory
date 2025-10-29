"""
Prompt generation tools for fast keyframe planning.
These are pure functions that generate prompts without calling image generation APIs.
"""

import re
import logging
from typing import Optional, List
from langchain.tools import tool
from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


# ============================================================================
# INPUT SCHEMAS
# ============================================================================

class CharacterPromptInput(BaseModel):
    """Input schema for character prompt generation"""
    character_name: str = Field(..., description="Character name")
    current_state: str = Field(..., description="Age, clothing, appearance (will be sanitized)")
    reference_image_path: Optional[str] = Field(default=None, description="Previous version for consistency")
    global_visual_style: str = Field(..., description="Global visual style")


class ScenePromptInput(BaseModel):
    """Input schema for scene prompt generation"""
    location_name: str = Field(..., description="Location name")
    scene_heading: str = Field(..., description="Scene heading (INT./EXT. LOCATION - TIME)")
    scene_description: str = Field(..., description="Atmosphere, lighting, mood")
    key_landmarks: List[str] = Field(default_factory=list, description="Recurring landmarks for continuity")
    global_visual_style: str = Field(..., description="Global visual style")


class PropPromptInput(BaseModel):
    """Input schema for prop prompt generation"""
    prop_name: str = Field(..., description="Prop name")
    current_condition: str = Field(..., description="Current condition/state")
    reference_image_path: Optional[str] = Field(default=None, description="Previous version for continuity")
    global_visual_style: str = Field(..., description="Global visual style")


class KeyframePromptInput(BaseModel):
    """Input schema for keyframe prompt generation"""
    shot_number: int = Field(..., description="Shot number")
    plot: str = Field(..., description="Plot description for this shot")
    reference_image_paths: List[str] = Field(..., description="Ordered reference paths")
    cinematography_notes: str = Field(..., description="Camera angle and composition")
    emotional_tone: str = Field(..., description="Emotional atmosphere")
    visual_style: str = Field(default="", description="Shot-specific visual style")
    global_visual_style: str = Field(..., description="Global visual style")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _sanitize_character_state(state: str) -> str:
    """Remove environment/action words, keep age + clothing/appearance only"""
    # Remove common environment/location words
    env_words = [
        "woods", "forest", "beach", "city", "balcony", "room", "garden",
        "navigating", "walking", "running", "standing", "sitting",
        "misty", "foggy", "rainy", "sunny", "dawn", "dusk"
    ]
    result = state
    for word in env_words:
        result = re.sub(rf'\b{word}\b', '', result, flags=re.IGNORECASE)
    
    # Clean up extra spaces
    result = ' '.join(result.split())
    return result


# ============================================================================
# PROMPT GENERATION TOOLS
# ============================================================================

@tool(args_schema=CharacterPromptInput)
def generate_character_prompt(
    character_name: str,
    current_state: str,
    reference_image_path: Optional[str],
    global_visual_style: str
) -> str:
    """
    Generate character portrait prompt following CHARACTER_SUBAGENT rules.
    Returns only the generation_prompt string.
    
    Rules:
    - Aspect ratio: 1:1
    - Cinematic full-body, frontal, neutral studio lighting
    - Hands empty, head bare, no environment
    - Sanitize current_state: keep age + clothing/appearance only
    """
    
    # Sanitize current_state: remove environment/location/action words
    sanitized_state = _sanitize_character_state(current_state)
    
    if reference_image_path:
        # Versioned character
        prompt = (
            f"{global_visual_style}, Take the character from the provided image, "
            f"modify to: {sanitized_state}. Maintain facial identity and core features. "
            f"Cinematic full-body portrait, frontal, neutral studio lighting, simple solid background. "
            f"No text. No environment. Hands empty. Head bare."
        )
    else:
        # New character
        prompt = (
            f"{global_visual_style}, Cinematic full-body portrait of {character_name}, {sanitized_state}, "
            f"facing camera frontally. Neutral studio lighting, simple background. "
            f"No text. No environment. Hands empty. Head bare."
        )
    
    return prompt


@tool(args_schema=ScenePromptInput)
def generate_scene_prompt(
    location_name: str,
    scene_heading: str,
    scene_description: str,
    key_landmarks: List[str],
    global_visual_style: str
) -> str:
    """
    Generate scene plate prompt following SCENE_SUBAGENT rules.
    Returns only the generation_prompt string.
    
    Rules:
    - Aspect ratio: 16:9
    - Wide establishing shot, no people
    - Include recurring landmarks for continuity
    """
    
    landmarks_text = ", ".join(key_landmarks) if key_landmarks else "establishing elements"
    
    prompt = (
        f"{global_visual_style}, {scene_description} based on scene heading: {scene_heading}. "
        f"Key landmarks: {landmarks_text}. "
        f"Wide establishing shot, cinematic composition. No text. No people."
    )
    
    return prompt


@tool(args_schema=PropPromptInput)
def generate_prop_prompt(
    prop_name: str,
    current_condition: str,
    reference_image_path: Optional[str],
    global_visual_style: str
) -> str:
    """
    Generate prop image prompt following PROP_SUBAGENT rules.
    Returns only the generation_prompt string.
    
    Rules:
    - Aspect ratio: 1:1
    - Professional product photography
    - Clean white background, studio lighting
    """
    
    if reference_image_path:
        # Versioned prop
        prompt = (
            f"{global_visual_style}, Take the object from the provided image, "
            f"modify to show: {current_condition}. Maintain object identity and design. "
            f"Clean white background, studio lighting. No text."
        )
    else:
        # New prop
        prompt = (
            f"{global_visual_style}, Professional product photography of {prop_name}, {current_condition}. "
            f"Neutral studio lighting, simple background, sharp focus, detailed texture, isolated object. No text."
        )
    
    return prompt


@tool(args_schema=KeyframePromptInput)
def generate_keyframe_prompt(
    shot_number: int,
    plot: str,
    reference_image_paths: List[str],
    cinematography_notes: str,
    emotional_tone: str,
    visual_style: str,
    global_visual_style: str
) -> str:
    """
    Generate keyframe composition prompt following KEYFRAME_SUBAGENT CKF rules.
    Returns only the generation_prompt string.
    
    Rules:
    - Aspect ratio: 16:9
    - One-based indexing: image1 .. imageN
    - ALL references MUST appear in prompt
    - CKF five-step structure
    """
    
    # Build reference map (one-based indexing)
    ref_map = []
    for i, path in enumerate(reference_image_paths, start=1):
        # Extract asset type from path
        if "/characters/" in path:
            ref_map.append(f"(image{i}) character")
        elif "/scenes/" in path:
            ref_map.append(f"(image{i}) scene plate")
        elif "/props/" in path:
            ref_map.append(f"(image{i}) prop")
        else:
            ref_map.append(f"(image{i}) reference")
    
    references_line = f"References: {', '.join(ref_map)}."
    
    # Build style text
    style_text = f"{global_visual_style}, {visual_style}" if visual_style else global_visual_style
    
    # CKF structure prompt
    prompt = (
        f"{references_line} "
        f"Create a {style_text} image. {plot}. "
        f"Shot from {cinematography_notes}, with a {emotional_tone} tone. "
        f"Maintain consistent identities and hairstyles; use only elements visible in the scene plate; "
        f"keep lighting/shadows coherent. No text."
    )
    
    return prompt

