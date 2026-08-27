# Project state — SorozatRenamero 0.6.1

Mentés dátuma: 2026-08-27.
Forrás: L1–L2.4 munkamenet + L2 integrációs audit + L7 előkészítő audit.
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

Checkpoint: **C.1 + L1 + L2.1 + L2.2 + L2.3 + L2.4 PASS.**

| Fázis | Állapot |
|---|---|
| C.1 — többfeliratos GUI | PASS (L1 előtt lezárva) |
| L1 — subtitle_pref infrastructure | PASS |
| L2.1 — pair-status | PASS |
| L2.2 — C.1 primary | PASS |
| L2.3 — checkbox + rename | PASS |
| L2.4 — filename strategy B | PASS |
| Új L2 regresszió | nincs |
| L7 — LANGS expansion | **deferred** (audit 2026-08-27; jelenleg nem indokolt) |
| L8 — teljes regresszió + fizikai GUI | nincs indítva |

Lánc: `subtitle_pref` → pair-status → C.1 primary → checkbox/rename kapu → B filename strategy.

L7 audit: LANGS = `hu, en, de, fr, es, it, pl, cs, sk, ro`; `subtitle_pref` = `hu, de, en, es`; RU nem támogatott. Nincs dokumentált release-blokkoló hiány LANGS-bővítésre. L7 csak új, explicit követelmény esetén indulhat.

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

## Következő lépés

L7 deferred; next step: L8 release stabilization planning.

L8 nincs started és nincs completed.

## Checkpoint

- Version: 0.6.1
- Completed: C.1, L1, L2.1, L2.2, L2.3, L2.4
- L7 deferred; next step: L8 release stabilization planning
- Release target: 2026-09-20
