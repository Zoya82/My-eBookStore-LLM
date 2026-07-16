"""大模型调用封装：统一入口 + 超时 + 重试 + 失败兜底。

对上层（services）只暴露一个 chat() 函数；所有异常收敛为 LLMError，
由路由层统一转成友好的降级响应，保证大模型挂掉时系统不崩。
"""
import time
import logging
from openai import OpenAI

from .config import settings

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """大模型调用失败（网络/鉴权/超时/额度等）。"""


_client = None


def _get_client() -> OpenAI:
    """惰性创建单例客户端。"""
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=settings.api_key,
            base_url=settings.base_url,
            timeout=settings.timeout,
        )
    return _client


def chat(messages: list, temperature: float = 0.7, max_retries: int = 2) -> str:
    """调用大模型对话接口。

    Args:
        messages: [{"role": "system/user/assistant", "content": "..."}]
        temperature: 采样温度，越低越稳定
        max_retries: 失败重试次数

    Returns:
        模型返回的文本

    Raises:
        LLMError: 重试后仍失败
    """
    if not settings.api_key:
        raise LLMError("未配置 DASHSCOPE_API_KEY，请在 ai_service/.env 中填写")

    last_err = None
    # qwen3 系列默认开启深度思考，摘要/推荐等场景延迟高达 20s+；
    # 关闭思考后 1~2s 返回且质量不降（仅 qwen 系模型支持该参数）
    extra = {"enable_thinking": False} if settings.model.startswith("qwen") else None
    for attempt in range(max_retries + 1):
        try:
            resp = _get_client().chat.completions.create(
                model=settings.model,
                messages=messages,
                temperature=temperature,
                extra_body=extra,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:  # noqa: BLE001 收敛所有异常
            last_err = e
            logger.warning("大模型调用失败(第%d次): %s", attempt + 1, e)
            if attempt < max_retries:
                time.sleep(1.5 * (attempt + 1))
    raise LLMError(str(last_err))
