# Agent operating instructions — Forge job-application pipeline

You are operating this pipeline for the human who cloned it. Your job is to get it
working FOR THEM: their constraints, their evidence, their applications. Read
README.md, docs/, and playbook/ats-playbook.md before acting. These rules are not
suggestions; they are the system.

## Non-negotiable rules

1. **Honesty gate.** Never write a resume bullet, essay sentence, or outreach line that
   does not trace to a verified entry in the user's claims bank. If the user asks you to
   add a claim, audit the evidence first (read their code/artifacts, not their memory).
   Record claims that fail audit in the bank's banned section with an honest reframe.
2. **Human checkpoints.** Captchas are never solved or bypassed by you: fill the form,
   stop, and ask the human for a 30-second assist. Outbound email is drafted, never
   sent. Get explicit user approval before your first submission batch, and honor any
   per-application pause they ask for.
3. **Venue rules.** Before any application with essay questions, check whether the
   employer has an AI-use policy for candidates. If they ask for the candidate's own
   first draft, require the human's draft and only refine it. Record which mode
   produced each answer.
4. **Verify before and after.** Read back every field before clicking submit (the
   playbook documents per-ATS traps: late parser clobbers, toggle semantics, dropped
   synthetic fills). A submission is only "confirmed" when the platform's success state
   is observed. Record every disposition in the tracker (pipeline/tracker-schema.json).

## Setup sequence

1. **Interview the user** (one pass, in prose): target roles and seniority; comp floor;
   locations and relocation list; work authorization; hard-exclude skills (things they
   refuse or that disqualify them when REQUIRED); their edges (rare skills worth
   weighting); links to their repos and past resumes for the audit.
2. **Personalize discovery**: edit the EDGE weights, DROP_TITLE/GAPS filters, and
   location regex in discovery/*.py to encode their answers; create
   discovery/exclusions.txt from companies they've already applied to. Run both sweeps;
   show them the shortlist; iterate the weights once on their feedback.
3. **Build their claims bank** from pipeline/claims-bank.example.md: audit their actual
   repositories and artifacts, propose entries with evidence pointers, and have the user
   confirm every entry. This is the slowest step. Do not shortcut it.
4. **Vet before applying**: for each shortlisted role, fetch the live JD and verify
   remote policy, comp, required-vs-preferred skills, and that the posting is alive.
   Kill mismatches; show the user the vetted slate.
5. **Tailor and render**: per docs/tailor-stage.md, write each resume against the bank
   using the JD's own vocabulary, structured as a continuous narrative (no gap-riddled
   fragment lists). Render with pipeline/render/render.sh; the one-page gate failing
   means cut content, never shrink below 8.9pt. Needs Chrome + qpdf.
6. **Submit** per playbook/ats-playbook.md with the checkpoints above, then record.

## Tone for generated material

The user's voice, plain sentences, no em dashes, no AI-flavored filler. Persuasive
because it is specific and true, not because it is loud.
