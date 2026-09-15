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
    "tip.hu": "Magyar",
    "tip.en": "English",
    "btn.bug": "Hibajelentés",
    "btn.donate": "Donate",
    "btn.cancel": "⛔  Feladat megszakítása",
    "btn.cancel_busy": "⛔  Megszakítás folyamatban…",
    "tab.files": "Fájlok",
    "tab.settings": "Sablon és beállítások",
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
    "adv.box": "Haladó beállítások",
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
        "Vegyes feldolgozáshoz válaszd az „Automatikus / Vegyes” módot."
    ),
    "check.no_issues": "Nincs problémás fájl.",
    "check.unknown_movie": "Ismeretlen film",
    "check.more_files": "• … és még {n} fájl",
    "welcome.title": "Üdvözöl a Sorozat & film átnevező",
    "welcome.headline": "Eleged van abból, hogy a felirat nem működik?",
    "welcome.intro": (
        "Biztos jártál már úgy, hogy egy filmet vagy sorozatot pendrive-ról "
        "vagy külső merevlemezről szerettél volna megnézni a tévén, de a "
        "felirat nem jelent meg.\n\n"
        "A feliratfájl ott van a videó mellett, mégsem találja meg a tévé, "
        "mert a két fájl neve nem egyezik.\n\n"
        "Egy egész sorozatnál pedig elég kellemetlen lehet ezeket egyenként "
        "átnevezni.\n\n"
        "Ezt a programot éppen erre készítettük: néhány kattintással "
        "felismeri a videókat és a hozzájuk tartozó feliratokat, megmutatja "
        "a tervezett új neveket, majd csak a jóváhagyásod után nevezi át a fájlokat."
    ),
    "welcome.example": "Példa",
    "welcome.original": "Eredeti:",
    "welcome.new_name": "Új név:",
    "welcome.note": (
        "A program alapfunkcióihoz nincs szükség internetkapcsolatra. "
        "A program a kiválasztott fájlokkal és mappákkal dolgozik."
    ),
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
        "{name}\nv{version}\n\nKészítette: {author}\n\n"
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
    "tip.hu": "Hungarian",
    "tip.en": "English",
    "btn.bug": "Report a bug",
    "btn.donate": "Donate",
    "btn.cancel": "⛔  Cancel task",
    "btn.cancel_busy": "⛔  Cancelling…",
    "tab.files": "Files",
    "tab.settings": "Template and settings",
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
    "review.needs": "⚠ Needs review",
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
    "adv.box": "Advanced settings",
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
    "hist.undo": "Restore selected operation",
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
        "For mixed processing choose Automatic / Mixed mode."
    ),
    "check.no_issues": "No problem files.",
    "check.unknown_movie": "Unknown movie",
    "check.more_files": "• … and {n} more files",
    "welcome.title": "Welcome to Series & movie renamer",
    "welcome.headline": "Tired of subtitles that do not work?",
    "welcome.intro": (
        "You have probably tried to watch a movie or series from a USB stick "
        "or external drive on a TV, but the subtitle did not appear.\n\n"
        "The subtitle file is next to the video, yet the TV cannot find it "
        "because the two file names do not match.\n\n"
        "For a full series, renaming them one by one is tedious.\n\n"
        "This program is built for that: in a few clicks it recognizes videos "
        "and matching subtitles, shows the planned new names, and only renames "
        "after you confirm."
    ),
    "welcome.example": "Example",
    "welcome.original": "Original:",
    "welcome.new_name": "New name:",
    "welcome.note": (
        "The core features do not need an internet connection. "
        "The program works with the files and folders you select."
    ),
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
        "{name}\nv{version}\n\nCreated by: {author}\n\n"
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
