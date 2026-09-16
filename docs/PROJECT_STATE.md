# Project state — SorozatRenamero 0.6.1

Mentés dátuma: 2026-09-16.
Stabil commit: **90b41c4** (`Fix guide rename gate consistency`).
HEAD = origin/main = `90b41c4`.
A kanonikus döntések: `docs/DECISIONS.md`. A munkamódszer: `docs/DEVELOPMENT_RULES.md`.

## Repository

- Root: `C:\Users\hunga\OneDrive\Asztali gép\SorozatAtnevezo_v0.3.1_PySide6_Projekt\SorozatRenamero_0.6.1-TEST_TISZTA`
- Remote: `https://github.com/rabapeti-dotcom/SorozatRenamero.git`
- Branch: `main`
- Verzió: **0.6.1** (`src/version.py`)

## Mi a projekt

Hordozható Windows PySide6 alkalmazás: videó- és feliratfájlok párosítása, előnézete, átnevezése vagy másolása.

A mappastruktúra: `docs/PROJEKT_STRUKTURA.txt`.

## Release állapot (2026-09-16)

A 0.6.1 **final RC** a `90b41c4` commitból készült. Nincs nyitott P0 vagy P1.

| Tétel | Állapot |
|---|---|
| Stabil commit | `90b41c4` |
| Final RC EXE | 2026-09-16 12:34:59, **2 258 579** bájt |
| Artifact | `dist\SorozatEsFilmAtnevezo\` (exe + `_internal`) |
| Portable data | sidecar `data/` az exe mellett; nem APPDATA |
| Fejlesztői `data/` | a projekt gyökér `data/` **nem** csomagolandó |
| P0 | nincs |
| P1 | nincs (guide/rename kapu: `90b41c4`, `GUI_26` PASS) |
| P2 | `testing.test_runner` bekerül a PYZ-be; frozenben a Tesztlabor UI rejtve |
| TV2.x | kísérleti; **nem** a 0.6.1 része (`src/i18n.py` unstaged, `src/ui_theme.py` untracked) |

Tervezett felhasználói kiadási dátum (változatlan, nem a jelenlegi checkpoint dátuma): **2026-09-20**.

## Funkcionális állapot

Lezárva és PASS: **C.1, L1, L2.1, L2.2, L2.3, L2.4**.

Utána (stabil `main`, 0.6.1 verziószám változatlan):

- M1 tesztizoláció (`3369084`) — `TEST_77` / `GUI_16` többé nem ismert FAIL
- L8.4 GUI design + tesztizoláció (`5c0d3bb`) — **nem** teljes L8 fizikai GUI-regresszió
- Rollback / History / partial undo (`fbf0666`, `f916f97`, `e623d24`)
- Guide/rename kapu (`90b41c4`)

| Fázis | Állapot |
|---|---|
| C.1 — többfeliratos GUI | PASS |
| L1 — subtitle_pref infrastructure | PASS |
| L2.1 — pair-status | PASS |
| L2.2 — C.1 primary | PASS |
| L2.3 — checkbox + rename | PASS |
| L2.4 — filename strategy B | PASS |
| L7 — LANGS expansion | **deferred** (2026-08-27; új követelmény nélkül nem indul) |
| L8 — teljes regresszió + fizikai GUI | nincs lezárva; az RC automatizált Engine/GUI regresszióra épül |

## Tesztállapot (2026-09-16, `90b41c4`)

| Csomag | Eredmény |
|---|---|
| Engine (`TEST_*.py`) | **56 PASS / 0 FAIL** |
| GUI (`GUI_*.py`) | **28 PASS / 0 FAIL** |
| VALOS | a teljes Engine része; 7 script |
| L2 gate | `TEST_86`, `TEST_87`, `TEST_97`, `GUI_22`, `GUI_23`, `GUI_24` — PASS |
| `TEST_96` (final RC EXE) | **PASS** |
| `GUI_26` (guide/rename kapu) | **PASS** |

Releváns engine/history tesztek: `TEST_90` F51, `TEST_91` F52A, `TEST_92` F52B, `TEST_97` L2.4, `TEST_98` F52 History, `GUI_14`, `GUI_25`.

`TEST_77` / `GUI_16`: izoláció után **PASS**. A 2026-08-26-os destination FAIL diagnózis történeti.

## TV2.x

Kísérleti working-tree munka, **nem** a 0.6.1 release.

- `src/i18n.py` — unstaged
- `src/ui_theme.py` — untracked
- A TV2.x `main.py` nincs a stabil fában; a `90b41c4` `src/main.py` a release.

Ne merge-eld, ne stage-eld, ne buildeld a 0.6.1 EXE-be.

## Következő lépés

A 0.6.1 RC artifact kiadható a `90b41c4` fából: `dist\SorozatEsFilmAtnevezo\` (projekt-gyökér `data/` nélkül).

L7 továbbra is deferred. Teljes L8 fizikai GUI nincs lezárva; ez nem release-blocker a jelenlegi automatizált regresszió mellett.

## Checkpoint

- Version: 0.6.1
- Stabil commit: 90b41c4
- Completed: C.1, L1, L2.1, L2.2, L2.3, L2.4 + rollback/History + guide/rename kapu
- Teszt: Engine 56/0, GUI 28/0, TEST_96 PASS
- L7 deferred
- Tervezett kiadás: 2026-09-20
