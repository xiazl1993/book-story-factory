"""CLI for source preparation, extraction, storyboard pack and rendering."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from .reader import prepare_book
from .episode import make_episode


def main() -> None:
    parser = argparse.ArgumentParser(prog="book-story")
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare-book", help="Build local book index")
    prepare.add_argument("source", type=Path)
    prepare.add_argument("--out", type=Path, required=True)
    prepare.add_argument("--max-chars", type=int, default=6000)
    extract = sub.add_parser("extract-stories", help="Optional LLM story extraction")
    extract.add_argument("index", type=Path)
    extract.add_argument("--out", type=Path, required=True)
    extract.add_argument("--max-chunks", type=int, default=3)
    episode = sub.add_parser("make-episode", help="Write six-shot content package")
    episode.add_argument("story", type=Path)
    episode.add_argument("--out", type=Path, required=True)
    render = sub.add_parser("render", help="Compose local images to vertical MP4")
    render.add_argument("episode", type=Path)
    render.add_argument("--out", type=Path, required=True)
    render.add_argument("--audio", type=Path)
    render.add_argument("--width", type=int, default=1080)
    render.add_argument("--height", type=int, default=1920)
    args = parser.parse_args()
    if args.command == "prepare-book":
        result = prepare_book(args.source, args.out, args.max_chars)
        summary = {"chunks": len(result["chunks"]), "total_chars": result["total_chars"]}
    elif args.command == "extract-stories":
        from .distill import extract_stories
        result = extract_stories(args.index, args.out, args.max_chunks)
        summary = {"stories": len(result["stories"]),
                   "rejected": result["rejected_candidates"],
                   "chunks_examined": result["chunks_examined"]}
    elif args.command == "make-episode":
        result = make_episode(args.story, args.out)
        summary = {"shots": len(result["shots"]), "seconds": result["total_seconds"]}
    else:
        from .render import render_episode
        out = render_episode(args.episode, args.out, args.audio, args.width, args.height)
        summary = {"output": str(out)}
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
