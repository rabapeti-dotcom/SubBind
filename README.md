# Sorozat & film átnevező – 0.6.1

Hordozható Windows program: videó- és feliratfájlok nevét hangolja össze, hogy a tévé megtalálja a feliratot.

Az alapfunkciókhoz nincs szükség internetre. A program nem írja át a fájlok tartalmát.

## Felhasználói (portable) használat

1. Csomagold ki a program mappáját egy helyre.
2. Indítsd a `SorozatEsFilmAtnevezo.exe` fájlt.
3. Adj hozzá mappát vagy fájlokat, ellenőrizd az előnézetet, majd hagyd jóvá az átnevezést vagy másolást.

A beállítások és az előzmény a program melletti `data` mappába kerülnek (`settings.json`, `history.json`). A mappa a géppel együtt mozgatható.

Kimeneti exe build: `build_exe.bat` → `dist\SorozatEsFilmAtnevezo\`.
A kiadott csomag az exe és a `_internal` mappa. A projekt gyökér `data` mappája fejlesztői; ne tedd a felhasználói zipbe. Első indításkor a program a saját `data` mappáját hozza létre az exe mellett.

## Fejlesztői futtatás

1. Csomagold ki a teljes projektet.
2. Futtasd a `setup.bat` fájlt.
3. Indítsd a `run_dev.bat` fájlt.

A Tesztlabor és a Patch Center csak fejlesztői módban jelenik meg (`run_dev.bat`, vagy `SERIESRENAMER_DEV=1`). Normál `python src/main.py` indításnál, valamint frozen / release buildben nincsenek a felhasználói felületen.

### Mappák

- `src` – főprogram
- `data` – hordozható beállítások és előzmény (futás közben jön létre)
- `TESTEK` – automata tesztek
- `Tesztadat_Generator/TESZT_KORNYEZET` – izolált tesztkörnyezet
- `patches` – helyi patchok (csak fejlesztői Patch Center)
- `docs` – projekt dokumentáció
