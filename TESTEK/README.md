# Sorozat & film átnevező – 0.6.1 TESTEK

Ez a csomag a jelenlegi `src/main.py` működéséhez igazított, izolált teszteket tartalmaz. A 0.6.1-TEST tesztlaborhoz javított futtatási sorrendet használ: a TestCase osztályok definíciója után indul a unittest.

## Könyvtárak

- 01_ALAP – alap fájl- és párosítási tesztek
- 02_FELISMERES – sorozat/film felismerés
- 03_FELIRAT – feliratkezelés
- 04_KIMENET – célfájl- és másolási biztonság
- 05_KIJELOLES – kijelölési logika
- 06_HIBAK_ES_BIZTONSAG – ütközések, helyhiány, megszakítás
- 07_ELOZMENY – előzmények és visszaállítás

A tesztek saját ideiglenes könyvtárat használnak, és nem a valódi médiagyűjteményt módosítják.

## Kézi futtatás

A projekt gyökeréből:

    py TESTEK/FUTTATAS_OSSZES_TEST.py

Fontos: ezek közül több engine-szintű biztonsági teszt. A teljes PySide6 GUI viselkedését külön GUI-integrációs tesztekkel érdemes tovább bővíteni.
