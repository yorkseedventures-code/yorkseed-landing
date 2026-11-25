"""Conference week sponsors on the share card: run by .github/workflows/week-sponsor-cards.yml every 2 hours.

Reads the live "Conference week sponsor" ads from the Yorkseed backend. When a week's sponsors change, it draws that
week's link-preview card with "Presented by" and up to 3 logos (list/img/og-share-<hash>-s<key>.jpg, a new file name
so WhatsApp/LinkedIn fetch the new picture) and records them in list/data/week-sponsors.json, which
scripts/build_list_pages.py uses for the week page's og:image and "Presented by ..." description.
Prints CHANGED when something was written, so the workflow only commits (and deploys) then.
"""
import hashlib, io, json, os, sys, urllib.request
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_share_cards import card, REPO

API = "https://yorkseed-backend-production.up.railway.app/api/list-ads/live"
UA = {"User-Agent": "Mozilla/5.0 (compatible; YorkseedListBuilder/1.0)"}
def get(url, timeout=20): return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read()

ads = json.loads(get(API)).get("ads", [])
by_week = {}
for a in ads:
    if a.get("kind") == "week" and a.get("hub"): by_week.setdefault(a["hub"], []).append(a)
path = os.path.join(REPO, "list", "data", "week-sponsors.json")
try: old = json.load(open(path))
except Exception: old = {}
weeks = {x["id"]: x for x in json.load(open(os.path.join(REPO, "list", "data", "share-weeks.json")))}
new, changed = {}, False
for wid, lst in by_week.items():
    lst = lst[:3]; key = hashlib.sha1("|".join(a["id"] + a.get("img", "") for a in lst).encode()).hexdigest()[:8]
    x = weeks.get(wid)
    if not x: continue
    rec = {"key": key, "brands": [a.get("brand", "") for a in lst], "card": f"/list/img/og-share-{x['hash']}-s{key}.jpg"}
    new[wid] = rec
    out = os.path.join(REPO, rec["card"].lstrip("/"))
    if old.get(wid, {}).get("key") == key and os.path.exists(out): continue
    sps = []
    for a in lst:
        logo = None
        if a.get("img"):
            try: logo = Image.open(io.BytesIO(get(a["img"])))
            except Exception as ex: print("logo failed", a.get("brand"), ex)
        sps.append({"brand": a.get("brand", ""), "logo": logo})
    card(x, out, sps); changed = True; print("wrote", out)
# drop cards of sponsors that ended
for wid, rec in old.items():
    if new.get(wid, {}).get("card") != rec.get("card"):
        try: os.remove(os.path.join(REPO, rec["card"].lstrip("/"))); changed = True
        except Exception: pass
if new != old: changed = True
json.dump(new, open(path, "w"), indent=1)
print("CHANGED" if changed else "no change")
