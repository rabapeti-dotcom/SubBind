TESZTEK

A Tesztlabor automatikusan beolvassa a projekt TESTEK mappájának .py fájljait.

A Tesztlaborban:
- + Script(ek) hozzáadása: tetszőleges tesztscriptek hozzáadása
- Kijelölt törlése: kiválasztott elemek eltávolítása a futtatási listából
- Lista ürítése: teljes futtatási lista törlése
- Teszt után takarítás: csak a rögzített TESZT_KORNYEZET tartalmát takarítja
- TESZT FUTTATÁSA: a listában szereplő tesztek futtatása
- Hiba kimenet: az utolsó STDERR megjelenítése
- Tesztjelentés: az utolsó mentett jelentés megjelenítése

A tesztek futtatása a projekt src könyvtárát PYTHONPATH-ra teszi, és
SERIES_RENAMER_TEST_ROOT környezeti változóval izolált tesztkörnyezetet ad.
