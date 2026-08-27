# OWNER: **T259**. Not T256. This directory's name is wrong and is being kept anyway.

*Filed by **T299**, fire `20260827-230001`. The filename answers the question without being
opened, because the reader who needs it arrives here by `ls` or by `grep t256`, and that reader
is the one T256 was.*

---

## 1. The fact

| | |
|---|---|
| **Directory** | `.softhouse/capture/t256-verdict-predicate/` |
| **Written by** | **T259** — *"A verdict field that never consults its own recorded predicate"* |
| **Created in** | commit `85197b2` — *"T259: the predicate was wrong, not the verdict…"* [VERIFIED: `git log --diff-filter=A -- .softhouse/capture/t256-verdict-predicate/` returns exactly this one commit, and it added all 21 files] |
| **Reviewed by** | T262 (`.softhouse/reviews/t262-verdict-predicate/`), verdict MICRO-FIX |
| **Handoff** | `.softhouse/handoff/T259-verdict-predicate.md` |
| **T256 is a different task** | *"The Mac toolchain path is hardcoded in 30 executable instruments"*, whose rig is `.softhouse/capture/t256-toolchain-population/` |

**Nothing in this directory is T256's work, and T256 never touched it.**

## 2. Why the name says `t256`

Not carelessness. The name is a **task id restated in a second place, which then rotted when
the id moved.**

> *"The directory is named `t256-…` because that is the `files_hint` T259 was dispatched with;
> the task was renumbered T256 → T259 on merge after a concurrent cloud fire published a
> different T256."*
> — [VERIFIED: `.softhouse/handoff/T259-verdict-predicate.md:10-12`]

> *"RENUMBERED T256->T259 on merge: the cloud catch-up fire published a different T256 first.
> Two orchestrators held the lock at once."*
> — [VERIFIED: `.softhouse/tasks.json`, T259's `note`]

The double allocation is **P-85**: *"TWO ORCHESTRATORS HELD THE LOCK AT ONCE… Three task IDs
(`T253`, `T254`, `T255`) and one pattern number (`P-78`) were **allocated twice with different
content**."* T256 was a fourth. And `tasks.json`'s T259 row **still carries
`.softhouse/capture/t256-verdict-predicate/` in its `files_hint`** — the dispatch artefact that
minted the name is still sitting there, which is why the rot is legible rather than mysterious.

The shape is **P-86**: *"an **ID IS A CARDINAL**. Never restate a pattern id in a second
document — make the second site NAME THE RULE, or cite the id AND its sentence together so a
shifted number is self-correcting… **Prefer the name over the number.**"* A directory named
`t256-` is a task id restated in a path. The id was corrected; the path was not; and a path is
the one restatement you cannot correct afterwards without invalidating everything that cites it.

## 3. Why it was NOT renamed — measured, not asserted

T299 renamed it in a **throwaway clone** and watched. Transcripts:
`.softhouse/capture/t299-namespace-and-default-safety/evidence/{10-collision-census.txt,30-rename-cost.txt}`.

**49 tracked files / 182 occurrences name this path** (both terms — P-67), over a corpus of
6,849 tracked paths, with the selector calibrated on three known positives first:

| class | files | occurrences | what a rename does to it |
|---|---:|---:|---|
| executable **inside** this directory | 2 | 3 | moves with it — but still hard-codes the old name |
| executable **outside** it | 16 | 26 | **stops resolving** |
| committed **transcripts** | 26 | 138 | **become false about the tree** |
| prose (handoffs, `tasks.json`) | 5 | 15 | stale citations |

`git mv` in the clone, 21 files moved, and then:

| probe | before | after |
|---|---|---|
| `t290-review-t271/guard_rvpa_floor_t290.py` | **exit 0** | **exit 2** |
| `t290-review-t271/prove_repair_inert.py` | **exit 0** | **exit 2** |
| `reviews/t262-verdict-predicate/pin_test_t262.py` | **exit 0** | **exit 1** |
| path references that resolve | **24** | **0** |
| path references that do not | 2 | **29** |

**Two of the three are guards**, and `guard_rvpa_floor_t290.py` is the guard T290 built
specifically to close the T114/T176 retro-edit evasion. A rename kills the guard that protects
this directory's own conclusions.

**No pin names this path, and here is where that was checked.** `conformance.sh` contains the
string `t256` **zero** times and `verdict-predicate` **zero** times.
`HOSTSTATE_PIN_TEMP_ASSIGN_LIST` has **18 rows**, of which **0** name `t256`.
`FAILOPEN_PIN_FILE_LIST`: **0**. Both scripts under `.softhouse/guards/` and every file under
`.softhouse/bin/`: **0**. So the rename was **pin-safe** — and that is exactly why the
measurement mattered: the cheap check said yes and the real one said no.

## 4. Is a directory rename an "edit in place" under T114/T176?

The ruling is quoted verbatim inside this very directory:

> *"**PINNED TO BYTES.** Each block names the sha256 of the file it acknowledges. Edit one byte
> of that file and the whole block goes VOID… That is **T114/T176 ('anything that produced
> COMMITTED EVIDENCE is superseded, NEVER edited in place')** enforced by the instrument instead
> of by discipline."*
> — [VERIFIED: `acknowledged.json`, `_about` block; and `check_verdict_predicate_agreement.py:29`]

**The argument, and it does not go the easy way.** Read literally, **a rename is not an edit in
place**: `git mv` changes no committed byte, and the sha256 pins in `acknowledged.json` are over
files in `t229-g8-site3/` and `t219-g8-residual/`, not over anything here — so the
acknowledgements would survive it. On the letter, the ruling does not forbid a rename, and it
would be dishonest to claim it does.

**It fails on the mechanism instead, and the mechanism is the ruling's real content.** T114/T176
pins *bytes* because the thing being protected is the correspondence between a recorded result
and the artefact that produced it. A rename leaves every byte intact **and destroys exactly that
correspondence**: 138 recorded occurrences in 26 committed transcripts describe a run at a
location that no longer exists, and 26 references in 16 other tasks' instruments stop resolving.
The bytes are innocent and the claim is false.

**And the second step is decisive.** A rename can only be *completed* by editing those 49 files —
which is unambiguously editing **eight other tasks' committed evidence in place** (T219, T262,
T271, T284, T286, T290, T291, T293). So the rename is a move whose only clean completion is the
prohibited act. **You must therefore refuse it at the first step, not the second** — an
incomplete rename is worse than either, because it leaves the guards red and the transcripts
lying at the same time.

T256 reached the same conclusion from a smaller premise and was right to: *"I did not rename it
— it is committed evidence and another task's."* [VERIFIED:
`.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T256.md:266-270`]. T259 had already
decided it too, in its handoff: *"The name is left alone deliberately — renaming it would break
the only pointer the task carries."*

**So the defect was never the name. It was that the reason lived in T259's handoff, which is not
where a reader who greps `t256` lands.** That reader lands *here*, and now the answer is here.

## 5. THE CONVENTION, so the next task does not re-collide

> **A capture or review directory is named for its SUBJECT. The task-id prefix is a
> CONVENIENCE, never the directory's identity. Identity lives in an `OWNER*.md` file inside
> the directory. The directory name is FROZEN AT FIRST COMMIT and is never renamed; when an
> id moves, the OWNER RECORD is corrected, because content can be superseded and a path
> cannot.**

Three rules, and each one is there because something already went wrong without it:

1. **Never rename a committed capture/review directory.** Its path is cited by transcripts that
   cannot be corrected without editing them (§3, §4).
2. **If the prefix id is not the owner, say so IN THE DIRECTORY, in the filename.** Not in the
   handoff — that is where T259 put it, and T256 still had to file a defect three fires later.
   The file is `OWNER-IS-T<owner>-NOT-T<prefix>.md`, or plain `OWNER.md` when there is no
   collision to shout about.
3. **Prefer the subject over the number** (P-86). `t259-verdict-predicate` and
   `t256-verdict-predicate` differ by a cardinal that can move; `verdict-predicate` cannot.
   A future rig may drop the prefix entirely — 22 of the 114 existing directories already have,
   and none of them can ever collide this way.

**Enforced, not merely written.** A convention that asks a future fire to remember something
enforces nothing — **P-45**: *"a test-only guard is not a guard… verify the path that actually
executes calls it, not merely that a test does."* The rule above is checked by
`.softhouse/guards/check-capture-namespace.sh`, which refuses any task id that prefixes more
than one directory without an `OWNER*.md` in each. **Read that guard's header before citing it
as a control: at the time of writing it is NOT wired into `conformance.sh`, which is outside
T299's grant, and the exact wiring line is in the guard and in T299's handoff.**
