"""Tell Bing, Yandex, Seznam and Naver (IndexNow) about every List page, so new events show up in search and AI answers fast."""
import json, re, urllib.request, pathlib
R = pathlib.Path(__file__).resolve().parent.parent
key = (R / "scripts/indexnow.key").read_text().strip()
urls = re.findall(r"<loc>(https://list\.yorkseed\.co/[^<]*)</loc>", (R / "list/sitemap.xml").read_text())
# conference and city pages first, then events
urls.sort(key=lambda u: ("/e/" in u, u))
body = json.dumps({"host": "list.yorkseed.co", "key": key, "keyLocation": f"https://list.yorkseed.co/{key}.txt", "urlList": urls[:10000]}).encode()
req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body, headers={"Content-Type": "application/json; charset=utf-8"})
try: print("IndexNow", urllib.request.urlopen(req, timeout=30).status, len(urls), "urls")
except Exception as e: print("IndexNow failed:", e)
