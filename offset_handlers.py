# Core logic borrowed from https://github.com/FrankwaP/mixxx-utils

from logging import ERROR
from pathlib import Path
from typing import Literal
import sys

import eyed3.mp3.headers  # type: ignore


Mp3Decoder = Literal["MAD", "CoreAudio", "FFmpeg"]
ACCEPTED_MP3_DECODERS: list[Mp3Decoder] = ["MAD", "CoreAudio", "FFmpeg"]


eyed3.core.log.setLevel(ERROR)
eyed3.id3.frames.log.setLevel(ERROR)
eyed3.mp3.headers.log.setLevel(ERROR)

OFFSET_ERROR_MESSAGES: list[str] = []


def has_xing_info(audiofile: eyed3.mp3.Mp3AudioFile) -> bool:
    return audiofile.info.xing_header is not None


def has_lame_tag(audiofile: eyed3.mp3.Mp3AudioFile) -> bool:
    return len(audiofile.info.lame_tag) > 0


def has_valid_CRC_tag(audiofile: eyed3.mp3.Mp3AudioFile) -> bool:
    try:
        return audiofile.info.lame_tag["music_crc"] > 0
    except KeyError:
        return False


def get_case_mp3(audiofile: eyed3.mp3.Mp3AudioFile) -> Literal["A", "B", "C", "D"]:
    if not has_xing_info(audiofile):
        return "A"
    elif not has_lame_tag(audiofile):
        return "B"
    elif not has_valid_CRC_tag(audiofile):
        return "C"
    else:
        return "D"


def get_offset_mp3(audiofile: eyed3.mp3.Mp3AudioFile, mp3_decoder: Mp3Decoder) -> int:
    check_mp3_decoder_value(mp3_decoder)
    #
    case = get_case_mp3(audiofile)
    if mp3_decoder == "MAD":
        if case == "A" or case == "D":
            return 26
    if mp3_decoder == "CoreAudio":
        if case == "A":
            return 13
        if case == "B":
            return 11
        if case == "C":
            return 26
        if case == "D":
            return 50
    if mp3_decoder == "FFmpeg":
        if case == "D":
            return 26
    return 0


def check_mp3_decoder_value(mp3_decoder: str) -> None:
    if mp3_decoder not in ACCEPTED_MP3_DECODERS:
        raise ValueError(
            "Incorrect value for Mixxx encoder: expecting {ACCEPTED_MP3_DECODERS}"
        )


def get_offset_ms(
    track_path: str | Path, source_path: str | Path, mp3_decoder: Mp3Decoder
) -> int:
    in_format = Path(source_path).suffix
    out_format = Path(track_path).suffix
    if out_format == ".m4a":
        return 48
    elif in_format == out_format == ".mp3":
        try:
            audiofile = eyed3.load(track_path)
            return get_offset_mp3(audiofile, mp3_decoder)
        except Exception as ex:
            OFFSET_ERROR_MESSAGES.append(f"{track_path}: {ex}")
            return 0
    elif in_format == ".flac" and out_format == ".wav":
        return 26
    elif in_format == ".flac" and out_format == ".mp3":
        return 26

    print(
        f"Warning: transcoding from {in_format} to {out_format} is experimental and may result in misaligned cues",
        file=sys.stderr
    )

    return 0


def get_offset_sec(
    track_path: str | Path, source_path: str | Path, mp3_decoder: Mp3Decoder = "MAD"
) -> float:
    return get_offset_ms(track_path, source_path, mp3_decoder) / 1000.0


def flush_offset_errors() -> None:
    if not OFFSET_ERROR_MESSAGES:
        return
    print("Unable to determine offsets for the following tracks:")
    for error_message in OFFSET_ERROR_MESSAGES:
        print(error_message)
    OFFSET_ERROR_MESSAGES.clear()
