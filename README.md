# Sorozat & film átnevező – 0.6.1

Hordozható Windows program: videó- és feliratfájlok nevét hangolja össze, hogy a tévé megtalálja a feliratot.

Az alapfunkciókhoz nincs szükség internetre. A program nem írja át a fájlok tartalmát.

## Felhasználói (portable) használat

1. Csomagold ki a program mappáját egy helyre.
2. Indítsd a `SorozatEsFilmAtnevezo.exe` fájlt.
3. Adj hozzá mappát vagy fájlokat, ellenőrizd az előnézetet, majd hagyd jóvá az átnevezést vagy másolást.

A beállítások és az előzmény a program melletti `data` mappába kerülnek (`settings.json`, `history.json`). A mappa a géppel együtt mozgatható.

Kimeneti exe build: `build_exe.bat` → `dist\SorozatEsFilmAtnevezo\`.

## Fejlesztői futtatás

1. Csomagold ki a teljes projektet.
2. Futtasd a `setup.bat` fájlt.
3. Indítsd a `run_dev.bat` fájlt.

Fejlesztői módban a főablakban megjelenik a Tesztlabor és a Patch Center. Frozen / release buildben ezek nincsenek a felhasználói felületen.

### Mappák

- `src` – főprogram
- `data` – hordozható beállítások és előzmény (futás közben jön létre)
- `TESTEK` – automata tesztek
- `Tesztadat_Generator/TESZT_KORNYEZET` – izolált tesztkörnyezet
- `patches` – helyi patchok (csak fejlesztői Patch Center)
- `docs` – projekt dokumentáció
