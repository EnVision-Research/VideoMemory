from langgraph.graph import StateGraph, START, END

from src.state import VideoMemoryState, VideoMemoryContext
from src.nodes import storyboard_node, memory_node, visualization_node

# storyboard graph
builder = StateGraph(state_schema = VideoMemoryState, context_schema = VideoMemoryContext)
# Add nodes
builder.add_node("storyboard", storyboard_node)
# Build linear flow: START → storyboard → END
builder.add_edge(START, "storyboard")
builder.add_edge("storyboard", END)
# Compile the graph
storyboard_graph = builder.compile()

# memory graph
builder = StateGraph(state_schema = VideoMemoryState, context_schema = VideoMemoryContext)
# Add nodes
builder.add_node("memory", memory_node) 
# Build linear flow: START → memory → END
builder.add_edge(START, "memory")
builder.add_edge("memory", END)
# Compile the graph
memory_graph = builder.compile()

# visualization graph
builder = StateGraph(state_schema = VideoMemoryState, context_schema = VideoMemoryContext)
# Add nodes
builder.add_node("visualization", visualization_node)
# Build linear flow: START → visualization → END
builder.add_edge(START, "visualization")
builder.add_edge("visualization", END)
# Compile the graph
visualization_graph = builder.compile()

# video memory graph
builder = StateGraph(state_schema = VideoMemoryState, context_schema = VideoMemoryContext)
# Add nodes
builder.add_node("storyboard", storyboard_node)
builder.add_node("memory", memory_node)
builder.add_node("visualization", visualization_node)
# Build linear flow: START → storyboard → memory → visualization → END
builder.add_edge(START, "storyboard")
builder.add_edge("storyboard", "memory")
builder.add_edge("memory", "visualization")
builder.add_edge("visualization", END)

# Compile the graph
video_memory_graph = builder.compile()