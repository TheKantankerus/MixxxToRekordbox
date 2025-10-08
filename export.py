import os
from utils.random_id import generate_random_number
from typing import List
from models import CuePoint, CuePointCollection, TrackContext
import sqlite3
from tqdm import tqdm
import rekordbox_gen

mixxx_db = f"{os.getenv('LOCALAPPDATA')}\\Mixxx\\mixxxdb.sqlite"


def mixxx_cuepos_to_ms(cuepos, samplerate, channels):
    return int(float(cuepos) / (int(samplerate) * int(channels)) * 1000)


def main():
    con = sqlite3.connect(mixxx_db)
    cur = con.cursor()

    playlists = [
        playlist
        for playlist in cur.execute("SELECT id, name from Playlists where hidden is 0")
    ]

    print(f"Preparing to export {len(playlists)} playlists...")
    xml_element = None
    for playlist in playlists:
        qpoint_collections: List[CuePointCollection] = []
        playlist_id = playlist[0]
        playlist_name = playlist[1]
        tracks = [
            track
            for track in cur.execute(
                "SELECT position, track_id FROM PlaylistTracks WHERE playlist_id = :id ORDER BY position",
                {"id": playlist_id},
            )
        ]
        track_cur = con.cursor()
        for track in tqdm(tracks):
            track_id = track[1]
            libaray_track_ctx = track_cur.execute(
                "SELECT location, samplerate, channels, duration, title, artist, album, genre FROM library WHERE id = :id",
                {"id": track_id},
            )
            (track_id, samplerate, channels, duration, title, artist, album, genre) = (
                libaray_track_ctx.fetchone()
            )

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
                location=track_location,
            )
            qpoint_collection = CuePointCollection(
                id=generate_random_number(8), track_context=track_context
            )
            cuepoints_ctx = track_cur.execute(
                "SELECT hotcue,position from cues WHERE cues.type = 1 and cues.hotcue >= 0 and cues.track_id = :id",
                {"id": track[1]},
            )
            for cuepoint in cuepoints_ctx:
                qpoint_collection.add_new_cue_point(
                    CuePoint(
                        1,
                        cuepoint[0],
                        mixxx_cuepos_to_ms(
                            cuepoint[1],
                            track_context.samplerate,
                            track_context.channels,
                        ),
                    )
                )
            qpoint_collections.append(qpoint_collection)

        xml_element = rekordbox_gen.generate(
            qpoint_collections, playlist_name, xml_element
        )
    with open("rekordbox.xml", "wb") as fd:
        fd.write(rekordbox_gen.encode_xml_element(xml_element))
        fd.close()
    print("done")


if __name__ == "__main__":
    main()
