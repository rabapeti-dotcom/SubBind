"""Display strings. Internal mode/output/sort/status identifiers stay Hungarian."""

MODE_IDS = ("Automatikus / Vegyes", "Sorozat", "Film")
OUTPUT_IDS = (
    "Másolás kimeneti mappába és átnevezés",
    "Helyben átnevezés",
)
SORT_IDS = ("Név", "Évad → epizód", "Fájltípus", "Módosítás dátuma")
MODE_IDS = MODE_IDS
OUTPUT_IDS = OUTPUT_IDS
SORT_IDS = SORT_IDS

MODE_KEYS = {
    "Automatikus / Vegyes": "mode.mixed",
    "Sorozat": "mode.series",
    "Film": "mode.movie",
}
OUTPUT_KEYS = {
    "Másolás kimeneti mappába és átnevezés": "output.copy",
    "Helyben átnevezés": "output.inplace",
}
SORT_KEYS = {
    "Név": "sort.name",
    "Évad → epizód": "sort.episode",
    "Fájltípus": "sort.type",
    "Módosítás dátuma": "sort.date",
}
SUBTITLE_PREF_KEYS = {
    "hu": "lang.hu",
    "de": "lang.de",
    "en": "lang.en",
    "es": "lang.es",
}
STATUS_KEYS = {
    "OK": "state.ok",
    "Kész": "state.done",
    "Várakozik": "state.waiting",
    "Átmásolva": "state.copied",
    "Másolás...": "state.copying",
    "Átnevezés...": "state.renaming",
    "Már létezik": "state.exists",
    "Névütközés": "state.conflict",
    "Nem egyező pár": "state.mismatch",
    "Hiba": "state.error",
    "Nem fért el": "state.nospace",
    "Megszakítva": "state.cancelled",
}

# Fájlok / Állapot oszlop: csak megjelenítés. A belső item.status változatlan.
STATUS_DISPLAY_KEYS = {
    "OK": "review.ok",
    "Kész": "review.ok",
    "Felirat nélkül": "review.no_sub",
    "Videó nélkül": "review.no_video",
    "Nem egyező pár": "review.mismatch",
    "Névütközés": "review.conflict",
    "Ellenőrzést igényel": "review.needs",
    "Nem támogatott": "review.blocked",
}

# Előzmény művelet/állapot: belső azonosító magyar, megjelenítés a UI nyelvén.
HIST_OP_KEYS = {
    "Másolás és átnevezés": "hist.op_copy",
    "Helyben átnevezés": "hist.op_inplace",
    "Átnevezés": "hist.op_rename",
}
HIST_STATUS_KEYS = {
    "Sikeres": "hist.status_ok",
    "Részben elkészült": "hist.status_partial",
    "Megszakítva": "state.cancelled",
    "Visszavonva": "hist.status_undone",
    "Hiba": "state.error",
}

# Motor/GUI note mező: belső szöveg változatlan, a UI a kulccsal jeleníti.
NOTE_KEYS = {
    "A célfájl már létezik – a program nem írta felül": "note.exists",
    "Több fájl ugyanarra a célra kerülne": "note.collision",
    "A felhasználó megszakította a műveletet": "note.cancelled",
    "A teljes videó + felirat pár nem fért el": "note.pair_nospace",
    "A videó + felirat pár visszaállítva": "note.pair_restored",
    "A teljes pár visszaállítva": "note.pair_restored_short",
    "Nem sikerült megbízható évad/epizód azonosítás": "note.no_ep",
    "Nincs megadható sorozatnév": "note.no_title",
    "Nem sikerült felismerni a film nevét": "note.no_movie",
    "Nem támogatott feldolgozási mód": "note.bad_mode",
    "Nincs ugyanahhoz a címhez tartozó videó + felirat pár": "note.no_pair",
}
NOTE_PREFIXES = (
    ("A felirat másik címhez tartozik: ", "note.sub_other_title"),
    ("A videó másik címhez tartozik: ", "note.vid_other_title"),
    ("Visszaállítás sikertelen: ", "note.undo_failed"),
    ("A pár rollbackje sikertelen; a célfájl megmaradt: ", "note.rollback_kept"),
)

_HU = {
    "win.title": "{name} v{version}",
    "btn.add": "＋ Hozzáadás",
    "menu.add_files": "Fájlok hozzáadása",
    "menu.add_folders": "Mappák hozzáadása",
    "menu.add_folder": "Mappa hozzáadása",
    "dlg.pick_folder": "Mappa kiválasztása",
    "btn.clear_list": "Lista ürítése",
    "btn.check": "Ellenőrzés",
    "btn.refresh_preview": "Előnézet frissítése",
    "btn.testlab": "Tesztlabor",
    "tip.testlab": "Ideiglenes automata tesztlabor — 0.6.0-TEST",
    "btn.patch": "Patch",
    "tip.patch": (
        "Tesztfázis: helyi patchok futtatása. "
        "Később online Upgrade központ használhatja ugyanezt a gombot."
    ),
    "btn.help": "Súgó ▾",
    "menu.help": "Súgó és használati útmutató",
    "menu.first_steps": "Első lépések",
    "menu.template_vars": "Sablonváltozók",
    "menu.updates": "Frissítések keresése",
    "menu.bug": "Hibajelentés",
    "menu.donate": "Adományozás / Donate",
    "menu.about": "Névjegy",
    "btn.rename": "Átnevezés",
    "tip.light": "Világos mód",
    "tip.dark": "Sötét mód",
    "tip.theme_toggle_light": "Világos megjelenés. Kattintásra sötét mód.",
    "tip.theme_toggle_dark": "Sötét megjelenés. Kattintásra világos mód.",
    "tip.rename_empty": "A kezdéshez adj hozzá videókat vagy feliratokat.",
    "tip.rename_added": "Ellenőrizd a listában, mit találtunk a fájlokból.",
    "tip.rename_select": "Jelöld ki a listában azokat a fájlokat, amelyeket át szeretnél nevezni.",
    "tip.rename_review": "Nézd át a jelzett fájlokat. Az átnevezéshez kell legalább egy rendben lévő, kijelölt fájl.",
    "tip.rename_output": "Válassz kimeneti mappát, vagy válts helybeni átnevezésre.",
    "tip.rename_busy": "Várj, amíg a folyamat befejeződik.",
    "tip.rename_done": "Ezek a fájlok már átnevezve. Új fájlokkal folytathatod.",
    "tip.rename_ready": "Az átnevezés elindítható.",
    "tip.hu": "Magyar",
    "tip.en": "English",
    "btn.bug": "Hibajelentés",
    "btn.donate": "Donate",
    "btn.cancel": "⛔  Feladat megszakítása",
    "btn.cancel_busy": "⛔  Megszakítás folyamatban…",
    "tab.files": "Fájlok",
    "tab.settings": "Haladó beállítások",
    "settings.intro": (
        "A napi használathoz elég a Fájlok fül. Itt a névsablon és a ritkábban "
        "használt beállítások találhatók — ezeket csak akkor kell módosítani, "
        "ha az alapértelmezett működés nem felel meg."
    ),
    "settings.naming_box": "Névadás",
    "tab.preview": "Előnézet",
    "tab.history": "Előzmények",
    "files.search_ph": "Keresés...",
    "files.search": "Keresés",
    "files.sort": "Rendezés:",
    "files.select_all": "Minden kiválasztása",
    "files.deselect": "Kijelölés törlése",
    "files.remove_selected": "Kijelöltek törlése",
    "tip.remove_selected": "Csak a bepipált sorokat távolítja el a listából.",
    "files.select_review": "Ellenőrzendők kijelölése",
    "tip.select_review": "A figyelmeztetett és a nem feldolgozható sorokat jelöli ki a listában.",
    "files.show_review_only": "Csak az ellenőrzendők",
    "tip.show_review_only": (
        "A táblázatban csak a figyelmeztetett és a nem feldolgozható sorokat "
        "mutatja. A kijelölést nem módosítja."
    ),
    "files.empty": (
        "<b>Kezdéshez adj hozzá egy mappát vagy fájlokat.</b><br>"
        "Húzd ide a videókat és feliratokat, vagy kattints a „Mappa hozzáadása” gombra."
    ),
    "btn.add_folder_cta": "Mappa hozzáadása",
    "guide.empty": "Kezdéshez adj hozzá fájlokat.",
    "guide.added": "Fájlok hozzáadva — ellenőrizd, mit találtunk.",
    "guide.preview": "Ellenőrizd az új neveket a listában.",
    "guide.ready": "Minden kész — az átnevezés elindítható.",
    "guide.review": "Néhány fájl ellenőrzést igényel.",
    "guide.busy": "Feldolgozás folyamatban...",
    "guide.done": "A feldolgozás befejeződött.",
    "guide.counts": "{ok} fájl rendben van, {issues} fájl ellenőrzést igényel.",
    "guide.rename_only_ok": "Az Átnevezés csak a rendben lévő fájlokat dolgozza fel.",
    "guide.counts_ok": "{ok} fájl rendben van.",
    "guide.counts_issues": "{issues} fájl ellenőrzést igényel.",
    "review.ok": "✓ Rendben",
    "review.needs": "⚠ Ellenőrzést igényel",
    "review.blocked": "✕ Nem dolgozható fel",
    "review.no_sub": "⚠ Hiányzó felirat",
    "review.no_video": "⚠ Hiányzó videó",
    "review.mismatch": "⚠ Nem egyező pár",
    "review.conflict": "⚠ Névütközés",
    "detect.summary_line": (
        "{episodes} epizód · {videos} videó · {subs} felirat · minden pár rendben"
    ),
    "detect.summary_line_missing": (
        "{episodes} epizód · {videos} videó · {subs} felirat · {missing} hiányzó pár"
    ),
    "detect.summary_line_movie": (
        "{videos} videó · {subs} felirat · minden pár rendben"
    ),
    "detect.summary_line_movie_missing": (
        "{videos} videó · {subs} felirat · {missing} hiányzó pár"
    ),
    "detect.summary_unknown": "Felismert fájlok",
    "output.box": "Kimenet",
    "output.action": "Művelet:",
    "output.folder": "Kimeneti mappa:",
    "output.folder_ph": "Válassz egy külön kimeneti mappát...",
    "output.browse": "Mappa kiválasztása…",
    "output.hint_copy": (
        "<b>Biztonságos másolás</b><br>"
        "Az eredeti fájlok érintetlenek maradnak. A program a kijelölt "
        "videókat és feliratokat a kimeneti mappába másolja az új nevekkel."
    ),
    "output.hint_inplace": (
        "<b>⚠ FIGYELEM – az eredeti fájlok neve megváltozik!</b><br>"
        "Ezt csak akkor válaszd, ha az eredeti fájlokat már külön "
        "munkamappába másoltad."
    ),
    "table.check": "✓",
    "table.original": "Eredeti",
    "table.new_name": "Új név",
    "table.status": "Állapot",
    "table.series": "Sorozat",
    "table.season": "Évad",
    "table.episode": "Epizód",
    "table.type": "Típus",
    "table.size": "Méret",
    "table.copy_state": "Másolási állapot",
    "table.progress": "Folyamat",
    "tip.table_check": (
        "Kijelölés: kattintásra mindent kijelöl / újabb kattintásra mindent töröl"
    ),
    "kind.video": "videó",
    "kind.sub": "felirat",
    "kind.other": "egyéb",
    "lang.hu": "Magyar",
    "lang.en": "Angol",
    "lang.de": "Német",
    "lang.fr": "Francia",
    "lang.es": "Spanyol",
    "lang.it": "Olasz",
    "lang.pl": "Lengyel",
    "lang.cs": "Cseh",
    "lang.sk": "Szlovák",
    "lang.ro": "Román",
    "sub.lang_none": "—",
    "sub.primary": "elsődleges",
    "meta.av_counts": "{videos} videó · {subs} felirat",
    "tip.lang": "Nyelv: {lang}",
    "tip.format": "Formátum: {fmt}",
    "tip.variant": "Variáns: {variant}",
    "tip.variant_none": "nincs",
    "tip.primary_yes": "Elsődleges: igen",
    "tip.primary_no": "Elsődleges: nem",
    "preview.group_head": "{title} — {episode}",
    "preview.group_counts": "{videos} videó · {subs} felirat",
    "preview.file_video": (
        "    {mark} {kind}\n"
        "      Eredeti: {original}\n"
        "      → {new_name}\n"
        "      [{status}] {note} | {copy}\n"
    ),
    "preview.file_sub": (
        "    {mark} {kind} · {meta}\n"
        "      Eredeti: {original}\n"
        "      → {new_name}\n"
        "      [{status}] {note} | {copy}\n"
    ),
    "mode.label": "Mód:",
    "mode.mixed": "Automatikus / Vegyes",
    "mode.series": "Sorozat",
    "mode.movie": "Film",
    "output.copy": "Másolás kimeneti mappába és átnevezés",
    "output.inplace": "Helyben átnevezés",
    "sort.name": "Név",
    "sort.episode": "Évad → epizód",
    "sort.type": "Fájltípus",
    "sort.date": "Módosítás dátuma",
    "name.series": "Sorozat neve:",
    "name.movie": "Film neve:",
    "name.mixed": "Alapértelmezett cím (opcionális):",
    "detect.box": "Felismerés",
    "detect.none": "Még nincs elemzés",
    "detect.fail": "Nem sikerült címet felismerni.",
    "detect.series": "Sorozatok: {names}",
    "detect.movies": "Filmek: {names}",
    "template.label": "Kívánt név sablon:",
    "vars.base": "Alap változók:",
    "vars.series": "Sorozatváltozók:",
    "tpl.series": "Alapértelmezett sorozatsablon: {CIM}.{SZEZON}{EPIZOD}",
    "tpl.movie": "Alapértelmezett filmsablon: {CIM}",
    "tpl.mixed": (
        "Vegyes módban az SxxEyy alapján sorozat, egyébként film kerül felismerésre. "
        "A film sablonja: {CIM}"
    ),
    "pref.label": "Preferált felirat nyelve:",
    "pref.tip": (
        "A feliratoknál előnyben részesített nyelv. "
        "Független a program nyelvétől (magyar / angol)."
    ),
    "adv.normalize": "Fájlnév normalizálása",
    "adv.lang_norm": "Feliratnevek normalizálása",
    "adv.subdirs": "Almappák bevonása",
    "adv.conflicts": "Névütközések előzetes ellenőrzése",
    "adv.preserve": "Kijelölések megőrzése",
    "adv.vars": "Haladó sablonváltozók: {NYELV}, {KITERJ}, {EP}, {EXT}",
    "btn.save_settings": "Beállítások mentése",
    "btn.refresh_list": "Lista frissítése",
    "tip.refresh_list": "Újraelemzi a listát és újragenerálja a tervezett neveket.",
    "btn.reset_settings": "Beállítások visszaállítása",
    "preview.select_all": "Összes kijelölése",
    "preview.select_none": "Kijelölés törlése",
    "preview.select_missing": "Csak a hiányzókat",
    "history.info": (
        "Itt láthatod a korábbi műveleteket. "
        "A jelölőnégyzetekkel több előzményt is kiválaszthatsz. "
        "Részlegesen sikeres műveletnél a Kimaradt fájlok gomb megmutatja a konkrét problémákat."
    ),
    "hist.check": "✓",
    "hist.num": "#",
    "hist.time": "Időpont",
    "hist.op": "Művelet",
    "hist.title": "Sorozat / film",
    "hist.files": "Fájlok",
    "hist.place": "Hely",
    "hist.select_all": "Minden kijelölése",
    "hist.deselect": "Kijelölés törlése",
    "hist.delete": "Kijelöltek törlése",
    "hist.undo": "Kiválasztott művelet visszaállítása",
    "hist.failed": "Kimaradt fájlok",
    "hist.failed_title": "Kimaradt fájlok",
    "hist.failed_need_one": "A kimaradt fájlok megtekintéséhez pontosan egy előzményt jelölj ki.",
    "hist.failed_none": "Ehhez a művelethez nincs kimaradt fájl.",
    "hist.failed_body": "{n} fájl kimaradt.\n\n{list}",
    "hist.failed_item": "{file}\n  {reason}",
    "hist.failed_tip": "A kimaradt fájlok okai a Kimaradt fájlok gombbal nézhetők meg.",
    "hist.export": "Előzmények exportálása",
    "hist.clear": "Összes előzmény törlése",
    "status.zero": "0 fájl",
    "status.files": "{n} fájl | kijelölve: {selected}",
    "status.selected": "Kijelölve: {selected} / {n} fájl",
    "status.added": "{added} új fájl hozzáadva — összesen {total} fájl",
    "status.none_added": "0 új fájl — a kiválasztott fájlok már a listában vannak",
    "preview.head": (
        "Feldolgozási lista: {series} sorozat | {movies} film | {seasons} évad | "
        "{files} fájl | Rendben: {ok} | Ellenőrzést igényel: {issues}"
    ),
    "preview.item": (
        "[{mark}] {title} — {episode} — {kind}\n"
        "    Eredeti: {original}\n"
        "    → {new_name}\n"
        "    [{status}] {note} | {copy}\n"
    ),
    "preview.unknown": "Ismeretlen",
    "progress.work": "Feldolgozás",
    "progress.file": "Fájl: {name}",
    "progress.done": "Kész  •  teljes művelet befejezve",
    "progress.fmt": "{label}  •  {current} / {total}  •  {percent}%",
    "state.ok": "OK",
    "state.done": "Kész",
    "state.waiting": "Várakozik",
    "state.copied": "Átmásolva",
    "state.copying": "Másolás...",
    "state.renaming": "Átnevezés...",
    "state.exists": "Már létezik",
    "state.conflict": "Névütközés",
    "state.mismatch": "Nem egyező pár",
    "state.error": "Hiba",
    "state.nospace": "Nem fért el",
    "state.cancelled": "Megszakítva",
    "check.title": "Ellenőrzés",
    "check.body": (
        "Sorozatok: {series}\nFilmek: {movies}\nÉvadok: {seasons}\n"
        "Fájlok: {files}\nKijelölve: {selected}\nRendben: {ok}\n"
        "Ellenőrzést igényel: {issues}\n\n"
        "Sorozatok: {series_names}\nFilmek: {movie_names}\n\n"
        "Problémás fájlok:\n{details}"
    ),
    "check.mixed_note": (
        "\n\nFigyelem: a lista filmfájlokat is tartalmaz. "
        "Vegyes feldolgozáshoz válaszd az „{mode}” módot."
    ),
    "check.no_issues": "Nincs problémás fájl.",
    "check.unknown_movie": "Ismeretlen film",
    "check.more_files": "• … és még {n} fájl",
    "welcome.title": "Üdvözöl a SubBind",
    "welcome.kicker": "HELYI FÁJLOK  ·  VIDEÓ ÉS FELIRAT",
    "welcome.headline": "Eleged van abból, hogy a felirat nem működik?",
    "welcome.intro": (
        "Pendrive-ról vagy külső lemezről a tévén gyakran eltűnik a felirat, "
        "pedig a fájl ott van a videó mellett. A lejátszó akkor találja meg, "
        "ha a két fájl neve megegyezik.\n\n"
        "Egy egész sorozatnál ezt egyenként átnevezni fárasztó. A program "
        "felismeri a párokat, megmutatja a tervezett új neveket, és csak "
        "a jóváhagyásod után nevez át."
    ),
    "welcome.example": "Így néz ki az átnevezés",
    "welcome.original": "Eredeti",
    "welcome.new_name": "Új név",
    "welcome.ex_orig_video": "film.cime.s01e01.web-dl.aac2.0.h.264-tdi.mkv",
    "welcome.ex_orig_sub": "FILM.CIME.S01E01.The.Eyes.ATV.WEB-DL.hu.srt",
    "welcome.ex_new_video": "film.cime.S01E01.mkv",
    "welcome.ex_new_sub": "film.cime.S01E01.srt",
    "welcome.note": (
        "Az alapfunkciókhoz nincs szükség internetre. "
        "A program a kiválasztott fájlokkal és mappákkal dolgozik."
    ),
    "footer.test_version": "Test Version 2",
    "welcome.language": "Nyelv:",
    "welcome.dont_show": "Ne jelenjen meg ez az ablak a következő indításkor",
    "welcome.first": "Első lépések",
    "welcome.ok": "Rendben, kezdjük",
    "msg.first_steps_title": "Első lépések",
    "msg.first_steps": (
        "1. Adj hozzá egy mappát vagy fájlokat.\n"
        "2. Ellenőrizd az előnézetet.\n"
        "3. A bizonytalan eseteket a program nem nevezi át automatikusan.\n"
        "4. Az Átnevezés csak a problémamentes, kijelölt fájlokat dolgozza fel."
    ),
    "msg.template_title": "Sablonváltozók",
    "msg.template": (
        "Alap változók:\n\n"
        "{CIM} – cím\n"
        "{SZEZON} – évad, például S01\n"
        "{EPIZOD} – epizód, például E01\n\n"
        "Haladó változók:\n\n"
        "{EP} – teljes epizódjelölés, például S01E01\n"
        "{NYELV} – felirat nyelve\n"
        "{EXT} – fájlkiterjesztés pont nélkül\n\n"
        "A kapcsos zárójelek a sablon szintaxisának részei."
    ),
    "msg.updates_title": "Frissítések keresése",
    "msg.updates": (
        "Jelenlegi verzió: {version}\n\n"
        "Online frissítés-ellenőrzés nincs beépítve. "
        "A program hordozható: a beállítások a program melletti data mappában vannak."
    ),
    "msg.bug_title": "Hibajelentés",
    "msg.bug": (
        "Online hibabejelentő nincs a programban.\n\n"
        "Ha hibát tapasztalsz, jegyezd fel a műveletet és a fájlneveket."
    ),
    "msg.donate_title": "Donate",
    "msg.donate": "Jelenleg nincs beépített támogatási link.",
    "msg.about_title": "Névjegy",
    "msg.about": (
        "{name}\nSmart Subtitle & Media Renamer\nv{version}\n\n"
        "Készítette: {author}\n"
        "Licensed under GNU GPL v3.0\n\n"
        "Freeware alkalmazás videó- és feliratfájlok nevének összehangolásához."
    ),
    "msg.saved_title": "Mentve",
    "msg.saved": "A beállításokat elmentettem.",
    "msg.no_sel_title": "Nincs kijelölés",
    "msg.no_sel": "Nincs kijelölt sor, amit törölni lehetne a listából.",
    "msg.remove_title": "Kijelöltek törlése",
    "msg.remove": (
        "{n} kijelölt fájl eltávolítása a feldolgozási listából?\n\n"
        "Az eredeti fájlokat ez nem törli és nem módosítja."
    ),
    "msg.nothing_title": "Nincs feldolgozható fájl",
    "msg.nothing": "Nincs kijelölt, feldolgozható videó + felirat csoport.",
    "msg.output_title": "Kimenet",
    "msg.pair_title": "Hiányos epizód kijelölés",
    "msg.pair": (
        "Egy vagy több epizódnál csak a videó vagy csak a felirat van kijelölve.\n\n"
        "A videó és a hozzá tartozó felirat csak együtt másolható.\n"
        "Jelöld ki a teljes párt, vagy használd a „Csak a hiányzókat” funkciót."
    ),
    "msg.idle_title": "Nincs teendő",
    "msg.idle": "Nem maradt végrehajtható művelet.",
    "confirm.title": "Mit fogunk most csinálni?",
    "confirm.files": "{n} fájl",
    "confirm.kinds": "{videos} videó + {subs} felirat",
    "confirm.preview": "Eredeti → új név",
    "confirm.rename_pair": "{old}\n→\n{new}",
    "confirm.copy_same": "{name}\n→\nmásolás a célmappába (a fájlnév nem változik)",
    "confirm.more": "… és még {n} fájl",
    "confirm.op_copy": "Művelet: biztonságos másolás",
    "confirm.op_inplace": "Művelet: helyben átnevezés",
    "confirm.target": "Célmappa: {path}",
    "confirm.keep": "Az eredeti fájlok megmaradnak.",
    "confirm.change": "Az eredeti fájlok neve megváltozik.",
    "confirm.cancel": "Mégse",
    "confirm.start": "Indítás",
    "help.title": "Súgó – {name} v{version}",
    "help.body": (
        "{name} – Súgó\n"
        "Verzió: {version}\n\n"
        "ELSŐ LÉPÉSEK\n"
        "1. Mappa hozzáadása vagy Fájlok hozzáadása.\n"
        "2. Ellenőrizd az Előnézetet.\n"
        "3. A bizonytalan eseteket a program nem nevezi át automatikusan.\n"
        "4. Az Átnevezés csak a problémamentes, kijelölt elemeket dolgozza fel.\n\n"
        "SOROZAT MÓD\n"
        "A program az S01E01 vagy 1x01 formátumú epizódazonosítókat "
        "biztonságosan felismeri. A puszta E05 formátumot szándékosan "
        "nem fogadja el automatikusan.\n\n"
        "FILM MÓD\n"
        "Film esetén nincs évad- és epizódkövetelmény.\n\n"
        "FONTOS\n"
        "A program nem írja át a fájlok tartalmát, csak a fájlneveket módosítja."
    ),
    "help.close": "Bezárás",
    "dlg.add_folders_title": "Könyvtárak hozzáadása",
    "dlg.add_folders_info": (
        "Jelölj ki egy vagy több könyvtárat. Ctrl/Shift segítségével több könyvtár is kiválasztható."
    ),
    "dlg.location": "Hely:",
    "dlg.path_ph": "Mappa útvonala – beilleszthető vagy begépelhető",
    "dlg.open": "Megnyitás",
    "dlg.selected_folders": "Kijelölve: {n} könyvtár",
    "dlg.invalid_folder_title": "Érvénytelen mappa",
    "dlg.invalid_folder": "A mappa nem található:\n{path}",
    "dlg.none_selected_title": "Nincs kijelölve",
    "dlg.none_selected_folders": "Jelölj ki legalább egy könyvtárat.",
    "dlg.add": "Hozzáadás",
    "dlg.cancel": "Mégsem",
    "dlg.add_folder_title": "Mappa hozzáadása",
    "dlg.add_folder_info": (
        "Illeszd be a mappa útvonalát, vagy tallózz. "
        "Az almappák a beállítások „Almappák bevonása” kapcsolóját követik."
    ),
    "dlg.browse": "Tallózás…",
    "dlg.path_example": r"C:\Sorozatok\Show",
    "dlg.pick_files": "Videók és feliratok kiválasztása",
    "dlg.files_filter": "Támogatott fájlok ({exts})",
    "dlg.all_files": "Minden fájl (*.*)",
    "msg.no_files_title": "Nincs hozzáadható fájl",
    "msg.no_files_folders": (
        "A kiválasztott könyvtárakban nem találtam támogatott videó- vagy feliratfájlt."
    ),
    "msg.no_files_folder": (
        "A kiválasztott mappában nem találtam támogatott fájlt:\n\n"
        "{path}\n\n"
        "Támogatott videók: MKV, MP4, AVI, M4V, MOV, WMV, WEBM, TS, M2TS\n"
        "Támogatott feliratok: SRT, ASS, SSA, VTT, SUB"
    ),
    "msg.no_files_drop": (
        "A húzott mappákban nem találtam támogatott videó- vagy feliratfájlt."
    ),
    "msg.no_direct_title": "Nincs közvetlenül feldolgozható fájl",
    "msg.no_direct": (
        "A kiválasztott mappában nem találtam támogatott videó- vagy "
        "feliratfájlt közvetlenül.\n\n"
        "Megnézzem az almappákat is?"
    ),
    "msg.path_missing_title": "Nem elérhető útvonal",
    "msg.path_missing": "A megadott fájl vagy mappa nem található:\n{paths}",
    "msg.clear_title": "Lista ürítése",
    "msg.clear": (
        "Biztosan törlöd a teljes feldolgozási listát?\n\n"
        "Ez csak a program listáját üríti ki, az eredeti fájlokat nem törli."
    ),
    "msg.idle_left": (
        "Nem maradt végrehajtható művelet. A problémás fájlok a listában maradtak."
    ),
    "msg.nospace_title": "A teljes anyag nem fog elférni",
    "msg.nospace": (
        "Szükséges hely: {needed} GB\n"
        "Szabad hely: {free} GB\n\n"
        "A program a teljes videó + felirat párokat addig másolja, amíg van hely.\n"
        "A már sikeresen átmásolt párok megmaradnak.\n\nFolytatod?"
    ),
    "msg.output_mkdir_title": "Kimeneti mappa",
    "msg.output_mkdir": (
        "A kimeneti mappát nem sikerült létrehozni:\n{path}\n\n{exc}"
    ),
    "msg.output_empty": "Nincs kiválasztva kimeneti mappa.",
    "msg.output_invalid": "A kimeneti mappa nem érvényes.",
    "msg.output_not_dir": "A kimeneti útvonal nem mappa.",
    "msg.output_same": (
        "A kimeneti mappa nem lehet ugyanaz a mappa, amelyben "
        "az eredeti fájlok találhatók."
    ),
    "msg.done_title": "Művelet vége",
    "msg.done_files": "{n} fájl elkészült.",
    "msg.done_failed": "{n} fájl kimaradt.",
    "msg.done_cancelled": "A feladatot megszakítottad.",
    "msg.done_copy": (
        "Kimenet:\n{path}\n\nAz eredeti fájlok változatlanok maradtak."
    ),
    "msg.done_exists": "A már létező célfájlokat nem módosítottuk.",
    "msg.op_error_title": "Műveleti hiba",
    "msg.op_error": "A művelet nem fejeződött be.\n\n{exc}",
    "ctx.open": "Megnyitás",
    "ctx.folder": "Mappa megnyitása",
    "ctx.copy_path": "Forrásútvonal másolása",
    "ctx.select": "Kijelölés",
    "ctx.deselect": "Kijelölés megszüntetése",
    "tip.row_check": "A sor kijelölése / kijelölés megszüntetése",
    "progress.copy": "Másolás",
    "progress.rename": "Átnevezés",
    "progress.pair_restored": "Pár visszaállítva",
    "progress.nospace_next": "Nem fért el – következő pár",
    "progress.remaining": "Hátralévő fájlok",
    "note.exists": "A célfájl már létezik – a program nem írta felül",
    "note.collision": "Több fájl ugyanarra a célra kerülne",
    "note.cancelled": "A felhasználó megszakította a műveletet",
    "note.pair_nospace": "A teljes videó + felirat pár nem fért el",
    "note.pair_restored": "A videó + felirat pár visszaállítva",
    "note.pair_restored_short": "A teljes pár visszaállítva",
    "note.no_ep": "Nem sikerült megbízható évad/epizód azonosítás",
    "note.no_title": "Nincs megadható sorozatnév",
    "note.no_movie": "Nem sikerült felismerni a film nevét",
    "note.bad_mode": "Nem támogatott feldolgozási mód",
    "note.no_pair": "Nincs ugyanahhoz a címhez tartozó videó + felirat pár",
    "note.sub_other_title": "A felirat másik címhez tartozik: {detail}",
    "note.vid_other_title": "A videó másik címhez tartozik: {detail}",
    "note.no_plain_sub": "Nincs sima {label} felirat",
    "note.multi_plain_sub": "Több sima {label} felirat ugyanahhoz a címhez",
    "note.undo_failed": "Visszaállítás sikertelen: {detail}",
    "note.rollback_kept": (
        "A pár rollbackje sikertelen; a célfájl megmaradt: {detail}"
    ),
    "hist.unknown": "Ismeretlen",
    "hist.op_copy": "Másolás és átnevezés",
    "hist.op_inplace": "Helyben átnevezés",
    "hist.op_rename": "Átnevezés",
    "hist.status_ok": "Sikeres",
    "hist.status_partial": "Részben elkészült",
    "hist.status_undone": "Visszavonva",
    "hist.result_ok": "{n} kész",
    "hist.result_partial": "{n} kész / {failed} kimaradt",
    "hist.none_title": "Nincs kijelölve",
    "hist.none": "Jelölj ki legalább egy előzményt.",
    "hist.delete_sel_title": "Kijelölt előzmények törlése",
    "hist.delete_sel": (
        "Biztosan törlöd a kijelölt {n} előzményt?\n\n"
        "Ez csak az előzménybejegyzéseket törli, a fájlokat nem állítja vissza és nem törli."
    ),
    "hist.save_title": "Előzmények mentése",
    "hist.save": "Az előzményeket nem sikerült elmenteni:\n{exc}",
    "hist.export_title": "Előzmények exportálása",
    "hist.export_txt_time": "Időpont",
    "hist.export_txt_op": "Művelet",
    "hist.export_txt_title": "Sorozat / film",
    "hist.export_txt_place": "Hely",
    "hist.export_txt_files": "Fájlok",
    "hist.export_txt_failed": "Kimaradt",
    "hist.clear_confirm_title": "Összes előzmény törlése",
    "hist.clear_confirm": "Biztosan törlöd az összes előzményt?",
    "undo.need_one_title": "Egy előzmény szükséges",
    "undo.need_one": "A visszaállításhoz pontosan egy előzményt jelölj ki.",
    "undo.already_title": "Már visszavonva",
    "undo.already": "Ez a művelet már vissza lett állítva.",
    "undo.unsafe_title": "Visszaállítás nem biztonságos",
    "undo.unsafe_missing": (
        "A kimeneti fájlok állapota megváltozott, ezért a műveletet nem hajtottam végre."
    ),
    "undo.unsafe_changed": (
        "A fájl időközben megváltozott:\n{path}\n\nA program nem törölte."
    ),
    "undo.unsafe_state": (
        "A fájlállapot megváltozott, ezért a műveletet nem hajtottam végre."
    ),
    "undo.copy_title": "Kimenet visszaállítása",
    "undo.copy_body": (
        "{n} létrehozott fájl törlésére készülsz.\n\n"
        "Az eredeti fájlokat ez nem érinti.\n\nFolytatod?"
    ),
    "undo.partial": (
        "A visszaállítás részben sikerült, a megmaradt fájlok az előzményben maradtak."
    ),
    "undo.done_title": "Kész",
    "undo.done": (
        "A kiválasztott művelet visszaállítva. Az előzmény megmaradt, Visszavonva állapotban."
    ),
    "patch.title": "Patch Center – tesztfázis",
    "patch.heading": "Patch Center",
    "patch.info": (
        "Tesztfázisban a program csak a helyi „patches” mappából futtat patchokat. "
        "A patch külön folyamatban indul, és siker esetén a program újraindítható. "
        "Nyilvános verzióban ez a felület később online Upgrade központra cserélhető."
    ),
    "patch.folder": "Patch mappa:",
    "patch.open_folder": "Mappa megnyitása",
    "patch.col_name": "Patch",
    "patch.col_size": "Méret",
    "patch.col_status": "Állapot",
    "patch.log_ph": "Patch napló...",
    "patch.scan": "Patchok keresése",
    "patch.run": "Kijelölt patch futtatása",
    "patch.none": "Nincs helyi patch.\n\nHelyezd a saját .py patchokat ide:\n{path}",
    "patch.found": (
        "{n} helyi patch található.\n"
        "A program csak a kiválasztott patchot futtatja."
    ),
    "patch.available": "Elérhető",
    "patch.no_sel_title": "Patch",
    "patch.no_sel": "Nincs kijelölt patch.",
    "patch.run_title": "Patch futtatása",
    "patch.run_body": (
        "Futtassam ezt a helyi patchot?\n\n{name}\n\n"
        "A patch módosíthatja a program fájljait. "
        "A futtatás előtt a patchnek saját biztonsági mentést kell készítenie."
    ),
    "patch.timeout": "A patch időtúllépés miatt leállt:\n{name}",
    "patch.start_fail": "Nem sikerült elindítani a patchot:\n{exc}",
    "patch.no_output": "A patch nem adott szöveges kimenetet.",
    "patch.err_title": "Patch hiba",
    "patch.err_body": (
        "A patch sikertelenül futott le.\n\n"
        "Visszatérési kód: {code}\n\n{output}"
    ),
    "patch.ok_title": "Patch sikeres",
    "patch.ok_body": "A patch sikeresen lefutott.\n\nÚjraindítsam most a programot?",
    "patch.restart_title": "Újraindítás",
    "patch.restart_fail": "A programot nem sikerült újraindítani:\n{exc}",
}

_EN = {
    "win.title": "{name} v{version}",
    "btn.add": "＋ Add",
    "menu.add_files": "Add files",
    "menu.add_folders": "Add folders",
    "menu.add_folder": "Add folder",
    "dlg.pick_folder": "Select folder",
    "btn.clear_list": "Clear list",
    "btn.check": "Check",
    "btn.refresh_preview": "Refresh preview",
    "btn.testlab": "Test lab",
    "tip.testlab": "Temporary automated test lab — 0.6.0-TEST",
    "btn.patch": "Patch",
    "tip.patch": (
        "Test phase: run local patches. "
        "An online Upgrade center may later reuse this button."
    ),
    "btn.help": "Help ▾",
    "menu.help": "Help and user guide",
    "menu.first_steps": "First steps",
    "menu.template_vars": "Template variables",
    "menu.updates": "Check for updates",
    "menu.bug": "Report a bug",
    "menu.donate": "Donate",
    "menu.about": "About",
    "btn.rename": "Rename",
    "tip.light": "Light mode",
    "tip.dark": "Dark mode",
    "tip.theme_toggle_light": "Light appearance. Click to switch to dark mode.",
    "tip.theme_toggle_dark": "Dark appearance. Click to switch to light mode.",
    "tip.rename_empty": "To get started, add videos or subtitles.",
    "tip.rename_added": "Check the list to see what we found.",
    "tip.rename_select": "Select the files in the list that you want to rename.",
    "tip.rename_review": "Review the flagged files. Renaming needs at least one selected file that is ready.",
    "tip.rename_output": "Choose an output folder, or switch to rename in place.",
    "tip.rename_busy": "Wait until the current task finishes.",
    "tip.rename_done": "These files are already renamed. Add new files to continue.",
    "tip.rename_ready": "Renaming can start.",
    "tip.hu": "Hungarian",
    "tip.en": "English",
    "btn.bug": "Report a bug",
    "btn.donate": "Donate",
    "btn.cancel": "⛔  Cancel task",
    "btn.cancel_busy": "⛔  Cancelling…",
    "tab.files": "Files",
    "tab.settings": "Advanced settings",
    "settings.intro": (
        "Everyday use only needs the Files tab. Name templates and less-used "
        "options live here — change them only when the defaults are not enough."
    ),
    "settings.naming_box": "Naming",
    "tab.preview": "Preview",
    "tab.history": "History",
    "files.search_ph": "Search...",
    "files.search": "Search",
    "files.sort": "Sort:",
    "files.select_all": "Select all",
    "files.deselect": "Clear selection",
    "files.remove_selected": "Remove selected",
    "tip.remove_selected": "Removes only the checked rows from the list.",
    "files.select_review": "Select items to review",
    "tip.select_review": "Selects warned and blocked rows in the list.",
    "files.show_review_only": "Review items only",
    "tip.show_review_only": (
        "Shows only warned and blocked rows in the table. "
        "Does not change the selection."
    ),
    "files.empty": (
        "<b>To get started, add a folder or files.</b><br>"
        "Drop videos and subtitles here, or click Add folder."
    ),
    "btn.add_folder_cta": "Add folder",
    "guide.empty": "To get started, add files.",
    "guide.added": "Files added — check what we found.",
    "guide.preview": "Check the new names in the list.",
    "guide.ready": "All set — renaming can start.",
    "guide.review": "Some files need a review.",
    "guide.busy": "Processing...",
    "guide.done": "Processing finished.",
    "guide.counts": "{ok} files are OK, {issues} files need a review.",
    "guide.rename_only_ok": "Rename will only process files that are OK.",
    "guide.counts_ok": "{ok} files are OK.",
    "guide.counts_issues": "{issues} files need a review.",
    "review.ok": "✓ OK",
    "review.needs": "⚠ Review needed",
    "review.blocked": "✕ Cannot process",
    "review.no_sub": "⚠ Missing subtitle",
    "review.no_video": "⚠ Missing video",
    "review.mismatch": "⚠ Unmatched pair",
    "review.conflict": "⚠ Name conflict",
    "detect.summary_line": (
        "{episodes} episodes · {videos} videos · {subs} subtitles · all pairs OK"
    ),
    "detect.summary_line_missing": (
        "{episodes} episodes · {videos} videos · {subs} subtitles · {missing} missing pair(s)"
    ),
    "detect.summary_line_movie": (
        "{videos} videos · {subs} subtitles · all pairs OK"
    ),
    "detect.summary_line_movie_missing": (
        "{videos} videos · {subs} subtitles · {missing} missing pair(s)"
    ),
    "detect.summary_unknown": "Recognized files",
    "output.box": "Output",
    "output.action": "Action:",
    "output.folder": "Output folder:",
    "output.folder_ph": "Choose a separate output folder...",
    "output.browse": "Choose folder…",
    "output.hint_copy": (
        "<b>Safe copy</b><br>"
        "Original files stay untouched. The program copies the selected "
        "videos and subtitles into the output folder with the new names."
    ),
    "output.hint_inplace": (
        "<b>⚠ WARNING – original file names will change!</b><br>"
        "Use this only if you have already copied the originals into a separate working folder."
    ),
    "table.check": "✓",
    "table.original": "Original",
    "table.new_name": "New name",
    "table.status": "Status",
    "table.series": "Series",
    "table.season": "Season",
    "table.episode": "Episode",
    "table.type": "Type",
    "table.size": "Size",
    "table.copy_state": "Copy status",
    "table.progress": "Progress",
    "tip.table_check": "Selection: click to select all / click again to clear all",
    "kind.video": "video",
    "kind.sub": "subtitle",
    "kind.other": "other",
    "lang.hu": "Hungarian",
    "lang.en": "English",
    "lang.de": "German",
    "lang.fr": "French",
    "lang.es": "Spanish",
    "lang.it": "Italian",
    "lang.pl": "Polish",
    "lang.cs": "Czech",
    "lang.sk": "Slovak",
    "lang.ro": "Romanian",
    "sub.lang_none": "—",
    "sub.primary": "primary",
    "meta.av_counts": "{videos} video · {subs} subtitle",
    "tip.lang": "Language: {lang}",
    "tip.format": "Format: {fmt}",
    "tip.variant": "Variant: {variant}",
    "tip.variant_none": "none",
    "tip.primary_yes": "Primary: yes",
    "tip.primary_no": "Primary: no",
    "preview.group_head": "{title} — {episode}",
    "preview.group_counts": "{videos} video · {subs} subtitle",
    "preview.file_video": (
        "    {mark} {kind}\n"
        "      Original: {original}\n"
        "      → {new_name}\n"
        "      [{status}] {note} | {copy}\n"
    ),
    "preview.file_sub": (
        "    {mark} {kind} · {meta}\n"
        "      Original: {original}\n"
        "      → {new_name}\n"
        "      [{status}] {note} | {copy}\n"
    ),
    "mode.label": "Mode:",
    "mode.mixed": "Automatic / Mixed",
    "mode.series": "Series",
    "mode.movie": "Movie",
    "output.copy": "Copy to output folder and rename",
    "output.inplace": "Rename in place",
    "sort.name": "Name",
    "sort.episode": "Season → episode",
    "sort.type": "File type",
    "sort.date": "Date modified",
    "name.series": "Series name:",
    "name.movie": "Movie name:",
    "name.mixed": "Default title (optional):",
    "detect.box": "Detection",
    "detect.none": "Not analyzed yet",
    "detect.fail": "Could not detect a title.",
    "detect.series": "Series: {names}",
    "detect.movies": "Movies: {names}",
    "template.label": "Desired name template:",
    "vars.base": "Basic variables:",
    "vars.series": "Series variables:",
    "tpl.series": "Default series template: {CIM}.{SZEZON}{EPIZOD}",
    "tpl.movie": "Default movie template: {CIM}",
    "tpl.mixed": (
        "In mixed mode, SxxEyy is treated as a series, everything else as a movie. "
        "Movie template: {CIM}"
    ),
    "pref.label": "Preferred subtitle language:",
    "pref.tip": (
        "Preferred language for subtitles. "
        "Independent of the program language (Hungarian / English)."
    ),
    "adv.normalize": "Normalize file names",
    "adv.lang_norm": "Normalize subtitle names",
    "adv.subdirs": "Include subfolders",
    "adv.conflicts": "Check name conflicts in advance",
    "adv.preserve": "Keep selections",
    "adv.vars": "Advanced template variables: {NYELV}, {KITERJ}, {EP}, {EXT}",
    "btn.save_settings": "Save settings",
    "btn.refresh_list": "Refresh list",
    "tip.refresh_list": "Re-analyzes the list and regenerates planned names.",
    "btn.reset_settings": "Reset settings",
    "preview.select_all": "Select all",
    "preview.select_none": "Clear selection",
    "preview.select_missing": "Missing only",
    "history.info": (
        "Previous operations are listed here. "
        "Use the checkboxes to select several history entries. "
        "For a partial result, Skipped files shows the concrete problems."
    ),
    "hist.check": "✓",
    "hist.num": "#",
    "hist.time": "Time",
    "hist.op": "Operation",
    "hist.title": "Series / movie",
    "hist.files": "Files",
    "hist.place": "Location",
    "hist.select_all": "Select all",
    "hist.deselect": "Clear selection",
    "hist.delete": "Delete selected",
    "hist.undo": "Undo selected operation",
    "hist.failed": "Skipped files",
    "hist.failed_title": "Skipped files",
    "hist.failed_need_one": "Select exactly one history entry to view skipped files.",
    "hist.failed_none": "This operation has no skipped files.",
    "hist.failed_body": "{n} files skipped.\n\n{list}",
    "hist.failed_item": "{file}\n  {reason}",
    "hist.failed_tip": "Open Skipped files to see why files were left out.",
    "hist.export": "Export history",
    "hist.clear": "Clear all history",
    "status.zero": "0 files",
    "status.files": "{n} files | selected: {selected}",
    "status.selected": "Selected: {selected} / {n} files",
    "status.added": "{added} new files added — {total} files in total",
    "status.none_added": "0 new files — the selected files are already in the list",
    "preview.head": (
        "Processing list: {series} series | {movies} movies | {seasons} seasons | "
        "{files} files | OK: {ok} | Needs review: {issues}"
    ),
    "preview.item": (
        "[{mark}] {title} — {episode} — {kind}\n"
        "    Original: {original}\n"
        "    → {new_name}\n"
        "    [{status}] {note} | {copy}\n"
    ),
    "preview.unknown": "Unknown",
    "progress.work": "Processing",
    "progress.file": "File: {name}",
    "progress.done": "Completed  •  operation finished",
    "progress.fmt": "{label}  •  {current} / {total}  •  {percent}%",
    "state.ok": "OK",
    "state.done": "Done",
    "state.waiting": "Waiting",
    "state.copied": "Copied",
    "state.copying": "Copying...",
    "state.renaming": "Renaming...",
    "state.exists": "Already exists",
    "state.conflict": "Name conflict",
    "state.mismatch": "Mismatched pair",
    "state.error": "Error",
    "state.nospace": "Not enough space",
    "state.cancelled": "Cancelled",
    "check.title": "Check",
    "check.body": (
        "Series: {series}\nMovies: {movies}\nSeasons: {seasons}\n"
        "Files: {files}\nSelected: {selected}\nOK: {ok}\n"
        "Needs review: {issues}\n\n"
        "Series: {series_names}\nMovies: {movie_names}\n\n"
        "Problem files:\n{details}"
    ),
    "check.mixed_note": (
        "\n\nNote: the list also contains movie files. "
        "For mixed processing choose “{mode}” mode."
    ),
    "check.no_issues": "No problem files.",
    "check.unknown_movie": "Unknown movie",
    "check.more_files": "• … and {n} more files",
    "welcome.title": "Welcome to SubBind",
    "welcome.kicker": "LOCAL FILES  ·  VIDEO AND SUBTITLE",
    "welcome.headline": "Tired of subtitles that do not work?",
    "welcome.intro": (
        "On a TV, a subtitle from a USB stick or external drive often does "
        "not appear, even when the file sits next to the video. Players "
        "match them only when the two file names are the same.\n\n"
        "Renaming a whole series by hand is tedious. This program finds "
        "the pairs, shows the planned new names, and only renames after "
        "you confirm."
    ),
    "welcome.example": "What renaming looks like",
    "welcome.original": "Original",
    "welcome.new_name": "New name",
    "welcome.ex_orig_video": "Show.Name.S01E01.WEB-DL.AAC.H264-GROUP.mkv",
    "welcome.ex_orig_sub": "Show.Name.S01E01.The.Pilot.WEB-DL.en.srt",
    "welcome.ex_new_video": "Show.Name.S01E01.mkv",
    "welcome.ex_new_sub": "Show.Name.S01E01.srt",
    "welcome.note": (
        "Core features do not need an internet connection. "
        "The program works with the files and folders you select."
    ),
    "footer.test_version": "Test Version 2",
    "welcome.language": "Language:",
    "welcome.dont_show": "Do not show this window on the next startup",
    "welcome.first": "First steps",
    "welcome.ok": "OK, let's start",
    "msg.first_steps_title": "First steps",
    "msg.first_steps": (
        "1. Add a folder or files.\n"
        "2. Check the preview.\n"
        "3. Uncertain cases are not renamed automatically.\n"
        "4. Rename only processes problem-free, selected files."
    ),
    "msg.template_title": "Template variables",
    "msg.template": (
        "Basic variables:\n\n"
        "{CIM} – title\n"
        "{SZEZON} – season, e.g. S01\n"
        "{EPIZOD} – episode, e.g. E01\n\n"
        "Advanced variables:\n\n"
        "{EP} – full episode tag, e.g. S01E01\n"
        "{NYELV} – subtitle language\n"
        "{EXT} – file extension without a dot\n\n"
        "Curly braces are part of the template syntax."
    ),
    "msg.updates_title": "Check for updates",
    "msg.updates": (
        "Current version: {version}\n\n"
        "Online update checking is not built in. "
        "The app is portable: settings are in the data folder next to the program."
    ),
    "msg.bug_title": "Report a bug",
    "msg.bug": (
        "There is no online bug reporter in the program.\n\n"
        "If you hit a bug, note the operation and the file names."
    ),
    "msg.donate_title": "Donate",
    "msg.donate": "There is currently no built-in donation link.",
    "msg.about_title": "About",
    "msg.about": (
        "{name}\nSmart Subtitle & Media Renamer\nv{version}\n\n"
        "Created by: {author}\n"
        "Licensed under GNU GPL v3.0\n\n"
        "Freeware for aligning video and subtitle file names."
    ),
    "msg.saved_title": "Saved",
    "msg.saved": "Settings have been saved.",
    "msg.no_sel_title": "Nothing selected",
    "msg.no_sel": "There is no selected row to remove from the list.",
    "msg.remove_title": "Remove selected",
    "msg.remove": (
        "Remove {n} selected files from the processing list?\n\n"
        "This does not delete or change the original files."
    ),
    "msg.nothing_title": "Nothing to process",
    "msg.nothing": "There is no selected, processable video + subtitle group.",
    "msg.output_title": "Output",
    "msg.pair_title": "Incomplete episode selection",
    "msg.pair": (
        "One or more episodes have only the video or only the subtitle selected.\n\n"
        "The video and its subtitle can only be copied together.\n"
        "Select the full pair, or use Missing only."
    ),
    "msg.idle_title": "Nothing to do",
    "msg.idle": "No executable operation remains.",
    "confirm.title": "What will we do now?",
    "confirm.files": "{n} files",
    "confirm.kinds": "{videos} videos + {subs} subtitles",
    "confirm.preview": "Original → new name",
    "confirm.rename_pair": "{old}\n→\n{new}",
    "confirm.copy_same": "{name}\n→\ncopy to the destination folder (file name stays the same)",
    "confirm.more": "… and {n} more files",
    "confirm.op_copy": "Operation: safe copy",
    "confirm.op_inplace": "Operation: rename in place",
    "confirm.target": "Target folder: {path}",
    "confirm.keep": "Original files will be kept.",
    "confirm.change": "Original file names will change.",
    "confirm.cancel": "Cancel",
    "confirm.start": "Start",
    "help.title": "Help – {name} v{version}",
    "help.body": (
        "{name} – Help\n"
        "Version: {version}\n\n"
        "FIRST STEPS\n"
        "1. Add folder or Add files.\n"
        "2. Check the Preview.\n"
        "3. Uncertain cases are not renamed automatically.\n"
        "4. Rename only processes problem-free, selected items.\n\n"
        "SERIES MODE\n"
        "The program safely recognizes episode IDs in S01E01 or 1x01 format. "
        "Bare E05 format is intentionally not accepted automatically.\n\n"
        "MOVIE MODE\n"
        "For movies there is no season or episode requirement.\n\n"
        "IMPORTANT\n"
        "The program does not rewrite file contents; it only changes file names."
    ),
    "help.close": "Close",
    "dlg.add_folders_title": "Add folders",
    "dlg.add_folders_info": (
        "Select one or more folders. Use Ctrl/Shift to select multiple folders."
    ),
    "dlg.location": "Location:",
    "dlg.path_ph": "Folder path – paste or type",
    "dlg.open": "Open",
    "dlg.selected_folders": "Selected: {n} folder(s)",
    "dlg.invalid_folder_title": "Invalid folder",
    "dlg.invalid_folder": "The folder was not found:\n{path}",
    "dlg.none_selected_title": "Nothing selected",
    "dlg.none_selected_folders": "Select at least one folder.",
    "dlg.add": "Add",
    "dlg.cancel": "Cancel",
    "dlg.add_folder_title": "Add folder",
    "dlg.add_folder_info": (
        "Paste the folder path, or browse. "
        "Subfolders follow the Include subfolders setting."
    ),
    "dlg.browse": "Browse…",
    "dlg.path_example": r"C:\Shows\Show",
    "dlg.pick_files": "Select videos and subtitles",
    "dlg.files_filter": "Supported files ({exts})",
    "dlg.all_files": "All files (*.*)",
    "msg.no_files_title": "No files to add",
    "msg.no_files_folders": (
        "No supported video or subtitle files were found in the selected folders."
    ),
    "msg.no_files_folder": (
        "No supported files were found in the selected folder:\n\n"
        "{path}\n\n"
        "Supported videos: MKV, MP4, AVI, M4V, MOV, WMV, WEBM, TS, M2TS\n"
        "Supported subtitles: SRT, ASS, SSA, VTT, SUB"
    ),
    "msg.no_files_drop": (
        "No supported video or subtitle files were found in the dropped folders."
    ),
    "msg.no_direct_title": "No files directly in this folder",
    "msg.no_direct": (
        "No supported video or subtitle files were found directly in the selected folder.\n\n"
        "Look in subfolders as well?"
    ),
    "msg.path_missing_title": "Path not available",
    "msg.path_missing": "The given file or folder was not found:\n{paths}",
    "msg.clear_title": "Clear list",
    "msg.clear": (
        "Clear the entire processing list?\n\n"
        "This only empties the program list; original files are not deleted."
    ),
    "msg.idle_left": (
        "No executable operation remains. The problematic files stayed in the list."
    ),
    "msg.nospace_title": "There is not enough space for everything",
    "msg.nospace": (
        "Space needed: {needed} GB\n"
        "Free space: {free} GB\n\n"
        "The program copies complete video + subtitle pairs while space remains.\n"
        "Pairs that already copied successfully are kept.\n\nContinue?"
    ),
    "msg.output_mkdir_title": "Output folder",
    "msg.output_mkdir": (
        "The output folder could not be created:\n{path}\n\n{exc}"
    ),
    "msg.output_empty": "No output folder is selected.",
    "msg.output_invalid": "The output folder is not valid.",
    "msg.output_not_dir": "The output path is not a folder.",
    "msg.output_same": (
        "The output folder cannot be the same folder that contains the original files."
    ),
    "msg.done_title": "Operation finished",
    "msg.done_files": "{n} files completed.",
    "msg.done_failed": "{n} files were skipped.",
    "msg.done_cancelled": "You cancelled the task.",
    "msg.done_copy": (
        "Output:\n{path}\n\nOriginal files were left unchanged."
    ),
    "msg.done_exists": "Existing destination files were not modified.",
    "msg.op_error_title": "Operation error",
    "msg.op_error": "The operation did not finish.\n\n{exc}",
    "ctx.open": "Open",
    "ctx.folder": "Open folder",
    "ctx.copy_path": "Copy source path",
    "ctx.select": "Select",
    "ctx.deselect": "Deselect",
    "tip.row_check": "Select or deselect this row",
    "progress.copy": "Copy",
    "progress.rename": "Rename",
    "progress.pair_restored": "Pair restored",
    "progress.nospace_next": "Not enough space – next pair",
    "progress.remaining": "Remaining files",
    "note.exists": "The destination file already exists – it was not overwritten",
    "note.collision": "Several files would go to the same destination",
    "note.cancelled": "The user cancelled the operation",
    "note.pair_nospace": "The full video + subtitle pair did not fit",
    "note.pair_restored": "The video + subtitle pair was restored",
    "note.pair_restored_short": "The full pair was restored",
    "note.no_ep": "Season/episode could not be identified reliably",
    "note.no_title": "No series title could be determined",
    "note.no_movie": "The movie name could not be recognized",
    "note.bad_mode": "Unsupported processing mode",
    "note.no_pair": "No video + subtitle pair belongs to the same title",
    "note.sub_other_title": "The subtitle belongs to another title: {detail}",
    "note.vid_other_title": "The video belongs to another title: {detail}",
    "note.no_plain_sub": "No plain {label} subtitle",
    "note.multi_plain_sub": "Several plain {label} subtitles for the same title",
    "note.undo_failed": "Undo failed: {detail}",
    "note.rollback_kept": (
        "Pair rollback failed; the destination file was kept: {detail}"
    ),
    "hist.unknown": "Unknown",
    "hist.op_copy": "Copy and rename",
    "hist.op_inplace": "Rename in place",
    "hist.op_rename": "Rename",
    "hist.status_ok": "Successful",
    "hist.status_partial": "Partially completed",
    "hist.status_undone": "Undone",
    "hist.result_ok": "{n} done",
    "hist.result_partial": "{n} done / {failed} skipped",
    "hist.none_title": "Nothing selected",
    "hist.none": "Select at least one history entry.",
    "hist.delete_sel_title": "Delete selected history",
    "hist.delete_sel": (
        "Delete the selected {n} history entries?\n\n"
        "This only removes history records; files are not restored or deleted."
    ),
    "hist.save_title": "Save history",
    "hist.save": "History could not be saved:\n{exc}",
    "hist.export_title": "Export history",
    "hist.export_txt_time": "Time",
    "hist.export_txt_op": "Operation",
    "hist.export_txt_title": "Series / movie",
    "hist.export_txt_place": "Location",
    "hist.export_txt_files": "Files",
    "hist.export_txt_failed": "Skipped",
    "hist.clear_confirm_title": "Clear all history",
    "hist.clear_confirm": "Delete all history entries?",
    "undo.need_one_title": "One history entry required",
    "undo.need_one": "Select exactly one history entry to undo.",
    "undo.already_title": "Already undone",
    "undo.already": "This operation has already been undone.",
    "undo.unsafe_title": "Undo is not safe",
    "undo.unsafe_missing": (
        "The output files have changed, so the operation was not performed."
    ),
    "undo.unsafe_changed": (
        "The file has changed in the meantime:\n{path}\n\nIt was not deleted."
    ),
    "undo.unsafe_state": (
        "The file state has changed, so the operation was not performed."
    ),
    "undo.copy_title": "Restore output",
    "undo.copy_body": (
        "You are about to delete {n} created files.\n\n"
        "Original files are not affected.\n\nContinue?"
    ),
    "undo.partial": (
        "Undo only partly succeeded; remaining files stayed in the history."
    ),
    "undo.done_title": "Done",
    "undo.done": (
        "The selected operation was undone. The history entry remains, in Undone status."
    ),
    "patch.title": "Patch Center – test phase",
    "patch.heading": "Patch Center",
    "patch.info": (
        "In the test phase the program only runs patches from the local patches folder. "
        "The patch starts in a separate process, and the program can be restarted on success. "
        "In a public release this surface can later become an online Upgrade center."
    ),
    "patch.folder": "Patch folder:",
    "patch.open_folder": "Open folder",
    "patch.col_name": "Patch",
    "patch.col_size": "Size",
    "patch.col_status": "Status",
    "patch.log_ph": "Patch log...",
    "patch.scan": "Find patches",
    "patch.run": "Run selected patch",
    "patch.none": "No local patch.\n\nPlace your .py patches here:\n{path}",
    "patch.found": (
        "{n} local patch(es) found.\n"
        "The program only runs the selected patch."
    ),
    "patch.available": "Available",
    "patch.no_sel_title": "Patch",
    "patch.no_sel": "No patch is selected.",
    "patch.run_title": "Run patch",
    "patch.run_body": (
        "Run this local patch?\n\n{name}\n\n"
        "The patch may change program files. "
        "It should make its own backup before running."
    ),
    "patch.timeout": "The patch stopped because it timed out:\n{name}",
    "patch.start_fail": "The patch could not be started:\n{exc}",
    "patch.no_output": "The patch produced no text output.",
    "patch.err_title": "Patch error",
    "patch.err_body": (
        "The patch did not finish successfully.\n\n"
        "Return code: {code}\n\n{output}"
    ),
    "patch.ok_title": "Patch succeeded",
    "patch.ok_body": "The patch finished successfully.\n\nRestart the program now?",
    "patch.restart_title": "Restart",
    "patch.restart_fail": "The program could not be restarted:\n{exc}",
}

STRINGS = {"hu": _HU, "en": _EN}

_active = "hu"


def set_active_language(language):
    global _active
    _active = language if language in STRINGS else "hu"
    return _active


def active_language():
    return _active


def t(key, **kwargs):
    table = STRINGS.get(_active) or STRINGS["hu"]
    text = table.get(key)
    if text is None:
        text = STRINGS["hu"].get(key, key)
    if not kwargs:
        return text
    try:
        return text.format(**kwargs)
    except (KeyError, IndexError, ValueError):
        return text


def status_text(internal):
    key = STATUS_KEYS.get(internal)
    return t(key) if key else (internal or "")


def hist_op_text(internal):
    key = HIST_OP_KEYS.get(internal or "")
    return t(key) if key else (internal or t("hist.op_rename"))


def hist_status_text(internal):
    key = HIST_STATUS_KEYS.get(internal or "")
    return t(key) if key else (internal or "")


def note_text(internal):
    """Felhasználói megjelenítés. A belső note/reason azonosító nem változik."""
    text = (internal or "").strip()
    if not text:
        return ""
    key = NOTE_KEYS.get(text)
    if key:
        return t(key)
    for prefix, key in NOTE_PREFIXES:
        if text.startswith(prefix):
            return t(key, detail=text[len(prefix):])
    if text.startswith("Nincs sima ") and text.endswith(" felirat"):
        label = text[len("Nincs sima "):-len(" felirat")]
        return t("note.no_plain_sub", label=label)
    suffix = " felirat ugyanahhoz a címhez"
    if text.startswith("Több sima ") and text.endswith(suffix):
        label = text[len("Több sima "):-len(suffix)]
        return t("note.multi_plain_sub", label=label)
    return text


def combo_id(combo):
    if combo is None:
        return ""
    data = combo.currentData()
    if data:
        return data
    return combo.currentText()


combo_id = combo_id


def set_combo_id(combo, ident):
    if combo is None:
        return
    for i in range(combo.count()):
        if combo.itemData(i) == ident or combo.itemText(i) == ident:
            combo.setCurrentIndex(i)
            return


set_combo_id = set_combo_id


def fill_combo(combo, ids, key_map):
    """Keep itemData as the Hungarian id; itemText follows the active language."""
    current = combo_id(combo) if combo.count() else None
    combo.blockSignals(True)
    combo.clear()
    for ident in ids:
        combo.addItem(t(key_map[ident]), ident)
    if current:
        set_combo_id(combo, current)
    combo.blockSignals(False)
    return combo_id(combo)


fill_combo = fill_combo
