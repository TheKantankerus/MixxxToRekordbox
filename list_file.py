"""Read and write collection list files.

A list file lets the user pre-select which crates and playlists to export.
Lines starting with ``#`` (after optional whitespace) are comments and are
ignored. Every other non-empty line must follow the form::

    <playlist|crate>: <name>

where ``<name>`` is the crate/playlist name exactly as it appears in Mixxx.
Non-commented lines are exported non-interactively when ``--list-file`` is
passed to the script.
"""
from pathlib import Path

from models import CollectionType

# Singular label used per collection type inside the list file.
LIST_TYPE_LABEL: dict[CollectionType, str] = {
    "playlists": "playlist",
    "crates": "crate",
}

LIST_FILE_HEADER = [
    "# MixxxToRekordbox collection list",
    "# Uncomment a line (remove the leading '# ') to export that collection.",
    "# Lines starting with '#' are ignored.",
    "# Format: <playlist|crate>: <name>",
    "",
]


def parse_list_file(path: str) -> dict[CollectionType, set[str]]:
    """Parse a list file and return the selected names per collection type.

    Only non-commented lines are returned. Unknown type labels are ignored.
    """
    selected: dict[CollectionType, set[str]] = {"playlists": set(), "crates": set()}
    with open(path, "r", encoding="utf-8") as fd:
        for raw_line in fd:
            line = raw_line.rstrip("\n")
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            # Format: "<type>: <name>". Split on the first ": " so that names
            # containing ": " are preserved.
            if ": " not in stripped:
                continue
            type_str, name = stripped.split(": ", 1)
            if type_str == "playlist":
                selected["playlists"].add(name)
            elif type_str == "crate":
                selected["crates"].add(name)
    return selected


def write_list_file(
    path: str,
    collections: dict[CollectionType, list[tuple[str, str]]],
) -> None:
    """Write all given collections to a list file, commented out.

    ``collections`` maps a collection type to a list of ``(id, name)`` tuples
    as returned by :func:`handlers.sql.get_collections`.
    """
    lines = list(LIST_FILE_HEADER)
    for ctype in ("playlists", "crates"):
        items = collections.get(ctype, [])
        if not items:
            continue
        label = LIST_TYPE_LABEL[ctype]
        lines.append(f"# {ctype}:")
        for _id, name in items:
            lines.append(f"# {label}: {name}")
        lines.append("")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
