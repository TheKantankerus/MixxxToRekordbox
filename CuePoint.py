from typing import List
from utils.random_id import generate_random_number


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


class CuePointCollection(dict):
    def __init__(
        self,
        track_filename: str,
        initial_cue_points: List[CuePoint] = None,
        id: str = generate_random_number(8),
        length: int = 999,
    ):
        if initial_cue_points is None:
            initial_cue_points: List[CuePoint] = list()
        self.cue_points: List[CuePoint] = initial_cue_points
        self.track_filename: str = track_filename
        self.id: str = id
        self.length: int = length
        super().__init__(
            self, cue_points=self.cue_points, track_filename=self.track_filename
        )

    def add_new_cue_point(self, cue_point: CuePoint):
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
