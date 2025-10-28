from lxml import etree
from lxml.builder import E
import platform

from models import ExportedTrack

TRACK_COLLECTION: dict[str, ExportedTrack] = {}


def format_track_id(track_id: int | str) -> str:
    return f"{int(track_id):010}"


def is_track_in_collection(track_id: str) -> bool:
    return track_id in TRACK_COLLECTION


def add_track_to_collection(track: ExportedTrack) -> None:
    TRACK_COLLECTION[track.id] = track


def find_or_create_element(
    index: int, name: str, root: etree.Element, *args, **kwargs
) -> etree.Element:
    return root[index] if len(root) > index else E(name, *args, **kwargs)


def set_length_key(key: str, element: etree.Element) -> None:
    element.set(key, str(len(element)))


def create_track_elm(track: ExportedTrack) -> etree.Element:
    track_elm = E.TRACK(
        TrackID=str(track.id),
        TotalTime=str(track.track_context.duration),
        Name=track.track_context.title,
        Artist=track.track_context.artist,
        Album=track.track_context.album,
        Genre=track.track_context.genre,
        SampleRate=str(track.track_context.samplerate),
        AverageBpm=str(track.track_context.bpm),
        Tonality=str(track.track_context.key),
        Rating=str(track.track_context.rating),
        Colour=str(track.track_context.colour),
        Location="file://localhost/" + track.track_context.location
        if platform.system() == "Windows"
        else "file://localhost" + track.track_context.location,
    )

    if track.beat_grid:
        tempo_elm = E.TEMPO(
            Inizio=str(track.beat_grid.start_sec),
            Bpm=str(track.beat_grid.bpm or track.track_context.bpm),
            Metro="4/4",
            Battito="1",
        )
        track_elm.append(tempo_elm)

    for cue_point in track.cue_points:
        cue_elm = E.POSITION_MARK(
            Name=cue_point.cue_text.rstrip("\x00"),
            Num=str(cue_point.cue_index),
            Start=str(cue_point.cue_position / 1000),
            Red=str(cue_point.cue_color.r_int),
            Green=str(cue_point.cue_color.g_int),
            Blue=str(cue_point.cue_color.b_int),
            Type="0",
        )
        track_elm.append(cue_elm)
    return track_elm


def create_playlist_track_elm(track_id: str) -> etree.Element:
    return E.TRACK(Key=track_id)


def generate_xml(
    tracks: list[ExportedTrack],
    playlist_name,
    dj_playlist: etree.Element | None,
) -> etree.Element:
    if dj_playlist is None:
        dj_playlist = E.DJ_PLAYLISTS(
            E.PRODUCT(Name="rekordbox", Version="6.5.2", Company="AlphaTheta"),
            Version="1.0.0",
        )

    collection_elm = find_or_create_element(1, "COLLECTION", dj_playlist)

    playlist_elm = find_or_create_element(2, "PLAYLISTS", dj_playlist)
    playlist_node_wrapper_elm = find_or_create_element(
        0, "NODE", playlist_elm, Type="0", Name="ROOT"
    )
    playlist_node_elm = E.NODE(Name=playlist_name, Type="1", KeyType="0")

    for track in tracks:
        playlist_node_elm.append(create_playlist_track_elm(track.id))

        if is_track_in_collection(track.id):
            continue
        collection_elm.append(create_track_elm(track))
        add_track_to_collection(track)

    playlist_node_wrapper_elm.append(playlist_node_elm)
    playlist_elm.append(playlist_node_wrapper_elm)

    set_length_key("Entries", collection_elm)
    set_length_key("Entries", playlist_node_elm)
    set_length_key("Count", playlist_node_wrapper_elm)

    dj_playlist.append(collection_elm)
    dj_playlist.append(playlist_elm)

    return dj_playlist


def encode_xml_element(xml_element: etree.Element) -> str:
    s = etree.tostring(xml_element, pretty_print=True, encoding="utf-8")
    s = str(s, "utf-8")
    s = (
        s
        if s.startswith("<?xml")
        else '<?xml version="1.0" encoding="%s"?>\n%s' % ("utf-8", s)
    )
    return s.encode("utf-8")
