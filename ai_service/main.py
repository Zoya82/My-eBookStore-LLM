"""独立运行入口 —— 方便本模块单独开发调试，不依赖后端主程序。

从 code/My_eBookStore/ 目录运行：
    uvicorn ai_service.main:app --reload --port 8001
然后打开接口文档：http://localhost:8001/docs 直接点开测试。
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .router import router

app = FastAPI(title="智能掌上书店 · 智能服务", version="0.1.0")

# 允许前端（Web / H5）跨域调试；正式集成时由后端主程序统一配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root():
    return {"service": "ai_service", "status": "ok", "docs": "/docs"}
