from pathlib import Path

from app.tools.crossfade import build_mix, require_ffmpeg


def test_crossfade_builds_mp3(tmp_path: Path):
    require_ffmpeg()

    track1 = tmp_path / "track1.wav"
    track2 = tmp_path / "track2.wav"
    output = tmp_path / "mix.mp3"

    import subprocess

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=220:duration=2",
            str(track1),
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
            "sine=frequency=440:duration=2",
            str(track2),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    build_mix(
        [track1, track2],
        output,
        seconds=0.5,
        bitrate="128k",
        keep_temp=False,
        quiet=True,
    )

    assert output.exists()
    assert output.stat().st_size > 0
