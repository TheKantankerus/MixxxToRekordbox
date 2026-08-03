import os
import shutil
from multiprocessing.synchronize import Semaphore
from pathlib import Path

from pydub import AudioSegment
from tinytag import TinyTag

# Prevent spawning too many processes
EXPORT_SEMAPHORE_COUNT = os.cpu_count() // 2

BITRATE_MAP = {
    "mp3": "320k",
    "aac": "256k",
}

FORMAT_MAP = {
    "opus": "ogg"
}


def get_bitrate_from_format(out_format: str) -> str | None:
    return BITRATE_MAP.get(out_format.lower())

def get_format_from_suffix(suffix: str) -> str:
    return FORMAT_MAP.get(suffix) or suffix


def transcode_track(
    track_path: Path,
    out_path: Path,
    out_format: str,
    export_semaphore: Semaphore,
    virtual_out_path: Path,
) -> str:
    in_format = track_path.suffix[1:]
    new_file = out_path.joinpath(f"{track_path.stem}.{out_format}")
    virtual_file = virtual_out_path.joinpath(f"{track_path.stem}.{out_format}")

    if new_file.exists():
        return str(virtual_file)

    if in_format == out_format:
        shutil.copy2(track_path, new_file)
        return str(virtual_file)

    if in_format == "aif":
        in_format = "aiff"

    with export_semaphore:
        segment = AudioSegment.from_file(track_path, format=get_format_from_suffix(in_format))
        tags = TinyTag.get(track_path)

        segment.export(
            new_file,
            format=out_format,
            bitrate=get_bitrate_from_format(out_format),
            tags=tags.as_dict(),
        )
    return str(virtual_out_path.joinpath(f"{track_path.stem}.{out_format}"))


def change_track_location(
    track_location: str,
    out_dir: str,
    out_format: str | None,
    export_semaphore: Semaphore,
    virtual_out_dir: str,
) -> str:
    track_path = Path(track_location)
    out_dir_path = Path(out_dir)
    virtual_out_path = Path(virtual_out_dir)
    if out_format:
        return transcode_track(track_path, out_dir_path, out_format, export_semaphore, virtual_out_path)
    else:
        out_file_path = out_dir_path.joinpath(track_path.name)
        shutil.copy2(track_path, out_file_path)
        return str(virtual_out_path.joinpath(track_path.name))
