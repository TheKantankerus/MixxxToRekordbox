import os
from os import path
from utils.random_id import generate_random_number
from typing import List
from models import CueColour, CuePoint, ExportedTrack, TrackContext
import sqlite3
from tqdm import tqdm
import rekordbox_gen


CUSTOM_DB_LOCATION = r""  # Change if your DB is not in the default location


def get_mixxx_db_location() -> str:
    if CUSTOM_DB_LOCATION:
        return CUSTOM_DB_LOCATION
    # Windows
    if os.getenv("LOCALAPPDATA"):
        return f"{os.getenv('LOCALAPPDATA')}\\Mixxx\\mixxxdb.sqlite"
    # MacOS
    if path.exists(r"~/Library/Application Support/Mixxx"):
        return r"~/Library/Application Support/Mixxx/mixxxdb.sqlite"
    # Linux
    if path.exists(r"~/.mixxx"):
        return r"~/.mixxx/mixxxdb.sqlite"


def mixxx_cuepos_to_ms(cuepos: int, samplerate: int, channels: int):
    return int((cuepos * 1000.0) / (samplerate * channels))


def main():
    con = sqlite3.connect(get_mixxx_db_location())
    cur = con.cursor()

    playlists = [
        playlist
        for playlist in cur.execute("SELECT id, name from Playlists where hidden is 0")
    ]

    print(f"Preparing to export {len(playlists)} playlists...\n")
    xml_element = None
    for playlist in playlists:
        exported_tracks: List[ExportedTrack] = []
        playlist_id = playlist[0]
        playlist_name = playlist[1]

        print(f"{playlist_name}:")

        tracks = [
            track
            for track in cur.execute(
                "SELECT position, track_id FROM PlaylistTracks WHERE playlist_id = :id ORDER BY position",
                {"id": playlist_id},
            )
        ]
        track_cur = con.cursor()
        for track in tqdm(
            tracks,
            unit="track",
        ):
            track_id = track[1]
            libaray_track_ctx = track_cur.execute(
                "SELECT location, samplerate, channels, duration, title, artist, album, genre, bpm FROM library WHERE id = :id",
                {"id": track_id},
            )
            (
                track_id,
                samplerate,
                channels,
                duration,
                title,
                artist,
                album,
                genre,
                bpm,
            ) = libaray_track_ctx.fetchone()

            track_location_ctx = track_cur.execute(
                "SELECT location FROM track_locations WHERE id = :id",
                {"id": track_id},
            )
            (track_location,) = track_location_ctx.fetchone()
            track_context = TrackContext(
                id=track_id,
                samplerate=int(samplerate),
                channels=int(channels),
                duration=int(duration),
                title=title or "",
                artist=artist or "",
                album=album or "",
                genre=genre or "",
                bpm=float(bpm) or 0.0,
                location=track_location,
            )
            exported_track = ExportedTrack(
                id=generate_random_number(), track_context=track_context
            )
            cuepoints_ctx = track_cur.execute(
                "SELECT hotcue,position,color from cues WHERE cues.type = 1 and cues.hotcue >= 0 and cues.track_id = :id",
                {"id": track[1]},
            )
            for cue_index, cue_position, color in cuepoints_ctx:
                exported_track.add_new_cue_point(
                    CuePoint(
                        1,
                        cue_index,
                        mixxx_cuepos_to_ms(
                            int(cue_position),
                            track_context.samplerate,
                            track_context.channels,
                        ),
                        CueColour(hex(color)),
                    )
                )
            exported_tracks.append(exported_track)

        xml_element = rekordbox_gen.generate(
            exported_tracks, playlist_name, xml_element
        )
        print("")
    with open("rekordbox.xml", "wb") as fd:
        fd.write(rekordbox_gen.encode_xml_element(xml_element))
        fd.close()
    print("done")


if __name__ == "__main__":
    main()
