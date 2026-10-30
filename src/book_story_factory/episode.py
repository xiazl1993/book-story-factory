"""Generate a six-shot illustrated episode from a verified story card."""
from __future__ import annotations

import json
from pathlib import Path


REQUIRED = ("title", "protagonist", "setting", "conflict", "decision", "outcome", "insight")
DURATIONS = (6, 10, 11, 12, 12, 9)
TITLES = ("悬念钩子", "人物和时代", "冲突升级", "关键选择", "结局与代价", "观点点题")
STYLE = (
    "竖屏9:16，中国历史叙事厚涂插画，低饱和暖灰、墨绿和暗金，"
    "自然光，纸张肌理，人物身份和服装跨镜头稳定，"
    "无文字无水印，上下保留字幕安全区；艺术化演绎，不是历史文献照片。"
)


def _timecode(seconds: int) -> str:
    hrs, remain = divmod(seconds, 3600)
    mins, secs = divmod(remain, 60)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},000"


def make_episode(story_path: Path, out: Path) -> dict:
    story = json.loads(story_path.read_text(encoding="utf-8"))
    missing = [field for field in REQUIRED if not str(story.get(field, "")).strip()]
    if missing:
        raise ValueError("Story fields missing: " + ", ".join(missing))

    narration = [
        f"如果你是{story['protagonist']}，面对这样的难题，会怎么选？",
        f"故事发生在{story['setting']}。{story['protagonist']}的处境并不轻松。",
        str(story["conflict"]),
        f"关键时刻，{story['protagonist']}做出一个决定：{story['decision']}",
        str(story["outcome"]),
        f"这个故事最值得思考的，是{story['insight']}。",
    ]
    visuals = [
        f"{story['protagonist']}，充满悬念的开场肖像，克制而紧张",
        f"{story['setting']}，建立时代与人物关系的远景",
        f"{story['conflict']}，人物遭遇挑战的中景",
        f"{story['decision']}，人物做出选择的动作近景",
        f"{story['outcome']}，结果揭晓的宽幅叙事镜头",
        f"{story['insight']}，棋盘和人物背影的收束画面",
    ]
    out.mkdir(parents=True, exist_ok=True)
    (out / "images").mkdir(exist_ok=True)
    (out / "audio").mkdir(exist_ok=True)
    elapsed = 0
    shots: list[dict] = []
    subtitles: list[str] = []
    for i, (title, words, image, seconds) in enumerate(
        zip(TITLES, narration, visuals, DURATIONS), 1
    ):
        shots.append({
            "shot": i, "title": title, "duration": seconds, "narration": words,
            "image_file": f"images/{i:02d}.png",
            "prompt": f"{STYLE} 人物：{story['protagonist']}。场景：{image}。",
        })
        subtitles.append(f"{i}\n{_timecode(elapsed)} --> {_timecode(elapsed+seconds)}\n{words}\n")
        elapsed += seconds

    result = {
        "title": story["title"],
        "source": story.get("source", {"type": "unknown"}),
        "source_checked": bool(story.get("source_checked", False)),
        "total_seconds": elapsed,
        "shots": shots,
    }
    (out / "storyboard.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out / "voiceover.txt").write_text("\n".join(narration) + "\n", encoding="utf-8")
    (out / "subtitles.srt").write_text("\n".join(subtitles), encoding="utf-8")
    (out / "script.md").write_text(
        "# " + story["title"] + "\n\n" +
        "\n\n".join(f"## {i}. {TITLES[i-1]}（{DURATIONS[i-1]}秒）\n{line}"
                    for i, line in enumerate(narration, 1)) +
        "\n\n> 这是模板初稿。书籍来源、历史事实、用词与节奏需人工审核。\n",
        encoding="utf-8",
    )
    (out / "prompts.md").write_text(
        "# 插画提示词\n\n" +
        "\n\n".join(f"## 镜头 {shot['shot']:02d}｜{shot['title']}\n{shot['prompt']}"
                    for shot in shots) + "\n",
        encoding="utf-8",
    )
    (out / "manifest.json").write_text(
        json.dumps({"status": "storyboard_ready", "images_required": 6,
                    "voice_recording_required": True, "needs_fact_review": True},
                   ensure_ascii=False, indent=2), encoding="utf-8",
    )
    return result
