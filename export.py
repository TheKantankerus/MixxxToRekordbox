from utils.random_id import generate_random_number
from rekorxbox_gen import generate
from typing import List
from CuePoint import CuePoint, CuePointCollection
import sqlite3
from tqdm import tqdm
import rekorxbox_gen
import platform

mixxx_db = r"C:\Users\admin\AppData\Local\Mixxx\mixxxdb.sqlite"

qpoint_collections: List[CuePointCollection] = []


def mixxx_cuepos_to_ms(cuepos, samplerate, channels):
    return int(float(cuepos) / (int(samplerate) * int(channels)) * 1000)


def get_user_options(playlist):
    if platform.system() == "Windows":
        for i in range(len(playlist)):
            print("{}, {}".format(i, playlist[i]))
        val = input("Enter Playlist Number: ")
        return int(val)
    else:
        from simple_term_menu import TerminalMenu

        terminal_menu = TerminalMenu(playlist, show_search_hint=True)
        choosed_playlist = terminal_menu.show()
        return choosed_playlist


def main():
    con = sqlite3.connect(mixxx_db)
    cur = con.cursor()

    playlist_ctx = cur.execute("SELECT id, name from Playlists where hidden is 0")

    playlist_options = []
    playlist_ids = []
    for playlist in playlist_ctx:
        playlist_options.append("{}".format(playlist[1]))
        playlist_ids.append(playlist[0])

    choosed_playlist = get_user_options(playlist_options)
    choosed_playlist_id = playlist_ids[choosed_playlist]

    tracks_ctx = cur.execute(
        "SELECT position, track_id FROM PlaylistTracks WHERE playlist_id = :id ORDER BY position",
        {"id": choosed_playlist_id},
    )
    track_cur = con.cursor()
    for track in tqdm(tracks_ctx):
        libaray_track_ctx = track_cur.execute(
            "SELECT location, samplerate, channels FROM library WHERE id = :id",
            {"id": track[1]},
        )
        track_serialized = libaray_track_ctx.fetchone()
        if track_serialized is None:
            continue
        track_location_ctx = track_cur.execute(
            "SELECT location FROM track_locations WHERE id = :id",
            {"id": track_serialized[0]},
        )
        track_location = track_location_ctx.fetchone()
        qpoint_collection = CuePointCollection(
            track_location[0], id=str(generate_random_number(8))
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
                        cuepoint[1], track_serialized[1], track_serialized[2]
                    ),
                )
            )
        qpoint_collections.append(qpoint_collection)

    generated_xml = rekorxbox_gen.generate(
        qpoint_collections, playlist_options[choosed_playlist]
    )
    with open("rekordbox.xml", "wb") as fd:
        fd.write(generated_xml)
        fd.close()
    print("done")


if __name__ == "__main__":
    main()
