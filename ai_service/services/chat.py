"""多轮问答：带对话历史的图书客服助手。"""
from ..llm_client import chat as llm_chat
from ..prompts import chat_messages


def run(user_message: str, history: list) -> str:
    """history: [{"role": "user"/"assistant", "content": "..."}]（由前端维护）。"""
    return llm_chat(chat_messages(history, user_message), temperature=0.7)
