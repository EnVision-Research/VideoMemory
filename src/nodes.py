from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain.agents.middleware import ToolRetryMiddleware
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime

from src.state import (
    VideoMemoryState, 
    VideoMemoryContext, 
    Storyboard, 
    MemoryBank,
    Visualization,
)
from src.tools import nano_banana_replicate_tool, keyframe_generation, video_generation

import os
import aiofiles

async def storyboard_node(state: VideoMemoryState, config: RunnableConfig, runtime: Runtime[VideoMemoryContext]):

    ctx = runtime.context
    thread_id = config["configurable"]["thread_id"]
    raw_script = state["messages"][-1].content

    llm = init_chat_model(model=ctx.storyboard_model).with_structured_output(Storyboard)

    human_message =  f"""
        Raw script is:\n{raw_script}\n
        The total number of shots is {ctx.total_shot_number}
    """

    query_messages = [
        SystemMessage(content=ctx.storyboard_prompt),
        HumanMessage(content=human_message)
    ]

    result = await llm.ainvoke(query_messages)
    storyboard = result.model_dump_json(indent=2)

    # save the memory_bank to a file
    os.makedirs(f"output/{thread_id}", exist_ok=True)
    async with aiofiles.open(f"output/{thread_id}/storyboard.json", "w") as f:
        await f.write(storyboard)
    
    return {
        "messages": AIMessage(content=storyboard, name="storyboard_agent"),
        "storyboard": storyboard,
    }

async def memory_node(state: VideoMemoryState, config: RunnableConfig, runtime: Runtime[VideoMemoryContext]):
    ctx = runtime.context
    thread_id = config["configurable"]["thread_id"]
    storyboard_json = state["messages"][-1].content

    memory_agent = create_agent(
        name = "memory_agent", 
        model = ctx.memory_model,
        tools = [nano_banana_replicate_tool],
        system_prompt = ctx.memory_prompt,
        response_format=MemoryBank,
        state_schema=VideoMemoryState,
        context_schema=VideoMemoryContext,
        middleware=[
            ToolRetryMiddleware(
                max_retries=5,
                backoff_factor=2.0,
                initial_delay=1.0,
            ),
        ],
    )

    human_message = f"""
        The base_path is: output/{thread_id}
        Storyboard is:\n{storyboard_json}\n
    """
    query_messages = [
        HumanMessage(content=human_message)
    ]

    result = await memory_agent.ainvoke(
        {"messages": query_messages},
        context=ctx,
        config=config,
    )
    memory_bank = result['structured_response'].model_dump_json(indent=2)

    # save the memory_bank to a file
    os.makedirs(f"output/{thread_id}", exist_ok=True)
    async with aiofiles.open(f"output/{thread_id}/memory_bank.json", "w") as f:
        await f.write(memory_bank)

    return{
        "messages": AIMessage(content=memory_bank, name="memory_agent"),
        "memory_bank": memory_bank,
    }


async def visualization_node(state: VideoMemoryState, config: RunnableConfig, runtime: Runtime[VideoMemoryContext]):
    """
    Visualization Node: Orchestrates keyframe and video generation for each shot.
    
    This node acts as a coordinator that:
    1. Parses storyboard and memory_bank data
    2. For each shot, generates a keyframe using the Keyframe sub-agent
    3. For each shot, generates a video clip using the Video sub-agent
    4. Compiles and saves the final visualization output
    """
    ctx = runtime.context

    visualization_agent = create_agent(
        name="visualization_agent",
        model=ctx.visualization_model,
        tools=[keyframe_generation, video_generation],
        system_prompt=ctx.visualization_prompt,
        state_schema=VideoMemoryState,
        context_schema=VideoMemoryContext,
        middleware=[
            ToolRetryMiddleware(
                max_retries=5,
                backoff_factor=2.0,
                initial_delay=1.0,
            ),
        ],
    )

    query_messages = [HumanMessage(content="Initiate the visual production pipeline for the current storyboard. Coordinate the Keyframe and Video sub-agents to deliver the final visualization, ensuring strict adherence to the two-phase dependency.")]

    result = await visualization_agent.ainvoke(
        {"messages": query_messages, "storyboard": state["storyboard"], "memory_bank": state["memory_bank"]},
        context=ctx,
        config=config,
    )


    return {
        "messages": AIMessage(content=result["messages"][-1].content, name="visualization_agent"),
    }

