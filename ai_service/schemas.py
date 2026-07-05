"""接口请求/响应模型 —— 前后端的接口契约。

前端（袁艺轩）按这里的字段对接；后端（李君怡）集成时可直接复用。
所有响应都带 success 字段：大模型失败时 success=false + message，前端据此降级提示。
"""
from typing import List, Optional
from pydantic import BaseModel, Field


# ---------- 摘要 ----------
class SummaryRequest(BaseModel):
    text: str = Field(..., description="要摘要的图书简介")
    max_length: int = Field(60, description="摘要最大字数")


class SummaryResponse(BaseModel):
    success: bool
    summary: str = ""
    message: str = ""


# ---------- 推荐 ----------
class RecommendRequest(BaseModel):
    query: str = Field(..., description="用户的自然语言需求，如\"想看适合周末放松的科幻小说\"")


class RecommendItem(BaseModel):
    id: Optional[int] = None
    title: str = ""
    reason: str = ""


class RecommendResponse(BaseModel):
    success: bool
    items: List[RecommendItem] = []
    reply: str = ""          # 模型原始输出，解析失败时兜底展示
    message: str = ""


# ---------- 多轮问答 ----------
class ChatMessage(BaseModel):
    role: str = Field(..., description="user 或 assistant")
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., description="用户本轮消息")
    history: List[ChatMessage] = Field(default_factory=list, description="历史对话，前端负责维护")


class ChatResponse(BaseModel):
    success: bool
    reply: str = ""
    message: str = ""
