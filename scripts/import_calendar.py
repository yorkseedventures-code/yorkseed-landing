"""Quick one-off: pull every upcoming event from given Luma calendars into list/data/calendar-import.json
(a separate file, merged into events.json afterwards). Usage: python3 scripts/import_calendar.py cal-xxx [cal-yyy ...]"""
import sys, json, time, importlib.util
spec = importlib.util.spec_from_file_location("le", __file__.replace("import_calendar.py", "list_enrich.py"))
le = importlib.util.module_from_spec(spec); sys.argv = sys.argv[:1] + sys.argv[1:]; ids = sys.argv[1:]
spec.loader.exec_module(le)
master = le.load(f"{le.REPO}/list/data/master.json", {"hubs": []}); hubs = master["hubs"]
out = []
for cid in ids:
    cursor, pages = None, 0
    while pages < 40:
        q = f"https://api.lu.ma/calendar/get-items?calendar_api_id={cid}&period=future&pagination_limit=50" + (f"&pagination_cursor={cursor}" if cursor else "")
        d = json.loads(le.urlopen(le.Request(q, headers={**le.UA, "Accept": "application/json"}), timeout=30).read()); pages += 1
        for en in d.get("entries") or []:
            e = en.get("event") or {}; g = e.get("geo_address_info") or {}
            if not e.get("name") or not e.get("start_at") or not e.get("url") or e.get("location_type") == "online": continue
            hub = le.city_hub(g.get("city"), g.get("country"), hubs) or "mex"
            date, start = le.to_local(e["start_at"], le.hub_tz(hub)); ed, et = le.to_local(e["end_at"], le.hub_tz(hub)) if e.get("end_at") else (None, None)
            venue = (g.get("sublocality") if g.get("mode") == "obfuscated" else (g.get("address") or "")) or ""
            out.append({"title": e["name"].strip(), "hub": hub, "date": date, "start": start, "end": et if ed == date else None, "venue": venue,
                        "host": (en.get("calendar") or {}).get("name") or "Mexico Tech Week 2026", "link": "https://luma.com/" + e["url"],
                        "desc": "Details and registration on the event page.", "src": "luma-cal", "_cover": e.get("cover_url") or ""})
        if not d.get("has_more") or not d.get("next_cursor"): break
        cursor = d["next_cursor"]; time.sleep(0.5)
json.dump(out, open(f"{le.REPO}/list/data/calendar-import.json", "w"), ensure_ascii=False, indent=1)
print(f"{len(out)} events from {len(ids)} calendar(s)")
