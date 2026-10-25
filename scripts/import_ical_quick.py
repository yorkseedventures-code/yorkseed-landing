"""Quick one-off: run only the iCal-feed importer, writing new events to list/data/ical-import.json (merged afterwards)."""
import sys, json, importlib.util
spec = importlib.util.spec_from_file_location("le", __file__.replace("import_ical_quick.py", "list_enrich.py"))
le = importlib.util.module_from_spec(spec); sys.argv = sys.argv[:1]; spec.loader.exec_module(le)
before = {e.get("link") for e in le.load(f"{le.REPO}/list/events.json", [])}
le.import_ical_feeds()
new = [e for e in le.load(f"{le.REPO}/list/events.json", []) if e.get("link") not in before]
json.dump(new, open(f"{le.REPO}/list/data/ical-import.json", "w"), ensure_ascii=False, indent=1); print(len(new), "events")
