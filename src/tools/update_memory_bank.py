import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from langchain.tools import tool
from pydantic import BaseModel, Field, field_validator


logger = logging.getLogger(__name__)


class Asset(BaseModel):
    """Represents a generated visual asset such as a character, scene plate, or prop."""

    name: str = Field(
        ...,
        description="The name of the asset that needs to be generated."
    )
    generation_prompt: str = Field(
        ...,
        description="The detailed prompt for generating the asset image."
    )
    image_path: str = Field(
        ...,
        description="The file path where the generated asset image is saved."
    )
    reference_image_list: Optional[List[str]] = Field(
        default=None,
        description="Optional file paths of reference images used while generating this asset."
    )


class KeyframeImage(BaseModel):
    """Represents the final keyframe output for a shot."""

    shot_number: int = Field(
        ...,
        description="The sequential number of the shot globally across the entire project (e.g., 1, 2, 3, ..., 8), never restarting between acts or scenes."
    )

    generation_prompt: str = Field(
        ...,
        description="The comprehensive prompt used to generate the keyframe."
    )
    image_path: str = Field(
        ...,
        description="The file path where the generated keyframe image is saved."
    )
    reference_image_list: Optional[List[str]] = Field(
        default=None,
        description="The list of file paths for images referenced while generating the keyframe."
    )


class KeyframeRecord(BaseModel):
    """Complete record of one keyframe generation cycle."""

    act: int = Field(
        ...,
        description="Act number for this shot."
    )
    scene: str = Field(
        ...,
        description="Scene heading (INT./EXT. LOCATION - TIME) for this shot."
    )
    shot_number: int = Field(
        ...,
        description="Shot number within the scene."
    )
    global_shot_number: Optional[int] = Field(
        default=None,
        description="Sequential shot number across the entire project, if available."
    )
    character_references: Dict[str, str] = Field(
        default_factory=dict,
        description="All character references used while generating this keyframe."
    )
    scene_references: Dict[str, str] = Field(
        default_factory=dict,
        description="All scene references used while generating this keyframe."
    )
    prop_references: Dict[str, str] = Field(
        default_factory=dict,
        description="All prop references used while generating this keyframe."
    )
    new_character_list: List[Asset] = Field(
        default_factory=list,
        description="Newly generated character assets introduced in this keyframe."
    )
    new_scene: Optional[Asset] = Field(
        default=None,
        description="Newly generated scene plate introduced in this keyframe."
    )
    new_prop_list: List[Asset] = Field(
        default_factory=list,
        description="Newly generated props introduced in this keyframe."
    )
    keyframe: KeyframeImage = Field(
        ...,
        description="The generated keyframe information."
    )

    @property
    def effective_global_shot_number(self) -> Optional[int]:
        """Prefer the provided global shot number when present."""
        return self.global_shot_number


class MemoryBank(BaseModel):
    """Persistent cumulative store for all generated visual references and keyframes."""

    characters: Dict[str, List[Asset]] = Field(
        default_factory=dict,
        description="Mapping of character names to their generated asset history."
    )
    scenes: Dict[str, List[Asset]] = Field(
        default_factory=dict,
        description="Mapping of scene names to their generated asset history."
    )
    props: Dict[str, List[Asset]] = Field(
        default_factory=dict,
        description="Mapping of prop names to their generated asset history."
    )
    keyframes: List[KeyframeRecord] = Field(
        default_factory=list,
        description="Chronological list of every keyframe generation record."
    )

    @field_validator("characters", "scenes", "props", mode="before")
    @classmethod
    def _coerce_asset_dict(cls, value: Optional[Dict[str, object]]) -> Dict[str, List[Asset]]:
        """Allow legacy dictionaries that may only contain file paths."""
        if not value:
            return {}
        coerced: Dict[str, List[Asset]] = {}
        for name, entry in value.items():
            if isinstance(entry, list):
                coerced[name] = [Asset.model_validate(item) for item in entry]
            elif isinstance(entry, dict):
                coerced[name] = [Asset.model_validate(entry)]
            elif isinstance(entry, str):
                coerced[name] = [
                    Asset(
                        name=name,
                        generation_prompt="Legacy entry (prompt unavailable)",
                        image_path=entry,
                        reference_image_list=None,
                    )
                ]
            else:
                raise ValueError(f"Unsupported asset entry for {name}: {entry}")
        return coerced

    @classmethod
    def load(cls, path: Path) -> "MemoryBank":
        if not path.exists():
            return cls()
        with path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
        return cls.model_validate(raw)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(self.model_dump(), handle, ensure_ascii=False, indent=2)

    def _append_asset(self, bucket: Dict[str, List[Asset]], asset: Asset) -> None:
        """Append asset to a given bucket while avoiding duplicate image paths."""
        entries = bucket.setdefault(asset.name, [])
        if all(existing.image_path != asset.image_path for existing in entries):
            entries.append(asset)

    def add_keyframe(self, record: KeyframeRecord) -> None:
        for asset in record.new_character_list:
            self._append_asset(self.characters, asset)
        if record.new_scene:
            self._append_asset(self.scenes, record.new_scene)
        for asset in record.new_prop_list:
            self._append_asset(self.props, asset)
        self.keyframes.append(record)


class UpdateMemoryBankInput(BaseModel):
    base_path: str = Field(
        ...,
        description="Project base path where memory bank data should be stored."
    )
    record: KeyframeRecord = Field(
        ...,
        description="The complete record for the keyframe that has just been generated."
    )


@tool(args_schema=UpdateMemoryBankInput)
def update_memory_bank(base_path: str, record: KeyframeRecord) -> Dict[str, object]:
    """
    Persist memory bank updates after generating a keyframe.

    This appends the new record to the cumulative memory bank, stores a JSON snapshot
    for the current keyframe, and returns useful summary statistics for confirmation.
    """

    base = Path(base_path)
    memory_bank_path = base / "memory_bank.json"

    memory_bank = MemoryBank.load(memory_bank_path)
    memory_bank.add_keyframe(record)
    memory_bank.save(memory_bank_path)

    # Persist a per-keyframe snapshot for easier inspection.
    effective_number = record.effective_global_shot_number
    if effective_number is not None:
        filename = f"{effective_number:01d}.json"
    else:
        filename = f"act{record.act}_shot{record.shot_number}.json"
    keyframe_snapshot_path = base / "keyframes" / filename
    keyframe_snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    with keyframe_snapshot_path.open("w", encoding="utf-8") as handle:
        json.dump(record.model_dump(), handle, ensure_ascii=False, indent=2)

    return {
        "memory_bank_path": str(memory_bank_path),
        "keyframe_snapshot_path": str(keyframe_snapshot_path),
        "total_keyframes": len(memory_bank.keyframes),
        "total_characters": len(memory_bank.characters),
        "total_scenes": len(memory_bank.scenes),
        "total_props": len(memory_bank.props),
    }


# ============================================================================
# FAST MEMORY BANK - SIMPLIFIED STRUCTURE FOR BATCH PROMPT GENERATION
# ============================================================================

class AssetPrompt(BaseModel):
    """Simplified asset with only prompt and path (no actual generation yet)"""
    
    name: str = Field(..., description="Asset name")
    generation_prompt: str = Field(..., description="Prompt for generating the asset")
    image_path: str = Field(..., description="Placeholder path where image will be saved")
    reference_image_list: Optional[List[str]] = Field(default=None, description="Reference images used")


class KeyframePrompt(BaseModel):
    """Simplified keyframe with only prompt and path"""
    
    shot_number: int = Field(..., description="Sequential shot number across entire project")
    generation_prompt: str = Field(..., description="Prompt for generating the keyframe")
    image_path: str = Field(..., description="Placeholder path where keyframe will be saved")
    reference_image_list: Optional[List[str]] = Field(default=None, description="Reference images used")


class ShotRecord(BaseModel):
    """Complete record for one shot - simplified structure"""
    
    shot_number: int = Field(..., description="Sequential shot number")
    act: int = Field(..., description="Act number")
    scene: str = Field(..., description="Scene heading")
    
    # Assets for this shot
    characters: List[AssetPrompt] = Field(default_factory=list, description="Character assets needed")
    scenes: List[AssetPrompt] = Field(default_factory=list, description="Scene assets needed")
    props: List[AssetPrompt] = Field(default_factory=list, description="Prop assets needed")
    
    # Final keyframe
    keyframe: KeyframePrompt = Field(..., description="The final keyframe for this shot")


class MemoryBankFast(BaseModel):
    """Simplified memory bank: list of shot records"""
    
    shots: List[ShotRecord] = Field(default_factory=list, description="All shot records in order")
    
    @classmethod
    def load(cls, path: Path) -> "MemoryBankFast":
        if not path.exists():
            return cls()
        with path.open("r", encoding="utf-8") as f:
            raw = json.load(f)
        return cls.model_validate(raw)
    
    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(self.model_dump(), f, ensure_ascii=False, indent=2)
    
    def get_asset_by_name(self, asset_type: str, name: str) -> Optional[AssetPrompt]:
        """Find latest version of an asset by name"""
        for shot in reversed(self.shots):  # Search from latest
            if asset_type == "character":
                for asset in shot.characters:
                    if asset.name == name:
                        return asset
            elif asset_type == "scene":
                for asset in shot.scenes:
                    if asset.name == name:
                        return asset
            elif asset_type == "prop":
                for asset in shot.props:
                    if asset.name == name:
                        return asset
        return None


class UpdateMemoryBankFastInput(BaseModel):
    """Input schema for fast memory bank update"""
    base_path: str = Field(..., description="Project base path")
    record: ShotRecord = Field(..., description="Shot record to add")


@tool(args_schema=UpdateMemoryBankFastInput)
def update_memory_bank_fast(base_path: str, record: ShotRecord) -> Dict[str, object]:
    """
    Update memory bank with new shot record (prompts only, no actual generation).
    Returns error if update fails - causes agent to halt.
    """
    try:
        base = Path(base_path)
        memory_bank_path = base / "memory_bank.json"
        
        memory_bank = MemoryBankFast.load(memory_bank_path)
        memory_bank.shots.append(record)
        memory_bank.save(memory_bank_path)
        
        logger.info(f"Updated memory bank for shot {record.shot_number}")
        
        return {
            "status": "success",
            "memory_bank_path": str(memory_bank_path),
            "total_shots": len(memory_bank.shots),
            "current_shot": record.shot_number
        }
    except Exception as e:
        logger.error(f"Failed to update memory bank for shot {record.shot_number}: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": f"Failed to update memory bank for shot {record.shot_number}. Processing halted."
        }
