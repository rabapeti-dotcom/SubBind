# Development rules — SubBind 0.6.1

A tényleges munkamódszer a 0.6.1 felirat-preferencia munkamenetből.
Ezek a szabályok a tartós állapot kanonikus forrásai a roadmapdel és a döntési dokumentummal együtt.

## Kanonikus dokumentumok

Új chat vagy külső beszélgetés ezekből folytatandó, a régi conversation nélkül:

| Fájl | Szerep |
|---|---|
| `docs/ROADMAP.md` | fázisok, történeti vs. tényleges bontás, következő lépés |
| `docs/PROJECT_STATE.md` | **élő checkpoint** — aktuális verzió, PASS/FAIL, ismert hibák, release cél |
| `docs/DECISIONS.md` | elfogadott döntések vs. implementációs következtetések |
| `docs/DEVELOPMENT_RULES.md` | ez a fájl — munkamódszer |
| `docs/PROJECT_HANDOFF.md` | új session indítása |
| `docs/PROJEKT_STRUKTURA.txt` | mappastruktúra (korábbi, nem felülírt) |

A roadmap és a döntési dokumentumok a projekt tartós állapotának kanonikus forrásai.
Hiányzó szabályt ne találjunk ki. Bizonytalanság esetén a `DECISIONS.md` „Projekt-döntések” szakasza a mérvadó, nem az implementációs következtetések.

## Élő checkpoint (`PROJECT_STATE.md`)

`docs/PROJECT_STATE.md` **élő checkpoint**, nem egyszeri snapshot.

Frissíteni kell a többi érintett kanonikus dokumentummal együtt, ha:

- jelentős fázis lezárul;
- jelentős döntés születik;
- a roadmap változik;
- fontos regresszió lezárul;
- release checkpoint van.

A frissített dokumentációt **külön checkpoint commitban** kell rögzíteni.
Automatikus commit / push továbbra sincs: commit és push csak kérésre.

## Egy fázis egyszerre

1. Előbb specifikáció / feltérképezés (kódmódosítás nélkül).
2. Minimális implementáció — csak az aktuális fázis fájljai és viselkedése.
3. Célzott teszt az új viselkedésre.
4. Regresszió (érintett csomag, majd indokolt teljes motor/GUI).
5. Rövid audit: mit változott, mit nem.
6. **STOP.** Következő fázist ne kezdjük ugyanabban a körben.

Scope creep tilos. Ne implementáljuk a következő L-lépést „már úgysem nagy”.

## Tiltott viselkedés

- Ne találjunk ki hiányzó szabályt.
- Ne találjunk ki új architektúrát a meglévő kód vizsgálata nélkül.
- Ne írjunk át működést, ha a fázis nem azt kéri.
- Ismert, független FAIL-t ne javítsunk másik fázisban.
- Ne hozzunk létre második helper-t ugyanarra a preferred-plain feltételre.
- LANGS-bővítés (L7) és teljes fizikai GUI-regresszió (L8) csak külön, explicit döntés után.
- Ne emeljük a verziót, ha a fázis nem kéri (L1–L2.4: 0.6.1 maradt).

## Bizonytalanság

Ha a spec, a kód és a teszt nem egyezik: **állj meg**.
Ne találjunk ki hiányzó viselkedést. Kérdezz, vagy zárd a fázist auditálva, javítás nélkül.

## Tesztelés

- Új viselkedéshez célzott teszt (engine és/vagy GUI, a fázis szerint).
- Tesztek ideiglenes könyvtárban dolgozzanak; ne használjanak valódi felhasználói fájlokat.
- A destination/test-isolation FAIL (`TEST_77`, `GUI_16`) a 2026-08-26-os auditban ismert volt; izoláció után **PASS**. Ne keverjük L2 regresszióval.
- Teljes L8 fizikai GUI nincs lezárva; a 0.6.1 RC automatizált Engine/GUI regresszióra épül.

## Git

- Commit csak kérésre.
- Push csak kérésre.
- Ne keverjük dokumentáció-mentést, fázis-implementációt és FAIL-javítást egy commitba.
- Docs-frissítés (élő checkpoint) külön checkpoint commit; automatikus commit/push nincs.

## Checkpoint

- Version: 0.6.1 RC1
- origin/main: b8c38c3
- RC1 GUI-stack: elfogadva (loc, Advanced, theme) — working tree, commit csak kérésre
- Completed: L1, L2.1, L2.2, L2.3, L2.4
- L7 deferred
- Tervezett kiadás: 2026-09-20
