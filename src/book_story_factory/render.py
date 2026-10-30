"""Compose a storyboard and locally supplied stills into MP4 with FFmpeg."""
from __future__ import annotations
import json
import shutil
import subprocess
import tempfile
from pathlib import Path


def _ffmpeg(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)


def render_episode(episode_dir: Path, output: Path, audio: Path | None = None,
                   width: int = 1080, height: int = 1920) -> Path:
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg must be installed and available on PATH")
    if min(width, height) <= 0 or width % 2 or height % 2:
        raise ValueError("Video dimensions must be positive and even")
    data = json.loads((episode_dir / "storyboard.json").read_text(encoding="utf-8"))
    shots = data["shots"]
    if not shots:
        raise ValueError("Storyboard has no shots")
    images = []
    for shot in shots:
        path = episode_dir / shot["image_file"]
        candidates = [path] + [path.with_suffix(suffix) for suffix in (".jpg", ".jpeg", ".webp")]
        match = next((p for p in candidates if p.is_file()), None)
        if match is None:
            raise FileNotFoundError(f"Missing image for shot {shot['shot']}: {path}")
        images.append(match)
    if audio and not audio.is_file():
        raise FileNotFoundError(audio)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="book-story-") as tmp:
        temp = Path(tmp)
        clips = []
        for i, (shot, image) in enumerate(zip(shots, images), 1):
            duration = int(shot["duration"])
            if duration <= 0:
                raise ValueError("Shot duration must be positive")
            clip = temp / f"{i:02d}.mp4"
            filter_spec = (
                f"scale={width}:{height}:force_original_aspect_ratio=increase,"
                f"crop={width}:{height},setsar=1"
            )
            _ffmpeg(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                     "-loop", "1", "-framerate", "25", "-i", str(image),
                     "-t", str(duration), "-vf", filter_spec, "-r", "25",
                     "-an", "-c:v", "libx264", "-preset", "veryfast",
                     "-pix_fmt", "yuv420p", str(clip)])
            clips.append(clip)
        listing = temp / "clips.txt"
        # Temporary files have controlled, ordinary absolute paths.
        listing.write_text("".join(f"file '{p}'\n" for p in clips), encoding="utf-8")
        silent = temp / "silent.mp4"
        _ffmpeg(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                 "-f", "concat", "-safe", "0", "-i", str(listing),
                 "-c", "copy", str(silent)])
        if audio:
            total_seconds = sum(int(s["duration"]) for s in shots)
            _ffmpeg(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                     "-i", str(silent), "-i", str(audio),
                     "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
                     "-c:a", "aac", "-af", "apad", "-t", str(total_seconds),
                     str(output)])
        else:
            shutil.copyfile(silent, output)
    return output
