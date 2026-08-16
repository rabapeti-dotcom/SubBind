# PATCH_0.6.1 – dupla epizódkód v02

A patch a feltöltött `renamer_engine.py` tényleges szerkezete alapján készült.

Javítja azt az esetet, amikor a renderelésnek átadott cím már tartalmazza
az epizódkódot és release-metaadatot, ezért az epizódkód kétszer jelenik meg.

Példa:

`Neon.Frontier.S02E04.1080p.mkv`
→ `Neon.Frontier.S02E04.mkv`

A patch:
- a pontos jelenlegi render_template blokkot keresi;
- módosítás előtt regressziós ellenőrzést futtat;
- `.bak_0.6.1_epizod_dupla` biztonsági mentést készít;
- eltérés esetén nem módosítja a projektet.

Helye a projektben: `patches`
