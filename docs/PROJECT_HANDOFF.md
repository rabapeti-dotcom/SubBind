# Project handoff — SorozatRenamero 0.6.1

Új Cursor / ChatGPT session **első lépése:** olvasd el a kanonikus dokumentumokat.
Ne kezdj L7-et. Ne merge-eld a TV2.x-et a 0.6.1-be. Ne találj ki hiányzó szabályt.

## Projekt

- Név: SorozatRenamero (Sorozat & film átnevező)
- Verzió: **0.6.1**
- Repository: `https://github.com/rabapeti-dotcom/SorozatRenamero.git`
- Branch: `main`
- Stabil commit: **90b41c4** (HEAD = origin/main)

## Checkpoint (2026-09-16)

- Lezárva: **C.1** + **L1, L2.1, L2.2, L2.3, L2.4**
- Utána: rollback/History (`e623d24`), guide/rename kapu (`90b41c4`)
- L7: **deferred**
- L8 teljes fizikai GUI: nincs lezárva
- 0.6.1 final RC: 2026-09-16 12:34:59, `dist\SorozatEsFilmAtnevezo\`
- Tervezett felhasználói kiadás: **2026-09-20**

## Tesztállapot

- Engine: **56 PASS / 0 FAIL**
- GUI: **28 PASS / 0 FAIL**
- `TEST_96` (final RC EXE): **PASS**
- P0 / P1: nincs. P2: `testing.test_runner` a PYZ-ben; frozen Tesztlabor UI rejtve
- `TEST_77` / `GUI_16`: izoláció után PASS (többé nem ismert FAIL)

## TV2.x

Kísérleti, **nem** a 0.6.1 része: `src/i18n.py` (unstaged), `src/ui_theme.py` (untracked).
Ne stage-eld, ne commitold, ne tedd a release EXE-be.

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

- LANGS-bővítés **nincs indítva** (L7 deferred). Explicit döntés kell; most ne implementálni.
- L8 teljes fizikai GUI nincs lezárva; ez nem a 0.6.1 RC következő lépése.

## Kanonikus dokumentumok (olvasd el először)

1. `docs/ROADMAP.md` — fázisok, L1–L8 vs. L2.1–L2.4
2. `docs/PROJECT_STATE.md` — élő checkpoint (PASS/FAIL, RC, TV2.x)
3. `docs/DECISIONS.md` — elfogadott döntések vs. implementációs következtetések
4. `docs/DEVELOPMENT_RULES.md` — egy fázis, STOP, docs-frissítési szabály

Kiegészítő: `docs/PROJEKT_STRUKTURA.txt` (mappák), ez a handoff.

## Checkpoint

- Version: 0.6.1
- Stabil commit: 90b41c4
- Completed: C.1, L1, L2.1, L2.2, L2.3, L2.4
- L7 deferred
- Tervezett kiadás: 2026-09-20
