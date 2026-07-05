"""第一步自检：验证通义千问是否调通。

从 code/My_eBookStore/ 目录运行：
    python -m ai_service.test_llm
"""
from .llm_client import chat, LLMError


def main():
    print("正在调用通义千问 ...")
    try:
        reply = chat([{"role": "user", "content": "用一句话介绍《三体》这本书。"}])
        print("✅ 大模型调通！返回：")
        print("   " + reply)
    except LLMError as e:
        print("❌ 调用失败：", e)
        print("请检查：")
        print("  1) ai_service/.env 里的 DASHSCOPE_API_KEY 是否填写正确")
        print("  2) 是否已在阿里云百炼开通模型服务")
        print("  3) 网络是否正常")


if __name__ == "__main__":
    main()
