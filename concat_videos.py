#!/usr/bin/env python3
"""
Script to concatenate shot videos in each case folder.
Outputs two versions: with audio and without audio.
"""

import os
import subprocess
import tempfile
from pathlib import Path


def find_video_folder(case_path: Path) -> Path | None:
    """Find the video folder (either 'videos' or 'video')."""
    for name in ["videos", "video"]:
        folder = case_path / name
        if folder.exists() and folder.is_dir():
            return folder
    return None


def get_shot_files(video_folder: Path) -> list[Path]:
    """Get all shot_XX.mp4 files sorted by number."""
    shot_files = []
    for f in video_folder.iterdir():
        if f.is_file() and f.suffix == ".mp4" and f.stem.startswith("shot_"):
            shot_files.append(f)
    # Sort by shot number
    shot_files.sort(key=lambda x: int(x.stem.split("_")[1]))
    return shot_files


def concat_videos(shot_files: list[Path], output_path: Path, with_audio: bool = True) -> bool:
    """Concatenate videos using ffmpeg."""
    if not shot_files:
        return False

    # Create a temporary file list for ffmpeg concat
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        for shot in shot_files:
            # Escape single quotes in path
            escaped_path = str(shot.absolute()).replace("'", "'\\''")
            f.write(f"file '{escaped_path}'\n")
        list_file = f.name

    try:
        # Build ffmpeg command
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output
            "-f", "concat",
            "-safe", "0",
            "-i", list_file,
        ]

        if with_audio:
            # Copy both video and audio streams
            cmd.extend(["-c", "copy"])
        else:
            # Copy video, remove audio
            cmd.extend(["-c:v", "copy", "-an"])

        cmd.append(str(output_path))

        # Run ffmpeg
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"  Error: {result.stderr}")
            return False
        return True

    finally:
        # Clean up temp file
        os.unlink(list_file)


def process_case(case_path: Path) -> None:
    """Process a single case folder."""
    case_name = case_path.name
    print(f"\nProcessing case {case_name}...")

    video_folder = find_video_folder(case_path)
    if not video_folder:
        print(f"  No video folder found in case {case_name}")
        return

    shot_files = get_shot_files(video_folder)
    if not shot_files:
        print(f"  No shot files found in {video_folder}")
        return

    print(f"  Found {len(shot_files)} shots: {[f.name for f in shot_files]}")

    # Output paths
    output_with_audio = case_path / f"case_{case_name}_with_audio.mp4"
    output_no_audio = case_path / f"case_{case_name}_no_audio.mp4"

    # Concatenate with audio
    print(f"  Creating version with audio...")
    if concat_videos(shot_files, output_with_audio, with_audio=True):
        print(f"  ✓ Saved: {output_with_audio.name}")
    else:
        print(f"  ✗ Failed to create with-audio version")

    # Concatenate without audio
    print(f"  Creating version without audio...")
    if concat_videos(shot_files, output_no_audio, with_audio=False):
        print(f"  ✓ Saved: {output_no_audio.name}")
    else:
        print(f"  ✗ Failed to create no-audio version")


def main():
    """Main entry point."""
    output_dir = Path(__file__).parent / "output"

    if not output_dir.exists():
        print(f"Output directory not found: {output_dir}")
        return

    # Get all case folders (numeric folders)
    case_folders = []
    for item in output_dir.iterdir():
        if item.is_dir() and item.name.isdigit():
            case_folders.append(item)

    # Sort by case number
    case_folders.sort(key=lambda x: int(x.name))

    print(f"Found {len(case_folders)} case folders: {[f.name for f in case_folders]}")

    for case_folder in case_folders:
        process_case(case_folder)

    print("\nDone!")


if __name__ == "__main__":
    main()

