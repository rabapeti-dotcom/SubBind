# Project state — SorozatRenamero 0.6.1

Mentés dátuma: 2026-08-26.
Forrás: L1–L2.4 munkamenet + L2 integrációs audit.
A kanonikus döntések: `docs/DECISIONS.md`. A munkamódszer: `docs/DEVELOPMENT_RULES.md`.

## Repository

- Root: `C:\Users\hunga\OneDrive\Asztali gép\SorozatAtnevezo_v0.3.1_PySide6_Projekt\SorozatRenamero_0.6.1-TEST_TISZTA`
- Remote: `https://github.com/rabapeti-dotcom/SorozatRenamero.git`
- Branch: `main`
- Verzió: **0.6.1** (`src/version.py`; a felirat-preferencia fázisokban nem emelkedett)

## Mi a projekt

Hordozható Windows PySide6 alkalmazás: videó- és feliratfájlok párosítása, előnézete, átnevezése vagy másolása.
A C.1 többfeliratos GUI-fejlesztés a felirat-preferencia előtt lezárult.

A mappastruktúra részletei: `docs/PROJEKT_STRUKTURA.txt` (ez a fájl nem lett felülírva).

## Funkcionális állapot

| Fázis | Állapot |
|---|---|
| L1 — subtitle_pref infrastructure | PASS |
| L2.1 — pair-status | PASS |
| L2.2 — C.1 primary | PASS |
| L2.3 — checkbox + rename | PASS |
| L2.4 — filename strategy B | PASS |
| Új L2 regresszió | nincs |
| L7 — LANGS expansion | nincs indítva |
| L8 — teljes regresszió + fizikai GUI | nincs indítva |

Lánc: `subtitle_pref` → pair-status → C.1 primary → checkbox/rename kapu → B filename strategy.

## Tesztállapot (L2 integrációs audit, 2026-08-26)

Engine: **54 PASS / 1 FAIL**
GUI: **25 PASS / 1 FAIL**

Ismert FAIL (nem L2 regresszió):

| Teszt | Diagnózis |
|---|---|
| `TEST_77` (`TESTEK/03_FELIRAT/TEST_77_M1_TELJES_PAR_VEDELEM.py`) | destination / test-isolation |
| `GUI_16` (`TESTEK/08_GUI_INTEGRACIO/GUI_16_M1_TELJES_PAR_VEDELEM.py`) | destination / test-isolation |

Az audit szerint a gyökér: a célmappában már létezett `G:/filmekujmappa/Murderbot.S01E01.srt` (Névütközés).
Ezeket **ne** javítsuk L7/L8 vagy más új fázis részeként, amíg a fázis célja nem ez.

Célzott L2 tesztek (audit): `TEST_87`, `TEST_97`, `TEST_86`, `GUI_22`, `GUI_23`, `GUI_24` — PASS.

## Release cél

- Dátum: **2026-09-20**
- Cél: működőképes, stabil, kiadható SorozatRenamero release

## Következő döntés

L7 előtt explicit döntés kell: szükséges-e LANGS-bővítés.
L8 csak a megfelelő funkcionális állapot után indul.

## Checkpoint

- Version: 0.6.1
- Completed: L1, L2.1, L2.2, L2.3, L2.4
- Next decision: L7
- Release target: 2026-09-20
