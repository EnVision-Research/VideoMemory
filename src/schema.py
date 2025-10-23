from pydantic import BaseModel, Field
from typing import List, Dict, Optional


# ScreenWriter
class Shot(BaseModel):
    shot: int = Field(
        ..., 
        description="The sequential number of the shot within its scene, restarting from 1 for each new scene."
    )
    plot: str = Field(
        ..., 
        description="Complete screenplay content in standard format. CRITICAL: Do NOT include scene heading (INT./EXT. LOCATION - TIME) as it's already in Scene.scene field. Include only: Action Lines (visual description, behaviors, movements), Character Names (UPPERCASE when speaking), Dialogue (indented below character name), Parentheticals (delivery notes like whispering, angry), and Transitions (only at scene end: CUT TO:, FADE OUT., etc.). First appearance of characters/props must include detailed descriptions in parentheses for visual consistency."
    )


class Scene(BaseModel):
    scene: str = Field(
        ...,
        description="Scene heading in standard screenplay format: INT./EXT. + LOCATION + TIME (e.g., 'INT. COFFEE SHOP - MORNING'). This heading applies to ALL shots in this Scene object."
    )
    shots: List[Shot] = Field(
        ..., 
        description="List of shots occurring in this specific scene (same location and time). ALL shots must take place within the location and time defined in the scene field. If location or time changes, create a new Scene object."
    )

class Act(BaseModel):
    act: int = Field(
        ..., 
        description="The act number (1, 2, or 3) following the three-act structure. Act 1: Introduction and Inciting Incident (~30% duration). Act 2: Rising Action and Midpoint (~40% duration). Act 3: Climax and Resolution (~30% duration)."
    )

    scenes: List[Scene] = Field(
        ...,
        description="List of Scene objects in this act. Each Scene represents a unique location+time combination. Create a new Scene object whenever location or time changes."
    )

class Script(BaseModel):
    acts: List[Act] = Field(
        ..., 
        description="A complete structured screenplay following the three-act structure. The entire screenplay should fit within 90 seconds total duration, containing between 11 and 22 shots (each 4s, 6s, or 8s) distributed across three acts. Act 1 covers ~30% (setup), Act 2 covers ~40% (conflict), and Act 3 covers ~30% (resolution) of the total duration. The story should span a significant time period (e.g., protagonist from age 8 to 38) to test consistency in character appearance, settings, and props over time."
    )


# Storyboard
class StoryboardShot(BaseModel):
    shot: int = Field(
        ...,
        description="The sequential number of the shot within its scene, restarting from 1 for each new scene."
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
        description="The dominant emotional tone of this shot (e.g., joyful, melancholic, tense, peaceful, nostalgic, etc.)."
    )
    visual_style: str = Field(
        ...,
        description="Description of the visual style for this shot, including color palette, lighting style, composition preferences, and overall aesthetic approach."
    )
    music_and_sound_effects: str = Field(
        ...,
        description="Description of music and sound effects that should accompany this shot, including mood, tempo, instrumentation, and specific sound design elements."
    )
    cinematography_notes: str = Field(
        ...,
        description="Camera techniques, angles, movements, and cinematography suggestions for this shot (e.g., close-up, wide shot, tracking shot, Dutch angle, etc.)."
    )


class StoryboardScene(BaseModel):
    scene: str = Field(
        ...,
        description="Scene heading from the script in standard format: INT./EXT. + LOCATION + TIME (e.g., 'INT. COFFEE SHOP - MORNING'). This heading applies to ALL shots in this scene."
    )
    scene_description: str = Field(
        ...,
        description="Rich description of the scene's visual and emotional elements, including physical location, time of day, lighting conditions, atmosphere, mood, and environmental details. Combine information from the script's scene heading with plot details."
    )
    shots: List[StoryboardShot] = Field(
        ...,
        description="List of storyboard shots occurring in this specific scene (same location and time). All shots must take place within the location and time defined in the scene field."
    )


class StoryboardAct(BaseModel):
    act: int = Field(
        ...,
        description="The act number (1, 2, or 3) matching the act structure from the input screenplay."
    )
    scenes: List[StoryboardScene] = Field(
        ...,
        description="List of StoryboardScene objects in this act. Each scene represents a unique location+time combination from the screenplay."
    )


class Storyboard(BaseModel):
    acts: List[StoryboardAct] = Field(
        ...,
        description="A complete storyboard following the same three-act and scene structure as the input screenplay. Each act contains scenes, and each scene contains detailed storyboard shots with production information including characters, props, emotional tone, visual style, music/sound effects, and cinematography notes."
    )