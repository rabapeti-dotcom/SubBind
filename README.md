# SubBind

## Smart Subtitle & Media Renamer

SubBind 0.6.1 is a portable Windows desktop app that aligns video and subtitle file names so a TV or player can find the matching subtitle.

It is freeware and open source, licensed under the GNU General Public License v3.0.

Developed by BadMusicHUN.

Core features do not require the internet. The program does not rewrite file contents.

## What it does

- Pairs videos with subtitles (series and movies)
- Preferred subtitle language is independent of the program UI language (HU/EN)
- Preview and Check before any file operation
- Rename in place, or copy into an output folder
- Portable settings: `data/` next to the executable (`settings.json`, `history.json`)

## User (portable) use

1. Unpack the program folder to one location.
2. Start `SubBind.exe`.
3. Add a folder or files, check the preview, then confirm rename or copy.

Settings and history go into the `data` folder beside the program. That folder can travel with the machine.

Build: `build_exe.bat` → `dist\SubBind\`.
The released package is the exe and the `_internal` folder. The project-root `data` folder is for development; do not put it in the user zip. On first run the program creates its own `data` folder next to the exe.

## Developer run

1. Unpack the full project.
2. Run `setup.bat`.
3. Start `run_dev.bat`.

Test lab and Patch Center appear only in developer mode (`run_dev.bat`, or `SERIESRENAMER_DEV=1`). A normal `python src/main.py` start, and frozen / release builds, do not show them on the user UI.

### Folders

- `src` – main program
- `data` – portable settings and history (created at runtime)
- `TESTEK` – automated tests
- `Tesztadat_Generator/TESZT_KORNYEZET` – isolated test environment
- `patches` – local patches (developer Patch Center only)
- `docs` – project documentation

## Magyar

A SubBind 0.6.1 hordozható Windows program: videó- és feliratfájlok nevét hangolja össze, hogy a tévé vagy a lejátszó megtalálja a feliratot.

Ingyenes, nyílt forráskódú szoftver, GNU GPL v3.0 licenc alatt.

Fejlesztő: BadMusicHUN.

Az alapfunkciókhoz nincs szükség internetre. A program nem írja át a fájlok tartalmát.

- Videó és felirat párosítása (sorozat és film)
- A preferált feliratnyelv független a program HU/EN felületétől
- Előnézet és ellenőrzés a fájlművelet előtt
- Helyben átnevezés, vagy másolás kimeneti mappába
- Hordozható beállítások a program melletti `data` mappában

1. Csomagold ki a program mappáját egy helyre.
2. Indítsd a `SubBind.exe` fájlt.
3. Adj hozzá mappát vagy fájlokat, ellenőrizd az előnézetet, majd hagyd jóvá az átnevezést vagy másolást.

A beállítások és az előzmény a program melletti `data` mappába kerülnek. Kimeneti exe: `build_exe.bat` → `dist\SubBind\`.
