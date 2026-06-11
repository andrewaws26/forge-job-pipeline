#!/usr/bin/env python3
"""VC portfolio board sweep: Consider API (a16z/Sequoia/Greylock/Bessemer/Lightspeed/Felicis)
+ Getro API (General Catalyst, Khosla). No keys needed. Verified live 2026-06-10.
Filters to Andrew's constraints, excludes applied/dispositioned orgs, dedupes on ATS apply URL.
Writes outputs/vc_boards.md. See outputs/new_sources.md for the full source map."""
import json, os, re, urllib.request

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

CONSIDER_BOARDS = [
    ("a16z", "jobs.a16z.com", "andreessen-horowitz"),
    ("Sequoia", "jobs.sequoiacap.com", "sequoia-capital"),
    ("Greylock", "jobs.greylock.com", "greylock-partners"),
    ("Bessemer", "jobs.bvp.com", "bessemer-ventures"),
    ("Lightspeed", "jobs.lsvp.com", "lightspeed"),
    ("Felicis", "jobs.felicis.com", "felicis"),
]
GETRO_NETWORKS = [("General Catalyst", 222), ("Khosla", 257)]

TITLE_QUERIES = ["AI engineer", "forward deployed", "applied AI", "AI agents", "software engineer AI"]

SEEN_CO = []  # load your own applied/dispositioned org names
try:
    SEEN_CO = [l.strip().lower() for l in open("exclusions.txt") if l.strip()]
except FileNotFoundError:
    pass
DROP_TITLE = re.compile(r"\b(staff|principal|lead\b|distinguished|director|head of|\bvp\b|vice president|chief|manager|intern|architect)\b", re.I)
GAPS = re.compile(r"\b(langchain|langgraph|kubernetes|k8s\b|java\b|scala|kafka|spark|airflow|pytorch|tensorflow)\b", re.I)
EDGE = [("claude",4),("anthropic",4),("mcp",4),("agent",2),("eval",2),("playwright",3),
        ("hipaa",4),("healthcare",2),("clinical",2),("legal",3),("document",2),("extraction",2),
        ("industrial",3),("logistics",2),("typescript",1),("python",1),("aws",1),("serverless",2)]
US_HUB = re.compile(r"\b(remote|united states|usa|\bus\b|new york|nyc|san francisco|bay area|chicago|nashville|tulsa|louisville|kentucky)\b", re.I)


def post(url, body, headers=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "User-Agent": UA, **(headers or {})})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())


def consider_sweep():
    out = []
    for name, host, board_id in CONSIDER_BOARDS:
        for q in TITLE_QUERIES:
            try:
                r = post(f"https://{host}/api-boards/search-jobs",
                         {"meta": {"size": 50}, "board": {"id": board_id, "isParent": True},
                          "query": {"titlePrefix": q, "remoteOnly": False}})
            except Exception as e:
                print(f"  {name} '{q}' error: {e}"); continue
            for j in r.get("jobs", []):
                locs = " ".join(l.get("label", "") if isinstance(l, dict) else str(l) for l in j.get("locations", []))
                sal = j.get("salary") or {}
                out.append({"src": name, "title": j.get("title", ""), "company": (j.get("companyName") or j.get("company", {}).get("name", "") if isinstance(j.get("company"), dict) else j.get("companyName", "")) or "",
                            "loc": locs, "remote": bool(j.get("remote")),
                            "comp": f"${sal.get('minValue','?')}-{sal.get('maxValue','?')}" if sal.get("minValue") else "",
                            "url": j.get("applyUrl") or j.get("url", ""),
                            "blob": json.dumps(j).lower()})
    return out


def getro_sweep():
    out = []
    for name, nid in GETRO_NETWORKS:
        for q in ["AI engineer", "forward deployed engineer"]:
            try:
                r = post(f"https://api.getro.com/api/v2/collections/{nid}/search/jobs",
                         {"hitsPerPage": 50, "page": 0, "query": q, "filters": {"work_mode": ["remote"]}},
                         headers={"Accept": "application/json"})
            except Exception as e:
                print(f"  {name} '{q}' error: {e}"); continue
            for j in r.get("results", {}).get("jobs", []):
                org = j.get("organization") or {}
                cmin, cmax = j.get("compensation_amount_min_cents"), j.get("compensation_amount_max_cents")
                out.append({"src": name, "title": j.get("title", ""), "company": org.get("name", ""),
                            "loc": " ".join(j.get("searchable_locations") or []), "remote": True,
                            "comp": f"${cmin//100000}K-{cmax//100000}K" if cmin and cmax else "",
                            "url": j.get("url", ""), "blob": json.dumps(j).lower()})
    return out


def main():
    os.makedirs("outputs", exist_ok=True)
    rows, seen_urls = [], set()
    print("Consider boards..."); jobs = consider_sweep()
    print(f"  {len(jobs)} raw")
    print("Getro networks..."); jobs += getro_sweep()
    print(f"  {len(jobs)} raw total")
    for j in jobs:
        key = j["url"].split("?")[0].rstrip("/")
        if not key or key in seen_urls: continue
        seen_urls.add(key)
        co = j["company"].lower()
        if any(s in co for s in SEEN_CO): continue
        if DROP_TITLE.search(j["title"]): continue
        if not (j["remote"] or US_HUB.search(j["loc"])): continue
        score = sum(w for kw, w in EDGE if kw in j["blob"])
        if GAPS.search(j["title"]): continue
        score += 3 if any(a in j["url"] for a in ("ashbyhq", "greenhouse", "lever.co")) else 0
        rows.append((score, j))
    rows.sort(key=lambda r: -r[0])
    with open("outputs/vc_boards.md", "w") as f:
        f.write(f"# VC board sweep — {len(rows)} deduped roles (Consider + Getro)\n\n")
        for score, j in rows[:80]:
            f.write(f"**[{score}] {j['title']} — {j['company']}** ({j['src']})\n")
            f.write(f"- {j['loc'] or ('Remote' if j['remote'] else '')} · {j['comp']}\n- [Apply]({j['url']})\n\n")
    print(f"wrote outputs/vc_boards.md: {len(rows)} kept")
    for score, j in rows[:15]:
        print(f"[{score:3}] {j['title'][:48]:48} | {j['company'][:24]:24} | {j['comp']:14} | {j['src']}")


if __name__ == "__main__":
    main()
