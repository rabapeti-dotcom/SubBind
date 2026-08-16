from pathlib import Path
import shutil
import sys

OLD = '''def render_template(template, item, title, normalize=True):
    season2 = f'S{item.season:02d}' if item.season is not None else ''
    ep2 = f'E{item.episode:02d}' if item.episode is not None else ''
    lang = item.lang or ''
    vals = {
'''

NEW = "def _clean_render_title(title, item):\n    if not title:\n        return title\n\n    s = str(title)\n    s = re.sub(r'(?i)\\bS\\d{1,2}[ ._-]*E\\d{1,3}\\b', ' ', s)\n    s = re.sub(r'(?i)\\b\\d{1,2}x\\d{1,3}\\b', ' ', s)\n\n    parts = re.split(r'[ ._\\-\\[\\]\\(\\)]+', s)\n    cleaned = []\n    for part in parts:\n        if not part:\n            continue\n        if part.lower() in TECH_TOKENS:\n            continue\n        cleaned.append(part)\n\n    result = norm_sep(' '.join(cleaned))\n    return result or norm_sep(str(title))\n\n\ndef render_template(template, item, title, normalize=True):\n    season2 = f'S{item.season:02d}' if item.season is not None else ''\n    ep2 = f'E{item.episode:02d}' if item.episode is not None else ''\n    lang = item.lang or ''\n    title = _clean_render_title(title, item)\n    vals = {\n"

def main():
    target = Path(__file__).resolve().parent.parent / "src" / "renamer_engine.py"

    if not target.is_file():
        raise SystemExit(f"PATCH HIBA: nem található: {target}")

    current = target.read_text(encoding="utf-8")

    if OLD not in current:
        raise SystemExit(
            "PATCH HIBA: a várt 0.6.1 render_template blokk nem található. "
            "A fájlhoz nem nyúltam."
        )

    if "_clean_render_title" in current:
        raise SystemExit(
            "PATCH LEÁLLT: a javítás már szerepel a fájlban. "
            "A fájlhoz nem nyúltam."
        )

    candidate = current.replace(OLD, NEW, 1)

    ns = {}
    exec(candidate, ns, ns)

    class Item:
        season = 2
        episode = 4
        lang = None
        ext = ".mkv"
        kind = "video"
        variant = None

    checks = [
        ("Neon.Frontier.S02E04.1080p", "Neon.Frontier.S02E04.mkv"),
        ("Neon Frontier S02E04", "Neon.Frontier.S02E04.mkv"),
    ]

    for title, expected in checks:
        got = ns["render_template"]("{CIM}.{SZEZON}{EPIZOD}", Item(), title)
        if got != expected:
            raise SystemExit(
                f"PATCH HIBA: belső ellenőrzés sikertelen: {got!r} != {expected!r}. "
                "A fájlhoz nem nyúltam."
            )

    backup = target.with_name(target.name + ".bak_0.6.1_epizod_dupla")
    if backup.exists():
        raise SystemExit(
            f"PATCH LEÁLLT: a biztonsági mentés már létezik: {backup}. "
            "A fájlhoz nem nyúltam."
        )

    shutil.copy2(target, backup)
    target.write_text(candidate, encoding="utf-8")

    print("PATCH SIKERES")
    print(f"Célfájl: {target}")
    print(f"Biztonsági mentés: {backup}")
    print("Ellenőrzés: Neon.Frontier.S02E04.1080p -> Neon.Frontier.S02E04.mkv")

if __name__ == "__main__":
    main()
