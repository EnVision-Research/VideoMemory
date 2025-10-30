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
class Storyboardshot(BaseModel):
    shot: int = Field(
        ...,
        description="The sequential number of the shot globally across the entire storyboard (e.g., 1, 2, 3, ..., 8), matching the shot number from the input script."
    )
    act: int = Field(
        ...,
        description="The act number (1, 2, or 3) matching the act structure from the input screenplay."
    )
    scene: str = Field(
        ...,
        description="Scene heading from the script in standard format: INT./EXT. + LOCATION + TIME (e.g., 'INT. COFFEE SHOP - MORNING')."
    )
    scene_description: str = Field(
        ...,
        description="Rich description of the scene's visual and emotional elements, including physical location, time of day, lighting conditions, atmosphere, mood, and environmental details. Combine information from the script's scene heading with plot details."
    )
    plot: str = Field(
        ...,
        description="A concise description of the plot/action happening in this shot, extracted from the shot's plot field in the script."
    )
    characters: List[str] = Field(
        ...,
        description="List of character names appearing in this shot. Extract from the shot's plot description (without the detailed descriptions in parentheses)."
    )
    key_props: List[str] = Field(
        ...,
        description="List of key props that are important to this shot. Extract prop names from the script (without the detailed descriptions in parentheses)."
    )
    emotional_tone: str = Field(
        ...,
        description="The dominant emotional tone of this shot (e.g., joyful, melancholic, tense, peaceful, nostalgic, suspenseful, romantic, etc.)."
    )
    visual_style: str = Field(
        ...,
        description="Description of the visual style for this shot, including color palette, lighting style, composition preferences, and overall aesthetic approach."
    )
    cinematography_notes: str = Field(
        ...,
        description="Natural language cinematography description (2-4 sentences in flowing prose) that serves dual purposes: (1) Keyframe Composition Design - describes static frame composition including shot type, camera angle, focal length, depth of field, lighting, and visual composition; (2) Video Shot Motion Design - describes camera movement path, starting position (matching keyframe), motion motivation, and pacing; (3) Shot Continuity - addresses relationship to adjacent shots for spatial logic, eye-lines, screen direction, and scene coverage. Must ensure shot-to-shot flow and serve narrative progression. Example: 'Open with a wide establishing shot at eye level using a 35mm lens with deep focus. For the video shot, begin locked off for two seconds, then slowly dolly in toward the character. This establishes spatial geography and sets up the subsequent close-up.'"
    )   

class Storyboard(BaseModel):
    title: str = Field(
        ...,
        description="The title of the script."
    )
    logline: str = Field(
        ...,
        description="The logline of the script."
    )    
    shots: List[Storyboardshot] = Field(
        ...,
        description="The list of shots for this storyboard."
    )

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

# Memory Bank (Fast Pipeline)
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