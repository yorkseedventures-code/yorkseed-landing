"""Quick one-off: grow Luma calendars from events on the List and pull their upcoming events -> list/data/calcal-import.json."""
import sys, json, importlib.util
spec = importlib.util.spec_from_file_location("le", __file__.replace("import_calendars_quick.py", "list_enrich.py"))
le = importlib.util.module_from_spec(spec); sys.argv = sys.argv[:1]; spec.loader.exec_module(le)
before = {e.get("link") for e in le.load(f"{le.REPO}/list/events.json", [])}
le.import_luma_calendars()
new = [e for e in le.load(f"{le.REPO}/list/events.json", []) if e.get("link") not in before]
json.dump(new, open(f"{le.REPO}/list/data/calcal-import.json", "w"), ensure_ascii=False, indent=1); print(len(new), "events")
