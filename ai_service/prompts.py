"""提示词模板集中管理，方便统一调优。"""


# ---------- 智能摘要 ----------
_SUMMARY_SYSTEM = "你是图书导购助手，擅长把冗长的图书简介浓缩成一句吸引人的速读摘要。"


def summary_prompt(text: str, max_length: int = 60) -> list:
    return [
        {"role": "system", "content": _SUMMARY_SYSTEM},
        {"role": "user", "content": (
            f"把下面的图书简介浓缩成不超过 {max_length} 字的一句话，突出最吸引读者的看点。\n"
            f"要求：直接输出摘要本身，不要任何前缀、引号或解释；不出现\"本书\"\"这本书\"等字样。\n\n"
            f"简介：{text}"
        )},
    ]


# ---------- 全文安利体摘要 ----------
_BOOK_SUMMARY_SYSTEM = "你是资深图书编辑，擅长写让读者心动的图书推荐语。"


def book_summary_prompt(title: str, author: str, material: str) -> list:
    return [
        {"role": "system", "content": _BOOK_SUMMARY_SYSTEM},
        {"role": "user", "content": (
            f"根据下面《{title}》（{author}）的内容节选，写一段约 200 字的图书推荐语。\n"
            "要求：\n"
            "1. 安利体三段式（合为一段自然衔接）：开头一句话勾住读者（一个引人的问题、场景或冲突），"
            "中间讲清这本书最打动人的看点（写什么、妙在哪），结尾点明它适合谁、适合什么时候读；\n"
            "2. 只依据下面的内容节选，不编造情节，不剧透关键结局；\n"
            "3. 180~220 字，单段成文，不用标题、列表、引号、表情符号；\n"
            "4. 语气真诚有感染力，不用\"本书\"\"该书\"等生硬指代，不用\"必读神作\"式广告腔。\n\n"
            f"内容节选：\n{material}"
        )},
    ]


# ---------- 智能推荐 ----------
_RECOMMEND_SYSTEM = "你是专业的图书推荐助手，只能从给定的图书列表中推荐，绝不编造列表之外的书。"


def recommend_prompt(query: str, books: list) -> list:
    book_lines = "\n".join(
        f'{b["id"]}. 《{b["title"]}》（{b.get("author", "")}，{b.get("category", "")}）：{b.get("intro", "")}'
        for b in books
    )
    user = (
        f"用户需求：{query}\n\n"
        f"可选图书：\n{book_lines}\n\n"
        "从中挑选 1-3 本最匹配用户需求的书；宁缺毋滥，没有合适的就少推荐、都不合适就返回空数组 []。\n"
        "只返回严格的 JSON 数组，每项形如 "
        '{"id": 图书编号, "title": "书名", "reason": "结合用户需求的具体推荐理由，20字以内"}。\n'
        "reason 要说清为什么符合用户的需求，别写空泛套话。不要输出 JSON 以外的任何内容。"
    )
    return [
        {"role": "system", "content": _RECOMMEND_SYSTEM},
        {"role": "user", "content": user},
    ]


# ---------- 多轮问答 ----------
_CHAT_SYSTEM = (
    "你是\"智能掌上书店\"的图书客服助手，友好、专业地解答图书、购买、阅读相关的问题。\n"
    "要求：回答简洁，一般不超过 3 句；聚焦图书与书店，无关问题礼貌引导回书店话题；"
    "不确定或超出了解范围时如实说明，不编造；可适度用表情，但不堆砌。\n"
    "涉及推荐或介绍在售图书时，只能引用下方\"本店在售图书\"清单中的书，"
    "不得推荐清单之外的书；清单中没有合适的就如实说明并引导用户描述需求。"
)


def chat_messages(history: list, user_message: str, books: list | None = None) -> list:
    """history: [{"role": "user"/"assistant", "content": "..."}]；books 为在售图书清单。"""
    system = _CHAT_SYSTEM
    if books:
        book_lines = "\n".join(
            f'- 《{b["title"]}》（{b.get("author", "")}，{b.get("category", "")}）'
            for b in books
        )
        system += f"\n\n本店在售图书：\n{book_lines}"
    msgs = [{"role": "system", "content": system}]
    msgs.extend(history)
    msgs.append({"role": "user", "content": user_message})
    return msgs
