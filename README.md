# Forge: an agentic job-application pipeline

An agent-orchestrated system that discovers, vets, tailors, and submits job applications
end to end, with a human at exactly the checkpoints that deserve one. Built and operated
for a real job search: **30 applications across 6 ATS platforms in 48 hours, 27 confirmed
submissions, every claim in every resume traceable to a verified evidence bank.**

## Why this exists

Job applications are an enterprise workflow problem wearing a personal-productivity costume:
multi-step form pipelines, inconsistent schemas across vendors (Ashby, Greenhouse, Lever,
Gem, Workday, Rippling, Gusto), validation quirks, human checkpoints, and an audit
requirement (what did we submit, where, when, claiming what?). The same architecture that
automates this automates claims intake, vendor onboarding, or any forms-and-evidence
workflow.

## Quickstart

No dependencies beyond Python 3.9+ (standard library only).

```bash
git clone https://github.com/andrewaws26/forge-job-pipeline.git
cd forge-job-pipeline/discovery

# Sweep 8 VC portfolio job boards (a16z, Sequoia, Greylock, Bessemer,
# Lightspeed, Felicis via the Consider API; General Catalyst, Khosla via Getro).
# Takes ~60s, writes a scored, deduped shortlist to outputs/vc_boards.md
python3 vc_boards.py

# Sweep JobDataLake (1M+ jobs, 40+ ATS vendors, free MCP endpoint, no key)
python3 jdl_client.py
```

Optional: put one company name per line in `discovery/exclusions.txt` to filter out
orgs you have already applied to. Scoring weights and hard-constraint filters live at
the top of each script and are meant to be edited; they encode one candidate's
constraints and are the part you would personalize first.

## Architecture

```
discover -> vet -> tailor -> submit -> verify -> record
   |         |        |         |         |        |
 multi-    parallel  claims-  per-ATS   field-   tracker
 source    agent     bank     adapter   by-field (human +
 sweeps    JD reads  gate     playbook  check    machine)
```

1. **Discover** (working code in `discovery/`): parallel sweeps over JobDataLake MCP,
   the Consider API (6 VC portfolio boards: a16z, Sequoia, Greylock, Bessemer, Lightspeed,
   Felicis), the Getro API (General Catalyst, Khosla), and HN Who-is-hiring thread mining
   via the Algolia API. Edge-weighted scoring, hard-constraint filters, cross-source
   dedupe on the canonical ATS apply URL.
2. **Vet** (agent stage): parallel subagents fetch each live JD and verify remote policy,
   comp, required-vs-preferred skills, and company reality. Kills keyword-score false
   positives; this run it caught 7 dead postings and 3 hard-requirement mismatches before
   any effort was spent.
3. **Tailor** (the honesty layer, see `docs/honesty-layer.md` and `docs/tailor-stage.md`; render pipeline in `pipeline/render/`): every resume bullet must
   trace to an entry in a verified claims bank. The tailor stage refuses claims not in the
   bank. Persuasion under a truth constraint is the differentiator: the output survives
   interview scrutiny because nothing in it is inflated.
4. **Submit** (per-ATS adapters, documented in `playbook/`): browser automation via
   Playwright with ATS-specific handling learned the hard way: React-state-aware fills,
   late-parser clobber detection, toggle-button semantics, portal-rendered selects,
   iframe embeds.
5. **Verify**: field-by-field readback of the entire form before submit, success-banner
   confirmation after. No submission is recorded as sent without platform confirmation.
6. **Record**: human-readable tracker + machine-readable JSON + append-only history.

## Human checkpoints by design

- **Captchas are not defeated; they are routed to a human.** A filled form blocked by
  hCaptcha is queued with a notification: a 30-second human assist beats an arms race,
  and it is the honest answer to anti-bot intent.
- **Essay questions follow the venue's rules.** Where an employer asks that application
  answers be the candidate's own first draft, the human writes the draft and the system
  only refines: that policy boundary is enforced in the workflow, not left to chance.
- **Outbound email never sends without human review.**

## Results (one real 48-hour window)

| Metric | Value |
|---|---|
| Roles discovered and scored | 350+ |
| Vetted by JD-reading agents | 26 |
| Killed by vetting (dead/mismatch) | 10 |
| Applications submitted + confirmed | 27 |
| ATS platforms handled | Ashby, Greenhouse, Lever, Gem, Workday, Rippling, Gusto |
| Resume length violations shipped | 0 (render gate: every PDF provably 1 page) |
| Claims shipped without evidence | 0 (claims-bank gate) |

## What is code vs. what is orchestration

Honest framing: `discovery/` is standalone working code. The vet/tailor/submit stages ran
as an agent (Claude) operating Playwright under the documented playbook with a human
approving scope; `playbook/` and `docs/` codify what the agent learned so the stages can
harden into standalone adapters. This repo is the system as designed and operated, not a
puffed-up wrapper: the distinction matters to me, because the whole point of the honesty
layer is that the artifact never claims more than the evidence supports.
