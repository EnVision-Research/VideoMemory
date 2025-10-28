import os
import logging
from pydantic import BaseModel, Field
from typing import List
from langchain.tools import tool
from moviepy import VideoFileClip, concatenate_videoclips

logger = logging.getLogger(__name__)


class ConcatVideosToolInput(BaseModel):
    video_paths: List[str] = Field(
        ..., description="List of video file paths to concatenate in order"
    )
    output_path: str = Field(
        ..., description="Output file path for the concatenated video"
    )


def _concat_videos_moviepy(video_paths: List[str], output_path: str) -> str:
    """
    Concatenate multiple videos using moviepy.
    
    Args:
        video_paths: List of video file paths to concatenate in order
        output_path: Output file path for the concatenated video
        
    Returns:
        str: The output path where the concatenated video is saved
    """
    if not video_paths:
        raise ValueError("No video files provided to concatenate")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    logger.info(f"Loading {len(video_paths)} video files for concatenation...")
    
    try:
        # Load all video clips
        clips = []
        for i, video_path in enumerate(video_paths):
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file not found: {video_path}")
            
            logger.info(f"Loading video {i+1}/{len(video_paths)}: {video_path}")
            clip = VideoFileClip(video_path)
            clips.append(clip)
        
        logger.info(f"All videos loaded. Starting concatenation...")
        
        # Concatenate clips
        final_clip = concatenate_videoclips(clips)
        
        logger.info(f"Writing concatenated video to: {output_path}")
        
        # Write the output video
        final_clip.write_videofile(
            output_path,
            verbose=False,
            logger=None,  # Suppress moviepy's verbose logging
        )
        
        # Close all clips to free up resources
        final_clip.close()
        for clip in clips:
            clip.close()
        
        logger.info(f"Video concatenation completed successfully: {output_path}")
        
    except Exception as e:
        logger.error(f"Video concatenation failed: {str(e)}")
        raise Exception(f"Failed to concatenate videos: {str(e)}")
    
    return output_path


@tool(args_schema=ConcatVideosToolInput)
def concat_videos_tool(
    video_paths: List[str],
    output_path: str,
) -> str:
    """
    Concatenate multiple video files in order using moviepy.
    Videos must have compatible formats (same codec, resolution, etc.).
    
    Args:
        video_paths: List of video file paths to concatenate in order
        output_path: Output file path for the concatenated video
        
    Returns:
        str: The local path where the concatenated video is saved
    """
    return _concat_videos_moviepy(video_paths, output_path)


if __name__ == "__main__":
    # Example usage
    concat_videos_tool.invoke(
        {
            "video_paths": [
                "output/OneLife/videos/shot_1.mp4",
                "output/OneLife/videos/shot_2.mp4",
                "output/OneLife/videos/shot_3.mp4",
            ],
            "output_path": "output/OneLife/final_video.mp4"
        }
    )
