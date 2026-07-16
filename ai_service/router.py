"""FastAPI 路由：智能服务对外的三个接口。

===== 后端集成 =====
在主后端程序中：
    from ai_service.router import router as ai_router
    app.include_router(ai_router)
即挂载：
    POST /api/ai/summary    图书摘要
    POST /api/ai/recommend  智能推荐
    POST /api/ai/chat       多轮问答（按 session_id 维护上下文）

所有接口失败时返回 success=false + message，不会抛 500，前端可安全降级。
"""
import logging

from fastapi import APIRouter

from .schemas import (
    SummaryRequest, SummaryResponse,
    RecommendRequest, RecommendResponse,
    ChatRequest, ChatResponse,
)
from .llm_client import LLMError
from .services import summary as summary_svc
from .services import recommend as recommend_svc
from .services import chat as chat_svc

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["智能服务"])

_FALLBACK = "智能服务暂时不可用，请稍后重试。"


@router.post("/summary", response_model=SummaryResponse)
def summary(req: SummaryRequest):
    try:
        if req.book_id is not None:                      # 全文 RAG 安利体摘要
            s, source = summary_svc.run_book(req.book_id)
            return SummaryResponse(success=True, summary=s, source=source)
        if req.text:                                     # 简介一句话摘要
            return SummaryResponse(success=True, summary=summary_svc.run(req.text, req.max_length), source="text")
        return SummaryResponse(success=False, message="请提供 book_id 或 text")
    except ValueError as e:
        return SummaryResponse(success=False, message=str(e))
    except LLMError as e:
        logger.error("摘要失败: %s", e)
        return SummaryResponse(success=False, message=_FALLBACK)


@router.post("/recommend", response_model=RecommendResponse)
def recommend(req: RecommendRequest):
    try:
        items, raw = recommend_svc.run(req.query)
        return RecommendResponse(success=True, items=items, reply=raw)
    except LLMError as e:
        logger.error("推荐失败: %s", e)
        return RecommendResponse(success=False, message=_FALLBACK)


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    try:
        reply, session_id = chat_svc.run(req.message, req.session_id)
        return ChatResponse(success=True, reply=reply, session_id=session_id)
    except LLMError as e:
        logger.error("问答失败: %s", e)
        return ChatResponse(success=False, session_id=req.session_id or "", message=_FALLBACK)
