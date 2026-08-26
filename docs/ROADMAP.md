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
| L7 | LANGS expansion, külön döntés alapján | **nincs indítva** — előtte explicit döntés kell |
| L8 | teljes regresszió + fizikai GUI | **nincs indítva** — csak megfelelő funkcionális állapot után |

L7 előtt explicit döntés szükséges arról, hogy valóban kell-e LANGS-bővítés.
L8 csak a megfelelő funkcionális állapot után indul.

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

## Következő lépés

1. **L7 döntés** — kell-e LANGS-bővítés (RU vagy más nyelv). Most ne implementálni.
2. **L8** — teljes regresszió + fizikai GUI, csak a funkcionális állapot után.

Release cél: **2026-09-20**.

## Checkpoint

- Version: 0.6.1
- Completed: L1, L2.1, L2.2, L2.3, L2.4
- Next decision: L7
- Release target: 2026-09-20
