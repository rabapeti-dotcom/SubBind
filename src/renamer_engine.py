import os, re, shutil
from dataclasses import dataclass
from pathlib import Path

VIDEO_EXTS = {'.mkv','.mp4','.avi','.m4v','.mov','.wmv','.webm','.ts','.m2ts'}
SUB_EXTS = {'.srt','.ass','.ssa','.vtt','.sub'}
ALL_EXTS = VIDEO_EXTS | SUB_EXTS

TECH_TOKENS = {
    '2160p','1080p','720p','576p','480p','360p','web-dl','webdl','webrip','web-rip',
    'bluray','brrip','bdrip','hdtv','dvdrip','hdr','hdr10','dv','dolbyvision',
    'x264','x265','h264','h265','hevc','avc','aac','ac3','eac3','ddp','ddp5',
    'ddp5.1','dts','proper','repack','remux','extended','limited','internal',
    'readnfo','complete','completefix','multi','dual'
}
LANGS = {
    'hu':'hu','hun':'hu','hungarian':'hu','magyar':'hu',
    'en':'en','eng':'en','english':'en',
    'de':'de','ger':'de','deu':'de','german':'de','deutsch':'de',
    'fr':'fr','fra':'fr','fre':'fr','french':'fr',
    'es':'es','spa':'es','spanish':'es',
    'it':'it','ita':'it','italian':'it',
    'pl':'pl','pol':'pl','polish':'pl',
    'cs':'cs','cze':'cs','ces':'cs','czech':'cs',
    'sk':'sk','slo':'sk','slk':'sk','slovak':'sk',
    'ro':'ro','rum':'ro','ron':'ro','romanian':'ro',
}
# L1 setting-cső. L2.1: pair-status. L2.2: C.1. L2.3: checkbox/rename partner. L2.4: B fájlnév-stratégia.
DEFAULT_SUBTITLE_PREF = 'hu'
SUBTITLE_PREF_CHOICES = ('hu', 'de', 'en', 'es')


def normalize_subtitle_pref(value):
    """Whitelist: hu/de/en/es. Hiányzó vagy érvénytelen érték → hu."""
    code = str(value or '').strip().lower()
    if code in SUBTITLE_PREF_CHOICES:
        return code
    return DEFAULT_SUBTITLE_PREF


EP_PATTERNS = [
    re.compile(r'(?i)\b(S\d{1,2})[ ._-]*E(\d{1,3})\b'),
    re.compile(r'(?i)\b(\d{1,2})x(\d{1,3})\b'),
]
# Gyenge hint: csak a közvetlen szülőmappa, csak egyértelmű név. Soha nem írja felül EP_PATTERNS-t.
FOLDER_SEASON_PATTERNS = [
    re.compile(r'(?i)^season[ ._-]*(\d{1,2})$'),
    re.compile(r'(?i)^s(\d{1,2})$'),
]
EPISODE_ONLY_IN_FILENAME = re.compile(r'(?i)\bE(\d{1,3})\b')


def parse_parent_folder_season(folder_name):
    """Egyértelmű évad a szülőmappa nevéből, vagy None.

    Első verzió: Season 01 / Season 1 / S01. Nem: 01, Season, Season 01 Complete, Évad 1.
    """
    name = (folder_name or '').strip()
    if not name:
        return None
    for pat in FOLDER_SEASON_PATTERNS:
        m = pat.fullmatch(name)
        if m:
            n = int(m.group(1))
            if 1 <= n <= 99:
                return n
    return None


@dataclass
class Item:
    path: str
    ext: str
    kind: str
    season: int|None = None
    episode: int|None = None
    confidence: str = 'unknown'
    lang: str|None = None
    variant: str|None = None
    title: str = ''
    new_name: str = ''
    status: str = 'Ellenőrzést igényel'
    selected: bool = True
    group: str = ''
    note: str = ''
    source_path: str | None = None
    size_bytes: int = 0
    mtime_ns: int = 0
    copy_status: str = 'Várakozik'
    copy_percent: int = 0

def norm_sep(s):
    return re.sub(r'[ ._-]+', '.', s).strip('.')

def _tokens(stem):
    return [x for x in re.split(r'[ ._\-\[\]\(\)]+', stem) if x]

def parse_item(path):
    p = Path(path)
    ext = p.suffix.lower()
    if ext in VIDEO_EXTS:
        kind = 'video'
    elif ext in SUB_EXTS:
        kind = 'sub'
    else:
        kind = 'other'
    stem = p.stem
    season = episode = None
    confidence = 'unknown'
    for pat in EP_PATTERNS:
        m = pat.search(stem)
        if m:
            if m.group(1).lower().startswith('s'):
                season, episode = int(m.group(1)[1:]), int(m.group(2))
            else:
                season, episode = int(m.group(1)), int(m.group(2))
            confidence = 'high'
            break

    folder_hint = False
    if season is None:
        folder_season = parse_parent_folder_season(p.parent.name)
        if folder_season is not None:
            em = EPISODE_ONLY_IN_FILENAME.search(stem)
            if em:
                epn = int(em.group(1))
                if 1 <= epn <= 999:
                    season = folder_season
                    episode = epn
                    confidence = 'high'
                    folder_hint = True

    tokens = _tokens(stem)
    lang = None
    variant = None
    for i, tok in enumerate(tokens):
        key = tok.lower()
        if key in LANGS:
            lang = LANGS[key]
            if i + 1 < len(tokens):
                nxt = tokens[i+1].lower()
                if nxt in {'forced','sdh','cc','full','complete'}:
                    variant = nxt
            break

    title_tokens = []
    for tok in tokens:
        low = tok.lower()
        if re.fullmatch(r'(?i)s\d{1,2}e\d{1,3}', tok) or re.fullmatch(r'(?i)\d{1,2}x\d{1,3}', tok):
            break
        if folder_hint and re.fullmatch(r'(?i)e\d{1,3}', tok):
            break
        if low in TECH_TOKENS or low in LANGS:
            continue
        title_tokens.append(tok)

    title = norm_sep(' '.join(title_tokens))
    if not title:
        title = norm_sep(stem)

    title_key = re.sub(r'[^a-z0-9]+', '.', title.lower()).strip('.')
    episode_key = f'S{season:02d}E{episode:02d}' if season is not None and episode is not None else ''
    group = f'{title_key}|{episode_key}' if title_key or episode_key else ''

    return Item(
        str(p), ext, kind, season, episode, confidence, lang, variant, title,
        group=group, source_path=str(p),
    )

def common_title(names):
    if not names:
        return ''
    vals = [Path(x).stem for x in names]
    return norm_sep(vals[0])

def _clean_render_title(title, item):
    if not title:
        return title

    s = str(title)
    s = re.sub(r'(?i)\bS\d{1,2}[ ._-]*E\d{1,3}\b', ' ', s)
    s = re.sub(r'(?i)\b\d{1,2}x\d{1,3}\b', ' ', s)

    parts = re.split(r'[ ._\-\[\]\(\)]+', s)
    cleaned = []
    for part in parts:
        if not part:
            continue
        if part.lower() in TECH_TOKENS:
            continue
        cleaned.append(part)

    result = norm_sep(' '.join(cleaned))
    return result or norm_sep(str(title))


def render_template(template, item, title, normalize=True, subtitle_pref=DEFAULT_SUBTITLE_PREF):
    season2 = f'S{item.season:02d}' if item.season is not None else ''
    ep2 = f'E{item.episode:02d}' if item.episode is not None else ''
    lang = item.lang or ''
    title = _clean_render_title(title, item)
    vals = {
        'CIM': title, 'SZEZON': season2, 'EPIZOD': ep2, 'EV': '',
        'NYELV': lang, 'KITERJ': item.ext.lstrip('.'),
        'EP': season2 + ep2, 'EXT': item.ext.lstrip('.'),
        'SEASONNUM': str(item.season or ''),
        'EPISODENUM': f'{item.episode:02d}' if item.episode is not None else '',
    }
    out = template
    for k, v in vals.items():
        out = out.replace('{' + k + '}', v)
    if normalize:
        out = re.sub(r'\.{2,}', '.', out)
        out = re.sub(r'\s{2,}', ' ', out)
    out = out.strip(' .')
    # B stratégia: preferált sima felirat = tiszta alapnév.
    # Minden más felirat, ha van nyelv és nincs {NYELV}: .lang, variant esetén .variant.
    if (
        item.kind == 'sub'
        and lang
        and '{NYELV}' not in template
        and not is_preferred_plain_sub(item, subtitle_pref)
    ):
        out += '.' + lang
        if item.variant:
            out += '.' + item.variant
    return _with_extension(out, item.ext)


def _with_extension(name, ext):
    """A sablon {EXT}/{KITERJ} mezője után ne legyen dupla kiterjesztés."""
    ext = ext or ''
    if ext and not ext.startswith('.'):
        ext = '.' + ext
    if not ext:
        return name
    if name.lower().endswith(ext.lower()):
        return name
    return name + ext


def disambiguate_subtitle_target_names(items):
    """
    Magyar feliratnál a variáns alapból nem kerül a névbe (meglévő konvenció).
    Ha emiatt két felirat azonos célnevet kapna, a variáns tokenrel szétválasztjuk.
    """
    buckets = {}
    for item in items:
        if getattr(item, 'kind', None) != 'sub' or not getattr(item, 'new_name', None):
            continue
        key = os.path.normcase(item.new_name)
        buckets.setdefault(key, []).append(item)

    for arr in buckets.values():
        if len(arr) < 2:
            continue
        for item in arr:
            variant = (item.variant or '').strip()
            if not variant:
                continue
            stem, ext = os.path.splitext(item.new_name)
            token = '.' + variant
            if stem.lower().endswith(token.lower()):
                continue
            item.new_name = stem + token + ext


@dataclass(frozen=True)
class NamingContext:
    """analyze() névgenerálási bemenete widget nélkül."""
    mode: str
    template: str
    normalize: bool = True
    title_manual: bool = False
    global_title: str = ''
    subtitle_pref: str = DEFAULT_SUBTITLE_PREF


def apply_item_target_names(items, ctx):
    """Item → new_name / group / render státusz. Nem hív pairinget, nem nyúl copy_*-hoz.

    {CIM} forrás: parsed item.title, kivéve Sorozat mód + title_manual.
    Azonos SxxEyy + különböző parsed cím nem keveredik (group a parse-ból marad).
    """
    global_title = (getattr(ctx, 'global_title', None) or '').strip()
    mode = ctx.mode
    template_value = ctx.template
    normalize = bool(ctx.normalize)
    title_manual = bool(ctx.title_manual)
    pref = getattr(ctx, 'subtitle_pref', DEFAULT_SUBTITLE_PREF)

    for item in items:
        item.new_name = ''
        item.status = 'Ellenőrzést igényel'
        item.note = ''

        if item.kind not in ('video', 'sub'):
            item.status = 'Nem támogatott'
            item.selected = False
            ext_label = (item.ext or '').lstrip('.') or 'ismeretlen'
            item.note = (
                f'A(z) .{ext_label} kiterjesztés nem támogatott videó- '
                f'vagy feliratformátum, ezért nem dolgozható fel.'
            )
            continue

        is_series_item = (
            item.season is not None
            and item.episode is not None
            and item.confidence == 'high'
        )

        if mode == 'Sorozat' or (mode == 'Automatikus / Vegyes' and is_series_item):
            if not is_series_item:
                item.note = 'Nem sikerült megbízható évad/epizód azonosítás'
                continue
            if mode == 'Automatikus / Vegyes':
                render_title = item.title.strip()
            elif title_manual and global_title:
                render_title = global_title
            else:
                render_title = item.title.strip() or global_title
            if not render_title:
                item.note = 'Nincs megadható sorozatnév'
                continue
            item.group = item.group or f'{render_title.lower()}|S{item.season:02d}E{item.episode:02d}'
            template = template_value
        elif mode == 'Film' or (mode == 'Automatikus / Vegyes' and not is_series_item):
            render_title = item.title.strip() or global_title
            if not render_title:
                item.note = 'Nem sikerült felismerni a film nevét'
                continue
            title_key = re.sub(r'[^a-z0-9]+', '.', render_title.lower()).strip('.')
            item.group = 'FILM:' + title_key
            template = '{CIM}' if mode == 'Automatikus / Vegyes' else template_value
        else:
            item.note = 'Nem támogatott feldolgozási mód'
            continue

        item.new_name = render_template(
            template, item, render_title, normalize, subtitle_pref=pref
        )
        item.status = 'OK'


def is_preferred_plain_sub(item, pref="hu"):
    """Preferált nyelvű, variant nélküli felirat. Pair-status és B fájlnév-stratégia közös feltétele."""
    return item.kind == "sub" and item.lang == pref and not item.variant


def apply_pair_group_status(items, pref="hu"):
    """Videó+felirat group státusz: hiányos pár, M1.1 mismatch, sima pref megjegyzés.

    A pairing kulcsa az Item.group (cím+epizód), nem a felirat nyelve.
    A sima preferált felirat (default: hu) a note/státusz szabályokhoz kell.
    Nem módosít: path, source_path, new_name, selected, group, copy_*.
    """
    groups = {}
    for item in items:
        if item.kind not in ("video", "sub"):
            continue
        groups.setdefault(item.group, []).append(item)

    for group, arr in groups.items():
        vids = [x for x in arr if x.kind == "video"]
        subs = [x for x in arr if x.kind == "sub"]

        if not vids or not subs:
            mismatched = False
            for other_group, other_arr in groups.items():
                if other_group == group:
                    continue
                other_vids = [x for x in other_arr if x.kind == "video"]
                other_subs = [x for x in other_arr if x.kind == "sub"]
                if vids and other_subs and any(
                    v.season == sub.season and v.episode == sub.episode
                    for v in vids for sub in other_subs
                ):
                    # Csak a hiányos saját csoportot minősítjük.
                    # Egy másik, akár teljes group elemeit nem írjuk felül.
                    for x in vids:
                        x.status = "Nem egyező pár"
                        x.note = f"A felirat másik címhez tartozik: {other_subs[0].title}"
                    mismatched = True
                elif subs and other_vids and any(
                    v.season == sub.season and v.episode == sub.episode
                    for v in other_vids for sub in subs
                ):
                    for x in subs:
                        x.status = "Nem egyező pár"
                        x.note = f"A videó másik címhez tartozik: {other_vids[0].title}"
                    mismatched = True

            if not mismatched:
                for item in arr:
                    item.status = "Felirat nélkül" if item.kind == "video" else "Videó nélkül"
                    item.note = "Nincs ugyanahhoz a címhez tartozó videó + felirat pár"
            continue

        preferred = [x for x in subs if is_preferred_plain_sub(x, pref)]
        label = str(pref).upper()
        if not preferred:
            for item in arr:
                if item.kind == "video" and item.status == "OK":
                    item.note = f"Nincs sima {label} felirat"
        if len(preferred) > 1:
            for item in arr:
                item.status = "Ellenőrzést igényel"
                item.note = f"Több sima {label} felirat ugyanahhoz a címhez"


def apply_destination_conflicts(items, destination_for, source_path):
    """Névütközés: több kijelölt OK tétel ugyanarra a célra, vagy idegen létező cél.

    Átmásolva/Kész és nem OK / nem kijelölt tételek kimaradnak.
    Nem hívja a rename() külön konfliktuságát; destination_for a hívóé.
    """
    targets = {}
    for item in items:
        if item.status != "OK" or not item.selected:
            continue
        if getattr(item, "copy_status", "") in {"Átmásolva", "Kész"}:
            continue
        key_path = destination_for(item)
        if key_path is None:
            continue
        try:
            key = os.path.normcase(str(key_path.resolve()))
        except OSError:
            key = os.path.normcase(str(key_path))
        targets.setdefault(key, []).append(item)

    for key, conflict_items in targets.items():
        if len(conflict_items) > 1:
            for item in conflict_items:
                item.status = "Névütközés"
                item.copy_status = "Névütközés"
                item.copy_percent = 0
                item.note = "Több fájl ugyanarra a célra kerülne"

    for item in items:
        if item.status != "OK" or not item.selected:
            continue
        if getattr(item, "copy_status", "") in {"Átmásolva", "Kész"}:
            continue
        key_path = destination_for(item)
        if key_path is None:
            continue
        try:
            same = os.path.normcase(str(source_path(item).resolve())) == os.path.normcase(str(key_path.resolve()))
        except OSError:
            same = os.path.normcase(str(item.path)) == os.path.normcase(str(key_path))
        if key_path.exists() and not same:
            # A saját, már sikeres másolás célfájlja nem ütközés.
            if getattr(item, "copy_status", "") in {"Átmásolva", "Kész"}:
                continue
            # Valódi célütközés: az elem nem feldolgozható,
            # a meglévő célfájlt a program soha nem írja felül.
            item.status = "Névütközés"
            item.copy_status = "Névütközés"
            item.copy_percent = 0
            item.note = "A célfájl már létezik – a program nem írta felül"


def destination_matches_output(item, destination_for, source_path):
    """A fizikai célfájl megléte / mérete, M10 destination_for szerint."""
    dest = destination_for(item)
    if dest is None:
        return False
    try:
        if not dest.is_file():
            return False
        src = source_path(item)
        if src.is_file():
            try:
                if src.resolve() == dest.resolve():
                    return True
            except OSError:
                pass
            return dest.stat().st_size == src.stat().st_size
        return True
    except OSError:
        return False


def apply_completion_status(items, destination_for, source_path):
    """Kész csak Átmásolva/Kész copy_status + létező egyező cél esetén."""
    for item in items:
        copy_st = getattr(item, "copy_status", "Várakozik")
        if copy_st not in {"Átmásolva", "Kész"}:
            continue
        if destination_matches_output(item, destination_for, source_path):
            item.status = "Kész"
        else:
            item.copy_status = "Várakozik"
            item.copy_percent = 0


COPY_CHUNK_SIZE = 4 * 1024 * 1024


def copy_to_destination(old, new, progress=None):
    """Egy fájl másolása .part-on át, felülírás nélkül a hívó felelőssége.

    A forrást nem módosítja. Sikertelen OSError után a .part törlődik, a kivétel megy tovább.
    progress(copied_bytes, total_bytes) opcionális; Qt-t nem ismer.
    """
    old = Path(old)
    new = Path(new)
    tmp = Path(str(new) + ".part")
    try:
        if tmp.exists():
            tmp.unlink()
        total_size = max(1, old.stat().st_size)
        copied = 0
        with old.open("rb") as src_f, tmp.open("wb") as dst_f:
            while True:
                chunk = src_f.read(COPY_CHUNK_SIZE)
                if not chunk:
                    break
                dst_f.write(chunk)
                copied += len(chunk)
                if progress is not None:
                    progress(copied, total_size)
        shutil.copystat(old, tmp)
        result = tmp.stat()
        tmp.replace(new)
        return result
    except OSError:
        try:
            if tmp.exists():
                tmp.unlink()
        except OSError:
            pass
        raise


def rollback_copied_files(paths):
    """Párban már véglegesített másolatok törlése, létrehozás fordított sorrendjében.

    .part-ot nem bántja (az a hibázó fájl except/copy_to_destination ága).
    A többi tagot rollback-hiba után is megkísérli. Visszatérés: a
    megmaradt célfájlok és a hozzájuk tartozó hibák listája.
    """
    failures = []
    for made in reversed(list(paths or ())):
        try:
            made = Path(made)
            if made.exists():
                made.unlink()
        except OSError as exc:
            failures.append({"path": str(made), "error": str(exc)})
    return failures


def rollback_renamed_files(changes):
    """Helyben átnevezett pártagok visszanevezése, átnevezés fordított sorrendjében.

    Csak ha a new létezik. A többi tagot rollback-hiba után is megkísérli.
    Visszatérés: a megmaradt új nevek és a hozzájuk tartozó hibák listája.
    """
    failures = []
    for old_path, new_path in reversed(list(changes or ())):
        try:
            old_path = Path(old_path)
            new_path = Path(new_path)
            if new_path.exists():
                new_path.rename(old_path)
        except OSError as exc:
            failures.append({
                "old": str(old_path), "new": str(new_path), "error": str(exc),
            })
    return failures


def verify_copy_undo(changes):
    """History copy undo előfeltétel. None = OK; ('missing', path) vagy ('changed', path)."""
    for change in changes or ():
        new = Path(change["new"])
        if not new.exists():
            return ("missing", new)
        stat = new.stat()
        if stat.st_size != change.get("size") or stat.st_mtime_ns != change.get("mtime_ns"):
            return ("changed", new)
    return None


def apply_copy_undo(changes):
    """Létrehozott kimenetek törlése fordított sorrendben. A forrást nem bántja.

    Unlink-hiba után a többi fájlt is megkísérli. Visszatérés: a megmaradt
    célfájlok és a hozzájuk tartozó hibák listája.
    """
    failures = []
    for change in reversed(list(changes or ())):
        try:
            new = Path(change["new"])
            if new.exists():
                new.unlink()
        except OSError as exc:
            failures.append({"path": str(new), "error": str(exc)})
    return failures


def verify_inplace_undo(changes):
    """History helyben-undo: new létezik, old még nem. False = nem biztonságos."""
    for change in changes or ():
        old = Path(change["old"])
        new = Path(change["new"])
        if not new.exists() or old.exists():
            return False
    return True


def apply_inplace_undo(changes):
    """new → old visszanevezés fordított sorrendben.

    Rename-hiba után a többi fájlt is megkísérli. Visszatérés: a megmaradt
    új nevek és a hozzájuk tartozó hibák listája.
    """
    failures = []
    for change in reversed(list(changes or ())):
        try:
            Path(change["new"]).rename(change["old"])
        except OSError as exc:
            failures.append({
                "old": str(change["old"]),
                "new": str(change["new"]),
                "error": str(exc),
            })
    return failures
