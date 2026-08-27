# `t24-probe` — provenance, and what it is and is not

**Salvaged by local fire `20260819-140003`** from branch
`softhouse/rescued-agent-a2027f85cea4effc9-20260818-200001`, which fire `20260818-200001` left stranded
when a worker was killed mid-flight. It was local to one Mac until fire `20260819-080001` pushed the
branch, and it is merged to `main` here.

## Why it was salvaged rather than deleted

Every independent DEC-1 round from T23 to T47 has a `t<N>-probe/` directory under `.softhouse/reviews/`
**except T24** — the round that applied T23's three P0 corrections to DEC-1 v2. This directory fills that
one gap in the evidence trail. Its `t24-probe-output.txt` is **observed oracle output at the production
`MathContext` (19, HALF_UP)**, not a re-derivation: twelve `L-` cases of the EMI re-adjust loop
(`P=1,000,000 n=6 rate=21.6 %` through `P=6,250,000 n=24 rate=16.8 %`, plus the `P=1000` small-principal
case), and a `W-` disbursement-window section.

Two provenance assertions were re-checked by the salvaging fire, not merely transcribed:

- `EmbeddableProgressiveLoanScheduleGenerator.java` in this directory is **byte-identical** to the pinned
  original at `/Users/buv/fineract/fineract-progressive-loan-embeddable-schedule-generator/src/main/java/
  org/apache/fineract/portfolio/loanaccount/loanschedule/domain/EmbeddableProgressiveLoanScheduleGenerator.java`
  [VERIFIED by `diff`, this fire — no output].
- `t24-probe-output.txt` records `PINNED_COMMIT = 426a23544e8426a38ae43ae404670a0a7e85b9eb`, the commit of
  record [VERIFIED by grep, this fire].

## What this directory is NOT

- **It is not current DEC-1 evidence.** It is a historical artefact of the **v2 → v3** round. DEC-1 is at
  **revision 10** and seven further rounds have run since. Any claim here that a later revision restated
  or corrected is superseded by the later revision, not by this file. Do not cite it against revision 10.
- **Nothing here is promoted.** Gate G-1 is open and DEC-1 is unratified. These are raw observations and
  probe sources, in the same non-promoted status as everything under `.softhouse/capture/`.
- **The branch's other change was deliberately NOT taken.** The stranded branch also carried a 37-line
  edit to `docs/adr/DEC-1-schedule-generator-adapter.md` from the v2 era. Merging it would have
  **regressed the document from revision 10**. Only `.softhouse/reviews/t24-probe/**` was cherry-picked.

## The sibling branch, and why nothing was taken from it

`softhouse/rescued-agent-a353b03c0dea4dd41-20260818-200001` holds 15 files: Path B attestation sidecars
(`B-01`…`B-04-attestation.json`), `pathb/capture.sh`, `run-pass3.sh`, `tools/compare-pass3-v1-v2.py`,
`tools/invariants-patha.py`, a `Capture3.java` **modification**, and two precondition self-tests.

**Nothing from it was merged, by decision of this fire.** The raw observations it contains are already on
`main` (`.softhouse/capture/pathb/out/B-0*-raw.json`). Its attestations are **stale by standard** — T42's
eight-point rule has since changed what an attestation must say, and T35/T36 produced their own
(`.softhouse/capture/pathb/t36/attest.py`, `preconditions.sh`, `mutation-test.sh`,
`.softhouse/capture/src/run-pass3b.sh`). Merging a stale attestation over T36's would be a **regression**,
and its `Capture3.java` is a *modification* of a file T35/T36 later rewrote. The branch is **kept on
`origin` as a historical record** rather than deleted, because it is the only copy; it should not be
merged.

This closes the triage item recorded in `.softhouse/RESUME.md` under *"Stranded work found during this
fire's exit sweep"*.

### T214 re-checked this decision mechanically (22 August 2026) — it stands

The paragraph above is the only place on `main` that records why `rescued-agent-a353b03c0dea4dd41-…` is not
merged, so **T214 re-derived its load-bearing claim instead of transcribing it.** The claim is *"the raw
observations it contains are already on `main`"*.

Each of the branch's four attestation sidecars states the sha256 of the response it attests. Compared
against the bytes of the corresponding file on `main`:

| attestation on the branch | `response.sha256` it records | `.softhouse/capture/pathb/out/…-raw.json` on `main` |
|---|---|---|
| `B-01-baseline-attestation.json` | `713a3560…c062009` | **identical** |
| `B-02-multiplesof100-attestation.json` | `9de8757d…d99d02f8` | **identical** |
| `B-03-diycs-fullleapyear-attestation.json` | `892dd6f5…f7da58bf` | **identical** |
| `B-04-diycs-feb29only-attestation.json` | `c80f62b0…b65c724a80` | **identical** |

[VERIFIED by T214: `git show <branch>:<attestation>` → `response.sha256`, against
`shasum -a 256` of `git show main:<raw>`, all four MATCH.] The four replacement artefacts this file names —
`pathb/t36/attest.py`, `t36/preconditions.sh`, `t36/mutation-test.sh`, `capture/src/run-pass3b.sh` — were
also confirmed present on `main`, as was `capture/src/Capture3.java`, the file the branch *modifies*.

So the 15 files are **derived sidecars over observations `main` already holds**, and the decision not to
merge them is a supersession, not a loss. **This branch is the one of T214's four that was deliberately
abandoned; the other three (`T108-grep-adjudication`, `T109-fork-point-digest-compare`, `T131-review-t108`)
were accidental omissions and their 64 evidence paths were landed on `main` by T214** — see
`.softhouse/obligations.md` §4.4. The branch is still not deleted, and is still the only copy.
