# Sorozat & film átnevező – 0.6.1-TEST

## Tiszta tesztprojekt

Ez a csomag új, önálló alap a további fejlesztéshez.

### Első indítás

1. Csomagold ki a teljes ZIP-et.
2. Nyisd meg a projekt gyökerét.
3. Futtasd a `setup.bat` fájlt.
4. Ha a SETUP SIKERES üzenet megjelenik, indítsd a `run_dev.bat` fájlt.

Ha a `setup.bat` dupla kattintással nem marad nyitva, nyisd meg a projektmappát PowerShellben, és futtasd:

```powershell
.\setup.bat
```

### Mappák

- `src` – főprogram
- `TESTEK` – ide kerülnek az automata tesztek
- `Tesztadat_Generator/TESZT_KORNYEZET` – izolált tesztkörnyezet
- `PATCH` – patch források és dokumentáció
- `patches` – a program Patch gombja innen futtatja a helyi patchokat
- `backups` – biztonsági mentések
- `docs` – projekt dokumentáció

A Tesztlabor megmarad a tesztfázis részeként.

A Patch Center jelenleg kizárólag helyi, saját Python patchokat futtat. Nyilvános kiadásban ugyanennek a felületnek a backendje később online Upgrade rendszerre cserélhető.
