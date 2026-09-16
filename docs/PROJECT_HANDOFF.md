# Project handoff — SubBind 0.6.1 RC1

Új Cursor / ChatGPT session **első lépése:** olvasd el a kanonikus dokumentumokat.
Ne kezdj L7-et. Ne találj ki hiányzó szabályt.

Az elfogadott GUI-stack **az RC1 része:** teljes HU/EN localization, lokalizált Help, Advanced mode, elfogadott TV2.x theme/UI (`src/main.py` + `src/i18n.py` + `src/ui_theme.py` + `GUI_27`).

## Projekt

- Név: SubBind
- Tagline: Smart Subtitle & Media Renamer
- Verzió: **0.6.1**
- Fejlesztő: BadMusicHUN
- Licenc: GNU GPL v3.0
- GitHub repository: SubBind
- Remote: `https://github.com/rabapeti-dotcom/SubBind.git`
- Branch: `main`
- origin/main HEAD: **b8c38c3** (`Update 0.6.1 release documentation`)
- P1 guide/rename commit (történeti, a fában benne van): `90b41c4`

## Checkpoint (2026-09-16)

- Lezárva: **C.1** + **L1, L2.1, L2.2, L2.3, L2.4**
- Utána: rollback/History (`e623d24`), guide/rename kapu (`90b41c4`)
- RC1 GUI-stack: loc + Advanced + elfogadott theme — working tree, **nincs commit/push**
- L7: **deferred**
- L8 teljes fizikai GUI: nincs lezárva
- Új SubBind EXE: **nincs** (várt: `dist\SubBind\`)
- Tervezett felhasználói kiadás: **2026-09-20**

## Tesztállapot

- GUI: **29 PASS / 0 FAIL** (`GUI_27`-tel)
- Engine: **55 PASS / 0 FAIL**; `TEST_96` SKIP új EXE nélkül
- P0 / P1: nincs. P2: `testing.test_runner` a PYZ-ben; frozen Tesztlabor UI rejtve
- `TEST_77` / `GUI_16`: izoláció után PASS (többé nem ismert FAIL)

## RC1 GUI-stack

Ez **nem** kísérleti mellékág. Az RC1 része:

- `src/main.py`
- `src/i18n.py`
- `src/ui_theme.py`
- `TESTEK/08_GUI_INTEGRACIO/GUI_27_I18N_LOCALIZATION.py`

A motor (`renamer_engine.py`) ettől független, ebben a körben nem változott.

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
2. `docs/PROJECT_STATE.md` — élő checkpoint (PASS/FAIL, RC1)
3. `docs/DECISIONS.md` — elfogadott döntések vs. implementációs következtetések
4. `docs/DEVELOPMENT_RULES.md` — egy fázis, STOP, docs-frissítési szabály

Kiegészítő: `docs/PROJEKT_STRUKTURA.txt` (mappák), ez a handoff.

## Checkpoint

- Version: 0.6.1 RC1
- origin/main: b8c38c3
- RC1 GUI-stack: working tree, commit/push nincs
- Completed: C.1, L1, L2.1, L2.2, L2.3, L2.4
- L7 deferred
- Tervezett kiadás: 2026-09-20
