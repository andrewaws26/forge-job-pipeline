# The tailor stage: how a resume gets written

Inputs: the vetted JD (with its exact vocabulary), the claims bank, the narrative
experience structure. Output: one HTML file, rendered to a provably one-page PDF.

1. **Angle selection** (agent): read the JD's required/preferred lists and pick which
   bank entries answer them. The JD's own nouns become the tagline and section emphasis;
   nothing is claimed to match that the bank cannot support.
2. **Narrative structure** (fixed): experience is told as a continuous arc (in this
   candidate's case: Fortune 50 training -> five-year independent practice with named
   engagements -> first-technical-hire ending in acquisition). Short stints and gaps are
   structural problems, solved structurally, never with padding.
3. **Generation under the honesty gate** (agent): every bullet must trace to a bank
   entry; deployment status is worded precisely; banned claims are checked by id.
4. **Render gate** (code, `pipeline/render/`): shared CSS + headless Chrome + qpdf page
   count. Over one page fails the build. The fix is cutting content, not shrinking type
   below legibility (floor: 8.9pt).
5. **Human review**: the candidate reads what ships under their name.

Per-application cost once the bank exists: roughly 10 minutes of agent time, including
form-specific essays, which are generated under the same gate.
