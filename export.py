import argparse
import os
from os import path
from pathlib import Path
import shutil

from models import (
    COLLECTION_QUERY_MAP,
    COLLECTION_TRACKS_QUERY_MAP,
    RATING_MAP,
    BeatGridInfo,
    CollectionType,
    CueColour,
    CuePoint,
    ExportedTrack,
    KeyTypes,
    TrackContext,
    get_key,
)
import sqlite3
from tqdm import tqdm
from offset_handlers import flush_offset_errors
import rekordbox_gen
from pydub import AudioSegment

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument(
    "--out-dir", type=str, help="Outputs tracks to a new directory."
)
arg_parser.add_argument(
    "--format",
    type=str,
    help="Change the file format of the tracks, requires --out-dir to be set.",
)
arg_parser.add_argument(
    "--export-all",
    action="store_true",
    help="Export all playlists without prompting. May take a while and fill up your drive if --out-dir is set.",
)
arg_parser.add_argument(
    "--mixxx-db-location", type=str, help="Specify Mixxx's DB location if non-standard."
)
arg_parser.add_argument(
    "--key-type",
    type=KeyTypes,
    help=f"Specify a key type to export: {[kt.value for kt in KeyTypes]}, defaults to {KeyTypes.LANCELOT}",
)
arg_parser.add_argument(
    "--use-crates",
    action="store_true",
    help="Source the tracks from crates instead of playlists, XML output will still be playlists.",
)


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


def mixxx_cuepos_to_ms(cuepos: int, samplerate: int, channels: int):
    return int((cuepos * 1000.0) / (samplerate * channels))


def transcode_track(track_path: Path, out_path: Path, format: str) -> str:
    segment = AudioSegment.from_file(track_path, format=track_path.suffix[1:])
    new_file = out_path.joinpath(f"{track_path.stem}.{format}")
    segment.export(new_file, format=format)
    return str(new_file)


def change_track_location(track_location: str, out_dir: str, format: str | None) -> str:
    track_path = Path(track_location)
    out_dir_path = Path(out_dir)
    if format:
        return transcode_track(track_path, out_dir_path, format)
    else:
        out_file_path = out_dir_path.joinpath(track_path.name)
        shutil.copy2(track_path, out_file_path)
        return str(out_file_path)


def main():
    args = arg_parser.parse_args()
    format: str | None = args.format
    out_dir: str | None = args.out_dir
    export_all: bool = args.export_all
    mixxx_db_location: str | None = args.mixxx_db_location
    key_type: KeyTypes = args.key_type or KeyTypes.LANCELOT
    use_crates: bool = args.use_crates

    collection_type: CollectionType = "crates" if use_crates else "playlists"

    if format and not out_dir:
        raise Exception("Output directory must be specified if changing file formats.")

    con = sqlite3.connect(get_mixxx_db_location(mixxx_db_location))
    cur = con.cursor()

    collections = [
        collection for collection in cur.execute(COLLECTION_QUERY_MAP[collection_type])
    ]

    print(f"Preparing to export {len(collections)} {collection_type}s...\n")
    xml_element = None
    for collection in collections:
        exported_tracks: list[ExportedTrack] = []
        collection_id = collection[0]
        collection_name = collection[1]
        if (
            not export_all
            and input(f"Export {collection_name}? [y/n]").lower().strip() != "y"
        ):
            continue

        print(f"{collection_name}:")

        track_ids = [
            track[0]
            for track in cur.execute(
                COLLECTION_TRACKS_QUERY_MAP[collection_type],
                {"id": collection_id},
            )
        ]
        track_cur = con.cursor()
        for track_id in tqdm(
            track_ids,
            unit="track",
        ):
            if rekordbox_gen.is_track_in_collection(track_id):
                exported_tracks.append(
                    rekordbox_gen.get_track_from_collection(track_id)
                )
                continue
            libaray_track_ctx = track_cur.execute(
                """
                SELECT
                    location, samplerate, channels, duration, title, artist, album, genre, bpm, beats, beats_version, key_id, rating, color
                FROM
                    library
                WHERE
                    id = :id
                """,
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
                beats,
                beats_version,
                key_id,
                rating,
                colour,
            ) = libaray_track_ctx.fetchone()

            (track_location,) = track_cur.execute(
                "SELECT location FROM track_locations WHERE id = :id",
                {"id": track_id},
            ).fetchone()

            if out_dir or format:
                track_location = change_track_location(track_location, out_dir, format)

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
                key=get_key(key_id, key_type),
                rating=RATING_MAP[rating],
                colour=colour,
            )
            cuepoints_ctx = track_cur.execute(
                "SELECT hotcue,position,color from cues WHERE cues.type = 1 and cues.hotcue >= 0 and cues.track_id = :id",
                {"id": track_id},
            )
            cue_points = [
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
                for (cue_index, cue_position, color) in cuepoints_ctx
            ]
            exported_tracks.append(
                ExportedTrack(
                    id=rekordbox_gen.format_track_id(track_id),
                    track_context=track_context,
                    beat_grid=BeatGridInfo(beats, beats_version, samplerate)
                    if beats
                    else None,
                    cue_points=cue_points,
                )
            )

        xml_element = rekordbox_gen.generate(
            exported_tracks, collection_name, xml_element
        )
        flush_offset_errors()
        print("")
    with open("rekordbox.xml", "wb") as fd:
        fd.write(rekordbox_gen.encode_xml_element(xml_element))
        fd.close()
    print("done")


if __name__ == "__main__":
    main()
