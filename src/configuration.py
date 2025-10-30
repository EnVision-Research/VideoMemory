import os
from pydantic import BaseModel, Field
from typing import Any, Optional
from langchain_core.runnables import RunnableConfig


from src.prompts import SCREENWRITER, STORYBOARD, KEYFRAME, CINETOGRAPHY

class Configuration(BaseModel):

    screenwriter_model: str = Field(
        default="google_genai:gemini-2.5-pro",
        metadata={"description": "The model to use for the screenwriter agent."}
    )
    screenwriter_prompt: str = Field(
        default=SCREENWRITER,
        metadata={"description": "The prompt to guide the screenwriter agent."}
    )


    storyboard_model: str = Field(
        default="google_genai:gemini-2.5-pro",
        metadata={"description": "The model to use for the storyboard agent."}
    )
    storyboard_prompt: str = Field(
        default=STORYBOARD,
        metadata={"description": "The prompt to guide the storyboard agent."}
    )

    keyframe_model: str = Field(
        default="google_genai:gemini-2.5-pro",
        metadata={"description": "The model to use for the keyframe agent."}
    )
    keyframe_prompt: str = Field(
        default=KEYFRAME,
        metadata={"description": "The prompt to guide the keyframe agent."}
    )

    cinetography_model: str = Field(
        default="google_genai:gemini-2.5-pro",
        metadata={"description": "The model to use for the cinetography agent."}
    )
    cinetography_prompt: str = Field(
        default=CINETOGRAPHY,
        metadata={"description": "The prompt to guide the cinetography agent."}
    )

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "Configuration":
        """Create a Configuration instance from a RunnableConfig."""
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )

        # Get raw values from environment or config
        raw_values: dict[str, Any] = {
            name: os.environ.get(name.upper(), configurable.get(name))
            for name in cls.model_fields.keys()
        }

        # Filter out None values
        values = {k: v for k, v in raw_values.items() if v is not None}

        return cls(**values)