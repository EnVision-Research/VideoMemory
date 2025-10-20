from pydantic import BaseModel, Field
from typing import List, Dict, Optional


# ScreenWriter
class Shot(BaseModel):
    shot: int = Field(
        ..., 
        description="The sequential number of the shot. Each shot should have a unique identifier within its act."
    )
    duration: int = Field(
        ...,
        description="The duration of the shot in seconds. Must be exactly 4, 6, or 8 seconds."
    )
    plot: str = Field(
        ..., 
        description="A complete and detailed description of the shot's content, including specific actions, dialogues, emotions, visual elements, time period/protagonist's age, and story developments. This should be comprehensive enough to fully represent the screenplay at this point in the narrative, contributing to the overall arc and ensuring smooth transitions. Should clearly indicate the time period to show temporal progression (e.g., protagonist's age). IMPORTANT: For each character, scene, and prop mentioned, provide detailed descriptions in parentheses immediately following the name. Format: 'Character Name (detailed physical description, age, clothing, etc.)', 'Scene Name (detailed environment description, lighting, atmosphere, etc.)', 'Prop Name (detailed appearance, material, condition, etc.)'."
    )

class Act(BaseModel):
    act: int = Field(
        ..., 
        description="The act number (1, 2, or 3) following the three-act structure. Act 1: Introduction and Inciting Incident (~30% duration). Act 2: Rising Action and Midpoint (~40% duration). Act 3: Climax and Resolution (~30% duration)."
    )
    shots: List[Shot] = Field(
        ..., 
        description="The list of shots in this act. Each shot represents a distinct moment in the narrative progression."
    )

class Script(BaseModel):
    acts: List[Act] = Field(
        ..., 
        description="A complete structured screenplay following the three-act structure. The entire screenplay should fit within 90 seconds total duration, containing between 11 and 22 shots (each 4s, 6s, or 8s) distributed across three acts. Act 1 covers ~30% (setup), Act 2 covers ~40% (conflict), and Act 3 covers ~30% (resolution) of the total duration. The story should span a significant time period (e.g., protagonist from age 8 to 38) to test consistency in character appearance, settings, and props over time."
    )


# Storyboard
class StoryboardItem(BaseModel):
    shot: int = Field(
        ...,
        description="The sequential number of the shot. Each shot should have a unique identifier within the entire storyboard."
    )
    plot: str = Field(
        ...,
        description="A concise description of the plot/action happening in this shot, extracted from the script."
    )
    characters: List[str] = Field(
        ...,
        description="List of character names appearing in this shot. Each character name should be extracted from the script's plot description (without the detailed descriptions in parentheses)."
    )
    scene: str = Field(
        ...,
        description="Description of the scene's visual and emotional elements, including location, time of day, atmosphere, and mood."
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


class Storyboard(BaseModel):
    storyboard: List[StoryboardItem] = Field(
        ...,
        description="A complete storyboard generated from the screenplay. Each storyboard item corresponds to a shot in the original script and provides detailed production information including characters, scene descriptions, props, emotional tone, visual style, music/sound effects, and cinematography notes."
    )


# Keyframe Agent
class NewCharacter(BaseModel):
    name: str = Field(
        ...,
        description="The name of the new character that needs to be generated."
    )
    generation_prompt: str = Field(
        ...,
        description="The detailed prompt for generating the character image, including physical appearance, age, clothing, and distinctive features."
    )
    image_path: str = Field(
        ...,
        description="The file path where the generated character image is saved."
    )


class NewScene(BaseModel):
    name: str = Field(
        ...,
        description="The name or description of the new scene that needs to be generated."
    )
    generation_prompt: str = Field(
        ...,
        description="The detailed prompt for generating the scene image, including environment, lighting, atmosphere, mood, and color palette."
    )
    image_path: str = Field(
        ...,
        description="The file path where the generated scene image is saved."
    )


class NewProp(BaseModel):
    name: str = Field(
        ...,
        description="The name of the new prop that needs to be generated."
    )
    generation_prompt: str = Field(
        ...,
        description="The detailed prompt for generating the prop image, including appearance, material, size, and distinctive features."
    )
    image_path: str = Field(
        ...,
        description="The file path where the generated prop image is saved."
    )


class KeyframeGeneration(BaseModel):
    generation_prompt: str = Field(
        ...,
        description="Comprehensive prompt for generating the final keyframe, incorporating all visual elements, plot, emotional tone, cinematography, and shot composition."
    )
    image_path: str = Field(
        ...,
        description="The file path where the generated keyframe image is saved."
    )
    reference_image_list: List[str] = Field(
        ...,
        description="List of image file paths to use as visual references for maintaining consistency in character appearance, scene style, and prop design."
    )


class MemoryBank(BaseModel):
    characters: Dict[str, str] = Field(
        default_factory=dict,
        description="Dictionary mapping character names to their reference image file paths."
    )
    scenes: Dict[str, str] = Field(
        default_factory=dict,
        description="Dictionary mapping scene names to their reference image file paths."
    )
    props: Dict[str, str] = Field(
        default_factory=dict,
        description="Dictionary mapping prop names to their reference image file paths."
    )


class Keyframe(BaseModel):
    thinking: str = Field(
        ...,
        description="Chain of thought reasoning process through all steps: analyzing shot requirements, checking memory bank, generating missing elements, preparing references, creating keyframe prompt, and updating memory bank."
    )
    new_character_list: List[NewCharacter] = Field(
        default_factory=list,
        description="List of new characters that were generated for this shot because they didn't exist in the memory bank."
    )
    new_scene: Optional[NewScene] = Field(
        default=None,
        description="The new scene that was generated for this shot if it didn't exist in the memory bank."
    )
    new_prop_list: List[NewProp] = Field(
        default_factory=list,
        description="List of new props that were generated for this shot because they didn't exist in the memory bank."
    )
    keyframe: KeyframeGeneration = Field(
        ...,
        description="The keyframe generation configuration, including the comprehensive prompt and list of reference images for maintaining visual consistency."
    )
    memory_bank: MemoryBank = Field(
        ...,
        description="The updated memory bank containing all characters, scenes, and props (both existing and newly generated) for use in future shots."
    )