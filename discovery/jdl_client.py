#!/usr/bin/env python3
"""JobDataLake MCP client + sweep (free endpoint, ~500 calls/day, no API key).

JobDataLake indexes 1M+ jobs across 40+ ATS vendors and exposes search as an MCP
(Model Context Protocol) server over plain HTTP. This client speaks just enough of
the protocol to use it from a script: initialize a session, call the search tool,
parse the markdown it returns, then apply MY filters client-side and write a ranked
shortlist. The constants (LANES, filters, scoring) encode one candidate's constraints
and are the parts you personalize first.
"""
import json, os, re, urllib.request

EP = "https://mcp.jobdatalake.com"


def _post(body, sid=None):
    # Two hard-won details live in these headers:
    # 1) User-Agent must NOT look like default Python. The endpoint 403s
    #    "python-urllib" style agents (bot filtering); a curl UA passes.
    #    Found empirically after every request bounced.
    # 2) MCP-over-HTTP responds as Server-Sent Events even for single replies,
    #    so we must accept text/event-stream and parse `data:` lines below.
    h = {"Content-Type": "application/json",
         "Accept": "application/json, text/event-stream",
         "User-Agent": "curl/8.4.0"}
    if sid: h["Mcp-Session-Id"] = sid  # session affinity comes back as a header
    req = urllib.request.Request(EP, data=json.dumps(body).encode(), headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=40) as r:
        sidout = r.headers.get("mcp-session-id")
        raw = r.read().decode("utf-8", "replace")
    # SSE framing: the JSON-RPC reply arrives on one or more `data: {...}` lines;
    # the last parseable one is the answer. Everything else is keep-alive noise.
    data = None
    for line in raw.splitlines():
        if line.startswith("data: "):
            try: data = json.loads(line[6:])
            except: pass
    return data, sidout


def init():
    # Minimal MCP handshake: initialize -> notifications/initialized.
    # Skipping the notification makes some servers reject later tool calls,
    # so we send it even though we ignore the response.
    _, sid = _post({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"a","version":"1"}}})
    _post({"jsonrpc":"2.0","method":"notifications/initialized"}, sid)
    return sid


def search(sid, args):
    d, _ = _post({"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"search_jobs","arguments":args}}, sid)
    if not d: return ""
    try: return d["result"]["content"][0]["text"]
    except Exception: return ""


# The search tool returns human-formatted MARKDOWN, not JSON ("1. **Title** at Co"
# then indented detail lines). So parsing is a small line-oriented state machine:
# a title line opens a record, the NEXT pipe-delimited line is location|remote|salary
# (hence the _loc_next flag), and labeled lines fill in the rest.
JOB_RE = re.compile(r"^\d+\.\s+\*\*(.+?)\*\*\s+at\s+(.+?)\s*$")

def parse(text):
    jobs, cur = [], None
    for line in text.splitlines():
        m = JOB_RE.match(line)
        if m:
            if cur: jobs.append(cur)
            cur = {"title":m.group(1).strip(),"company":m.group(2).strip(),"loc":"","remote":"","salary":"","skills":"","apply":"","id":""}
            cur["_loc_next"] = True; continue
        if not cur: continue
        s = line.strip()
        if cur.get("_loc_next") and " | " in s:
            parts = [p.strip() for p in s.split("|")]
            cur["loc"] = parts[0]; cur["remote"] = parts[1] if len(parts) > 1 else ""; cur["salary"] = parts[2] if len(parts) > 2 else ""
            cur["_loc_next"] = False
        elif s.startswith("Skills:"): cur["skills"] = s[7:].strip()
        elif s.startswith("Apply:"): cur["apply"] = s[6:].strip()
        elif s.startswith("ID:"): cur["id"] = s[3:].strip()
    if cur: jobs.append(cur)
    for j in jobs: j.pop("_loc_next", None)
    return jobs


# ---- Candidate-specific filters: EVERYTHING below is client-side on purpose. ----
# Lesson learned: the server-side filters lie. The seniority filter leaks Staff
# titles, location search returns false positives (a "Louisville" query matched
# Louisville, COLORADO), and salary is mostly undisclosed. So the server is used
# only for cheap recall; precision happens here where I can test it.
EXCLUDE_CO = ["humana", "openai"]            # personal do-not-apply list
DOMAIN_MISMATCH_CO = ["esri"]                # posts eng titles, all roles are GIS
DROP_TITLE = re.compile(r"\b(staff|principal|lead\b|distinguished|director|head of|\bvp\b|vice president|chief|manager)\b", re.I)
# Two-sided title gate: must look like work I do (RELEVANT) and must not look like
# work I don't (OUT_OF_DOMAIN). Both are needed: "engineer" alone matches civil
# engineers; an allowlist alone misses oddball-but-real titles.
RELEVANT = re.compile(r"\b(software|backend|back-end|front.?end|full.?stack|\bai\b|\bml\b|applied ai|agentic|"
                      r"machine learning|\bllm\b|genai|cloud|platform|devops|site reliability|\bsre\b|"
                      r"data engineer|solutions? (engineer|architect)|forward.?deployed|developer|"
                      r"web engineer|application engineer|integration engineer|systems engineer)\b", re.I)
OUT_OF_DOMAIN = re.compile(r"\b(gis|controls|network engineer|hardware|electrical|mechanical|civil|firmware|"
                           r"embedded|database administrator|\bdba\b|oracle|salesforce|sharepoint|"
                           r"qa engineer|test engineer|security analyst|sales engineer|technician|robotics)\b", re.I)
# GAPS are flagged, not auto-killed, at this layer: metadata can't tell "Kafka
# required" from "Kafka nice-to-have". The vet stage reads the full JD and makes
# the kill decision; here a gap just costs score.
GAPS = [("LangChain/Graph", r"\blang(chain|graph)\b"), ("Kubernetes", r"\b(kubernetes|k8s|eks)\b"),
        ("Java", r"\bjava\b"), ("Scala", r"\bscala\b"), ("Kafka", r"\bkafka\b"), ("Spark", r"\bspark\b"),
        ("PyTorch/TF", r"\b(pytorch|tensorflow)\b"), ("C#/C++", r"\b(c#|c\+\+)\b"),
        ("model-training", r"\b(fine[- ]tun\w*|model training|pre-?train)\b")]
STRONG = ["claude", "anthropic", "openai api", "gpt", "llm", "agent", "mcp", "rag", "prompt", "python",
          "typescript", "react", "next.js", "node", "postgres", "aws", "lambda", "terraform", "serverless"]
LOU = re.compile(r"\b(louisville|kentucky|jeffersonville|clarksville|new albany)\b|,\s*ky\b", re.I)

# Lanes mix retrieval modes deliberately: semantic queries catch title variance
# ("Member of Technical Staff" doing agent work), keyword queries catch exact
# titles, skills-filtered queries catch stack matches with generic titles, and one
# local lane covers the home market. Each mode surfaces jobs the others miss;
# dedupe-by-id downstream makes overlap free.
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
    os.makedirs("data", exist_ok=True)  # raw dump lands here; both dirs are gitignored
    sid = init()
    print("session ok; running", len(LANES), "searches")
    allj = {}
    for a in LANES:
        txt = search(sid, a)
        found = parse(txt)
        for j in found:
            # Dedupe across lanes on the provider's job id; first lane to find a
            # job wins (lanes are ordered roughly best-precision-first).
            if j["id"] and j["id"] not in allj: allj[j["id"]] = j
        print(f"  {(a.get('query') or a.get('semantic_query') or a.get('location') or '')[:34]:34} -> {len(found)} jobs")
    # Keep the raw pre-filter dump: when a filter change is being tuned, re-scoring
    # from disk beats re-spending API budget.
    json.dump(list(allj.values()), open("data/jdl_raw.json", "w"), indent=1)
    rows = []
    for j in allj.values():
        co = j["company"].lower(); t = j["title"].lower()
        if any(x in co for x in EXCLUDE_CO) or any(x in co for x in DOMAIN_MISMATCH_CO): continue
        if DROP_TITLE.search(j["title"]): continue
        if OUT_OF_DOMAIN.search(t) or not RELEVANT.search(t): continue
        blob = (j["title"] + " " + j["skills"]).lower()
        gaps = [lab for lab, p in GAPS if re.search(p, blob)]
        bucket = "LOUISVILLE" if (LOU.search(j["loc"]) or "louisville" in j["loc"].lower()) else ("REMOTE" if j["remote"] == "fully_remote" else j["remote"] or "?")
        strong = [s for s in STRONG if s in blob]
        # Scoring: a location prior (local roles convert best for this candidate),
        # plus strong-signal count CAPPED at 7 so keyword-stuffed postings can't
        # buy their way up, minus 2 per flagged gap. Weights are opinions, not
        # physics; they're meant to be tuned against what the human shortlists.
        score = (6 if bucket == "LOUISVILLE" else 3) + min(len(strong), 7) - 2 * len(gaps)
        rows.append({**j, "bucket": bucket, "gaps": gaps, "strong": strong, "score": score})
    rows.sort(key=lambda r: -r["score"])
    with open("outputs/jdl_batch.md", "w") as f:
        f.write(f"# JobDataLake batch — {len(rows)} roles (exclusions applied; gaps flagged)\n\n")
        for r in rows:
            gap = " · ⚠ " + ", ".join(r["gaps"]) if r["gaps"] else ""
            sal = " · " + r["salary"] if r["salary"] and r["salary"] != "Not disclosed" else ""
            f.write(f"**[{r['score']}] {r['title']} — {r['company']}** [{r['bucket']}]\n- {r['loc']}{sal} · skills: {r['skills'][:90]}{gap}\n- [Apply]({r['apply']})\n\n")
    print(f"\n{len(rows)} after filters -> outputs/jdl_batch.md")
    print("LOUISVILLE hits:", sum(1 for r in rows if r["bucket"] == "LOUISVILLE"))
    for r in rows[:26]:
        g = f" ⚠{','.join(r['gaps'])}" if r["gaps"] else ""
        loc = f" | {r['loc'][:24]}" if r["bucket"] == "LOUISVILLE" else ""
        print(f"[{r['score']:>2}] {r['bucket'][:10]:10} | {r['title'][:38]:38} | {r['company'][:16]:16}{loc}{g}")


if __name__ == "__main__":
    main()
