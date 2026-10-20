"""Customer-side OpenAI Agents SDK tool; no model call or agent loop on import."""
from agents import Agent, function_tool
from daknode_tools import count_recent_mail

recent_mail = function_tool(count_recent_mail)


def build_agent(model: str) -> Agent:
    """Build only; the customer chooses a model and explicitly runs their agent."""
    return Agent(name="DakNode mail inspector", model=model,
        instructions="Use the count tool for this configured inbox. It does not read bodies or send email.",
        tools=[recent_mail])
