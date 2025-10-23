from dotenv import load_dotenv
load_dotenv()

from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain.agents import create_agent

from src.llm import init_llm_model
from src.configuration import Configuration
from src.state import AgentState
from src.schema import Script, Storyboard
from src.tools.nano_banana import nano_banana_replicate_tool

import os
import aiofiles
import logging
logger = logging.getLogger(__name__)


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
        "memory_bank": resp.memory_bank.model_dump_json(indent=2),
    }