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
    "-c",
    "--use-crates",
    action="store_true",
    help="Source the tracks from crates instead of playlists, XML output will still be playlists.",
)


def main() -> None:
    args = arg_parser.parse_args()
    out_format: str | None = args.format
    out_dir: str | None = args.out_dir
    export_all: bool = args.export_all
    mixxx_db_location: str | None = args.mixxx_db_location
    key_type: KeyType = args.key_type or KeyType.LANCELOT
    use_crates: bool = args.use_crates
    collection_type: CollectionType = "crates" if use_crates else "playlists"

    export_to_rekordbox_xml(
        out_format, out_dir, export_all, mixxx_db_location, key_type, collection_type
    )


if __name__ == "__main__":
    main()
