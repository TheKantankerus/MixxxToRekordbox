from typing import List
from lxml import etree
import models
import platform


def find_or_create_element(index: int, name: str, root: etree.Element) -> etree.Element:
    return root[index] if len(root) > index else etree.Element(name)


def set_length_key(key: str, element: etree.Element) -> None:
    element.set(key, str(len(element)))


def generate(
    tracks: List[models.CuePointCollection],
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

    for track in tracks:
        track_elm = etree.Element("TRACK")
        track_elm.set("TrackID", str(track.id))
        track_elm.set("TotalTime", str(track.track_context.duration))
        track_elm.set("Name", track.track_context.title)
        track_elm.set("Artist", track.track_context.artist)
        track_elm.set("Album", track.track_context.album)
        track_elm.set("Genre", track.track_context.genre)
        track_elm.set("SampleRate", str(track.track_context.samplerate))
        if platform.system() == "Windows":
            track_elm.set(
                "Location", "file://localhost/" + track.track_context.location
            )
        else:
            track_elm.set("Location", "file://localhost" + track.track_context.location)
        for cue_point in track.cue_points:
            cue_element = etree.Element("POSITION_MARK")
            cue_element.set("Name", cue_point.cue_text.rstrip("\x00"))
            cue_element.set("Num", str(cue_point.cue_index))
            cue_element.set("Start", str(cue_point.cue_position / 1000))
            cue_element.set("Red", "40")
            cue_element.set("Green", "226")
            cue_element.set("Blue", "20")
            cue_element.set("Type", "0")
            track_elm.append(cue_element)
        collection_elm.append(track_elm)
    set_length_key("Entries", collection_elm)

    playlist_elm = find_or_create_element(2, "PLAYLISTS", dj_playlist)
    playlist_node_wrapper_elm = find_or_create_element(0, "NODE", playlist_elm)
    playlist_node_wrapper_elm.set("Type", "0")
    playlist_node_wrapper_elm.set("Name", "ROOT")
    playlist_node_elm = etree.Element("NODE")
    playlist_node_elm.set("Name", playlist_name)
    playlist_node_elm.set("Type", "1")
    playlist_node_elm.set("KeyType", "0")

    for track in tracks:
        track_elm = etree.Element("TRACK")
        track_elm.set("Key", track.id)
        playlist_node_elm.append(track_elm)
    playlist_node_wrapper_elm.append(playlist_node_elm)
    playlist_elm.append(playlist_node_wrapper_elm)

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
