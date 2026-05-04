from pathlib import Path
import subprocess

from app.tools.mux_video import mux_video_with_audio, require_ffmpeg


def test_mux_video_builds_mp4_loop_mode(tmp_path: Path):
    require_ffmpeg()

    video = tmp_path / "loop.mp4"
    audio = tmp_path / "audio.wav"
    output = tmp_path / "final.mp4"

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc=size=320x180:rate=24:duration=1",
            "-pix_fmt",
            "yuv420p",
            str(video),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=330:duration=2",
            str(audio),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    mux_video_with_audio(
        video,
        audio,
        output,
        mode="loop",
        video_bitrate="1000k",
        audio_bitrate="128k",
        keep_temp=False,
        quiet=True,
    )

    assert output.exists()
    assert output.stat().st_size > 0
