"""智能摘要：把长篇图书简介浓缩成一句话。"""
from ..llm_client import chat
from ..prompts import summary_prompt


def run(text: str, max_length: int = 60) -> str:
    """生成图书摘要。失败时向上抛 LLMError，由路由层兜底。"""
    return chat(summary_prompt(text, max_length), temperature=0.5)
