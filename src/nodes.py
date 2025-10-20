from dotenv import load_dotenv
load_dotenv()

from langchain.chat_models import init_chat_model
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from src.configuration import Configuration
from src.state import AgentState
from src.schema import Script


def screenwriter_node(state: AgentState, config: RunnableConfig) -> Script:
    configuration = Configuration.from_runnable_config(config)
    
    llm = init_chat_model(
        model = configuration.screenwriter_model,
        temperature=0
        ).with_structured_output(Script)

    messages = [
        SystemMessage(content=configuration.screenwriter_prompt),
        HumanMessage(content=state["raw_script"])
    ]

    script = llm.invoke(messages).model_dump_json(indent=2)

    return {
        "messages": script,
        "script": script,
    }
