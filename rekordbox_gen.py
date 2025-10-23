from lxml import etree
import platform

from models import ExportedTrack

TRACK_COLLECTION: dict[str, ExportedTrack] = {}


def format_track_id(track_id: int | str) -> str:
    return f"{int(track_id):010}"


def is_track_in_collection(track_id: str) -> bool:
    return track_id in TRACK_COLLECTION


def add_track_to_collection(track: ExportedTrack) -> None:
    TRACK_COLLECTION[track.id] = track


def find_or_create_element(index: int, name: str, root: etree.Element) -> etree.Element:
    return root[index] if len(root) > index else etree.Element(name)


def set_length_key(key: str, element: etree.Element) -> None:
    element.set(key, str(len(element)))


def create_track_elm(track: ExportedTrack) -> etree.Element:
    track_elm = etree.Element("TRACK")
    track_elm.set("TrackID", str(track.id))
    track_elm.set("TotalTime", str(track.track_context.duration))
    track_elm.set("Name", track.track_context.title)
    track_elm.set("Artist", track.track_context.artist)
    track_elm.set("Album", track.track_context.album)
    track_elm.set("Genre", track.track_context.genre)
    track_elm.set("SampleRate", str(track.track_context.samplerate))
    track_elm.set("AverageBpm", str(track.track_context.bpm))
    track_elm.set("Tonality", str(track.track_context.key))
    track_elm.set("Rating", str(track.track_context.rating))
    track_elm.set("Colour", str(track.track_context.colour))

    if track.beat_grid:
        tempo_elm = etree.Element("TEMPO")
        tempo_elm.set("Inizio", str(track.beat_grid.start_sec))
        tempo_elm.set("Bpm", str(track.beat_grid.bpm or track.track_context.bpm))
        tempo_elm.set("Metro", str("4/4"))
        tempo_elm.set("Battito", str(1))
        track_elm.append(tempo_elm)

    if platform.system() == "Windows":
        track_elm.set("Location", "file://localhost/" + track.track_context.location)
    else:
        track_elm.set("Location", "file://localhost" + track.track_context.location)
    for cue_point in track.cue_points:
        cue_element = etree.Element("POSITION_MARK")
        cue_element.set("Name", cue_point.cue_text.rstrip("\x00"))
        cue_element.set("Num", str(cue_point.cue_index))
        cue_element.set("Start", str(cue_point.cue_position / 1000))
        cue_element.set("Red", str(cue_point.cue_color.r_int))
        cue_element.set("Green", str(cue_point.cue_color.g_int))
        cue_element.set("Blue", str(cue_point.cue_color.b_int))
        cue_element.set("Type", "0")
        track_elm.append(cue_element)
    return track_elm


def create_playlist_track_elm(track_id: str) -> etree.Element:
    playlist_track_elm = etree.Element("TRACK")
    playlist_track_elm.set("Key", track_id)
    return playlist_track_elm


def generate_xml(
    tracks: list[ExportedTrack],
    playlist_name,
    dj_playlist: etree.Element | None,
) -> etree.Element:
    if dj_playlist is None:
        dj_playlist = etree.Element("DJ_PLAYLISTS")
        dj_playlist.set("Version", "1.0.0")
        product_elm = etree.Element("PRODUCT")
        product_elm.set("Name", "rekordbox")
        product_elm.set("Version", "6.5.2")
        product_elm.set("Company", "AlphaTheta")
        dj_playlist.append(product_elm)

    collection_elm = find_or_create_element(1, "COLLECTION", dj_playlist)

    playlist_elm = find_or_create_element(2, "PLAYLISTS", dj_playlist)
    playlist_node_wrapper_elm = find_or_create_element(0, "NODE", playlist_elm)
    playlist_node_wrapper_elm.set("Type", "0")
    playlist_node_wrapper_elm.set("Name", "ROOT")
    playlist_node_elm = etree.Element("NODE")
    playlist_node_elm.set("Name", playlist_name)
    playlist_node_elm.set("Type", "1")
    playlist_node_elm.set("KeyType", "0")

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
