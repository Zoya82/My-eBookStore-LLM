"""智能推荐：根据自然语言需求，从图书库中推荐最匹配的书。"""
import json
import re

from ..llm_client import chat
from ..prompts import recommend_prompt
from ..book_repo import get_all_books


def run(query: str):
    """返回 (items, raw_reply)。

    items: [{"id", "title", "reason"}, ...]（已校验只含库内图书）
    raw_reply: 模型原始输出，解析失败时供前端兜底展示
    """
    books = get_all_books()
    raw = chat(recommend_prompt(query, books), temperature=0.6)
    return _parse(raw, books), raw


def _parse(raw: str, books: list) -> list:
    """从模型输出中提取 JSON 数组；解析失败或越界则安全降级为空列表。"""
    try:
        match = re.search(r"\[.*\]", raw, re.S)
        data = json.loads(match.group(0) if match else raw)
        by_id = {b["id"]: b for b in books}
        items = []
        for it in data:
            bid = it.get("id")
            # 只保留库内存在的书，防止模型编造
            if bid is not None and bid not in by_id:
                continue
            book = by_id.get(bid, {})
            items.append({
                "id": bid,
                # 书名/作者以库内数据为准，不依赖模型输出
                "title": book.get("title") or it.get("title", ""),
                "author": book.get("author", ""),
                "reason": it.get("reason", ""),
            })
        return items
    except Exception:
        return []
