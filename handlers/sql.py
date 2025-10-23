import functools
from os import path
import os
import sqlite3

from models import CollectionType

COLLECTION_QUERY_MAP: dict[CollectionType, str] = {
    "playlists": "SELECT id, name from Playlists where hidden is 0 ORDER BY name",
    "crates": "SELECT id, name from crates where show is 1 ORDER BY name",
}
COLLECTION_TRACKS_QUERY_MAP: dict[CollectionType, str] = {
    "playlists": "SELECT track_id FROM PlaylistTracks WHERE playlist_id = :id ORDER BY position",
    "crates": "SELECT track_id FROM crate_tracks WHERE crate_id = :id",
}

global _db_location


def get_mixxx_db_location(custom_db_location: str | None) -> str:
    if custom_db_location:
        return custom_db_location
    # Windows
    if os.getenv("LOCALAPPDATA"):
        return f"{os.getenv('LOCALAPPDATA')}\\Mixxx\\mixxxdb.sqlite"
    # MacOS
    if path.exists(r"~/Library/Application Support/Mixxx"):
        return r"~/Library/Application Support/Mixxx/mixxxdb.sqlite"
    # Linux
    if path.exists(r"~/.mixxx"):
        return r"~/.mixxx/mixxxdb.sqlite"


def set_db_location(db_location: str) -> None:
    global _db_location
    _db_location = db_location


@functools.cache
def get_connection() -> sqlite3.Connection:
    if not _db_location:
        raise Exception("Database location not set.")
    return sqlite3.connect(_db_location, check_same_thread=False)


def get_cursor() -> sqlite3.Cursor:
    return get_connection().cursor()


def get_track_info(track_id: str) -> sqlite3.Row:
    return (
        get_cursor()
        .execute(
            """
                SELECT
                    l.samplerate,
                    l.channels,
                    l.duration,
                    l.title,
                    l.artist,
                    l.album,
                    l.genre,
                    l.bpm,
                    l.beats,
                    l.beats_version,
                    l.key_id,
                    l.rating,
                    l.color,
                    tl.location
                FROM
                    library l
                INNER JOIN
                    track_locations tl
                USING (id)
                WHERE
                    id = :id
                """,
            {"id": track_id},
        )
        .fetchone()
    )


def get_cue_points(track_id: str) -> list[sqlite3.Row]:
    return (
        get_cursor()
        .execute(
            "SELECT hotcue,position,color from cues WHERE cues.type = 1 and cues.hotcue >= 0 and cues.track_id = :id",
            {"id": track_id},
        )
        .fetchall()
    )


def get_collection_tracks(collection_type: str, collection_id: str) -> list[str]:
    return [
        track[0]
        for track in get_cursor().execute(
            COLLECTION_TRACKS_QUERY_MAP[collection_type],
            {"id": collection_id},
        )
    ]


def get_collections(collection_type: str) -> list[sqlite3.Row]:
    return get_cursor().execute(COLLECTION_QUERY_MAP[collection_type]).fetchall()
