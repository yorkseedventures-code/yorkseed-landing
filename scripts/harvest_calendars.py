"""Quick one-off: read one page of every known Luma calendar, collect the organizer calendars behind their tech events,
then pull upcoming tech events from those new calendars -> list/data/harvest-import.json (+ updates luma-calendars.json)."""
import sys, json, time, importlib.util
spec = importlib.util.spec_from_file_location("le", __file__.replace("harvest_calendars.py", "list_enrich.py"))
le = importlib.util.module_from_spec(spec); sys.argv = sys.argv[:1]; spec.loader.exec_module(le)
master = le.load(f"{le.REPO}/list/data/master.json", {"hubs": []}); hubs = master["hubs"]
p = f"{le.REPO}/list/data/luma-calendars.json"; known = le.load(p, {})
get = lambda q: json.loads(le.urlopen(le.Request(q, headers={**le.UA, "Accept": "application/json"}), timeout=30).read())
found = {}
for cid in list(known):
    try: d = get(f"https://api.lu.ma/calendar/get-items?calendar_api_id={cid}&period=future&pagination_limit=50")
    except Exception as ex:
        if getattr(ex, "code", 0) in (429, 403): time.sleep(20)
        continue
    for en in d.get("entries") or []:
        cal = en.get("calendar") or {}; e = en.get("event") or {}
        if cal.get("api_id") and cal["api_id"] not in known and (cal.get("name") or "").strip().lower() != "personal" and le.TECH.search(e.get("name") or ""):
            found[cal["api_id"]] = cal.get("name") or ""
    time.sleep(0.35)
print(len(found), "new organizer calendars")
out = []
for cid, name in found.items():
    known[cid] = {"name": name, "first": le.TODAY, "last": le.TODAY}
    try: d = get(f"https://api.lu.ma/calendar/get-items?calendar_api_id={cid}&period=future&pagination_limit=50")
    except Exception: continue
    for en in d.get("entries") or []:
        e = en.get("event") or {}; g = e.get("geo_address_info") or {}
        if not e.get("name") or not e.get("start_at") or not e.get("url") or e.get("location_type") == "online": continue
        if not le.TECH.search(e["name"]) or le.NOT.search(e["name"]): continue
        hub = le.city_hub(g.get("city"), g.get("country"), hubs)
        if not hub: continue
        date, start = le.to_local(e["start_at"], le.hub_tz(hub)); ed, et = le.to_local(e["end_at"], le.hub_tz(hub)) if e.get("end_at") else (None, None)
        venue = (g.get("sublocality") if g.get("mode") == "obfuscated" else (g.get("address") or "")) or ""
        out.append({"title": e["name"].strip(), "hub": hub, "date": date, "start": start, "end": et if ed == date else None, "venue": venue,
                    "host": name, "link": "https://luma.com/" + e["url"], "desc": "Details and registration on the event page.", "src": "luma-cal", "_cover": e.get("cover_url") or ""})
    time.sleep(0.35)
json.dump(known, open(p, "w"), ensure_ascii=False, indent=0)
json.dump(out, open(f"{le.REPO}/list/data/harvest-import.json", "w"), ensure_ascii=False, indent=1)
print(len(out), "events")
