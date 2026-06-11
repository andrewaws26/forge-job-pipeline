# The honesty layer

The hardest problem in automated application tailoring is not generation, it is restraint.
A model asked to "make this resume fit the JD" will drift toward claims the candidate
cannot defend. The fix is structural, not prompt-level:

1. **A claims bank**, built once, by auditing the candidate's actual repositories and
   work artifacts. Each entry is a verified fact with its evidence (file, metric, date).
   The bank also records BANNED claims: numbers that sound good but did not survive
   audit, with the honest reframe to use instead.
2. **A tailor gate**: no resume bullet, essay sentence, or outreach line ships unless it
   traces to a bank entry. New claims require a new audit, not a better prompt.
3. **Soft-claim discipline**: deployment status is stated precisely ("deployed", "in
   production at one site", "design goal, not measured") because the difference is the
   first thing a technical interviewer probes.
4. **Venue rules are workflow rules**: if an employer's policy asks for the candidate's
   own first draft on application questions, the system enforces draft-by-human,
   refine-by-agent. The artifact records which mode produced each answer.

The result is slower than pure generation and dramatically more durable: every interview
that follows is an interview the materials can survive.
