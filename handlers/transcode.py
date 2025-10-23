import os
from pydub import AudioSegment
from pathlib import Path
import shutil

from tinytag import TinyTag

from multiprocessing.synchronize import Semaphore

# Prevent spawning too many processes
EXPORT_SEMAPHORE_COUNT = os.cpu_count() // 2

BITRATE_MAP = {
    "mp3": "320k",
    "aac": "256k",
}


def get_bitrate_from_format(out_format: str) -> str | None:
    return BITRATE_MAP.get(out_format.lower())


def transcode_track(
    track_path: Path, out_path: Path, out_format: str, export_semaphore: Semaphore
) -> str:
    with export_semaphore:
        segment = AudioSegment.from_file(track_path, format=track_path.suffix[1:])
        tags = TinyTag.get(track_path)
        new_file = out_path.joinpath(f"{track_path.stem}.{out_format}")
        segment.export(
            new_file,
            format=out_format,
            bitrate=get_bitrate_from_format(out_format),
            tags=tags.as_dict(),
        )
    return str(new_file)


def change_track_location(
    track_location: str,
    out_dir: str,
    out_format: str | None,
    export_semaphore: Semaphore,
) -> str:
    track_path = Path(track_location)
    out_dir_path = Path(out_dir)
    if out_format:
        return transcode_track(track_path, out_dir_path, out_format, export_semaphore)
    else:
        out_file_path = out_dir_path.joinpath(track_path.name)
        shutil.copy2(track_path, out_file_path)
        return str(out_file_path)
