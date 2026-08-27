# Project handoff — SorozatRenamero 0.6.1

Új Cursor / ChatGPT session **első lépése:** olvasd el a kanonikus dokumentumokat.
Ne kezdj L7-et. Ne javítsd TEST_77 / GUI_16 hibát. Ne találj ki hiányzó szabályt.

## Projekt

- Név: SorozatRenamero (Sorozat & film átnevező)
- Verzió: **0.6.1**
- Repository: `https://github.com/rabapeti-dotcom/SorozatRenamero.git`
- Branch: `main`

## Checkpoint (L2.4 után, stabil)

- Lezárva: **C.1** (többfeliratos GUI) + **L1, L2.1, L2.2, L2.3, L2.4**
- L1–L2.4: **PASS**
- Új L2 regresszió: nincs
- L7 / L8: nincs indítva
- Release target: **2026-09-20**

## Tesztállapot

- Engine: 54 PASS / 1 FAIL
- GUI: 25 PASS / 1 FAIL
- Ismert FAIL (destination / test-isolation, **nem** L2 regresszió):
  - `TEST_77`
  - `GUI_16`
- Ezeket ne javítsuk másik fázisban.

## `subtitle_pref` — fő döntések

- UI nyelv (HU/EN) és `subtitle_pref` teljesen külön.
- Default: `hu`. Első kör: `hu` / `de` / `en` / `es`. RU nincs.
- Preferred plain = `lang == pref` AND nincs variant.
- Forced / SDH / CC nem preferred plain.
- Nincs automatikus subtitle fallback más nyelvre.
- 0 preferred → nincs automatikus partner; 1 → az a partner; 2+ → nincs `[0]`, review.
- Explicit felhasználói kijelölés megmarad.

## B filename strategy

- Preferred plain → tiszta fájlnév.
- Minden más subtitle → language / variant suffix.
- Preferred forced / SDH / CC sem tiszta név.
- Két azonos preferred plain: nincs új suffix-szabály.

## LANGS

- LANGS-bővítés **nincs indítva**.
- Következő döntési pont: **L7** — kell-e LANGS-bővítés. Explicit döntés kell; most ne implementálni.
- L8 célja: teljes regresszió + fizikai GUI, csak a megfelelő funkcionális állapot után.

## Kanonikus dokumentumok (olvasd el először)

1. `docs/ROADMAP.md` — fázisok, L1–L8 vs. L2.1–L2.4
2. `docs/PROJECT_STATE.md` — élő checkpoint (PASS/FAIL, ismert hibák, release)
3. `docs/DECISIONS.md` — elfogadott döntések vs. implementációs következtetések
4. `docs/DEVELOPMENT_RULES.md` — egy fázis, STOP, docs-frissítési szabály

Kiegészítő: `docs/PROJEKT_STRUKTURA.txt` (mappák), ez a handoff.

## Checkpoint

- Version: 0.6.1
- Completed: C.1, L1, L2.1, L2.2, L2.3, L2.4
- Next decision: L7
- Release target: 2026-09-20
