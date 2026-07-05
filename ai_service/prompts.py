"""提示词模板集中管理，方便统一调优（柴子萱"提示词设计"职责）。"""


# ---------- 智能摘要 ----------
_SUMMARY_SYSTEM = "你是一个图书导购助手，擅长把冗长的图书简介浓缩成简洁、准确、有吸引力的摘要。"


def summary_prompt(text: str, max_length: int = 60) -> list:
    return [
        {"role": "system", "content": _SUMMARY_SYSTEM},
        {"role": "user", "content": (
            f"请把下面这段图书简介浓缩成不超过 {max_length} 字的一句话摘要，"
            f"突出核心看点，不要出现\"本书\"\"这本书\"等废话：\n\n{text}"
        )},
    ]


# ---------- 智能推荐 ----------
_RECOMMEND_SYSTEM = "你是一个专业的图书推荐助手。你只能从给定的图书列表中推荐，绝不能编造列表之外的书。"


def recommend_prompt(query: str, books: list) -> list:
    book_lines = "\n".join(
        f'{b["id"]}. 《{b["title"]}》（{b.get("author", "")}，{b.get("category", "")}）：{b.get("intro", "")}'
        for b in books
    )
    user = (
        f"用户需求：{query}\n\n"
        f"可选图书列表：\n{book_lines}\n\n"
        "请从上述列表中挑选最多 3 本最匹配的书，只返回严格的 JSON 数组，"
        '每个元素形如 {"id": 图书编号, "title": "书名", "reason": "20字以内推荐理由"}。'
        "不要输出 JSON 以外的任何内容。"
    )
    return [
        {"role": "system", "content": _RECOMMEND_SYSTEM},
        {"role": "user", "content": user},
    ]


# ---------- 多轮问答 ----------
_CHAT_SYSTEM = (
    "你是\"智能掌上书店\"的图书客服助手，友好、专业地解答用户关于图书、购买、阅读的问题，回答简洁明了。"
)


def chat_messages(history: list, user_message: str) -> list:
    """history: [{"role": "user"/"assistant", "content": "..."}]"""
    msgs = [{"role": "system", "content": _CHAT_SYSTEM}]
    msgs.extend(history)
    msgs.append({"role": "user", "content": user_message})
    return msgs
