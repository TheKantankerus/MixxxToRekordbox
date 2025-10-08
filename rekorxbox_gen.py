from typing import List
from lxml import etree
import CuePoint
import platform


def generate(tracks: List[CuePoint.CuePointCollection], playlist_name):
    entry_length = len(tracks)

    dj_playlist = etree.Element("DJ_PLAYLISTS")
    dj_playlist.set("Version", "1.0.0")
    product_elm = etree.Element("PRODUCT")
    product_elm.set("Name", "rekordbox")
    product_elm.set("Version", "6.5.2")
    product_elm.set("Company", "AlphaTheta")
    collection_elm = etree.Element("COLLECTION")
    collection_elm.set("Entries", str(entry_length))

    for track in tracks:
        track_elm = etree.Element("TRACK")
        track_elm.set("TrackID", str(track.id))
        track_elm.set("TotalTime", str(track.length))
        if platform.system() == "Windows":
            track_elm.set("Location", "file://localhost/" + track.track_filename)
        else:
            track_elm.set("Location", "file://localhost" + track.track_filename)
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

    playlist_elm = etree.Element("PLAYLISTS")
    playlist_node_warpper_elm = etree.Element("NODE")
    playlist_node_warpper_elm.set("Type", "0")
    playlist_node_warpper_elm.set("Name", "ROOT")
    playlist_node_warpper_elm.set("Count", "1")
    playlist_node_elm = etree.Element("NODE")
    playlist_node_elm.set("Name", playlist_name)
    playlist_node_elm.set("Type", "1")
    playlist_node_elm.set("KeyType", "0")
    playlist_node_elm.set("Entries", str(entry_length))

    for track in tracks:
        track_elm = etree.Element("TRACK")
        track_elm.set("Key", track.id)
        playlist_node_elm.append(track_elm)
    playlist_node_warpper_elm.append(playlist_node_elm)
    playlist_elm.append(playlist_node_warpper_elm)

    dj_playlist.append(product_elm)
    dj_playlist.append(collection_elm)
    dj_playlist.append(playlist_elm)

    s = etree.tostring(dj_playlist, pretty_print=True, encoding="utf-8")
    s = str(s, "utf-8")
    s = (
        s
        if s.startswith("<?xml")
        else '<?xml version="1.0" encoding="%s"?>\n%s' % ("utf-8", s)
    )
    return s.encode("utf-8")
