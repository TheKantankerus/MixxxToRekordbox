# MixxxToRekordbox
Sync all your Mixxx Playlists to Rekordbox XML

# Getting Started

Install [uv](https://docs.astral.sh/uv/) and [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git), then run:

```
git clone https://github.com/TheKantankerus/MixxxToRekordbox.git
cd .\MixxxToRekordbox
uv run .\export.py
```

You will see your plalists and tracks being read, generating a `rekordbox.xml` file in the `MixxxToRekordbox` folder. This XML file can then be read in Rekordbox by going to 
```
Preferences > Advanced > rekordbox xml > Imported Library
```
and pointing it to your generated file.

You can then see it in the "Display rekordbox xml" tab.

# Change Mixxx Database Location

By default the database points to [Mixxx's settings directory](https://manual.mixxx.org/2.3/en/chapters/appendix/settings_directory.html). If your database is located somewhere else you'll need to specify this in `export.py`