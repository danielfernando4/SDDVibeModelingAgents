from typing import TypedDict, Annotated, Optional
from langgraph.graph.message import add_messages


class RedirectionItem(TypedDict):
    source: str
    target: str
    summary: str
    suggestions: str


class AgentState(TypedDict):
    messages: Annotated[list[dict], add_messages]
    user_prompt: str
    is_redirection: bool
    redirection_source: Optional[str]

    product_content: str
    requirements_content: str
    design_content: str
    product_exists: bool
    requirements_exists: bool
    design_exists: bool

    redirection_queue: list[RedirectionItem]
    current_redirection: Optional[dict]

    target_phase: str
    spec_name: str
    spec_directory: str
