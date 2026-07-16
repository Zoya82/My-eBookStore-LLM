"""多轮问答：按 session_id 维护上下文（存储见 session_store，TTL 自动过期）。"""
import uuid

from ..llm_client import chat as llm_chat
from ..prompts import chat_messages
from ..book_repo import get_all_books, get_book_detail
from .. import session_store

_MAX_DETAIL_BOOKS = 2   # 每轮最多注入几本书的资料，控制提示词长度


def _mentioned_book_details(message: str, history: list, books: list | None) -> list:
    """找出本轮对话涉及的在售图书，取其目录/简介供模型引用。

    书名匹配范围：本轮消息优先，其次近 4 条上下文（支持"它的目录呢"这类指代）。
    """
    if not books:
        return []
    texts = [message] + [h.get("content", "") for h in history[-4:]]
    details = []
    for b in books:
        title = b.get("title", "")
        if not title:
            continue
        for rank, t in enumerate(texts):
            if title in t:
                details.append((rank, b["id"]))
                break
    details.sort()
    result = []
    for _, book_id in details[:_MAX_DETAIL_BOOKS]:
        d = get_book_detail(book_id)
        if d and (d.get("catalog") or d.get("intro")):
            result.append(d)
    return result


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
    try:
        books = get_all_books()   # 注入在售书单，约束对话只引用库内图书
    except Exception:  # noqa: BLE001 书单获取失败不阻塞对话
        books = None
    details = _mentioned_book_details(message, history, books)  # 按需注入目录/简介
    reply = llm_chat(chat_messages(history, message, books, details))
    session_store.append(session_id, message, reply)  # 追加本轮，刷新过期时间
    return reply, session_id
