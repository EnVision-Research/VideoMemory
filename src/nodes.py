from dotenv import load_dotenv
load_dotenv()

from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain.agents import create_agent

from src.llm import init_llm_model
from src.configuration import Configuration
from src.state import AgentState
from src.schema import Script, Storyboard, MemoryBank, Cinetography
from src.tools import nano_banana_replicate_tool, wan22_i2v_tool, concat_videos_tool
from src.utils import retry_with_backoff

import os
import json
import aiofiles
import asyncio
import logging
from collections import deque
from time import time

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate limiter to control API call frequency.
    Ensures no more than max_calls within time_window seconds.
    """
    def __init__(self, max_calls: int, time_window: float):
        self.max_calls = max_calls
        self.time_window = time_window  # in seconds
        self.call_times = deque()
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """
        Wait if necessary to respect rate limit before making a call.
        """
        async with self.lock:
            current_time = time()
            
            # Remove timestamps outside the time window
            while self.call_times and current_time - self.call_times[0] >= self.time_window:
                self.call_times.popleft()
            
            # If we've hit the limit, wait until we can make another call
            if len(self.call_times) >= self.max_calls:
                sleep_time = self.time_window - (current_time - self.call_times[0])
                if sleep_time > 0:
                    logger.info(f"Rate limit reached. Waiting {sleep_time:.2f} seconds...")
                    await asyncio.sleep(sleep_time)
                    # After sleeping, remove old timestamps again
                    current_time = time()
                    while self.call_times and current_time - self.call_times[0] >= self.time_window:
                        self.call_times.popleft()
            
            # Record this call
            self.call_times.append(time())


async def screenwriter_node(state: AgentState, config: RunnableConfig) -> AgentState:

    thread_id = config.get("configurable", {}).get("thread_id")
    cfgs = Configuration.from_runnable_config(config)

    raw_script = state["messages"][-1].content
    llm = init_llm_model(model = cfgs.screenwriter_model).with_structured_output(Script)

    query_messages = [
        SystemMessage(content=cfgs.screenwriter_prompt),
        HumanMessage(content=f"Raw script is:\n{raw_script}")
    ]

    result = await llm.ainvoke(query_messages)
    script = result.model_dump_json(indent=2)

    # save the script to a file
    os.makedirs(f"output/{thread_id}", exist_ok=True)
    async with aiofiles.open(f"output/{thread_id}/script.json", "w") as f:
        await f.write(script)


    return {
        "messages": AIMessage(content=script, name="screenwriter"),
        "script": script,
    }

async def storyboard_node(state: AgentState, config: RunnableConfig) -> AgentState:
    thread_id = config.get("configurable", {}).get("thread_id")
    cfgs = Configuration.from_runnable_config(config)

    llm = init_llm_model(
        model = cfgs.storyboard_model
        ).with_structured_output(Storyboard)

    query_messages = [
        SystemMessage(content=cfgs.storyboard_prompt),
        HumanMessage(content=f"The script is:\n{state['script']}"),
    ]

    result = await llm.ainvoke(query_messages)
    storyboard = result.model_dump_json(indent=2)

    # save the storyboard to a file
    os.makedirs(f"output/{thread_id}", exist_ok=True)
    async with aiofiles.open(f"output/{thread_id}/storyboard.json", "w") as f:
        await f.write(storyboard)

    return {
        "messages": AIMessage(content=storyboard, name="storyboard"),
        "storyboard": storyboard,
    }

async def keyframe_node(state: AgentState, config: RunnableConfig) -> AgentState:
    thread_id = config.get("configurable", {}).get("thread_id")
    cfgs = Configuration.from_runnable_config(config)

    llm = init_llm_model(
        model=cfgs.keyframe_model
        ).with_structured_output(MemoryBank)
    
    # Prepare messages
    query_messages = [
        SystemMessage(content=cfgs.keyframe_prompt),
        HumanMessage(content=f"""Base path: f"output/{thread_id}"

Process this storyboard:

{json.dumps(state['storyboard'], indent=2)}""")
    ]
    
    
    resp = await llm.ainvoke(query_messages)
    memory_bank = resp.model_dump_json(indent=2)

    # save the memory_bank to a file
    os.makedirs(f"output/{thread_id}", exist_ok=True)
    async with aiofiles.open(f"output/{thread_id}/memory_bank.json", "w") as f:
        await f.write(memory_bank)

    return {
        "messages": AIMessage(content=memory_bank, name="keyframe"),
        "memory_bank": resp.model_dump(),
    }


async def keyframe_generation_node(state: AgentState, config: RunnableConfig) -> AgentState:

    memory_bank = state['memory_bank']
    
    generated_asset_paths: set[str] = set()
    generated_keyframes: list[str] = []
    
    # Create rate limiter for image generation API calls
    # Limit to calls per minute to avoid overwhelming the API
    rate_limiter = RateLimiter(max_calls=4, time_window=60.0)

    async def generate_image(payload: dict) -> str:
        """Run the nano banana tool in a worker thread with timeout."""
        try:
            # Acquire rate limiter before making API call
            await rate_limiter.acquire()
            
            # Add timeout for image generation (5 minutes)
            return await asyncio.wait_for(
                asyncio.to_thread(nano_banana_replicate_tool.invoke, payload),
                timeout=300.0  # 5 minutes
            )
        except asyncio.TimeoutError:
            logger.error(f"Image generation timed out for prompt: {payload.get('prompt', 'Unknown')[:100]}...")
            raise

    async def generate_asset(asset, shot: int, asset_type: str) -> str:
        """Generate an individual asset if it has not been created already."""
        save_path = asset["image_path"]
        if save_path in generated_asset_paths or os.path.exists(save_path):
            logger.info(
                "Skipping existing %s asset for shot %s: %s",
                asset_type,
                shot,
                save_path,
            )
            generated_asset_paths.add(save_path)
            return save_path

        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        logger.info(
            "Generating %s asset for shot %s: %s",
            asset_type,
            shot,
            asset['name'],
        )
        payload = {
            "prompt": asset["generation_prompt"],
            "aspect_ratio": asset["aspect_ratio"],
            "save_path": save_path,
            "images": asset["reference_image_list"] or None,
        }
        
        # Add retry logic for asset generation using generic retry function
        async def generate_asset_with_retry():
            result_path = await generate_image(payload)
            generated_asset_paths.add(result_path)
            logger.info(
                "✓ Generated %s asset for shot %s at %s",
                asset_type,
                shot,
                result_path,
            )
            return result_path
        
        return await retry_with_backoff(
            operation_name=f"{asset_type} asset generation for shot {shot}",
            max_retries=2,
            initial_delay=5.0,
            operation_func=generate_asset_with_retry
        )

    async def generate_keyframe_image(keyframe, shot: int) -> str:
        """Generate the keyframe image after all dependent assets exist."""
        save_path = keyframe["image_path"]
        if os.path.exists(save_path):
            logger.info("Skipping existing keyframe for shot %s: %s", shot, save_path)
            return save_path

        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        missing_refs = [
            ref for ref in keyframe['reference_image_list'] if not os.path.exists(ref)
        ]
        if missing_refs:
            logger.warning(
                "Shot %s keyframe references missing files: %s",
                shot,
                ", ".join(missing_refs),
            )

        logger.info("Generating keyframe for shot %s at %s", shot, save_path)
        payload = {
            "prompt": keyframe['generation_prompt'],
            "aspect_ratio": keyframe['aspect_ratio'],
            "save_path": save_path,
            "images": keyframe['reference_image_list'],
        }
        
        # Add retry logic for keyframe generation using generic retry function
        async def generate_keyframe_with_retry():
            result_path = await generate_image(payload)
            logger.info("✓ Generated keyframe for shot %s at %s", shot, result_path)
            return result_path
        
        return await retry_with_backoff(
            operation_name=f"Keyframe generation for shot {shot}",
            max_retries=2,
            initial_delay=5.0,
            operation_func=generate_keyframe_with_retry
        )

    for shot in memory_bank['shots']:
        shot_num = shot['shot']
        total_shots = len(memory_bank['shots'])
        
        logger.info(f"🚀 Processing shot {shot_num}/{total_shots}")
        
        shot_assets = [
            ("character", asset) for asset in shot['characters']
        ] + [
            ("scene", asset) for asset in shot['scenes']
        ] + [
            ("prop", asset) for asset in shot['props']
        ]

        logger.info(f"📦 Generating {len(shot_assets)} assets for shot {shot_num}")
        
        asset_tasks = [
            asyncio.create_task(generate_asset(asset, shot_num, asset_type))
            for asset_type, asset in shot_assets
        ]

        if asset_tasks:
            await asyncio.gather(*asset_tasks)

        logger.info(f"🎨 Generating keyframe for shot {shot_num}")
        keyframe_path = await generate_keyframe_image(shot['keyframe'], shot_num)
        generated_keyframes.append(keyframe_path)
        
        logger.info(f"✅ Completed shot {shot_num}/{total_shots}")

    message = (
        f"🎉 Successfully generated assets and keyframes for {len(memory_bank['shots'])} shots. "
        f"Keyframes saved to: {', '.join(generated_keyframes)}"
    )

    return {
        "messages": AIMessage(content=message, name="keyframe_generation"),
    }


async def generate_and_concat_videos(shots: list, thread_id: str) -> str:
    """
    Generate videos from shots in parallel and concatenate them.
    
    Args:
        shots: List of shot objects containing generation parameters
        thread_id: Thread ID for output path organization
        
    Returns:
        Path to the final concatenated video
    """
    logger.info(f"Starting parallel video generation for {len(shots)} shots...")
    
    # Create rate limiter: 4 calls per 60 seconds (1 minute)
    rate_limiter = RateLimiter(max_calls=2, time_window=60.0)
    
    # Generate videos in parallel using asyncio.to_thread
    async def generate_video_async(shot_data: dict, shot_index: int) -> str:
        """Async wrapper for wan22_i2v_tool with rate limiting"""
        try:
            # Acquire rate limiter before making the call
            await rate_limiter.acquire()
            logger.info(f"Begin generating video for shot...")

            result = await asyncio.to_thread(
                wan22_i2v_tool.invoke,
                {
                    "prompt": shot_data["generation_prompt"],
                    "image_path": shot_data["image_path"],
                    "save_path": shot_data["save_path"],
                    "negative_prompt": shot_data.get("negative_prompt"),
                    "image_size": "1280x720",
                }
            )
            logger.info(f"✓ Video {shot_index + 1}/{len(shots)} completed: {result}")
            return result
        except Exception as e:
            logger.error(f"✗ Video {shot_index + 1}/{len(shots)} failed: {str(e)}")
            raise
    
    # Create tasks for all shots
    video_tasks = [
        generate_video_async(shot.model_dump(), idx) 
        for idx, shot in enumerate(shots)
    ]
    
    # Execute all tasks in parallel and gather results
    video_paths = await asyncio.gather(*video_tasks)
    
    logger.info(f"All {len(video_paths)} videos generated successfully")
    logger.info("Concatenating videos...")
    
    # Concatenate all videos into final output
    final_video_path = f"output/{thread_id}/final_video.mp4"
    concat_result = await asyncio.to_thread(
        concat_videos_tool.invoke,
        {
            "video_paths": video_paths,
            "output_path": final_video_path
        }
    )
    
    logger.info(f"✓ Final video saved to: {concat_result}")
    return concat_result


async def cinetography_node(state: AgentState, config: RunnableConfig) -> AgentState:
    
    thread_id = config.get("configurable", {}).get("thread_id")
    cfgs = Configuration.from_runnable_config(config)

    llm = init_llm_model(
        model = cfgs.cinetography_model
        ).with_structured_output(Cinetography)

    # Extract keyframe contents from memory bank (excluding index 0)
    memory_bank = json.loads(state['memory_bank']) if isinstance(state['memory_bank'], str) else state['memory_bank']
    keyframes_content = [kf['keyframe'] for kf in memory_bank.get('keyframes', [])]
    keyframes_json = json.dumps(keyframes_content, indent=2)

    query = f"""
The thread id is:\n {thread_id}
The storyboard is:\n {state['storyboard']}
The keyframes history is:\n {keyframes_json}
"""
    
    query_messages = [
        SystemMessage(content=cfgs.cinetography_prompt),
        HumanMessage(content=query),
    ]

    resp = await llm.ainvoke(query_messages)
    shots = resp.shots
    
    # Save cinetography shots configuration to file
    os.makedirs(f"output/{thread_id}", exist_ok=True)
    shots_json = json.dumps([shot.model_dump() for shot in shots], indent=2)
    async with aiofiles.open(f"output/{thread_id}/cinetography.json", "w") as f:
        await f.write(shots_json)
    
    # Generate and concatenate videos
    # final_video = await generate_and_concat_videos(shots, thread_id)
    
    return {
        "messages": AIMessage(
            content=f"Video generation completed.", 
            name="cinetography"
        ),
    }
