"""Optional Chat Completions extraction, anchored to exact source excerpts."""
from __future__ import annotations
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

REQUIRED = ("title", "protagonist", "setting", "conflict", "decision", "outcome", "insight")
PROMPT = (
    "你是历史案例提取助手，只从用户给出的书籍文本寻找完整且有独立情节的案例。"
    "不得补充正文未交代的史实、动机和结局。没有完整故事时返回空数组。"
    "必须只返回 JSON 对象，字段 stories 为数组。每项含 title, protagonist, setting, "
    "conflict, decision, outcome, insight, source_quote，所有字段均为字符串。"
    "source_quote 是正文连续原样出现的10至80字短证据。不输出 Markdown。"
)


def _chat_json(chunk: dict) -> dict:
    key = os.environ.get("OPENAI_COMPAT_API_KEY")
    model = os.environ.get("OPENAI_COMPAT_MODEL")
    if not key or not model:
        raise RuntimeError("Set OPENAI_COMPAT_API_KEY and OPENAI_COMPAT_MODEL")
    base_url = os.environ.get("OPENAI_COMPAT_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    body = json.dumps({
        "model": model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": "章节：" + chunk["chapter"] + "\n原文：\n" + chunk["text"]},
        ],
    }, ensure_ascii=False).encode("utf-8")
    req = Request(base_url + "/chat/completions", data=body, method="POST",
                  headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
    try:
        with urlopen(req, timeout=120) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise RuntimeError("Model API request failed; inspect your provider configuration") from exc
    content = payload["choices"][0]["message"]["content"]
    if not isinstance(content, str):
        raise ValueError("Expected JSON text in model response")
    parsed = json.loads(content)
    if not isinstance(parsed, dict) or not isinstance(parsed.get("stories"), list):
        raise ValueError("Expected JSON object with stories array")
    return parsed


def extract_stories(index_path: Path, out: Path, max_chunks: int = 3) -> dict:
    if max_chunks < 1:
        raise ValueError("max_chunks must be >= 1")
    index = json.loads(index_path.read_text(encoding="utf-8"))
    selected = index["chunks"][:max_chunks]
    accepted = []
    rejected = 0
    seen = set()
    for chunk in selected:
        for item in _chat_json(chunk)["stories"]:
            if not isinstance(item, dict):
                rejected += 1
                continue
            anchor = item.get("source_quote", "")
            if any(not isinstance(item.get(k), str) or not item[k].strip() for k in REQUIRED):
                rejected += 1
                continue
            if not isinstance(anchor, str) or not (10 <= len(anchor) <= 80) or anchor not in chunk["text"]:
                rejected += 1
                continue
            key = (item["title"], anchor)
            if key in seen:
                continue
            seen.add(key)
            story = {field: item[field] for field in REQUIRED}
            story["source"] = {
                "type": "book_reported_case",
                "book_filename": index["source_name"],
                "book_sha256": index["source_sha256"],
                "chapter": chunk["chapter"],
                "chunk_id": chunk["id"],
                "start_char": chunk["start_char"],
                "end_char": chunk["end_char"],
                "short_evidence_anchor": anchor
            }
            story["source_checked"] = False
            accepted.append(story)
    result = {
        "chunks_examined": len(selected),
        "chunks_available": len(index["chunks"]),
        "historical_facts_checked": False,
        "rejected_candidates": rejected,
        "stories": accepted
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result
