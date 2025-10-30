from langgraph.graph import StateGraph, START, END

from src.nodes import screenwriter_node, storyboard_node, keyframe_node, cinetography_node, keyframe_generation_node
from src.state import AgentState
from src.configuration import Configuration

# video memory graph
builder = StateGraph(AgentState, config_schema=Configuration)

builder.add_node("screenwriter", screenwriter_node)
builder.add_node("storyboard", storyboard_node)
builder.add_node("keyframe", keyframe_node)
builder.add_node("keyframe_generation", keyframe_generation_node)
builder.add_node("cinetography", cinetography_node)

builder.add_edge(START, "screenwriter")
builder.add_edge("screenwriter", "storyboard")
builder.add_edge("storyboard", "keyframe")
builder.add_edge("keyframe", "keyframe_generation")
builder.add_edge("keyframe_generation", END)

video_memory_graph = builder.compile()

# screenwriter and storyboard graph
builder = StateGraph(AgentState, config_schema=Configuration)

# Add nodes
builder.add_node("screenwriter", screenwriter_node)
builder.add_node("storyboard", storyboard_node)
builder.add_node("keyframe", keyframe_node)

# Build linear flow: START → screenwriter → storyboard → keyframe → END
builder.add_edge(START, "screenwriter")
builder.add_edge("screenwriter", "storyboard")
builder.add_edge("storyboard", "keyframe")
builder.add_edge("keyframe", END)

# Compile the graph
screenwriter_storyboard_keyframe_graph = builder.compile()

# keyframe graph 
builder = StateGraph(AgentState, config_schema=Configuration)

builder.add_node("keyframe", keyframe_node)

builder.add_edge(START, "keyframe")
builder.add_edge("keyframe", END)

keyframe_graph = builder.compile()


# keyframe generation graph
builder = StateGraph(AgentState, config_schema=Configuration)

builder.add_node("keyframe_generation", keyframe_generation_node)

builder.add_edge(START, "keyframe_generation")
builder.add_edge("keyframe_generation", END)

keyframe_generation_graph = builder.compile()

# cinetography graph
builder = StateGraph(AgentState, config_schema=Configuration)

# Add nodes
builder.add_node("cinetography", cinetography_node)

# Build linear flow: START → cinetography → END
builder.add_edge(START, "cinetography")
builder.add_edge("cinetography", END)

# Compile the graph
cinetography_graph = builder.compile()


