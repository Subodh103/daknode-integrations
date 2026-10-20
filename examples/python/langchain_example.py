"""A real LangChain tool wrapper; no model, planner or network call on import."""
from langchain_core.tools import tool
from daknode_tools import count_recent_mail

recent_mail = tool("daknode_count_recent_mail")(count_recent_mail)

if __name__ == "__main__":
    print(recent_mail.invoke({}))
