"""会话上下文存储：内存 TTLCache，按 session_id 维护多轮对话历史。

- 每个会话在 SESSION_TTL 秒内无新对话则自动过期（对话是临时的，超时该忘）；
- 每个会话只保留最近 MAX_MESSAGES 条消息，防止上下文过长、token 过多；
- 纯内存，无需 Redis 等外部组件。服务重启会话会清空（课设单机演示无影响）。
"""
from cachetools import TTLCache

# 最多同时保留的会话数；每个会话空闲多少秒后过期
MAX_SESSIONS = 1000
SESSION_TTL = 30 * 60          # 30 分钟
MAX_MESSAGES = 20              # 每会话最多保留最近 20 条消息（约 10 轮）

_sessions: TTLCache = TTLCache(maxsize=MAX_SESSIONS, ttl=SESSION_TTL)


def get_history(session_id: str) -> list:
    """取某会话的历史消息（只读，不影响过期时间）。"""
    return list(_sessions.get(session_id, []))


def append(session_id: str, user_msg: str, assistant_msg: str) -> None:
    """把本轮的用户消息与助手回复追加进会话历史。

    写入会刷新该会话的过期时间（活跃会话不会被清理）。
    """
    history = list(_sessions.get(session_id, []))
    history.append({"role": "user", "content": user_msg})
    history.append({"role": "assistant", "content": assistant_msg})
    _sessions[session_id] = history[-MAX_MESSAGES:]   # 只保留最近若干条


def clear(session_id: str) -> None:
    """清空某会话（前端点"清空对话"时可调）。"""
    _sessions.pop(session_id, None)
