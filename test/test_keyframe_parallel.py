"""
Test keyframe generation combining Supervisor Agent with Parallel Execution.

Architecture:
- Supervisor Agent (with KEYFRAME_SUPERVISOR prompt) analyzes shots and makes decisions
- StateGraph controls parallel execution of character/scene/prop generation
- Sub-agents wrapped as tools for granular generation tasks
- Combines agent intelligence with deterministic parallel workflow
"""

import json
import operator
from typing import Annotated, TypedDict, Literal

from langgraph.graph import StateGraph, START, END, MessagesState
from langchain.agents import create_agent
from langchain.tools import tool
from langchain.chat_models import init_chat_model

from src.tools import nano_banana_replicate_tool, update_memory_bank
from src.prompts import (
    KEYFRAME_SUPERVISOR,
    CHARACTER_SUBAGENT,
    SCENE_SUBAGENT,
    PROP_SUBAGENT,
    KEYFRAME_SUBAGENT
)


# ============================================================================
# Step 1: Define State
# ============================================================================

class KeyframeState(TypedDict):
    """State for keyframe generation workflow."""
    # Input
    storyboard: dict
    base_path: str
    
    # Processing tracking
    current_shot_index: int
    total_shots: int
    all_shots: list
    
    # Current shot processing
    current_shot: dict
    supervisor_decision: str  # Supervisor's analysis and plan
    
    # Parallel execution results (using list with add reducer)
    character_results: Annotated[list, operator.add]
    scene_results: Annotated[list, operator.add]
    prop_results: Annotated[list, operator.add]
    
    # Final results
    keyframe_results: list
    current_keyframe: str


# ============================================================================
# Step 2: Create Sub-Agents
# ============================================================================

def create_sub_agents():
    """Create specialized sub-agents for each generation task."""
    model_name = "deepseek:deepseek-chat"
    
    character_agent = create_agent(
        model=model_name,
        tools=[nano_banana_replicate_tool],
        system_prompt=CHARACTER_SUBAGENT
    )
    
    scene_agent = create_agent(
        model=model_name,
        tools=[nano_banana_replicate_tool],
        system_prompt=SCENE_SUBAGENT
    )
    
    prop_agent = create_agent(
        model=model_name,
        tools=[nano_banana_replicate_tool],
        system_prompt=PROP_SUBAGENT
    )
    
    keyframe_agent = create_agent(
        model=model_name,
        tools=[nano_banana_replicate_tool],
        system_prompt=KEYFRAME_SUBAGENT
    )
    
    return character_agent, scene_agent, prop_agent, keyframe_agent


# ============================================================================
# Step 3: Wrap Sub-Agents as Tools
# ============================================================================

# Create sub-agents globally (will be used by tools)
CHARACTER_AGENT, SCENE_AGENT, PROP_AGENT, KEYFRAME_AGENT = create_sub_agents()


@tool
def generate_characters(request: str) -> str:
    """
    Generate character portraits for a shot.
    
    Args:
        request: Task description including character details, base_path, and shot context.
    
    Returns:
        Generation result with paths and status.
    """
    result = CHARACTER_AGENT.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    return result["messages"][-1].content


@tool
def generate_scene(request: str) -> str:
    """
    Generate scene/environment image for a shot.
    
    Args:
        request: Task description including scene heading, description, base_path.
    
    Returns:
        Generation result with path and status.
    """
    result = SCENE_AGENT.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    return result["messages"][-1].content


@tool
def generate_props(request: str) -> str:
    """
    Generate prop images for a shot.
    
    Args:
        request: Task description including prop details, base_path, and shot context.
    
    Returns:
        Generation result with paths and status.
    """
    result = PROP_AGENT.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    return result["messages"][-1].content


@tool
def composite_keyframe(request: str) -> str:
    """
    Composite final keyframe from generated assets.
    
    Args:
        request: Task description including shot details, reference paths, and output path.
    
    Returns:
        Final keyframe path and status.
    """
    result = KEYFRAME_AGENT.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    return result["messages"][-1].content


# ============================================================================
# Step 4: Create Supervisor Agent
# ============================================================================

def create_supervisor():
    """Create supervisor agent with sub-agent tools."""
    supervisor_tools = [
        generate_characters,
        generate_scene,
        generate_props,
        composite_keyframe,
        update_memory_bank
    ]
    
    supervisor = create_agent(
        model="deepseek:deepseek-chat",
        tools=supervisor_tools,
        system_prompt=KEYFRAME_SUPERVISOR
    )
    
    return supervisor


# ============================================================================
# Step 5: Define Workflow Nodes
# ============================================================================

def supervisor_node(state: KeyframeState) -> dict:
    """
    Supervisor analyzes current shot and creates execution plan.
    """
    shots = state.get("all_shots", [])
    current_idx = state.get("current_shot_index", 0)
    
    if current_idx >= len(shots):
        return {"supervisor_decision": "COMPLETE"}
    
    current_shot = shots[current_idx]
    
    print(f"\n{'='*80}")
    print(f"📋 Supervisor Analyzing Shot {current_idx + 1}/{len(shots)}")
    print(f"{'='*80}\n")
    
    # Prepare analysis request for supervisor
    request = f"""Analyze this shot and determine what needs to be generated:

Base path: {state['base_path']}
Shot #{current_idx + 1}:
{json.dumps(current_shot, indent=2)}

Provide your analysis and plan for generating this shot's assets.
Identify which characters, scenes, and props are needed.
"""
    
    # Get supervisor's analysis (but don't execute tools yet)
    supervisor = create_supervisor()
    response = supervisor.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    
    decision = response["messages"][-1].content
    print(f"📝 Supervisor Decision:\n{decision}\n")
    
    return {
        "current_shot": current_shot,
        "current_shot_index": current_idx + 1,
        "supervisor_decision": decision,
        "character_results": [],
        "scene_results": [],
        "prop_results": [],
        "current_keyframe": ""
    }


def parallel_character_node(state: KeyframeState) -> dict:
    """Execute character generation based on supervisor's plan."""
    print("🎭 [Parallel] Generating characters...")
    
    shot = state["current_shot"]
    characters = shot.get("characters", [])
    
    if not characters:
        print("   No characters needed")
        return {"character_results": ["No characters"]}
    
    request = f"""Base path: {state['base_path']}
Shot: {json.dumps(shot, indent=2)}
Characters to generate: {characters}

Generate required character images."""
    
    result = generate_characters.invoke(request)
    print(f"   ✅ Characters done")
    
    return {"character_results": [result]}


def parallel_scene_node(state: KeyframeState) -> dict:
    """Execute scene generation based on supervisor's plan."""
    print("🌄 [Parallel] Generating scene...")
    
    shot = state["current_shot"]
    scene = shot.get("scene", "")
    
    request = f"""Base path: {state['base_path']}
Scene: {scene}
Description: {shot.get('scene_description', '')}

Generate scene image."""
    
    result = generate_scene.invoke(request)
    print(f"   ✅ Scene done")
    
    return {"scene_results": [result]}


def parallel_prop_node(state: KeyframeState) -> dict:
    """Execute prop generation based on supervisor's plan."""
    print("📦 [Parallel] Generating props...")
    
    shot = state["current_shot"]
    props = shot.get("key_props", [])
    
    if not props:
        print("   No props needed")
        return {"prop_results": ["No props"]}
    
    request = f"""Base path: {state['base_path']}
Shot: {json.dumps(shot, indent=2)}
Props to generate: {props}

Generate required prop images."""
    
    result = generate_props.invoke(request)
    print(f"   ✅ Props done")
    
    return {"prop_results": [result]}


def keyframe_compositor_node(state: KeyframeState) -> dict:
    """Composite final keyframe after parallel generation completes."""
    print("🎬 [Sequential] Compositing keyframe...")
    
    shot_num = state["current_shot_index"]
    
    request = f"""Composite final keyframe for shot #{shot_num}:

Base path: {state['base_path']}
Output: {state['base_path']}/keyframes/{shot_num}.png

Shot: {json.dumps(state['current_shot'], indent=2)}

Available assets:
- Characters: {state['character_results']}
- Scene: {state['scene_results']}
- Props: {state['prop_results']}

Create final composited keyframe."""
    
    result = composite_keyframe.invoke(request)
    
    keyframe_results = state.get("keyframe_results", [])
    keyframe_results.append(result)
    
    print(f"   ✅ Keyframe complete\n")
    
    return {
        "current_keyframe": result,
        "keyframe_results": keyframe_results
    }


# ============================================================================
# Step 6: Helper Functions
# ============================================================================

def flatten_shots(storyboard: dict) -> list:
    """Flatten storyboard structure into list of shots with context."""
    all_shots = []
    
    for act in storyboard.get("acts", []):
        act_num = act.get("act", "N/A")
        
        for scene in act.get("scenes", []):
            scene_heading = scene.get("scene", "")
            scene_desc = scene.get("scene_description", "")
            
            for shot in scene.get("shots", []):
                shot_with_context = {
                    **shot,
                    "act": act_num,
                    "scene": scene_heading,
                    "scene_description": scene_desc
                }
                all_shots.append(shot_with_context)
    
    return all_shots


def should_continue(state: KeyframeState) -> Literal["supervisor", "end"]:
    """Decide whether to process next shot or end."""
    if state.get("supervisor_decision") == "COMPLETE":
        return "end"
    
    current_idx = state.get("current_shot_index", 0)
    total = state.get("total_shots", 0)
    
    return "supervisor" if current_idx < total else "end"


# ============================================================================
# Step 7: Build Graph
# ============================================================================

def create_keyframe_graph():
    """
    Create hybrid graph combining supervisor intelligence with parallel execution:
    
              START
                |
                v
          [Supervisor] ←──┐
           (analyzes)      │
                |          │
             ┌──┴──┐       │
             │  │  │       │ (loop)
             v  v  v       │
            [C][S][P]      │ (parallel generation)
             │  │  │       │
             └──┬──┘       │
                |          │
                v          │
           [Keyframe] ─────┘
                |
                v
               END
    """
    workflow = StateGraph(KeyframeState)
    
    # Add nodes
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("character", parallel_character_node)
    workflow.add_node("scene", parallel_scene_node)
    workflow.add_node("prop", parallel_prop_node)
    workflow.add_node("keyframe", keyframe_compositor_node)
    
    # Start with supervisor
    workflow.add_edge(START, "supervisor")
    
    # Fan-out: Supervisor -> parallel nodes
    workflow.add_edge("supervisor", "character")
    workflow.add_edge("supervisor", "scene")
    workflow.add_edge("supervisor", "prop")
    
    # Fan-in: parallel nodes -> keyframe
    workflow.add_edge("character", "keyframe")
    workflow.add_edge("scene", "keyframe")
    workflow.add_edge("prop", "keyframe")
    
    # Conditional: back to supervisor or end
    workflow.add_conditional_edges(
        "keyframe",
        should_continue,
        {
            "supervisor": "supervisor",
            "end": END
        }
    )
    
    return workflow.compile()


# ============================================================================
# Step 8: Test Execution
# ============================================================================

def test_keyframe_parallel():
    """Test hybrid supervisor + parallel execution."""
    
    # Load storyboard
    thread_id = "OneLife"
    base_path = f"output/{thread_id}"
    storyboard_path = f"{base_path}/storyboard.json"
    
    with open(storyboard_path, "r") as f:
        storyboard = json.load(f)
    
    # Flatten shots
    all_shots = flatten_shots(storyboard)
    
    print("=" * 80)
    print(f"🎬 Keyframe Generation Pipeline")
    print(f"   Architecture: Supervisor Agent + Parallel Execution")
    print(f"   Project: {thread_id}")
    print(f"   Total Shots: {len(all_shots)}")
    print("=" * 80)
    
    # Create graph
    graph = create_keyframe_graph()
    
    # Initial state
    initial_state = {
        "storyboard": storyboard,
        "base_path": base_path,
        "current_shot_index": 0,
        "total_shots": len(all_shots),
        "all_shots": all_shots,
        "current_shot": {},
        "supervisor_decision": "",
        "character_results": [],
        "scene_results": [],
        "prop_results": [],
        "keyframe_results": [],
        "current_keyframe": ""
    }
    
    # Run graph
    final_state = graph.invoke(initial_state)
    
    # Print summary
    print("=" * 80)
    print("✅ Pipeline Complete!")
    print("=" * 80)
    print(f"Total keyframes: {len(final_state.get('keyframe_results', []))}")


if __name__ == "__main__":
    test_keyframe_parallel()
