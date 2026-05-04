from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path


def require_ffmpeg() -> None:
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg is required but was not found.")


def run(cmd: list[str], *, quiet: bool = False) -> None:
    if not quiet:
        print(" ".join(cmd))
    result = subprocess.run(cmd, text=True)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def validate_inputs(paths: list[Path]) -> None:
    if len(paths) < 2:
        raise SystemExit("Need at least 2 tracks to crossfade.")

    for path in paths:
        if not path.exists():
            raise SystemExit(f"Missing input file: {path}")


def convert_to_wav(source: Path, dest: Path, *, quiet: bool) -> None:
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(source),
            "-ar",
            "44100",
            "-ac",
            "2",
            "-sample_fmt",
            "s16",
            str(dest),
        ],
        quiet=quiet,
    )


def crossfade_pair(current_mix: Path, next_track: Path, dest: Path, seconds: float, *, quiet: bool) -> None:
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(current_mix),
            "-i",
            str(next_track),
            "-filter_complex",
            f"[0:a][1:a]acrossfade=d={seconds}:c1=tri:c2=tri[a]",
            "-map",
            "[a]",
            str(dest),
        ],
        quiet=quiet,
    )


def export_mp3(source_wav: Path, output_mp3: Path, bitrate: str, *, quiet: bool) -> None:
    output_mp3.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(source_wav),
            "-codec:a",
            "libmp3lame",
            "-b:a",
            bitrate,
            str(output_mp3),
        ],
        quiet=quiet,
    )


def build_mix(inputs: list[Path], output: Path, seconds: float, bitrate: str, keep_temp: bool, quiet: bool) -> Path:
    require_ffmpeg()
    validate_inputs(inputs)

    temp_context = tempfile.TemporaryDirectory(prefix="drakonya_crossfade_")
    temp_dir = Path(temp_context.name)

    print(f"Preparing {len(inputs)} tracks...")

    wavs: list[Path] = []
    for index, source in enumerate(inputs, start=1):
        wav = temp_dir / f"track_{index:03d}.wav"
        print(f"[{index}/{len(inputs)}] Preparing {source.name}")
        convert_to_wav(source, wav, quiet=quiet)
        wavs.append(wav)

    current = wavs[0]

    print("Crossfading tracks...")
    for index, next_track in enumerate(wavs[1:], start=2):
        dest = temp_dir / f"mix_{index:03d}.wav"
        print(f"[{index - 1}/{len(wavs) - 1}] Crossfading into {next_track.name}")
        crossfade_pair(current, next_track, dest, seconds, quiet=quiet)
        current = dest

    print(f"Exporting final MP3: {output}")
    export_mp3(current, output, bitrate, quiet=quiet)

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
    parser = argparse.ArgumentParser(description="Crossfade multiple audio tracks into one MP3.")
    parser.add_argument("tracks", nargs="+", help="Input audio files")
    parser.add_argument("--seconds", type=float, default=3.0, help="Crossfade duration in seconds")
    parser.add_argument("--output", default="drakonya_mix.mp3", help="Output MP3 path")
    parser.add_argument("--bitrate", default="320k", help="MP3 bitrate")
    parser.add_argument("--keep-temp", action="store_true", help="Keep temp WAV files")
    parser.add_argument("--quiet", action="store_true", help="Hide ffmpeg command output")
    args = parser.parse_args()

    build_mix(
        [Path(track) for track in args.tracks],
        Path(args.output),
        args.seconds,
        args.bitrate,
        args.keep_temp,
        args.quiet,
    )


if __name__ == "__main__":
    main()
