# MixxxToRekordbox
Sync your Mixxx Playlists to Rekordbox XML, optionally reformatting your files, all without losing metadata, beat grid or your hot cue info.

# Getting Started

Install [uv](https://docs.astral.sh/uv/) and [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git), then run:

```
git clone https://github.com/TheKantankerus/MixxxToRekordbox.git
cd .\MixxxToRekordbox
```

You can run the script immediately using:
```
uv run export.py
```

You will see a `[y/n]` prompt for each playlist, asking if you want it exported. Once all playlists have been read, a `rekordbox.xml` file will be generated in the `MixxxToRekordbox` folder. This XML file can then be read in Rekordbox by going to
```
Preferences > Advanced > rekordbox xml > Imported Library
```
and pointing it to your generated file. You can then see it in the "Display rekordbox xml" tab.

If you want to export all your playlists without prompting, simply run:

```
uv run export.py --export-all
```

# Change Mixxx Database Location

By default the database is retrieved from [Mixxx's settings directory](https://manual.mixxx.org/2.3/en/chapters/appendix/settings_directory.html). If your database is located somewhere else you'll need to specify this using `--mixxx-db-location` like so:

```
uv run export.py --mixxx-db-location='C:\SomeOtherMixxxLocation\mixxxdb.sqlite'
```

# Change file format and output directory

If you want your files to be output in a different format, you can specify this by running the script with the `--format` and `--out-dir` flags set. You can also just set the `--out-dir` flag if you want to copy your files to a different location.

This is particularly useful if you have music files that aren't supported by older Pioneer hardware (e.g FLACs), allowing you to transcode them whilst keeping your cue points and tags like so:

```
uv run export.py --out-dir='C:\Temp\' --format='.aiff'
```

You can then process the files in Rekordbox, export them to your USB drive and delete the temporary folder.

In order to change the file format you'll need to install [ffmpeg](https://ffmpeg.org/) so that the `ffmpeg` and `ffprobe` commands are accessible by the script. If you're having trouble on Windows, downloading the latest executables from ffmpeg into the script's directory should work.

# Key tagging

If you prefer your track Keys tagged in Musical style (Cm, F#, etc.) rather than Lancelot (5A, 2B, etc.) you can run the script like so
```
uv run export.py --key-type=musical
```
Otherwise, the script will default to Lancelot.

# Crates vs Playlists

If you like to keep your Mixxx tracks in Crates, as opposed to Playlists, you can export these by running:
```
uv run export-py --use-crates
```
Otherwise, the script defaults to exporting Playlists.
