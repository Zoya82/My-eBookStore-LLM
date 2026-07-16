"""书籍全文 RAG 管线：结构感知切分 → 双路召回（BM25+向量）→ RRF 融合 → MMR 多样性 → 素材块。

设计要点：
- 切分：按章（正则识别）→ 章内按段聚合 500~800 字、约 10% 重叠，块带位置比例元数据；
- 分档：全文 < 30000 字直接返回全文（不检索）；更长走检索；
- 召回：BM25（jieba 分词，词面命中）+ 向量（qwen3.7-text-embedding，语义），各取 top-20；
- 融合：RRF（倒数排名融合）合并双路结果；
- 精选：MMR（最大边际相关，本地余弦计算）选 top-k，兼顾相关与多样；
- 防剧透：位置比例 > 0.85 的块（结尾部分）不进入摘要素材；
- 缓存：chunks 与 embedding 按 book_id 持久化于 data/rag_cache/，重复请求不再向量化。
"""
import json
import logging
import os
import re

import httpx
import jieba
import numpy as np
from openai import OpenAI
from rank_bm25 import BM25Okapi

from .config import settings

logger = logging.getLogger(__name__)

EMBED_MODEL = os.getenv("EMBED_MODEL", "qwen3.7-text-embedding")
# 同机演示环境：直读业务后端 media 目录；生产应改为后端提供的内部只读接口
BOOK_CONTENT_ROOT = os.getenv(
    "BOOK_CONTENT_ROOT",
    os.path.join(os.path.dirname(__file__), "..", "..", "backend", "media"),
)
BACKEND_API_BASE = os.getenv("BACKEND_API_BASE", "http://127.0.0.1:8000/api")
CACHE_DIR = os.path.join(os.path.dirname(__file__), "data", "rag_cache")

FULLTEXT_DIRECT_LIMIT = 30000   # 小书直通阈值（字）
CHUNK_TARGET = 650              # 目标块长（字）
CHUNK_OVERLAP = 60              # 章内相邻块重叠（字）
SPOILER_POS = 0.85              # 位置比例超过此值的块视为结尾，不进摘要素材
RECALL_K = 20                   # 每路召回数
FINAL_K = 8                     # 最终素材块数

# 摘要场景无用户 query，用固定查询集覆盖"主题/人物冲突/精彩片段"三个维度
SUMMARY_QUERIES = ["这本书的核心主题与整体内容", "主要人物与核心冲突", "最精彩动人的情节片段"]

_CHAPTER_RE = re.compile(r'^\s*(第[零一二三四五六七八九十百千0-9]+[章卷回节部篇]|楔子|序章|尾声)[^\n]*$', re.M)


# ---------- 全文获取 ----------
def get_full_text(book_id: int):
    """经后端详情接口取 content_file_path，再从 media 目录读全文；失败返回 None。"""
    try:
        resp = httpx.get(f"{BACKEND_API_BASE}/books/{book_id}/", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        rel = (data.get("data") or data).get("content_file_path")
        if not rel:
            return None
        path = os.path.normpath(os.path.join(BOOK_CONTENT_ROOT, rel))
        if not os.path.isfile(path):
            logger.warning("全文文件不存在: %s", path)
            return None
        with open(path, encoding="utf-8-sig") as f:
            text = f.read().strip()
        return text or None
    except Exception as e:  # noqa: BLE001
        logger.warning("获取全文失败(book_id=%s): %s", book_id, e)
        return None


# ---------- 结构感知切分 ----------
def split_book(text: str) -> list:
    """章 → 段聚合切分，返回 [{text, chapter, position}]，块不跨章。"""
    marks = list(_CHAPTER_RE.finditer(text))
    if marks:
        bounds = [m.start() for m in marks] + [len(text)]
        chapters = [(i + 1, text[bounds[i]:bounds[i + 1]]) for i in range(len(marks))]
        if marks[0].start() > 200:                       # 章前有前言等内容
            chapters.insert(0, (0, text[:marks[0].start()]))
    else:
        chapters = [(1, text)]

    chunks = []
    for ch_no, ch_text in chapters:
        paras = [p.strip() for p in ch_text.split("\n") if p.strip()]
        buf = ""
        for p in paras:
            if len(buf) + len(p) > CHUNK_TARGET and buf:
                chunks.append({"text": buf, "chapter": ch_no})
                buf = buf[-CHUNK_OVERLAP:] + "\n" + p    # 章内重叠
            else:
                buf = (buf + "\n" + p) if buf else p
            while len(buf) > CHUNK_TARGET * 2:           # 超长段落按长度硬切
                chunks.append({"text": buf[:CHUNK_TARGET], "chapter": ch_no})
                buf = buf[CHUNK_TARGET - CHUNK_OVERLAP:]
        if buf.strip():
            chunks.append({"text": buf, "chapter": ch_no})

    n = max(len(chunks) - 1, 1)
    for i, c in enumerate(chunks):
        c["position"] = round(i / n, 3)                  # 位置比例 0~1
    return chunks


# ---------- 向量化 ----------
_embed_client = None

def _client() -> OpenAI:
    global _embed_client
    if _embed_client is None:
        _embed_client = OpenAI(api_key=settings.api_key, base_url=settings.base_url, timeout=60)
    return _embed_client


def embed_texts(texts: list) -> np.ndarray:
    """批量向量化（每批 ≤10 条，百炼限制内保守取值）。"""
    vecs = []
    for i in range(0, len(texts), 10):
        resp = _client().embeddings.create(model=EMBED_MODEL, input=texts[i:i + 10])
        vecs.extend(d.embedding for d in resp.data)
    arr = np.array(vecs, dtype=np.float32)
    return arr / (np.linalg.norm(arr, axis=1, keepdims=True) + 1e-9)


# ---------- 检索：BM25 + 向量 → RRF → MMR ----------
def _rrf(rank_lists: list, k: int = 60) -> dict:
    scores = {}
    for ranks in rank_lists:
        for r, idx in enumerate(ranks):
            scores[idx] = scores.get(idx, 0.0) + 1.0 / (k + r + 1)
    return scores


def _mmr(cand: list, cand_vecs: np.ndarray, q_vec: np.ndarray, k: int, lam: float = 0.7) -> list:
    """最大边际相关：兼顾与查询的相关性和已选素材的多样性。"""
    picked = []
    rel = cand_vecs @ q_vec
    while cand and len(picked) < k:
        if not picked:
            j = int(np.argmax([rel[i] for i in range(len(cand))]))
        else:
            pv = cand_vecs[[c[1] for c in picked]]
            div = cand_vecs @ pv.T
            scores = [lam * rel[i] - (1 - lam) * float(div[i].max()) for i in range(len(cand))]
            j = int(np.argmax(scores))
        picked.append((cand[j], j))
        cand = cand[:j] + cand[j + 1:]
        cand_vecs = np.delete(cand_vecs, j, axis=0)
        rel = np.delete(rel, j)
    return [p[0] for p in picked]


def retrieve(chunks: list, vecs: np.ndarray, queries: list = None, k: int = FINAL_K) -> list:
    """双路召回 + RRF 融合 + MMR 精选，返回素材块列表（已按防剧透过滤）。"""
    queries = queries or SUMMARY_QUERIES
    texts = [c["text"] for c in chunks]
    bm25 = BM25Okapi([list(jieba.cut(t)) for t in texts])
    q_vecs = embed_texts(queries)

    rank_lists = []
    for qi, q in enumerate(queries):
        bm_rank = list(np.argsort(-np.array(bm25.get_scores(list(jieba.cut(q))))))[:RECALL_K]
        vec_rank = list(np.argsort(-(vecs @ q_vecs[qi])))[:RECALL_K]
        rank_lists += [bm_rank, vec_rank]

    fused = sorted(_rrf(rank_lists).items(), key=lambda x: -x[1])
    cand_idx = [i for i, _ in fused if chunks[i]["position"] <= SPOILER_POS][:RECALL_K]
    if not cand_idx:
        cand_idx = [i for i, _ in fused][:RECALL_K]

    q_center = q_vecs.mean(axis=0)
    q_center /= (np.linalg.norm(q_center) + 1e-9)
    sel = _mmr(cand_idx, vecs[cand_idx], q_center, k)
    sel.sort(key=lambda i: chunks[i]["position"])        # 按原文顺序输出，利于叙事连贯
    return [chunks[i] for i in sel]


# ---------- 缓存 ----------
def _cache_path(book_id: int) -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    return os.path.join(CACHE_DIR, f"book_{book_id}.json")


def load_cache(book_id: int):
    try:
        with open(_cache_path(book_id), encoding="utf-8") as f:
            return json.load(f)
    except Exception:  # noqa: BLE001
        return None


def save_cache(book_id: int, data: dict):
    try:
        with open(_cache_path(book_id), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception as e:  # noqa: BLE001
        logger.warning("写缓存失败: %s", e)


# ---------- 对外主函数 ----------
def get_summary_material(book_id: int):
    """返回 (素材文本, 模式)；素材不可得返回 (None, 原因)。

    模式：full=小书全文直通；rag=检索素材；cached_summary=命中成品摘要缓存。
    """
    cache = load_cache(book_id) or {}
    if cache.get("summary"):
        return cache["summary"], "cached_summary"

    text = get_full_text(book_id)
    if not text:
        return None, "no_fulltext"

    if len(text) <= FULLTEXT_DIRECT_LIMIT:
        return text, "full"

    if cache.get("chunks") and cache.get("vecs"):
        chunks, vecs = cache["chunks"], np.array(cache["vecs"], dtype=np.float32)
    else:
        chunks = split_book(text)
        vecs = embed_texts([c["text"] for c in chunks])
        save_cache(book_id, {"chunks": chunks, "vecs": vecs.tolist()})

    material = retrieve(chunks, vecs)
    joined = "\n\n---\n\n".join(
        f"【第{c['chapter']}章 · 位置{int(c['position'] * 100)}%】\n{c['text']}" for c in material
    )
    return joined, "rag"


def cache_summary(book_id: int, summary: str):
    data = load_cache(book_id) or {}
    data["summary"] = summary
    save_cache(book_id, data)
