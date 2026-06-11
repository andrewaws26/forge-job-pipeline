#!/usr/bin/env python3
"""JobDataLake MCP client (free HTTP endpoint, 500 calls/day, no key).
Runs Andrew's criteria across his lanes + a real Louisville search, parses results,
applies client-side filters (exclude Humana/OpenAI, drop staff+/leadership, flag hard
gaps), dedupes, ranks (Louisville > clean remote > gap-flagged), writes outputs/jdl_batch.md."""
import json, os, re, urllib.request

EP = "https://mcp.jobdatalake.com"

def _post(body, sid=None):
    h = {"Content-Type":"application/json","Accept":"application/json, text/event-stream",
         "User-Agent":"curl/8.4.0"}
    if sid: h["Mcp-Session-Id"] = sid
    req = urllib.request.Request(EP, data=json.dumps(body).encode(), headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=40) as r:
        sidout = r.headers.get("mcp-session-id")
        raw = r.read().decode("utf-8","replace")
    data = None
    for line in raw.splitlines():
        if line.startswith("data: "):
            try: data = json.loads(line[6:])
            except: pass
    return data, sidout

def init():
    _, sid = _post({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"a","version":"1"}}})
    _post({"jsonrpc":"2.0","method":"notifications/initialized"}, sid)
    return sid

def search(sid, args):
    d,_ = _post({"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"search_jobs","arguments":args}}, sid)
    try: return d["result"]["content"][0]["text"]
    except Exception: return ""

JOB_RE = re.compile(r"^\d+\.\s+\*\*(.+?)\*\*\s+at\s+(.+?)\s*$")
def parse(text):
    jobs, cur = [], None
    for line in text.splitlines():
        m = JOB_RE.match(line)
        if m:
            if cur: jobs.append(cur)
            cur = {"title":m.group(1).strip(),"company":m.group(2).strip(),"loc":"","remote":"","salary":"","skills":"","apply":"","id":""}
            cur["_loc_next"]=True; continue
        if not cur: continue
        s=line.strip()
        if cur.get("_loc_next") and " | " in s:
            parts=[p.strip() for p in s.split("|")]
            cur["loc"]=parts[0]; cur["remote"]=parts[1] if len(parts)>1 else ""; cur["salary"]=parts[2] if len(parts)>2 else ""
            cur["_loc_next"]=False
        elif s.startswith("Skills:"): cur["skills"]=s[7:].strip()
        elif s.startswith("Apply:"): cur["apply"]=s[6:].strip()
        elif s.startswith("ID:"): cur["id"]=s[3:].strip()
    if cur: jobs.append(cur)
    for j in jobs: j.pop("_loc_next",None)
    return jobs

EXCLUDE_CO = ["humana","openai"]
DOMAIN_MISMATCH_CO = ["esri"]   # all-GIS roles; not AS's domain
DROP_TITLE = re.compile(r"\b(staff|principal|lead\b|distinguished|director|head of|\bvp\b|vice president|chief|manager)\b", re.I)
# roles AS is actually qualified for
RELEVANT = re.compile(r"\b(software|backend|back-end|front.?end|full.?stack|\bai\b|\bml\b|applied ai|agentic|"
                      r"machine learning|\bllm\b|genai|cloud|platform|devops|site reliability|\bsre\b|"
                      r"data engineer|solutions? (engineer|architect)|forward.?deployed|developer|"
                      r"web engineer|application engineer|integration engineer|systems engineer)\b", re.I)
# clearly out of his domain
OUT_OF_DOMAIN = re.compile(r"\b(gis|controls|network engineer|hardware|electrical|mechanical|civil|firmware|"
                           r"embedded|database administrator|\bdba\b|oracle|salesforce|sharepoint|"
                           r"qa engineer|test engineer|security analyst|sales engineer|technician|robotics)\b", re.I)
GAPS = [("LangChain/Graph",r"\blang(chain|graph)\b"),("Kubernetes",r"\b(kubernetes|k8s|eks)\b"),
        ("Java",r"\bjava\b"),("Scala",r"\bscala\b"),("Kafka",r"\bkafka\b"),("Spark",r"\bspark\b"),
        ("PyTorch/TF",r"\b(pytorch|tensorflow)\b"),("C#/C++",r"\b(c#|c\+\+)\b"),
        ("model-training",r"\b(fine[- ]tun\w*|model training|pre-?train)\b")]
STRONG = ["claude","anthropic","openai api","gpt","llm","agent","mcp","rag","prompt","python",
          "typescript","react","next.js","node","postgres","aws","lambda","terraform","serverless"]
LOU = re.compile(r"\b(louisville|kentucky|jeffersonville|clarksville|new albany)\b|,\s*ky\b", re.I)

LANES = [
  {"semantic_query":"applied AI engineer building LLM agent applications","remote_type":"fully_remote","job_function":"eng","seniority":"Mid Level,Senior","countries":"US","posted_within":"30d","per_page":40},
  {"query":"agentic AI engineer","remote_type":"fully_remote","job_function":"eng","seniority":"Mid Level,Senior","countries":"US","posted_within":"30d","per_page":40},
  {"query":"full stack engineer","skills":"TypeScript,React","remote_type":"fully_remote","job_function":"eng","seniority":"Mid Level,Senior","countries":"US","posted_within":"30d","per_page":40},
  {"query":"backend engineer","skills":"AWS,Python","remote_type":"fully_remote","job_function":"eng","seniority":"Mid Level,Senior","countries":"US","posted_within":"30d","per_page":40},
  {"query":"forward deployed engineer","remote_type":"fully_remote","job_function":"eng","seniority":"Mid Level,Senior","countries":"US","posted_within":"30d","per_page":40},
  {"location":"Louisville","job_function":"eng","seniority":"Mid Level,Senior","countries":"US","per_page":50},
]

def main():
    os.makedirs("outputs", exist_ok=True)
    sid = init()
    print("session ok; running", len(LANES), "searches")
    allj = {}
    for a in LANES:
        txt = search(sid, a)
        found = parse(txt)
        for j in found:
            if j["id"] and j["id"] not in allj: allj[j["id"]] = j
        print(f"  {(a.get('query') or a.get('semantic_query') or a.get('location'))[:34]:34} -> {len(found)} jobs")
    json.dump(list(allj.values()), open("data/jdl_raw.json","w"), indent=1)
    rows=[]
    for j in allj.values():
        co=j["company"].lower(); t=j["title"].lower()
        if any(x in co for x in EXCLUDE_CO) or any(x in co for x in DOMAIN_MISMATCH_CO): continue
        if DROP_TITLE.search(j["title"]): continue
        if OUT_OF_DOMAIN.search(t) or not RELEVANT.search(t): continue
        blob=(j["title"]+" "+j["skills"]).lower()
        gaps=[lab for lab,p in GAPS if re.search(p,blob)]
        bucket="LOUISVILLE" if (LOU.search(j["loc"]) or "louisville" in j["loc"].lower()) else ("REMOTE" if j["remote"]=="fully_remote" else j["remote"] or "?")
        strong=[s for s in STRONG if s in blob]
        score=(6 if bucket=="LOUISVILLE" else 3) + min(len(strong),7) - 2*len(gaps)
        rows.append({**j,"bucket":bucket,"gaps":gaps,"strong":strong,"score":score})
    rows.sort(key=lambda r:-r["score"])
    with open("outputs/jdl_batch.md","w") as f:
        f.write(f"# JobDataLake batch — {len(rows)} roles (Humana/OpenAI + staff+/leadership excluded; gaps flagged)\n\n")
        for r in rows:
            gap=" · ⚠ "+", ".join(r["gaps"]) if r["gaps"] else ""
            sal=" · "+r["salary"] if r["salary"] and r["salary"]!="Not disclosed" else ""
            f.write(f"**[{r['score']}] {r['title']} — {r['company']}** [{r['bucket']}]\n- {r['loc']}{sal} · skills: {r['skills'][:90]}{gap}\n- [Apply]({r['apply']})\n\n")
    print(f"\n{len(rows)} after filters -> outputs/jdl_batch.md")
    print("LOUISVILLE hits:", sum(1 for r in rows if r["bucket"]=="LOUISVILLE"))
    for r in rows[:26]:
        g=f" ⚠{','.join(r['gaps'])}" if r["gaps"] else ""
        loc=f" | {r['loc'][:24]}" if r["bucket"]=="LOUISVILLE" else ""
        print(f"[{r['score']:>2}] {r['bucket'][:10]:10} | {r['title'][:38]:38} | {r['company'][:16]:16}{loc}{g}")

if __name__ == "__main__":
    main()
