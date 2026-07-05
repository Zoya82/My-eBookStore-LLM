"""配置：从环境变量 / .env 读取大模型设置。"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 无论从哪个目录运行，都能加载到本模块下的 .env
load_dotenv(Path(__file__).parent / ".env")


class Settings:
    # 阿里云百炼 API Key（通义千问）
    api_key: str = os.getenv("DASHSCOPE_API_KEY", "")
    # OpenAI 兼容接口地址（百炼，一般无需修改）
    base_url: str = os.getenv("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    # 模型：qwen-turbo(快/省) / qwen-plus(均衡) / qwen-max(强)
    model: str = os.getenv("LLM_MODEL", "qwen-plus")
    # 单次请求超时（秒）
    timeout: float = float(os.getenv("LLM_TIMEOUT", "30"))


settings = Settings()
