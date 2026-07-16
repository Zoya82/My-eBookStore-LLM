"""智能摘要：简介一句话摘要 + 基于全文 RAG 的安利体推荐语。"""
import logging

from ..llm_client import chat
from ..prompts import summary_prompt, book_summary_prompt
from .. import rag
from ..book_repo import get_book

logger = logging.getLogger(__name__)


def run(text: str, max_length: int = 60) -> str:
    """简介摘要（原有能力，亦作为全文摘要的降级路径）。"""
    return chat(summary_prompt(text, max_length), temperature=0.5)


def run_book(book_id: int):
    """全文安利体摘要（约 200 字）。

    返回 (summary, source)：source ∈ rag / full / cached / intro（降级到简介）。
    素材与简介均不可得时抛 ValueError。
    """
    material, mode = rag.get_summary_material(book_id)
    if mode == "cached_summary":
        return material, "cached"

    book = get_book(book_id) or {}
    if material:
        summary = chat(
            book_summary_prompt(book.get("title", ""), book.get("author", ""), material),
            temperature=0.7,
        )
        rag.cache_summary(book_id, summary)
        return summary, mode

    intro = book.get("intro", "")
    if intro:                                            # 无全文 → 降级简介摘要
        logger.info("book_id=%s 无全文，降级简介摘要", book_id)
        return run(intro, 60), "intro"
    raise ValueError("该图书暂无可用于摘要的内容")
