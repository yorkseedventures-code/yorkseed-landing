"""Quick one-off: Luma events by coordinates for List cities with no Luma place feed -> list/data/geo-import.json (merged afterwards)."""
import sys, json, time, re, importlib.util
spec = importlib.util.spec_from_file_location("le", __file__.replace("import_geo.py", "list_enrich.py"))
le = importlib.util.module_from_spec(spec); sys.argv = sys.argv[:1]; spec.loader.exec_module(le)
master = le.load(f"{le.REPO}/list/data/master.json", {"hubs": []}); hubs = master["hubs"]; hub_ids = {h["id"] for h in hubs}
placed = set(next(x for x in le.load(f"{le.REPO}/list/data/sources.json", []) if x.get("type") == "luma_place")["places"].values())
ll = re.search(r"HUB_LL=\{(.*?)\}", open(f"{le.REPO}/list/index.html", encoding="utf-8").read(), re.S).group(1)
coords = {k: (a, b) for k, a, b in re.findall(r"(\w+):\[(-?[\d.]+),(-?[\d.]+)\]", ll)}
out = []
for hid, (la, lo) in coords.items():
    if hid in placed or hid not in hub_ids or hid == "virtual": continue
    cursor, pages, n = None, 0, 0
    while pages < 12:
        q = f"https://api.lu.ma/discover/get-paginated-events?latitude={la}&longitude={lo}&pagination_limit=25" + (f"&pagination_cursor={cursor}" if cursor else "")
        try: d = json.loads(le.urlopen(le.Request(q, headers={**le.UA, "Accept": "application/json"}), timeout=30).read())
        except Exception as ex: print(hid, ex); break
        pages += 1
        for en in d.get("entries") or []:
            e = en.get("event") or {}; g = e.get("geo_address_info") or {}
            if not e.get("name") or not e.get("start_at") or not e.get("url") or e.get("location_type") == "online": continue
            if not le.TECH.search(e["name"]) or le.NOT.search(e["name"]): continue
            hub = le.city_hub(g.get("city"), g.get("country"), hubs) or hid
            date, start = le.to_local(e["start_at"], le.hub_tz(hub)); ed, et = le.to_local(e["end_at"], le.hub_tz(hub)) if e.get("end_at") else (None, None)
            venue = (g.get("sublocality") if g.get("mode") == "obfuscated" else (g.get("address") or "")) or ""
            host = " & ".join([h.get("name") for h in (en.get("hosts") or []) if h.get("name")][:2]) or ((en.get("calendar") or {}).get("name") or "")
            out.append({"title": e["name"].strip(), "hub": hub, "date": date, "start": start, "end": et if ed == date else None, "venue": venue,
                        "host": host, "link": "https://luma.com/" + e["url"], "desc": "Details and registration on the event page.", "src": "luma", "_cover": e.get("cover_url") or ""})
            n += 1
        if not d.get("entries") or not d.get("next_cursor"): break
        cursor = d["next_cursor"]; time.sleep(0.6)
    print(f"{hid}: {pages} pages, {n} tech events"); time.sleep(1)
json.dump(out, open(f"{le.REPO}/list/data/geo-import.json", "w"), ensure_ascii=False, indent=1)
print(len(out), "events")
