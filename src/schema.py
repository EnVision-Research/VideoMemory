from pydantic import BaseModel, Field
from typing import List, Dict, Optional


# ScreenWriter
class Scriptshot(BaseModel):
    shot: int = Field(
        ..., 
        description="The sequential number of the shot globally across the entire script (e.g., 1, 2, 3, ..., 8), never restarting between acts or scenes."
    )
    act: int = Field(
        ...,
        description="The act number (1, 2, or 3) following the three-act structure. Act 1: Introduction and Inciting Incident (~30% duration). Act 2: Rising Action and Midpoint (~40% duration). Act 3: Climax and Resolution (~30% duration)."
    )
    scene: str = Field(
        ...,
        description="The scene heading in standard screenplay format: INT./EXT. + LOCATION + TIME (e.g., 'INT. COFFEE SHOP - MORNING')."
    )
    plot: str = Field(
        ..., 
        description="Complete screenplay content in standard format. CRITICAL: Do NOT include scene heading (INT./EXT. LOCATION - TIME) as it's already in Scene.scene field. Include only: Action Lines (visual description, behaviors, movements), Character Names (UPPERCASE when speaking), Dialogue (indented below character name), Parentheticals (delivery notes like whispering, angry), and Transitions (only at scene end: CUT TO:, FADE OUT., etc.). First appearance of characters/props must include detailed descriptions in parentheses for visual consistency."
    )

class Script(BaseModel):
    title: str = Field(
        ...,
        description="The title of the script."
    )
    logline: str = Field(
        ...,
        description="The logline of the script."
    )
    shots: List[Scriptshot] = Field(
        ...,
        description="The list of shots for this script."
    )

# Storyboard
class StoryboardShot(BaseModel):
    shot: int = Field(
        ...,
        description="Sequential shot number (e.g., 1, 2, 3) matching the input screenplay."
    )
    act: int = Field(
        ...,
        description="Act number (1, 2, or 3) matching the input screenplay."
    )
    scene: str = Field(
        ...,
        description="The exact scene heading from the screenplay (e.g., 'INT. LOCATION - TIME')."
    )
    scene_description: str = Field(
        ...,
        description="Location, time of day, and atmosphere derived *only* from the screenplay JSON. No new details."
    )
    plot: str = Field(
        ...,
        description="The exact, verbatim 'plot' string for this shot from the screenplay JSON."
    )
    characters: List[str] = Field(
        ...,
        description="List of character NAMES appearing in this shot, matching the screenplay."
    )
    key_props: List[str] = Field(
        ...,
        description="Only include props that appear in **more than 50% of the shots** throughout the screenplay, representing persistent or significant items that contribute to visual continuity."
    )
    emotional_tone: str = Field(
        ...,
        description="The dominant emotional mood of the shot (e.g., 'Tense', 'Joyful', 'Melancholic')."
    )
    visual_style: str = Field(
        ...,
        description="The film’s visual style as applied to this shot."
    )
    cinematography_notes: str = Field(
        ...,
        description="Prose describing keyframe composition (framing, angle, lens, light) and video motion (movement, pacing), motivated by the plot. Must ensure continuity with adjacent shots."
    )

class Storyboard(BaseModel):
    title: str = Field(
        ...,
        description="The title of the screenplay."
    )
    logline: str = Field(
        ...,
        description="The logline of the screenplay."
    )
    shots: List[StoryboardShot] = Field(
        ...,
        description="Ordered list of StoryboardShot items forming the complete storyboard."
    )

# Memory Bank 
class AssetPrompt(BaseModel):
    """Asset with generation prompt and path (for batch generation later)"""
    name: str = Field(..., description="Asset name (e.g., 'LINA_(29_warm_smile)')")
    aspect_ratio: str = Field(..., description="The aspect ratio of the asset")
    generation_prompt: str = Field(..., description="Complete prompt for generating the asset")
    image_path: str = Field(..., description="Path where image will be saved")
    reference_image_list: Optional[List[str]] = Field(default=None, description="Reference images used (if versioned asset)")

class KeyframePrompt(BaseModel):
    """Keyframe with generation prompt and references"""
    aspect_ratio: str = Field(..., description="The aspect ratio of the keyframe")
    generation_prompt: str = Field(..., description="Complete keyframe prompt with all references")
    image_path: str = Field(..., description="Path where keyframe will be saved")
    reference_image_list: List[str] = Field(..., description="Ordered list of reference image paths")

class ShotRecord(BaseModel):
    """Complete record for one shot"""
    shot: int = Field(..., description="Sequential shot number")
    act: int = Field(..., description="Act number (1, 2, or 3)")
    scene: str = Field(..., description="Scene heading (e.g., 'EXT. LOCATION - TIME')")
    characters: List[AssetPrompt] = Field(default_factory=list, description="Character assets for this shot")
    scenes: List[AssetPrompt] = Field(default_factory=list, description="Scene assets for this shot")
    props: List[AssetPrompt] = Field(default_factory=list, description="Prop assets for this shot")
    keyframe: KeyframePrompt = Field(..., description="Final keyframe for this shot")

class MemoryBank(BaseModel):
    """Complete memory bank with all shots"""
    shots: List[ShotRecord] = Field(..., description="All shot records in sequential order")



# Cinetography
class Cinetographyshot(BaseModel):
    shot: int = Field(
        ...,
        description="The sequential number of the shot globally across the entire cinetography (e.g., 1, 2, 3, ..., 8), matching the shot number from the input storyboard."
    )
    generation_prompt: str = Field(
        ...,
        description="Concise video generation prompt (max 500 characters) focusing on action, movement, and camera motion. Derived from storyboard's cinematography_notes, emphasizing the motion design aspects (camera movement path, pacing, character actions). Should maintain narrative continuity with adjacent shots and exclude technical image generation instructions."
    )
    image_path: str = Field(
        ...,
        description="The path to the keyframe image file that serves as the starting frame for this video shot."
    )
    negative_prompt: str = Field(
        ...,
        description="Negative prompt specifying what to avoid in video generation (e.g., 'blurry, distorted, static, jittery motion, artifacts')."
    )
    save_path: str = Field(
        ...,
        description="Output path where the generated video file will be saved (e.g., 'output/{project_name}/videos/{shot_number}.mp4')."
    )

class Cinetography(BaseModel):
    title: str = Field(
        ...,
        description="The title of the script."
    )
    logline: str = Field(
        ...,
        description="The logline of the script."
    )
    shots: List[Cinetographyshot] = Field(
        ...,
        description="The list of shots for this cinetography."
    )