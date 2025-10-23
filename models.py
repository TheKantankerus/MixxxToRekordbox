from dataclasses import dataclass, field
from enum import StrEnum, auto
from typing import Literal
from offset_handlers import get_offset_sec
from proto.beats_pb2 import BeatGrid, BeatMap

CollectionType = Literal["playlists", "crates"]


SERATO_COLOURS = [
    "0xc02626",  # Red
    "0xf8821a",  # Orange
    "0xfac313",  # Yellow
    "0x1fad26",  # Green
    "0x00FFFF",  # Cyan
    "0x173ba2",  # Blue
    "0x6823b6",  # Indigo
    "0xce359e",  # Light Magenta
]

# 0 star = "0", 1 star = "51", 2 stars = "102", 3 stars = "153", 4 stars = "204", 5 stars = "255"
RATING_MAP = {0: 0, 1: 51, 2: 102, 3: 153, 4: 204, 5: 255}


class KeyType(StrEnum):
    LANCELOT = auto()
    MUSICAL = auto()


LancelotKey = Literal[
    "1A",
    "1B",
    "2A",
    "2B",
    "3A",
    "3B",
    "4A",
    "4B",
    "5A",
    "5B",
    "6A",
    "6B",
    "7A",
    "7B",
    "8A",
    "8B",
    "9A",
    "9B",
    "10A",
    "10B",
    "11A",
    "11B",
    "12A",
    "12B",
]
MusicalKey = Literal[
    "A",
    "Am",
    "Ab",
    "Abm",
    "C",
    "Cm",
    "D",
    "Dm",
    "Db",
    "Dbm",
    "E",
    "Em",
    "Eb",
    "Ebm",
    "F",
    "Fm",
    "F#",
    "F#m",
    "G",
    "Gm",
    "Bb",
    "Bbm",
    "B",
    "Bm",
]

LANCELOT_MAP: dict[int, LancelotKey] = {
    21: "1A",
    12: "1B",
    16: "2A",
    7: "2B",
    23: "3A",
    2: "3B",
    18: "4A",
    9: "4B",
    13: "5A",
    4: "5B",
    20: "6A",
    11: "6B",
    15: "7A",
    6: "7B",
    22: "8A",
    1: "8B",
    17: "9A",
    8: "9B",
    24: "10A",
    3: "10B",
    19: "11A",
    10: "11B",
    14: "12A",
    5: "12B",
    0: "",
}

MUSICAL_MAP: dict[int, MusicalKey] = {
    21: "Abm",
    12: "B",
    16: "Ebm",
    7: "F#",
    23: "Bbm",
    2: "Db",
    18: "Fm",
    9: "Ab",
    13: "Cm",
    4: "Eb",
    20: "Gm",
    11: "Bb",
    15: "Dm",
    6: "F",
    22: "Am",
    1: "C",
    17: "Em",
    8: "G",
    24: "Bm",
    3: "D",
    19: "F#m",
    10: "A",
    14: "Dbm",
    5: "E",
    0: "",
}


def get_key(key_id: str, key_type: KeyType) -> str:
    match key_type:
        case KeyType.LANCELOT:
            return LANCELOT_MAP[key_id]
        case KeyType.MUSICAL:
            return MUSICAL_MAP[key_id]


def frame_pos_to_sec(frame: int, samplerate: float) -> float:
    return frame / samplerate


def frame_pos_to_inizio_sec(
    frame_pos: int, samplerate: float, bpm: float, beats_per_bar: int = 4
) -> float:
    hot_cue_sec = frame_pos_to_sec(frame_pos, samplerate)
    interval_sec = 60 / bpm
    return hot_cue_sec % (beats_per_bar * interval_sec)


BeatsVersion = Literal["BeatGrid-2.0", "BeatMap-1.0"]


@dataclass
class BeatGridInfo:
    start_pos: int
    beats_version: BeatsVersion
    samplerate: float
    bpm: float | None = None
    offset_sec: float = 0.0

    def __init__(
        self,
        beat_bytes: bytes,
        beats_version: BeatsVersion,
        samplerate: float,
    ):
        self.beats_version = beats_version
        self.samplerate = samplerate
        match beats_version:
            case "BeatGrid-2.0":
                beatgrid = BeatGrid()
                beatgrid.ParseFromString(beat_bytes)
                self.start_pos = beatgrid.first_beat.frame_position
                self.bpm = beatgrid.bpm.bpm
            case "BeatMap-1.0":
                # Just use the first available beat for now, we can get BPM from the track context
                beatmap = BeatMap()
                beatmap.ParseFromString(beat_bytes)
                first_beat = next(
                    beat
                    for beat in sorted(beatmap.beat, key=lambda b: -b.source)
                    if beat.enabled and beat.frame_position > 1
                )
                self.start_pos = first_beat.frame_position

    @property
    def start_sec(self) -> float:
        if not self.bpm:
            return frame_pos_to_sec(self.start_pos, self.samplerate) + self.offset_sec
        return (
            frame_pos_to_inizio_sec(self.start_pos, self.samplerate, self.bpm)
            + self.offset_sec
        )


@dataclass
class TrackContext:
    id: str
    title: str
    artist: str
    album: str
    genre: str
    duration: int
    location: str
    samplerate: int
    channels: int
    bpm: float
    key: LancelotKey | MusicalKey
    rating: int
    colour: str


@dataclass
class CueColour:
    hex_rgb: hex  # 0xRRGGBB

    @property
    def r_int(self) -> int:
        return int(self.hex_rgb[:4], 0)

    @property
    def g_int(self) -> int:
        return int(self.hex_rgb[:2] + self.hex_rgb[4:6], 0)

    @property
    def b_int(self) -> int:
        return int(self.hex_rgb[:2] + self.hex_rgb[6:8], 0)


@dataclass
class CuePoint(dict):
    cue_type: hex
    cue_index: int
    cue_position: float
    cue_color: CueColour
    cue_text: str = ""


@dataclass
class ExportedTrack:
    id: str
    track_context: TrackContext
    beat_grid: BeatGridInfo | None = None
    cue_points: list[CuePoint] = field(default_factory=list)
    offset_sec: float = 0.0

    def __init__(
        self,
        id: str,
        track_context: TrackContext,
        beat_grid: BeatGridInfo | None,
        cue_points: list[CuePoint],
    ):
        self.id = id
        self.track_context = track_context
        self.offset_sec = get_offset_sec(self.track_context.location)
        if beat_grid:
            self._add_beat_grid(beat_grid)
        self.cue_points = []
        for cue_point in cue_points:
            self._add_new_cue_point(cue_point)

    def _add_beat_grid(self, beat_grid: BeatGridInfo):
        beat_grid.offset_sec = self.offset_sec
        beat_grid.bpm = beat_grid.bpm or self.track_context.bpm
        self.beat_grid = beat_grid

    def _add_new_cue_point(self, cue_point: CuePoint):
        if not len(cue_point.cue_color.hex_rgb) == 8:
            cue_point.cue_color.hex_rgb = SERATO_COLOURS[
                len(self.cue_points) % len(SERATO_COLOURS)
            ]
        cue_point.cue_position += self.offset_sec
        self.cue_points.append(cue_point)


class CuePointNotFoundException(Exception):
    pass


class NotACuePointFileException(Exception):
    pass
