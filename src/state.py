from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage

from typing import Annotated
from typing_extensions import TypedDict


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

    script: str
    storyboard: str
    
    # Memory
    memory_bank: dict

