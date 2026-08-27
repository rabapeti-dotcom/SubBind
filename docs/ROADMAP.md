# Roadmap — SorozatRenamero 0.6.1

Ez a fájl a felirat-preferencia (`subtitle_pref`) fejlesztés kanonikus ütemterve.
A történeti (eredeti) fázisnevek nem lettek utólag átnevezve.
A későbbi, finomabb implementációs bontás külön szakasz.

## Eredeti roadmap (L1–L8)

Ezek a fázisnevek maradnak a történeti hivatkozás.

| Fázis | Cél | Állapot |
|---|---|---|
| L1 | `subtitle_pref` infrastructure | **PASS** (2026-08-26) |
| L2 | közös preference-helper + C.1 primary | lásd tényleges bontás: L2.1–L2.2 |
| L3 | checkbox / auto-pair | lásd tényleges bontás: L2.3 |
| L4 | rename kapu | lásd tényleges bontás: L2.3 |
| L5 | motor státusz/note | lásd tényleges bontás: L2.1 |
| L6 | `render_template` + B filename strategy | lásd tényleges bontás: L2.4 |
| L7 | LANGS expansion, külön döntés alapján | **deferred** (2026-08-27) — audit megtörtént; jelenleg nem indokolt; új követelmény nélkül nem implementálható |
| L8 | teljes regresszió + fizikai GUI | **nincs indítva** — csak megfelelő funkcionális állapot után |

L7 történeti/halasztott fázis marad; a fázis **nincs törölve**.
L7 csak új, explicit követelmény esetén indulhat.
L8 csak a megfelelő funkcionális állapot után indul; nincs started és nincs completed.

## Tényleges implementációs bontás (L2–L6)

Az L2–L6 eredeti tételei később finomabb lépésekben készültek el.
Ez a bontás **nem** írja felül az eredeti L1–L8 neveket.

| Fázis | Eredeti lefedettség | Cél | Állapot |
|---|---|---|---|
| L2.1 | L2 helper + L5 státusz/note | pair-status: `is_preferred_plain_sub` + `apply_pair_group_status(pref)` | **PASS** |
| L2.2 | L2 C.1 primary | C.1 primary megjelenítés `subtitle_pref` szerint | **PASS** |
| L2.3 | L3 + L4 | checkbox auto-pair + rename kapu | **PASS** |
| L2.4 | L6 | B filename strategy (`render_template` + `NamingContext.subtitle_pref`) | **PASS** |

L1–L2.4 jelenleg **PASS**.
Nincs új L2 regresszió.

## Lánc (aktuális)

```
subtitle_pref
    → L2.1 pair-status
    → L2.2 C.1 primary
    → L2.3 checkbox / rename kapu
    → L2.4 filename strategy B
```

Közös feltétel: `is_preferred_plain_sub(item, pref)` —
`kind == "sub"` AND `lang == pref` AND nincs variant.

## L7 audit (2026-08-27)

Explicit döntés: L7 a 2026-09-20 release céljához **jelenleg nem indokolt** (`docs/DECISIONS.md`).

- LANGS: `hu`, `en`, `de`, `fr`, `es`, `it`, `pl`, `cs`, `sk`, `ro`
- `subtitle_pref`: `hu`, `de`, `en`, `es`
- RU továbbra sem támogatott
- Nincs dokumentált release-blokkoló hiány LANGS-bővítésre
- Parserben ismert, pref-ként nem választható nyelvek: külön kérdés

## Következő lépés

L7 deferred; next step: L8 release stabilization planning.

Release cél: **2026-09-20** (változatlan).

## Checkpoint

- Version: 0.6.1
- Completed: C.1, L1, L2.1, L2.2, L2.3, L2.4
- L7 deferred; next step: L8 release stabilization planning
- Release target: 2026-09-20
