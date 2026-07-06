# ai_service · 智能服务模块

智能掌上书店的大模型智能服务：智能摘要、智能推荐、多轮问答。
基于 **FastAPI + 通义千问（阿里云百炼）**，设计成可独立运行、可一行挂载进后端的标准包。

## 目录结构

```
ai_service/
├── config.py          # 配置（读 .env）
├── llm_client.py      # 大模型调用封装（超时/重试/失败兜底）★核心
├── prompts.py         # 提示词模板（集中调优）
├── schemas.py         # 请求/响应模型（前后端接口契约）
├── book_repo.py       # 图书数据访问层（现读JSON，后期换DB的插槽）
├── session_store.py   # 多轮问答的会话上下文（内存 TTLCache，自动过期）
├── services/          # 三个功能的业务逻辑
│   ├── summary.py     #   智能摘要
│   ├── recommend.py   #   智能推荐
│   └── chat.py        #   多轮问答
├── router.py          # FastAPI 路由（对外3个接口）★集成入口
├── main.py            # 独立运行入口
├── test_llm.py        # 第一步自检脚本
└── data/sample_books.json  # 样例图书（后期由真实数据替换）
```

## 快速开始（3 步）

> 均在 `code/My_eBookStore/` 目录下执行。

```bash
# 1. 装依赖
pip install -r ai_service/requirements.txt

# 2. 配置 Key（复制模板后填入自己的百炼 Key）
cp ai_service/.env.example ai_service/.env
#   然后编辑 ai_service/.env，填 DASHSCOPE_API_KEY

# 3. 自检：确认大模型调通
python -m ai_service.test_llm
```

看到 `✅ 大模型调通！` 就说明第一步成功。然后启动服务：

```bash
uvicorn ai_service.main:app --reload --port 8001
# 打开 http://localhost:8001/docs 直接点开测试三个接口
```

## 接口（给前端对接）

统一前缀 `/api/ai`，均为 `POST`，请求/响应见 `schemas.py`。
响应都带 `success` 字段，失败时 `success=false` + `message`，前端据此降级提示。

| 接口 | 请求体 | 关键返回 |
|---|---|---|
| `/api/ai/summary` | `{text, max_length}` | `{success, summary}` |
| `/api/ai/recommend` | `{query}` | `{success, items:[{id,title,reason}], reply}` |
| `/api/ai/chat` | `{message, session_id?}` | `{success, reply, session_id}` |

示例（推荐）：
```json
// 请求
{"query": "想找一本适合周末放松看的科幻小说"}
// 响应
{"success": true, "items": [{"id": 1, "title": "三体", "reason": "宏大科幻，适合沉浸阅读"}], "reply": "..."}
```

## 集成说明（给后端）

**挂载路由**——在后端主程序里两行搞定：
```python
from ai_service.router import router as ai_router
app.include_router(ai_router)
```

**接入真实图书数据**——只改 `book_repo.py` 一个文件，把 `get_all_books()` 换成查数据库，返回同样结构（`id/title/author/category/intro`）即可，`services/` 无需改动：
```python
def get_all_books():
    return [book_to_dict(b) for b in db.query(Book).all()]
```

## 分工衔接
- **本模块（AI 服务）**：摘要/推荐/问答/提示词/封装/兜底
- **后端**：挂载路由 + 用真实图书数据替换 `book_repo`
- **前端**：按上表接口调用；多轮问答带上 `session_id`

## TODO
- [ ] 拿到百炼 Key，跑通 `test_llm`
- [ ] 调优三个功能的提示词
- [ ] 推荐功能接入真实图书库（等后端）
- [ ] 前端页面对接联调
