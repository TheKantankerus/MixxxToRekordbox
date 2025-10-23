from functools import partial
from multiprocessing import Manager
from multiprocessing.pool import Pool
from multiprocessing.synchronize import Semaphore
from lxml import etree
from handlers import sql as sql_handlers
from handlers.transcode import EXPORT_SEMAPHORE_COUNT, change_track_location
from models import (
    RATING_MAP,
    BeatGridInfo,
    CollectionType,
    CueColour,
    CuePoint,
    ExportedTrack,
    KeyType,
    TrackContext,
    get_key,
)
from tqdm import tqdm
from offset_handlers import flush_offset_errors
from rekordbox_gen import (
    TRACK_COLLECTION,
    encode_xml_element,
    format_track_id,
    generate_xml,
)


def mixxx_cuepos_to_ms(cuepos: int, samplerate: int, channels: int):
    return int((cuepos * 1000.0) / (samplerate * channels))


def get_track_info(
    track_id: str,
    out_dir: str | None,
    out_format: str | None,
    key_type: KeyType,
    export_semaphore: Semaphore,
) -> tuple[TrackContext, BeatGridInfo | None]:
    (
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
        track_location,
    ) = sql_handlers.get_track_info(track_id)

    if out_dir or out_format:
        track_location = change_track_location(
            track_location, out_dir, out_format, export_semaphore
        )

    return TrackContext(
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
    ), (BeatGridInfo(beats, beats_version, samplerate) if beats else None)


def get_cue_points(
    track_id: str,
    samplerate: int,
    channels: int,
) -> list[CuePoint]:
    return [
        CuePoint(
            1,
            cue_index,
            mixxx_cuepos_to_ms(
                int(cue_position),
                samplerate,
                channels,
            ),
            CueColour(hex(color)),
        )
        for (cue_index, cue_position, color) in sql_handlers.get_cue_points(track_id)
    ]


def get_exported_track(
    track_id: str,
    out_dir: str | None,
    out_format: str | None,
    key_type: KeyType,
    export_semaphore: Semaphore,
    track_collection: dict,
) -> ExportedTrack:
    if track_id in track_collection:
        return track_collection[track_id]

    track_context, beat_grid = get_track_info(
        track_id, out_dir, out_format, key_type, export_semaphore
    )
    return ExportedTrack(
        id=format_track_id(track_id),
        track_context=track_context,
        beat_grid=beat_grid,
        cue_points=get_cue_points(
            track_id, track_context.samplerate, track_context.channels
        ),
    )


def init_track_worker(db_location: str) -> None:
    sql_handlers.set_db_location(db_location)


def get_data_for_tracks(
    track_ids: list[str],
    out_dir: str | None,
    out_format: str | None,
    key_type: KeyType,
    db_location: str | None,
) -> list[ExportedTrack]:
    manager = Manager()
    export_semaphore = manager.Semaphore(EXPORT_SEMAPHORE_COUNT)
    track_collection = manager.dict()
    track_collection.update(TRACK_COLLECTION)
    with Pool(
        # os.cpu_count() // (2 if out_format else 1),
        initializer=init_track_worker,
        initargs=(db_location,),
    ) as pool:
        return list(
            tqdm(
                pool.imap(
                    partial(
                        get_exported_track,
                        out_dir=out_dir,
                        out_format=out_format,
                        key_type=key_type,
                        export_semaphore=export_semaphore,
                        track_collection=track_collection,
                    ),
                    track_ids,
                    chunksize=1 if out_format else 2,
                ),
                unit="track",
                total=len(track_ids),
            )
        )


def append_collection_to_element(
    collection_id: str,
    collection_name: str,
    xml_element: etree.Element,
    export_all: bool,
    collection_type: CollectionType,
    out_dir: str | None,
    out_format: str | None,
    key_type: KeyType,
    db_location: str | None,
) -> etree.Element:
    if (
        not export_all
        and input(f"Export {collection_name}? [y/n]").lower().strip() != "y"
    ):
        return xml_element

    print(f"{collection_name}:")
    track_ids = sql_handlers.get_collection_tracks(collection_type, collection_id)

    return generate_xml(
        get_data_for_tracks(track_ids, out_dir, out_format, key_type, db_location),
        collection_name,
        xml_element,
    )


def export_to_rekordbox_xml(
    out_format: str | None,
    out_dir: str | None,
    export_all: bool,
    mixxx_db_location: str | None,
    key_type: KeyType,
    collection_type: CollectionType,
) -> None:
    db_location = sql_handlers.get_mixxx_db_location(mixxx_db_location)
    if out_format and not out_dir:
        raise Exception("Output directory must be specified if changing file formats.")
    sql_handlers.set_db_location(db_location)

    collections = sql_handlers.get_collections(collection_type)

    print(f"Preparing to export {len(collections)} {collection_type}s...\n")
    xml_element = None
    for collection in collections:
        collection_id = collection[0]
        collection_name = collection[1]
        xml_element = append_collection_to_element(
            collection_id,
            collection_name,
            xml_element,
            export_all,
            collection_type,
            out_dir,
            out_format,
            key_type,
            db_location,
        )
        flush_offset_errors()
        print("")
    with open("rekordbox.xml", "wb") as fd:
        fd.write(encode_xml_element(xml_element))
        fd.close()
    print("done")
