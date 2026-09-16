# Decisions — SubBind 0.6.1

Csak a munkamenetben **expliciten elfogadott** projekt-döntések.
Az implementációs következtetések külön szakaszban vannak; azok nem döntések.

## Projekt-döntések (elfogadott)

### UI nyelv vs. felirat-preferencia

- A program UI nyelve és a `subtitle_pref` teljesen külön fogalom.
- UI nyelv: HU/EN marad (jobb felső zászló).
- Felirat preferált nyelve ettől független.

### `subtitle_pref` setting (L1)

- Setting neve: `subtitle_pref`.
- Default: `hu`.
- Első kör whitelist: `hu` / `de` / `en` / `es`.
- RU jelenleg nincs (korai jelöltlista tartalmazta; az L1 whitelistbe nem került be).
- Érvénytelen vagy hiányzó érték → `hu`.
- Load / save / reset működik.
- GUI: QComboBox a Sablon és beállítások részen, a Haladó box fölött.
- HU/EN i18n címke és tooltip.
- A jelenlegi HU-alapú működés visszafelé kompatibilis (`subtitle_pref=hu` a 0.6.1 névkonvenciót tartja).

### Preferált plain definíció

- Preferred plain = `lang == pref` AND nincs variant.
- Forced / SDH / CC nem preferred plain.
- Forced / SDH / CC soha nem automatikusan preferált.

### Automatikus partner (0 / 1 / 2+)

- 0 preferred → nincs automatikus partner, nincs automatikus subtitle fallback más nyelvre.
- 1 preferred → az az automatikus partner.
- 2+ preferred → nincs `[0]` választás, review.
- Explicit felhasználói kijelölés megmarad: más nyelvű vagy variáns felirat továbbra is feldolgozható a meglévő szabályok szerint.
- „Nincs preferált felirat” **nem** automatikus feldolgozási tiltás.
- A videó/felirat pár-integritását ne lazítsuk fel csak azért, mert nincs preferált nyelv.
- A „preferencia hiánya” és a „felirat hiánya” két külön állapot.

### B filename strategy (L2.4)

- Elfogadott stratégia: **B**.
- Preferred plain → tiszta fájlnév (pl. `Show.S01E01.srt`).
- Minden más subtitle → language / variant suffix.
- Preferred forced / SDH / CC sem tiszta név (pl. pref=de: `Show.S01E01.de.forced.srt`).
- Két azonos preferred plain esetére nincs új suffix-szabály.
- `subtitle_pref=hu` esetén a 0.6.1 névkonvenció marad.

### Nyelvek és formátumok

- Ritka `.sup` / `.idx` formátumok nem prioritások.
- LANGS-bővítés (L7) külön, explicit döntés. Most nincs indítva.

### L7 — LANGS expansion halasztva (2026-08-27)

Explicit projekt-döntés az L7 előkészítő audit után. A korábbi L1–L2.4 döntések változatlanok.

- Az L7 audit **megtörtént**. L7 **jelenleg nem indokolt** a 2026-09-20 release céljához; állapot: **deferred**.
- L7 **nem implementálható** új, explicit követelmény nélkül.
- LANGS jelenleg: `hu`, `en`, `de`, `fr`, `es`, `it`, `pl`, `cs`, `sk`, `ro`.
- `subtitle_pref` whitelist változatlan: `hu` / `de` / `en` / `es`.
- RU továbbra sem támogatott.
- Nincs dokumentált release-blokkoló hiány, amely LANGS-bővítést igényelne.
- A parser által már ismert, de preference-ként nem választható nyelvek (`fr`, `it`, `pl`, `cs`, `sk`, `ro`) **külön kérdés**, nem L7-feladat most.
- TEST_77 / GUI_16 a 2026-08-27-es L7 audit idején ismert destination/test-isolation FAIL volt. Az izoláció (`3369084`) után **PASS**; lásd a 2026-09-16-os megjegyzést.

### Fázis-határok (elfogadott munkarend)

- Egy fázis egyszerre.
- L1 csak setting/GUI; pairing, analyze, rename, C.1, fájlnév akkor még nem olvasta a prefet.
- L2.1 csak pair-status.
- L2.2 csak C.1 primary.
- L2.3 csak `_checkbox_changed()` + `rename()` kapu; új helper tilos, a meglévő `is_preferred_plain_sub` használandó.
- L2.4 csak B filename strategy.
- Ismert, független FAIL-t ne javítsunk másik fázisban (történeti példa: TEST_77, GUI_16 az izoláció előtt).

## Implementációs következtetések (nem döntések)

Ezek Cursor/audit megfigyelések a kódból. Új szabályt **ne** vezessünk le belőlük.

- Közös helper: `is_preferred_plain_sub(item, pref="hu")` — `kind == "sub" AND lang == pref AND not item.variant`.
- `full` / `complete` a parserben variant, ezért a helper szerint nem preferred plain (a döntés forced/SDH/CC-t említ; a kód a `not item.variant` feltételt használja).
- Pairing kulcsa a `group` (cím + epizód), nyelvfüggetlen — meglévő viselkedés, a preferencia ezt nem írta felül.
- L2.1 után `set_subtitle_pref()` meglévő listán újra `analyze()`-t futtat.
- C.1 primary a GUI-ban `is_ui_primary_sub` / `subtitle_pref` szerint.
- L2.4: `NamingContext.subtitle_pref` + `render_template(..., subtitle_pref=...)`; `analyze()` átadja a prefet.
- TEST_77 / GUI_16 2026-08-26-os FAIL oka az akkori audit szerint: célmappa ütközés (`G:/filmekujmappa/Murderbot.S01E01.srt` már létezett), nem L2 logikai hiba. Izoláció után (2026-09-16): PASS.
- A WelcomeDialog és a jobb felső HU/EN zászló L1-ben nem változott.

### 0.6.1 RC1 GUI-stack (2026-09-16)

Explicit döntés: az elfogadott GUI-stack **az RC1 része**, nem kísérleti mellékág.

- Teljes HU/EN localization, lokalizált Help, Advanced mode, elfogadott TV2.x theme/UI.
- Fájlok: `src/main.py`, `src/i18n.py`, `src/ui_theme.py`, `GUI_27`.
- Product: SubBind. Fejlesztő: BadMusicHUN. Licenc: GNU GPL v3.0.
- origin/main HEAD: **b8c38c3**. A `90b41c4` a P1 guide/rename commit, nem a jelenlegi HEAD.
- RC1 working tree commit/push: még nincs. Új SubBind EXE: még nincs.
- A motor ettől a döntéstől független, ebben a körben nem változott.

### 0.6.1 motor RC checkpoint (2026-09-16, történeti)

Nem L7-döntés; a P1 utáni stabil motor állapot. **Nem** a jelenlegi RC1 HEAD.

- Akkori commit: **90b41c4**. Verzió 0.6.1.
- Engine 56 PASS / 0 FAIL; GUI 28 PASS / 0 FAIL; `TEST_96` az akkori EXE-n PASS.
- P0/P1: nincs. P2: `testing.test_runner` a PYZ-ben; frozen Tesztlabor UI rejtve.
- Akkor a TV2.x még working-tree kísérlet volt; az RC1 döntés ezt felülírja (lásd fent).
- Tervezett felhasználói kiadás: 2026-09-20.

## Checkpoint

- Version: 0.6.1 RC1
- origin/main: b8c38c3
- RC1 GUI-stack: elfogadva, working tree
- Completed: C.1, L1, L2.1, L2.2, L2.3, L2.4
- L7 deferred
- Tervezett kiadás: 2026-09-20
