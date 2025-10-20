import os, json

from dotenv import load_dotenv
load_dotenv()

from langchain_core.messages import SystemMessage, HumanMessage
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent


from src.schema import Script, Storyboard, Keyframe
from src.tools.nano_banana import nano_banana_replicate_tool
from src.prompts import SCREENWRITER, STORYBOARD, KEYFRAME



def test_screenwriter():
    raw_script_path = "datasets/raw_scripts/FronzenII.txt"
    with open(raw_script_path, "r") as f:
        raw_script = f.read()
        
    llm = init_chat_model(
        model = "deepseek:deepseek-chat",
        temperature=0
        ).with_structured_output(Script)

    query_messages = [
        SystemMessage(content=SCREENWRITER),
        HumanMessage(content=raw_script)
    ]
    script = llm.invoke(query_messages)
    print(script.model_dump_json(indent=2))
    # save the script to a file
    os.makedirs("output/FronzenII", exist_ok=True)
    with open("output/FronzenII/script.json", "w") as f:
        f.write(script.model_dump_json(indent=2))

def test_storyboard():
    script_path = "output/FronzenII/script.json"
    with open(script_path, "r") as f:
        # Read as raw string
        script = f.read()

    llm = init_chat_model(
        model = "deepseek:deepseek-chat",
        temperature=0
        ).with_structured_output(Storyboard)

    query_messages = [
        SystemMessage(content=STORYBOARD),
        HumanMessage(content=script)
    ]

    storyboard = llm.invoke(query_messages)
    print(storyboard.model_dump_json(indent=2))
    
    # save the storyboard to a file
    os.makedirs("output/FronzenII", exist_ok=True)
    with open("output/FronzenII/storyboard.json", "w") as f:
        f.write(storyboard.model_dump_json(indent=2))
        
def test_keyframe():
    storyboard_path = "output/FronzenII/storyboard.json"
    with open(storyboard_path, "r") as f:
        # Read as raw string
        storyboard = json.load(f)

    memory_bank = {
        "characters": {
            "ELSA": "output/FronzenII/memory_bank/characters/ELSA.png",
            "ANNA": "output/FronzenII/memory_bank/characters/ANNA.png"
        },
        "scenes": {
            "Arendelle Castle balcony": "output/FronzenII/memory_bank/scenes/Arendelle_Castle_balcony.png"
        },
        "props": {}
    }

    agent = create_agent(
        model = "deepseek:deepseek-chat",
        tools=[nano_banana_replicate_tool],
        system_prompt=KEYFRAME,
    )

    query = f"""
The shot is: {storyboard["storyboard"][1]}
The memory bank is: {memory_bank}
The base path is: "output/FronzenII/"
"""

    for msgs in agent.stream(input={"messages": [("user", query)]}, stream_mode="values"):
        msgs['messages'][-1].pretty_print()


    

if __name__ == "__main__":
    # test_screenwriter()
    # test_storyboard()
    test_keyframe()
