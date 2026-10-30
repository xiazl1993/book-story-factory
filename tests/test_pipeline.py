import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from book_story_factory.reader import build_index
from book_story_factory.episode import make_episode
from book_story_factory.distill import extract_stories

REPO = Path(__file__).resolve().parents[1]


class PipelineTests(unittest.TestCase):
    def test_source_positions(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "book.txt"
            source = "第一章 开端\n" + "这是一段原创测试文本。\n" * 100 + "第二章 转折\n" + "又一段测试文本。\n" * 100
            path.write_text(source, encoding="utf-8")
            result = build_index(path, max_chars=500)
            self.assertGreaterEqual(len(result["chunks"]), 3)
            for chunk in result["chunks"]:
                self.assertEqual(
                    chunk["text"], source[chunk["start_char"]:chunk["end_char"]]
                )
            self.assertTrue(any("第二章" in c["chapter"] for c in result["chunks"]))

    def test_episode_outputs_six_shots_and_srt(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "episode"
            result = make_episode(REPO / "examples/story.demo.json", out)
            self.assertEqual(6, len(result["shots"]))
            self.assertEqual(60, result["total_seconds"])
            self.assertFalse(result["source_checked"])
            self.assertIn("00:01:00,000", (out / "subtitles.srt").read_text(encoding="utf-8"))
            self.assertTrue((out / "prompts.md").is_file())
            self.assertTrue((out / "storyboard.json").is_file())

    def test_unanchored_model_story_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            directory = Path(td)
            index = {
                "source_name": "book.txt", "source_sha256": "demo",
                "chunks": [{
                    "id": "chunk-0001", "chapter": "第一章",
                    "start_char": 0, "end_char": 100,
                    "text": "这个故事发生于大雨之夜，主人公决定先撤离城中百姓，再等待援军。"
                }]
            }
            index_path = directory / "index.json"
            index_path.write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")
            basic = {
                "title": "演示", "protagonist": "主人公", "setting": "雨夜",
                "conflict": "城池危急", "decision": "撤离百姓",
                "outcome": "等待援军", "insight": "先保护生命"
            }
            good = {**basic, "source_quote": "主人公决定先撤离城中百姓，再等待援军"}
            bad = {**basic, "source_quote": "这是原文中根本就不存在的伪造句子"}
            with patch("book_story_factory.distill._chat_json", return_value={"stories": [good, bad]}):
                result = extract_stories(index_path, directory / "stories.json", 1)
            self.assertEqual(1, len(result["stories"]))
            self.assertEqual(1, result["rejected_candidates"])
            self.assertFalse(result["stories"][0]["source_checked"])


if __name__ == "__main__":
    unittest.main()
