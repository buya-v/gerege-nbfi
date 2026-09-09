# Agent briefs — what each OpenHands run was actually told

Provenance for the branches and merges in this repository. A commit message says
what changed; these say what the agent was *asked* for, which is the other half of
why a change exists. Kept because several of this programme's findings came from
an instruction being wrong, and that is only visible if the instruction survives.

* `*.md`        — the brief handed to one run, verbatim
* `logs/*.log`  — that run's stdout (agent-side; the full event stream lives in
                  `~/.openhands/conversations/<id>/events`, which is TOOL state and
                  is deliberately NOT vendored here)

## Known-defective briefs, kept deliberately

* `OH-DEEP-E.md` set a VECTOR COUNT target ("take it to 18+"). The agent reached it
  by cloning: 18 files carrying 10 distinct (request, expect) pairs, eight discarded
  at review. Later briefs say "you are measured on defects provably caught, never on
  file count" because of this one.
* `OH-CAP-J.md` told the agent to find a rounding tie "with an ODD truncated value".
  That is INVERTED — HALF_UP and HALF_EVEN differ when the truncated value is EVEN
  (0.025 -> 0.03 vs 0.02; 0.035 -> 0.04 under both). The error was copied from the
  `loanschedule-wrong-half-even` defect string, itself corrected in 93f70645. The
  agent ignored the instruction, reasoned from the arithmetic, and found the tie
  anyway (1162502.50 x 1% = 11625.0250).

Do not "fix" either file. They are the record.
