# Project state — SubBind 0.6.1 RC1

Mentés dátuma: 2026-09-16.
A kanonikus döntések: `docs/DECISIONS.md`. A munkamódszer: `docs/DEVELOPMENT_RULES.md`.

## Repository

- Product: **SubBind** 0.6.1 — Smart Subtitle & Media Renamer
- Fejlesztő: **BadMusicHUN**
- Licenc: **GNU GPL v3.0**
- Root (lokális working copy): `<PROJECT_ROOT>\SorozatRenamero_0.6.1-TEST_TISZTA`
- GitHub repository: **SubBind**
- Remote: `https://github.com/rabapeti-dotcom/SubBind.git`
- Branch: `main`
- Verzió: **0.6.1** (`src/version.py`)

## Git állapot (élő)

- **HEAD / origin/main:** `b8c38c3` (`Update 0.6.1 release documentation`)
- A `90b41c4` (`Fix guide rename gate consistency`) a P1 guide/rename kapu commit; **nem** a jelenlegi HEAD.
- A SubBind 0.6.1 **RC1 working tree** (branding, GPL, localization, Advanced mode, elfogadott TV2.x GUI-stack) **még nincs commitolva és nincs pusholva**.
- Új **SubBind.exe** ebből a fából **még nincs elkészítve**. A `TEST_96` ezért SKIP, amíg nincs `dist\SubBind\SubBind.exe`.

## Mi a projekt

Hordozható Windows PySide6 alkalmazás: videó- és feliratfájlok párosítása, előnézete, átnevezése vagy másolása.

Freeware és open source, GNU GPL v3.0 alatt. A motor ebben a körben nem változott.

A mappastruktúra: `docs/PROJEKT_STRUKTURA.txt`.

## RC1 tartalom (elfogadott)

A következő **az RC1 része** (working tree, commit előtt):

- SubBind branding (`APP_NAME`, Welcome, EXE-név `SubBind.exe`)
- Fejlesztői identitás: BadMusicHUN
- LICENSE + AUTHORS + public README (English-first + Magyar)
- Teljes HU/EN localization, lokalizált Help
- Advanced mode (Haladó mód)
- Elfogadott TV2.x theme/UI (`src/ui_theme.py` + a WT `src/main.py`)
- GUI-stack: `src/main.py` + `src/i18n.py` + `src/ui_theme.py`
- `GUI_27` localization regression teszt

A motor (`src/renamer_engine.py`) stabil; ebben a körben nem módosult.
A P1 guide/rename kapu (`90b41c4`) a GUI-stackben megmaradt.

## Release állapot

Nincs nyitott P0 vagy P1.

| Tétel | Állapot |
|---|---|
| origin/main HEAD | `b8c38c3` |
| P1 guide/rename | `90b41c4`, `GUI_26` PASS (benne van a WT GUI-stackben) |
| RC1 commit / push | **nincs** |
| Új SubBind EXE | **nincs** |
| Várt artifact | `dist\SubBind\` (exe + `_internal`) — következő build kör |
| Portable data | sidecar `data/` az exe mellett; nem APPDATA |
| Fejlesztői `data/` | a projekt gyökér `data/` **nem** csomagolandó |
| P2 | `testing.test_runner` bekerül a PYZ-be; frozenben a Tesztlabor UI rejtve |

Tervezett felhasználói kiadási dátum: **2026-09-20**.

## Funkcionális állapot

Lezárva és PASS: **C.1, L1, L2.1, L2.2, L2.3, L2.4**.

Utána (0.6.1 verziószám változatlan):

- M1 tesztizoláció (`3369084`) — `TEST_77` / `GUI_16` többé nem ismert FAIL
- L8.4 GUI design + tesztizoláció (`5c0d3bb`) — **nem** teljes L8 fizikai GUI-regresszió
- Rollback / History / partial undo (`fbf0666`, `f916f97`, `e623d24`)
- Guide/rename kapu (`90b41c4`)
- RC1 GUI-stack (loc, Help, Advanced mode, elfogadott theme) — working tree, commit előtt

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

## Tesztállapot

Utolsó mért (2026-09-16, docs-szinkron után): GUI **29 PASS / 0 FAIL**. Engine **55 PASS / 0 FAIL**. `TEST_96` **SKIP** (nincs új `dist\SubBind\SubBind.exe`).

| Csomag | Eredmény |
|---|---|
| GUI (`GUI_*.py`) | **29** fájl (`GUI_27`-tel) |
| Engine (`TEST_*.py`, TEST_96 nélkül) | utolsó futás PASS |
| `TEST_96` (frozen EXE) | **SKIP**, amíg nincs `dist\SubBind\SubBind.exe` |
| `GUI_26` (guide/rename kapu) | **PASS** |
| `GUI_27` (HU/EN loc) | **PASS** |

`TEST_77` / `GUI_16`: izoláció után **PASS**.

## Következő lépés

1. RC1 working tree commit + push (csak kérésre).
2. Új portable EXE: `build_exe.bat` → `dist\SubBind\SubBind.exe`.
3. `TEST_96` az új artifacton.

L7 továbbra is deferred. Teljes L8 fizikai GUI nincs lezárva; ez nem release-blocker a jelenlegi automatizált regresszió mellett.

## Checkpoint

- Product: SubBind 0.6.1 RC1
- origin/main: **b8c38c3**
- RC1 GUI-stack: working tree, nincs commit/push
- Motor: változatlan ebben a körben
- EXE: új SubBind build nincs
- L7 deferred
- Tervezett kiadás: 2026-09-20
