"""多轮问答：按 session_id 维护上下文（存储见 session_store，TTL 自动过期）。"""
import uuid

from ..llm_client import chat as llm_chat
from ..prompts import chat_messages
from .. import session_store


def run(message: str, session_id: str | None):
    """处理一轮对话。

    Args:
        message: 用户本轮消息
        session_id: 会话 ID；为空则新建一个会话

    Returns:
        (reply, session_id)：助手回复 + 本次使用的会话 ID
    """
    if not session_id:
        session_id = uuid.uuid4().hex          # 首次对话，生成新会话 ID

    history = session_store.get_history(session_id)   # 取上下文
    reply = llm_chat(chat_messages(history, message))
    session_store.append(session_id, message, reply)  # 追加本轮，刷新过期时间
    return reply, session_id
