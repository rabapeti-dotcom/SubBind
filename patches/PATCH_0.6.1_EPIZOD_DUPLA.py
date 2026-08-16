from pathlib import Path
import shutil
import sys

PATCH_NAME = "PATCH_0.6.1_EPIZOD_DUPLA.py"

def find_target():
    here = Path(__file__).resolve()
    candidates = [
        here.parent.parent / "src" / "renamer_engine.py",
        here.parent.parent / "renamer_engine.py",
        here.parent.parent.parent / "src" / "renamer_engine.py",
        here.parent.parent.parent / "renamer_engine.py",
    ]
    found = [p for p in candidates if p.is_file()]
    if len(found) != 1:
        raise RuntimeError(
            "Nem találtam pontosan egy renamer_engine.py fájlt; "
            "a patch nem módosított semmit."
        )
    return found[0]

def main():
    target = find_target()
    current = target.read_text(encoding="utf-8")

    # Pontosan a jelenlegi 0.6.1-TEST render_template blokkra támaszkodunk.
    required = [
        "def render_template(template,item,title,normalize=True):",
        "season2=f'S{item.season:02d}' if item.season is not None else ''",
        "'CIM': title,",
        "out=template",
        "return out + item.ext",
    ]
    missing = [x for x in required if x not in current]
    if missing:
        raise RuntimeError(
            "A várt 0.6.1 render_template blokk nem található; "
            "a patch NEM módosított semmit.\nHiányzó elemek: "
            + ", ".join(missing)
        )

    old = """    lang=item.lang or ''
    vals={
        'CIM': title,
        'SZEZON': season2,
"""
    new = """    lang=item.lang or ''

    # Biztonsági normalizálás:
    # ha a renderelésnek átadott cím már tartalmazza az SxxEyy / 1xNN
    # epizódkódot vagy release-metaadatot, azt nem szabad még egyszer
    # a sablon {SZEZON}{EPIZOD} változóival hozzáadni.
    # Példák:
    #   Show.S01E01.mkv -> Show.S01E01.mkv
    #   Neon.Frontier.S02E04.1080p.mkv -> Neon.Frontier.S02E04.mkv
    render_title = title
    if item.season is not None and item.episode is not None:
        cleaned = clean_title(title, item.season, item.episode)
        if cleaned:
            render_title = cleaned

    vals={
        'CIM': render_title,
        'SZEZON': season2,
"""
    if old not in current:
        raise RuntimeError(
            "A render_template belső célblokkja eltér a várt 0.6.1-TEST verziótól; "
            "a patch NEM módosított semmit."
        )

    new_text = current.replace(old, new, 1)

    # Beépített regressziós ellenőrzés a módosított forrás szintjén.
    # Nem írunk fájlt a projektbe, csak a forrásból ellenőrizzük a szabályt.
    namespace = {}
    exec(
        new_text,
        namespace,
        namespace
    )

    from types import SimpleNamespace
    test_item = SimpleNamespace(
        season=2, episode=4, lang=None, ext=".mkv",
        kind="video", variant=None
    )
    got = namespace["render_template"](
        "{CIM}.{SZEZON}{EPIZOD}",
        test_item,
        "Neon.Frontier.S02E04.1080p",
        True
    )
    expected = "Neon.Frontier.S02E04.mkv"
    if got != expected:
        raise RuntimeError(
            f"A beépített ellenőrzés sikertelen: {got!r} != {expected!r}. "
            "A projekt nem módosult."
        )

    test_item2 = SimpleNamespace(
        season=1, episode=1, lang=None, ext=".mkv",
        kind="video", variant=None
    )
    got2 = namespace["render_template"](
        "{CIM}.{SZEZON}{EPIZOD}",
        test_item2,
        "Show.S01E01",
        True
    )
    expected2 = "Show.S01E01.mkv"
    if got2 != expected2:
        raise RuntimeError(
            f"A második ellenőrzés sikertelen: {got2!r} != {expected2!r}. "
            "A projekt nem módosult."
        )

    backup = target.with_name(target.name + ".bak_0.6.1_epizod_dupla")
    if backup.exists():
        raise RuntimeError(
            f"A biztonsági mentés már létezik: {backup}\n"
            "A patch nem módosított semmit."
        )

    shutil.copy2(target, backup)
    target.write_text(new_text, encoding="utf-8")

    print("PATCH SIKERES")
    print(f"Cél: {target}")
    print(f"Biztonsági mentés: {backup}")
    print("Javítás: az SxxEyy / 1xNN kód nem kerülhet kétszer a névbe.")
    print("Javítás: a release/quality tokenek, például 1080p, nem kerülnek a címbe.")
    print("Teszt: Neon.Frontier.S02E04.1080p -> Neon.Frontier.S02E04.mkv")
    print("Teszt: Show.S01E01 -> Show.S01E01.mkv")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"PATCH HIBA: {exc}")
        sys.exit(1)
