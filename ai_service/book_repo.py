"""图书数据访问层（隔离数据来源）。

现在从样例 JSON 读取；后期由后端替换为从 MySQL 查询——
只要保持 get_all_books() / get_book() 的返回结构不变，
上层的推荐/摘要服务完全不用改。这就是给集成留的"插槽"。

后端集成示例（替换本文件实现即可）：
    def get_all_books():
        return db.query(Book).all()   # 返回同结构的 dict 列表
"""
import json
import os
from functools import lru_cache

_DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "sample_books.json")


@lru_cache(maxsize=1)
def get_all_books() -> list:
    """返回全部图书：[{id, title, author, category, intro}, ...]"""
    with open(_DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def get_book(book_id: int):
    return next((b for b in get_all_books() if b["id"] == book_id), None)
