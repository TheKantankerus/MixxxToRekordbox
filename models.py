from dataclasses import dataclass, field

from utils.random_id import generate_random_number

SERATO_COLOURS = [
    "c02626",  # Red
    "f8821a",  # Orange
    "fac313",  # Yellow
    "1fad26",  # Green
    "00FFFF",  # Cyan
    "173ba2",  # Blue
    "6823b6",  # Indigo
    "ce359e",  # Light Magenta
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


class CuePoint(dict):
    def __init__(
        self,
        cue_type=0x00,
        cue_index=0,
        cue_position=0,
        cue_color="000000",
        cue_text: str = "",
    ):
        self.cue_type: hex = cue_type
        self.cue_index: int = cue_index
        self.cue_position: float = cue_position
        self.cue_color: str = cue_color
        self.cue_text: str = cue_text
        super().__init__(
            self,
            cue_type=cue_type,
            cue_index=cue_index,
            cue_position=cue_position,
            cue_color=cue_color,
            cue_text=cue_text,
        )

    def __repr__(self):
        return str(
            {
                "cue_type": self.cue_type,
                "cue_index": self.cue_index,
                "cue_position": self.cue_position,
                "cue_color": self.cue_color,
                "cue_text": self.cue_text,
            }
        )


@dataclass
class CuePointCollection:
    id: str
    track_context: TrackContext
    cue_points: list[CuePoint] = field(default_factory=list)

    def add_new_cue_point(self, cue_point: CuePoint):
        cue_point.cue_color = SERATO_COLOURS[len(self.cue_points) % len(SERATO_COLOURS)]
        self.cue_points.append(cue_point)

    def __repr__(self):
        return str(
            {
                "track_filename": self.track_filename,
                "cue_points": self.cue_points,
                "id": self.id,
                "length": self.length,
            }
        )


class CuePointNotFoundException(Exception):
    pass


class NotACuePointFileException(Exception):
    pass
