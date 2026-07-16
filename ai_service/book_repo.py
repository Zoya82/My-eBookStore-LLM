"""图书数据访问层（隔离数据来源）。

优先从业务后端（Django，GET /api/books/）获取真实图书；
后端不可用时自动降级为本地样例数据 sample_books.json，
保证 AI 服务始终可独立运行与演示。

上层（services/）只依赖 get_all_books() 返回的统一结构：
    [{id, title, author, category, intro}, ...]
"""
import json
import logging
import os

import httpx
from cachetools import TTLCache, cached

logger = logging.getLogger(__name__)

# 业务后端地址（Django），可用环境变量覆盖
BACKEND_API_BASE = os.getenv("BACKEND_API_BASE", "http://127.0.0.1:8000/api")

_DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "sample_books.json")


def _from_backend() -> list:
    """从业务后端分页拉取全部图书，映射为统一结构。"""
    books, url = [], f"{BACKEND_API_BASE}/books/?page_size=100"
    while url:
        resp = httpx.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        for b in data.get("results", []):
            books.append({
                "id": b["id"],
                "title": b.get("title", ""),
                "author": b.get("author", ""),
                "category": b.get("category_name", ""),
                # 列表接口暂无简介字段，留空不影响推荐主流程；
                # 后端在列表接口补充 description 后此处自动生效
                "intro": b.get("description", ""),
            })
        url = data.get("next")
    return books


def _from_sample() -> list:
    with open(_DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


@cached(TTLCache(maxsize=1, ttl=300))   # 缓存 5 分钟，避免每次推荐都全量拉取
def get_all_books() -> list:
    """返回全部图书：[{id, title, author, category, intro}, ...]"""
    try:
        books = _from_backend()
        if books:
            return books
        logger.warning("后端图书列表为空，降级使用样例数据")
    except Exception as e:  # noqa: BLE001 后端未启动/网络异常等
        logger.warning("获取后端图书失败(%s)，降级使用样例数据", e)
    return _from_sample()


def get_book(book_id: int):
    return next((b for b in get_all_books() if b["id"] == book_id), None)
