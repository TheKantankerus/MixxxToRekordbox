import argparse
from handlers.export import export_to_rekordbox_xml
from models import (
    CollectionType,
    KeyType,
)


arg_parser = argparse.ArgumentParser()
arg_parser.add_argument(
    "--out-dir", type=str, help="Outputs tracks to a new directory."
)
arg_parser.add_argument(
    "--virtual-out-dir", type=str, help="Rekordbox will find tracks in this location, requires --out-dir to be set"
)
arg_parser.add_argument(
    "--format",
    type=str,
    help="Change the file format of the tracks, requires --out-dir to be set.",
)
arg_parser.add_argument(
    "-a",
    "--export-all",
    action="store_true",
    help="Export all playlists without prompting. May take a while and fill up your drive if --out-dir is set.",
)
arg_parser.add_argument(
    "--mixxx-db-location", type=str, help="Specify Mixxx's DB location if non-standard."
)
arg_parser.add_argument(
    "--key-type",
    type=KeyType,
    help=f"Specify a key type to export: {[kt.value for kt in KeyType]}, defaults to {KeyType.LANCELOT}",
)
arg_parser.add_argument(
    "--playlists",
    action="store_true",
    help="Export playlists. If neither --playlists nor --crates is given, playlists are exported by default.",
)
arg_parser.add_argument(
    "--crates",
    action="store_true",
    help="Export crates. Combine with --playlists to export both in a single run.",
)
arg_parser.add_argument(
    "-c",
    "--use-crates",
    action="store_true",
    help="Equivalent to --crates. Kept for backwards compatibility.",
)
arg_parser.add_argument(
    "--playlists-prefix",
    type=str,
    default="",
    help="Prefix prepended to every exported playlist name in the Rekordbox XML.",
)
arg_parser.add_argument(
    "--playlists-suffix",
    type=str,
    default="",
    help="Suffix appended to every exported playlist name in the Rekordbox XML.",
)
arg_parser.add_argument(
    "--crates-prefix",
    type=str,
    default="",
    help="Prefix prepended to every exported crate name in the Rekordbox XML (crates are exported as playlists).",
)
arg_parser.add_argument(
    "--crates-suffix",
    type=str,
    default="",
    help="Suffix appended to every exported crate name in the Rekordbox XML (crates are exported as playlists).",
)
arg_parser.add_argument(
    "--list-file",
    type=str,
    help="Path to a list file. Non-commented entries are exported non-interactively; all other collections are skipped.",
)
arg_parser.add_argument(
    "--generate-list-file",
    type=str,
    help="Write a list file of all available crates/playlists (commented out) to the given path and exit. Edit the file and pass it back via --list-file to pre-select collections.",
)


def main() -> None:
    args = arg_parser.parse_args()
    out_format: str | None = args.format
    out_dir: str | None = args.out_dir
    virtual_out_dir: str | None = args.virtual_out_dir
    export_all: bool = args.export_all
    mixxx_db_location: str | None = args.mixxx_db_location
    key_type: KeyType = args.key_type or KeyType.LANCELOT

    include_playlists: bool = args.playlists
    include_crates: bool = args.crates or args.use_crates

    collection_types: list[CollectionType] = []
    if include_playlists:
        collection_types.append("playlists")
    if include_crates:
        collection_types.append("crates")
    if not collection_types:
        # When generating a list file with no explicit collection type, list
        # both so the user can choose from everything available. Otherwise
        # default to playlists for backwards compatibility.
        if args.generate_list_file:
            collection_types = ["playlists", "crates"]
        else:
            collection_types = ["playlists"]

    prefixes: dict[CollectionType, str] = {
        "playlists": args.playlists_prefix,
        "crates": args.crates_prefix,
    }
    suffixes: dict[CollectionType, str] = {
        "playlists": args.playlists_suffix,
        "crates": args.crates_suffix,
    }

    export_to_rekordbox_xml(
        out_format,
        out_dir,
        export_all,
        mixxx_db_location,
        key_type,
        collection_types,
        virtual_out_dir,
        prefixes,
        suffixes,
        args.list_file,
        args.generate_list_file,
    )


if __name__ == "__main__":
    main()
