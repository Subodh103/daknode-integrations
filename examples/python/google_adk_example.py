"""Register this FunctionTool in your own ADK agent's tools list."""
from google.adk.tools import FunctionTool
from daknode_tools import count_recent_mail

recent_mail = FunctionTool(func=count_recent_mail)

if __name__ == "__main__":
    print(count_recent_mail())
