from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path


def require_ffmpeg() -> None:
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg is required but was not found.")

    if not shutil.which("ffprobe"):
        raise SystemExit("ffprobe is required but was not found.")


def run(cmd: list[str], *, quiet: bool = False) -> None:
    if not quiet:
        print(" ".join(cmd))
    result = subprocess.run(cmd, text=True)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def probe_duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def create_pingpong_video(source: Path, dest: Path, *, quiet: bool) -> None:
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(source),
            "-filter_complex",
            "[0:v]reverse[r];[0:v][r]concat=n=2:v=1:a=0[v]",
            "-map",
            "[v]",
            "-an",
            str(dest),
        ],
        quiet=quiet,
    )


def mux_video_with_audio(
    video: Path,
    audio: Path,
    output: Path,
    *,
    mode: str,
    video_bitrate: str,
    audio_bitrate: str,
    keep_temp: bool,
    quiet: bool,
) -> Path:
    require_ffmpeg()

    if not video.exists():
        raise SystemExit(f"Missing video file: {video}")

    if not audio.exists():
        raise SystemExit(f"Missing audio file: {audio}")

    if mode not in {"loop", "pingpong"}:
        raise SystemExit("Mode must be 'loop' or 'pingpong'.")

    output.parent.mkdir(parents=True, exist_ok=True)

    temp_context = tempfile.TemporaryDirectory(prefix="drakonya_mux_")
    temp_dir = Path(temp_context.name)

    working_video = video

    if mode == "pingpong":
        print("Creating ping-pong video loop...")
        working_video = temp_dir / "pingpong.mp4"
        create_pingpong_video(video, working_video, quiet=quiet)

    audio_duration = probe_duration(audio)
    print(f"Audio duration: {audio_duration:.2f}s")
    print(f"Exporting final video: {output}")

    run(
        [
            "ffmpeg",
            "-y",
            "-stream_loop",
            "-1",
            "-i",
            str(working_video),
            "-i",
            str(audio),
            "-t",
            str(audio_duration),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-b:v",
            video_bitrate,
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            audio_bitrate,
            "-shortest",
            str(output),
        ],
        quiet=quiet,
    )

    if keep_temp:
        keep_path = output.with_suffix(".temp")
        if keep_path.exists():
            shutil.rmtree(keep_path)
        shutil.copytree(temp_dir, keep_path)
        print(f"Kept temp files at: {keep_path}")

    temp_context.cleanup()
    print(f"Done: {output}")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Loop or ping-pong a video and mux it with an audio track.")
    parser.add_argument("video", help="Input video loop")
    parser.add_argument("audio", help="Input audio file")
    parser.add_argument("--output", default="drakonya_video.mp4", help="Output MP4 path")
    parser.add_argument("--mode", choices=["loop", "pingpong"], default="loop", help="Video repeat mode")
    parser.add_argument("--video-bitrate", default="8000k", help="Video bitrate")
    parser.add_argument("--audio-bitrate", default="192k", help="Audio bitrate")
    parser.add_argument("--keep-temp", action="store_true", help="Keep temp files")
    parser.add_argument("--quiet", action="store_true", help="Hide ffmpeg command output")
    args = parser.parse_args()

    mux_video_with_audio(
        Path(args.video),
        Path(args.audio),
        Path(args.output),
        mode=args.mode,
        video_bitrate=args.video_bitrate,
        audio_bitrate=args.audio_bitrate,
        keep_temp=args.keep_temp,
        quiet=args.quiet,
    )


if __name__ == "__main__":
    main()
