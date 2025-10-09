from dataclasses import dataclass, field


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
    cue_points: list[CuePoint] = field(default_factory=list)

    def add_new_cue_point(self, cue_point: CuePoint):
        if not len(cue_point.cue_color.hex_rgb) == 8:
            cue_point.cue_color.hex_rgb = SERATO_COLOURS[
                len(self.cue_points) % len(SERATO_COLOURS)
            ]
        self.cue_points.append(cue_point)


class CuePointNotFoundException(Exception):
    pass


class NotACuePointFileException(Exception):
    pass
