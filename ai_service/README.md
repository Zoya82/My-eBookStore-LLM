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

## 常用位置

- 提示词：`prompts.py`　·　样例图书：`data/sample_books.json`　·　接口字段：`schemas.py`
- 换 API Key：编辑 `ai_service/.env`
