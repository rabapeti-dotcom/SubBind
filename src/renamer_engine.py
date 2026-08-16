import os, re
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
EP_PATTERNS = [
    re.compile(r'(?i)\b(S\d{1,2})[ ._-]*E(\d{1,3})\b'),
    re.compile(r'(?i)\b(\d{1,2})x(\d{1,3})\b'),
]

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

def norm_sep(s):
    return re.sub(r'[ ._-]+', '.', s).strip('.')

def _tokens(stem):
    return [x for x in re.split(r'[ ._\-\[\]\(\)]+', stem) if x]

def parse_item(path):
    p = Path(path)
    ext = p.suffix.lower()
    kind = 'video' if ext in VIDEO_EXTS else 'sub'
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
        if low in TECH_TOKENS or low in LANGS:
            continue
        title_tokens.append(tok)

    title = norm_sep(' '.join(title_tokens))
    if not title:
        title = norm_sep(stem)

    title_key = re.sub(r'[^a-z0-9]+', '.', title.lower()).strip('.')
    episode_key = f'S{season:02d}E{episode:02d}' if season is not None and episode is not None else ''
    group = f'{title_key}|{episode_key}' if title_key or episode_key else ''

    return Item(str(p), ext, kind, season, episode, confidence, lang, variant, title, group=group)

def common_title(names):
    if not names:
        return ''
    vals = [Path(x).stem for x in names]
    return norm_sep(vals[0])

def render_template(template, item, title, normalize=True):
    season2 = f'S{item.season:02d}' if item.season is not None else ''
    ep2 = f'E{item.episode:02d}' if item.episode is not None else ''
    lang = item.lang or ''
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
    if item.kind == 'sub' and lang and lang != 'hu' and '{NYELV}' not in template:
        out += '.' + lang
        if item.variant:
            out += '.' + item.variant
    return out + item.ext
