from dotenv import load_dotenv
load_dotenv()

from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain.agents import create_agent

from src.llm import init_llm_model
from src.configuration import Configuration
from src.state import AgentState
from src.schema import Script, Storyboard, Cinetography
from src.tools.nano_banana import nano_banana_replicate_tool
from src.tools.Wan22_I2V_A14B import wan22_i2v_tool
from src.tools.concat_videos import concat_videos_tool

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
        HumanMessage(content=f"Script is:\n{state['script']}"),
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

    agent = create_agent(
        model = cfgs.keyframe_model,
        tools=[nano_banana_replicate_tool],
        system_prompt=cfgs.keyframe_prompt,
    )

    query = f"""
The base path is:\n "output/{thread_id}/"
The storyboard is:\n {state['storyboard']}
"""

    query_messages = [
        SystemMessage(content=cfgs.keyframe_prompt),
        HumanMessage(content=query),
    ]

    resp = agent.invoke(query_messages)


    return {
        "messages": HumanMessage(content=resp.keyframe.model_dump_json(indent=2)),
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
    rate_limiter = RateLimiter(max_calls=4, time_window=60.0)
    
    # Generate videos in parallel using asyncio.to_thread
    async def generate_video_async(shot_data: dict, shot_index: int) -> str:
        """Async wrapper for wan22_i2v_tool with rate limiting"""
        logger.info(f"Begin generating video for shot...")
        try:
            # Acquire rate limiter before making the call
            await rate_limiter.acquire()
            
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
    final_video = await generate_and_concat_videos(shots, thread_id)
    
    return {
        "messages": AIMessage(
            content=f"Video generation completed. Final video: {final_video}", 
            name="cinetography"
        ),
        "final_video": final_video,
    }