from langchain.agents import create_agent
from langchain.agents.middleware import ToolRetryMiddleware
from langchain.tools import tool
import replicate.exceptions

from src.prompts import (
    KEYFRAME_SUPERVISOR, 
    CHARACTER_SUBAGENT, 
    SCENE_SUBAGENT, 
    PROP_SUBAGENT, 
    KEYFRAME_SUBAGENT
)
from src.tools import (
    nano_banana_replicate_tool,
    update_memory_bank
)

thread_id = "Harry"
base_path = f"output/{thread_id}"
storyboard_path = f"{base_path}/storyboard.json"

with open(storyboard_path, "r") as f:
    storyboard = f.read()


def test_keyframe_supervisor():
    """
    Test keyframe generation using the official LangChain supervisor pattern.
    
    Architecture:
    - Supervisor agent coordinates specialized sub-agents
    - Each sub-agent is wrapped as a tool
    - Sub-agents handle specific domains (character, scene, prop, keyframe)
    """

    # Model identifier for all agents
    model_name = "deepseek:deepseek-chat"
    
    # ========================================================================
    # Step 0: Configure retry middleware for Replicate API calls
    # ========================================================================
    
    # Create retry middleware to handle transient Replicate errors (500, network issues, etc.)
    retry_middleware = ToolRetryMiddleware(
        max_retries=3,              # Retry up to 3 times after initial attempt
        backoff_factor=2.0,         # Exponential backoff: 1s, 2s, 4s
        initial_delay=1.0,          # Start with 1 second delay
        max_delay=60.0,             # Cap delays at 60 seconds
        jitter=True,                # Add random jitter to avoid thundering herd
        retry_on=(                  # Only retry on specific exceptions
            replicate.exceptions.ReplicateError,  # Replicate API errors (including 500)
            ConnectionError,                       # Network connection errors
            TimeoutError,                          # Timeout errors
        ),
    )
    
    # ========================================================================
    # Step 1: Create specialized sub-agents with retry middleware
    # ========================================================================
    
    character_agent = create_agent(
        model=model_name,
        tools=[nano_banana_replicate_tool],
        system_prompt=CHARACTER_SUBAGENT,
        middleware=[retry_middleware]
    )
    
    scene_agent = create_agent(
        model=model_name,
        tools=[nano_banana_replicate_tool],
        system_prompt=SCENE_SUBAGENT,
        middleware=[retry_middleware]
    )
    
    prop_agent = create_agent(
        model=model_name,
        tools=[nano_banana_replicate_tool],
        system_prompt=PROP_SUBAGENT,
        middleware=[retry_middleware]
    )
    
    keyframe_agent = create_agent(
        model=model_name,
        tools=[nano_banana_replicate_tool],
        system_prompt=KEYFRAME_SUBAGENT,
        middleware=[retry_middleware]
    )
    
    # ========================================================================
    # Step 2: Wrap sub-agents as tools for the supervisor
    # ========================================================================
    
    @tool
    def character_generator(request: str) -> str:
        """
        Generate versioned character portraits with consistent identity across aging.
        
        Use this tool when you need to:
        - Create a new base character portrait
        - Generate a new version of an existing character (showing aging/different appearance)
        - Maintain character identity across timeline
        
        Input format in request string:
            - character_name: Name of the character
            - current_state: Age, clothing, and appearance details
            - base_path: Base directory for storage
            - reference_image_path: (Optional) Path to existing character version for identity consistency
            - global_visual_style: Overall visual style (e.g., "photorealistic", "anime style")
        
        Returns (as structured text):
            - generation_prompt: Complete prompt used for image generation
            - save_path: File path where image was saved
            - reference_image_list: List of reference images used (empty if none)
            - brief_status: One-line confirmation message
        """
        result = character_agent.invoke({
            "messages": [{"role": "user", "content": request}]
        })
        return result["messages"][-1].content
    
    @tool
    def scene_generator(request: str) -> str:
        """
        Generate scene/environment images without any human presence.
        
        Use this tool when you need to:
        - Create location/environment references
        - Generate scenes with specific lighting and atmosphere
        - Establish visual context for keyframes
        
        Input format in request string:
            - location_name: Name of the location
            - scene_heading: Scene heading (e.g., "INT./EXT. LOCATION - TIME")
            - scene_description: Atmosphere, lighting, and mood description
            - base_path: Base directory for storage
            - global_visual_style: Overall visual style for the image
        
        Returns (as structured text):
            - generation_prompt: Complete prompt used for image generation
            - save_path: File path where image was saved
            - reference_image_list: List of reference images used (empty if none)
            - brief_status: One-line confirmation message
        """
        result = scene_agent.invoke({
            "messages": [{"role": "user", "content": request}]
        })
        return result["messages"][-1].content
    
    @tool
    def prop_generator(request: str) -> str:
        """
        Generate versioned prop images showing evolution and wear over time.
        
        Use this tool when you need to:
        - Create a new base prop image
        - Generate a new version showing wear/aging
        - Maintain prop identity across timeline
        
        Input format in request string:
            - prop_name: Name of the prop (e.g., "Journal")
            - current_condition: State to be depicted (e.g., "pristine leather", "tattered")
            - base_path: Base directory for storage
            - reference_image_path: (Optional) Path to previous version for continuity
            - global_visual_style: Overall visual style (e.g., "photorealistic", "anime")
        
        Returns (as structured text):
            - generation_prompt: Complete prompt used for image generation
            - save_path: File path where image was saved
            - reference_image_list: List of reference images used (empty if none)
            - brief_status: One-line confirmation message
        """
        result = prop_agent.invoke({
            "messages": [{"role": "user", "content": request}]
        })
        return result["messages"][-1].content
    
    @tool
    def keyframe_compositor(request: str) -> str:
        """
        Composite final keyframe images from pre-generated reference images.
        
        Use this tool when you need to:
        - Create final shot keyframes
        - Composite characters, scenes, and props into a cohesive image
        - Apply cinematography and emotional tone
        
        Input format in request string:
            - shot_number: Shot identifier (e.g., "A1_S1_Sh1")
            - plot: Plot description for this shot
            - reference_image_paths: Ordered list of reference image paths (characters, scenes, props)
            - cinematography_notes: Camera angle and composition guidance
            - emotional_tone: Emotional atmosphere of the shot
            - visual_style: Shot-specific visual styling (optional)
            - global_visual_style: Overall visual style for the project
            - output_path: Base directory for saving the keyframe
        
        Returns (as structured text):
            - generation_prompt: Complete prompt used for image generation
            - save_path: File path where keyframe was saved
            - reference_image_list: List of reference images used
            - brief_status: One-line confirmation message
        """
        result = keyframe_agent.invoke({
            "messages": [{"role": "user", "content": request}]
        })
        return result["messages"][-1].content
    
    # ========================================================================
    # Step 3: Create supervisor agent with sub-agent tools
    # ========================================================================
    
    supervisor_tools = [
        character_generator,
        scene_generator,
        prop_generator,
        keyframe_compositor,
        update_memory_bank
    ]
    
    supervisor_agent = create_agent(
        model=model_name,
        tools=supervisor_tools,
        system_prompt=KEYFRAME_SUPERVISOR
    )
    
    # ========================================================================
    # Step 4: Execute workflow
    # ========================================================================
    
    # Prepare input message
    user_message = f"""Base path for this project: {base_path}

Storyboard to process:
{storyboard}"""
    
    input_data = {
        "messages": [{"role": "user", "content": user_message}]
    }
    
    config = {
        "configurable": {
            "thread_id": thread_id,
        },
        "recursion_limit": 200
    }
    
    # Stream execution
    print(f"🎬 Starting keyframe generation for: {thread_id}")
    print("=" * 80)
    
    for chunk in supervisor_agent.stream(
        input=input_data,
        stream_mode="values",
        config=config
    ):
        # Display messages as they arrive
        if "messages" in chunk:
            chunk["messages"][-1].pretty_print()
    
    print("=" * 80)
    print("✅ Keyframe generation complete!")


if __name__ == "__main__":  
    test_keyframe_supervisor()