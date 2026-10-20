"""Register recent_mail in your own LiveKit Agent tools list."""
from livekit.agents import function_tool
from daknode_tools import count_recent_mail

recent_mail = function_tool(count_recent_mail, name="daknode_count_recent_mail")

if __name__ == "__main__":
    print(recent_mail())
