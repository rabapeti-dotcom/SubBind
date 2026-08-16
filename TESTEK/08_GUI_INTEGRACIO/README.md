# GUI-10 v03

A főprogramhoz nem nyúl.

## Mi derült ki a v02 után?

A `main.py` `analyze()` logikája szerint ha egy videócsoportban nincs
felirat, akkor a videó státusza:

`Felirat nélkül`

Ezért az előző GUI-10 teszt hibás tesztadatot használt: csak videót hozott létre,
majd `OK` státuszú elemet várt.

## v03 javítás

A teszt most valódi párosított adatot hoz létre:

- `Show.S01E01.mkv`
- `Show.S01E01.hu.srt`

Ezután:

1. `analyze()`
2. `OK` státuszú elemek ellenőrzése
3. explicit kijelölés
4. modális QMessageBox-ok automatikus kezelése
5. `rename()`
6. célfájl ellenőrzése
7. videó és felirat forrásának érintetlenség-ellenőrzése

## Futtatás

A projekt gyökeréből:

`python TESTEK/08_GUI_INTEGRACIO/FUTTATAS_GUI10_v03.py`

Ezt a tesztet először közvetlenül Git Bash-ből futtasd, ne a Tesztlaborból.
