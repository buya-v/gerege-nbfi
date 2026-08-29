# T445 — T444's conditions, one by one, each closed on its own evidence

## M-1 (MAJOR) — CLOSED, and it was one of FOUR live members of the same class

**Re-derived, not inherited.** I read the guard first, predicted where an index/working-tree
divergence could decide a verdict, then built the construction from my own reading. The
transcripts are `11-RED-CASE-*` and `13-RED-index-vs-filesystem.txt`.

Reproduced on `eb795f1d` (this branch before any change; `conformance.sh` byte-identical to
`main`): **EXIT 0, `grep -c 'probe = ' = 1`, `probe = up`, `VERDICT: PASS 46 / 7884`,
`population=7 invoked=3 declared=2 reached-by=2 invoked-by-nothing=0 symlink-members=0`**, and the
guard printing

```
REACHED-BY .softhouse/guards/zz-t445k/zz-t445k-member.sh — declared in its own header, reached by
           .softhouse/guards/zz-t445k/W.txt (verified: it names zz-t445k-member.sh)
```

over a witness that, on disk, is `w.txt -> zz-t445k-member.sh` — a symlink to the member itself.
The index at that moment [VERIFIED: `13-RED-index-vs-filesystem.txt`]:

```
100644 482067d1… .softhouse/guards/zz-t445k/W.txt          <- DECLARED; blob is "a decoy that names nothing"
120000 5e6810c2… .softhouse/guards/zz-t445k/w.txt          <- WINS the checkout collision
100644 236b9620… .softhouse/guards/zz-t445k/zz-t445k-member.sh
```

**Remedy, driven both ways:** the closing `grep` reads `git cat-file blob "$self_blob"` — the
tracked blob — instead of `"$REPO_ROOT/$self_norm"`. That is T375's own argument, applied for the
first time to the test that decides.

## The three MORE that came out of asking "what does THIS miss by one"

| lever | arm | on `eb795f1d` (= `main`) | what the guard printed |
|---|---|---|---|
| DIRECTORY names differing only in case, same basename | `MCASE` | **EXIT 0, probe PRESENT, PASS, `reached-by=3`** | `REACHED-BY .softhouse/guards/ZZ-T445M/x.sh — declared in its own header` over a member whose own index entry contains **no row at all** |
| an ordinary UNCOMMITTED edit adding the registration row | `LEGDIRTY` | **EXIT 0, probe PRESENT, PASS, `reached-by=2`** | a member registered by a row that is in no commit |
| an ordinary UNCOMMITTED edit making the WITNESS name the member | `WDIRTY` | **EXIT 0, probe PRESENT, PASS, `reached-by=2`** | a witness whose committed bytes name nothing |

And in the opposite direction, showing the DECLARED table was decided by this host too:

| lever | arm | on `eb795f1d` |
|---|---|---|
| the DECLARED witness stops naming its token **in the working tree only** | `CDIRTY` | **EXIT 2, probe ABSENT** — `repo-state-attest.sh is DECLARED as being run by … NO LONGER NAMES` — a refusal produced by a file this host happened to hold, with the commit unchanged |

## C-1 (MINOR) — the 'unreachable-by-construction' sentence — CORRECTED

T431's sentence about `member_multi` ("a literal pathspec matches AT MOST ONE index entry, so THIS
BRANCH CANNOT FIRE … deliberately unreachable-by-construction") is replaced in place by what T444
measured: a CONFLICTED INDEX carries one entry per STAGE for a single path, `:(literal)` pins the
PATH and not the stage, so `git ls-files -s -- ':(literal)<p>'` returns three lines and the branch
fires — on a conforming git, with no revert of anything. The new text says the direction of failure
is safe, keeps the instruction not to delete the branch and not to cite R1 as coverage, and adds
the standing rule this chain has now paid for four times: **treat "unreachable by construction" as
a claim that requires a drive, not a reading.**

I did not re-drive the conflicted index myself; the correction adopts T444's measurement and says
so. `[VERIFIED: T444 evidence/02-conflicted-index-literal-pathspec.txt]`

## C-2 (MINOR) — the only independently necessary line now has an automated arm — CLOSED

`guard_registration_decisive_lines`, called from `guard_guards_dir_registration` immediately after
its haystack is derived, on every graded run.

**Wiring, established by grep and not by assertion:**
```
main_grade            :5203  (the graded-run entry; the only two call sites are the CLI dispatch)
  run_guards          :5206
    timed_guard guard_guards_dir_registration   :4757
      guard_registration_decisive_lines "$conf" :3303
```

It does two things to the DEPLOYED text of this file, with every needle **assembled at run time
from fragments** so that this function can never be the occurrence it counts:

* **PRESENCE** — seven decisive lines must occur in the executable (comment-stripped) text.
* **BEHAVIOUR** — the two decisive comparisons are **cut out of the deployed line and evaluated**,
  once on an input they must refuse and once on an input they must accept. A line kept but neutered
  is present and not discriminating, and presence alone would call that green (P-22).

**Driven RED:** arm `RVQ` deletes the round-trip line. On `main` that is **EXIT 0 / probe PRESENT /
VERDICT PASS** — T444's finding, reproduced independently, `roundtrip=NO` detected by the
instrument from the tree's own text. On this branch the same deletion must refuse at EXIT 2 with
the probe ABSENT. Arm `RWB` deletes the witness tracked-blob read and must refuse the same way.
Clean-tree control: arm `Z`.

## C-3 — the rotted citation — MEASURED, and the sweep found three MORE inside my own file

**`.softhouse/RESUME.md` no longer carries the citation at all.** T444 recorded
`RESUME.md:52 → conformance.sh:3677`, later `:3782`. The driver rewrote `RESUME.md` at the start of
THIS fire, and I re-measured rather than inheriting: `grep -c 'conformance\.sh:[0-9]' .softhouse/RESUME.md`
returns **0**. The only mentions of `conformance.sh` in it now are the bar command and prose about
who writes the file. **Nothing to fix; the row is gone.** [VERIFIED: that grep, plus `grep -n
'conformance' .softhouse/RESUME.md`.]

**Where I looked, so the absence is a statement about a search:** `.softhouse/RESUME.md`,
`.softhouse/patterns.md`, `.softhouse/obligations.md`, `.softhouse/gates.md`,
`.softhouse/nonnegotiable-guard-audit.md`, `.softhouse/bin/`, `.claude/skills/`, `docs/`,
`CLAUDE.md` — every `*.md`, `*.sh`, `*.py` outside `capture/`, `reviews/`, `runs/`, `logs/`,
`handoff/`, `observations/`. **Exactly two live citations land above `conformance.sh:3200`:
`patterns.md:3426 → :3271` and `fire-program.sh:1406 → :3217-3220`.**

* `patterns.md:3426 → conformance.sh:3271` — **PRESERVED.** Every line T445 adds is below `:3271`;
  `sed -n 3271p` prints the same `population is EMPTY` refusal before and after.
* `fire-program.sh:1406 → conformance.sh:3217-3220` — **already rotted before T445 and NOT moved by
  T445.** Out of grant; filed.

**The method, applied in the other direction, found live rot.** T444's lesson is that "I checked
the citation I knew about" is the defect. So I swept every `patterns.md:NNNN` citation **inside
`conformance.sh`**: nine distinct line numbers, of which **THREE were rotted by exactly 31 lines** —
`:1472` (cited for P-45, which is at `:1503`), `:2782` (cited for P-84, at `:2813`) and `:3084`
(cited for P-95, at `:3115`). Nothing grades them, so nothing was ever going to say so.
**All seventeen occurrences now cite the rule by ID and by its sentence, and carry no line number at
all** — which is P-80's own prescription, and `guard_pnumber_citations` grades the sentence under
the id, never a line.

## C-4 (MINOR) — the plain-ASCII constraint — NOT CLOSED, and the reason is the grant

The remedy of record is a paragraph in `.softhouse/patterns.md`. **`patterns.md` is outside T445's
grant** ("nothing outside these paths": `conformance.sh` and this capture directory), and this wave
serialises writers per file. What `conformance.sh` already does, unchanged by T445: both the
empty-lookup refusal and the round-trip refusal print *"Name a witness with a plain ASCII path"* and
name C-quoting as the cause. **Filed as `FU-T445-4`.** I did not verify T444's measurement that
`-c core.quotePath=false` narrows the constraint; I neither adopted nor rejected it. `[UNVERIFIED]`

## LOW-1 — a wording slip in T431's bar-figure justification

Historical, in a merged handoff, about a distance in lines. Nothing in the tree depends on it and
`conformance.sh` does not restate it. **No action.** T445 does not introduce a replacement: no
comment added by this commit restates a distance in lines, a count of lines, or a line number —
checked with `grep -n 'lines up\|line above\|lines below\|lines down'` over the changed span.

## LOW-2 — `C-T407-2` cites two P-numbers by line — CLOSED BY REMOVAL

Both `patterns.md:1654` (P-57) and `patterns.md:2775` (P-80) resolved today [VERIFIED: `sed -n`].
They are ungraded and `patterns.md` grows every fire, so they were rot waiting to happen — and the
sweep above found three siblings that had already rotted. **All of them, including these two, are
now cited by rule id and sentence with no line number.**

## LOW-3 — the committed tip was not itself barred

Adopted as a requirement, not an observation: the GREEN drive and the final bar both run on
`be2ebea5`, the committed tip, with `git status --porcelain` empty before and after.

## LOW-4 — the `-f` test grades a different file from everything downstream — CLOSED BY DELETION

`[ ! -f "$REPO_ROOT/$self_wit" ]` read the TYPED spelling on this host while every test after it
graded `$self_norm` out of the index. It could not fail open — it only refuses — but it could
refuse honest work: a witness that is committed and simply not materialised in this checkout (a
sparse checkout, or the loser of a case collision) has a perfectly readable blob. **Removed**, and
the downstream "NOT TRACKED" message, which asserted *"the existence test above passed"*, is
corrected in the same commit. Driven as arm `WGONE`.

## LOW-5 — a member's SECOND `REACHED-BY` row is never graded — CLOSED BY REFUSAL

The rows are now COUNTED (from the tracked blob) and more than one is a refusal, with the reason
printed: a reader of the file sees several declarations and the harness verified one, so the
unverified rows read as verified. Driven as arm `2ROW`, which is ACCEPTED on `main` at
`reached-by=2` with the ungraded second row sitting in the file.
