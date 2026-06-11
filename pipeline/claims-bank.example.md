# Claims bank — EXAMPLE (replace every entry with your own audited facts)

This file is the load-bearing wall of the tailor stage: no resume bullet, essay sentence,
or outreach line ships unless it traces to an entry here. Build yours by auditing your
actual repositories and work artifacts, not your memory — memory inflates. Each entry
records the claim, where the evidence lives, and how precisely it may be worded.

Entry format:
- **id**: short stable slug, referenced from generated material
- **claim**: the strongest wording the evidence supports (use this verbatim or weaker)
- **evidence**: file path, metric source, artifact, or witness
- **status**: verified | banned
- For banned entries: **why** it failed audit and the **honest reframe** to use instead

---

## verified entries (examples — fictional)

### platform-test-count
- claim: "CI runs 800+ unit tests and 200+ integration tests"
- evidence: `repo/ci/summary.json` test counts on main, 2026-01-15
- status: verified
- note: hedge DOWN from the README's "1,200 tests" — actual collected count was 1,043.
  Always claim the floor you can prove, not the ceiling someone once wrote down.

### intake-extraction-fields
- claim: "document extraction into a 94-field typed schema"
- evidence: `src/schema/intake.ts` field count
- status: verified
- note: deployment status wording: "in production at one customer site." NOT "in
  production" unqualified, NOT "used by customers" (plural). Precision here is what
  survives the interview.

### oncall-incident
- claim: "diagnosed and resolved a production outage during peak traffic"
- evidence: incident postmortem doc 2025-08-02, on-call rotation log
- status: verified

## banned entries (examples — this section is the whole point)

### forty-automations
- claim (as found on an old resume): "40 autonomous remediations in production"
- why banned: the only "40" in the repo was an incident log of 40 wasted API calls
  against one unfixable issue — an anti-pattern, not 40 fixes
- honest reframe: "an autonomous watchdog that auto-triaged hundreds of health events
  and learned to suppress duplicate alerts"

### six-modules
- claim (as found in old notes): "supports six document types"
- why banned: four have real generators; two exist only as roadmap text
- honest reframe: "four document types end to end"

---

Audit discipline: rebuild this file by reading code, not by recalling achievements.
Anything you cannot point to, you cannot claim. The banned section is not embarrassing;
it is the proof the verified section means something.
