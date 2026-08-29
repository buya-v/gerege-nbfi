# T476 — corrections to claims shipped by T467, and one pointer T455's handoff still needs

**Why this is a file and not an edit.** `.softhouse/handoff/T467-handoff.md` is another task's
record of its own reasoning. T455 set the precedent by recording rather than editing T448's
instrument; T467 followed it with `T433-CORRECTION.md` and
`T455-ATTRIBUTION-CORRECTION.md`; T472 said in terms that not editing another task's handoff
was the right call. T476's grant is `.softhouse/reviews/A2-11/`,
`.softhouse/capture/t476-t472-repair/` and its own handoff, so the same rule applies here.
**Every wrong sentence below is QUOTED rather than deleted**, so the next reader sees what was
wrong instead of a negation with nothing under it.

**What this means for the record that ships.** T467 is not merged; `softhouse/T476-t472-repair`
is merged in its place and it CARRIES T467's handoff unchanged. So the corrected claims and the
uncorrected sentences land in the same tree. That is a residue, it is declared here rather than
glossed, and closing it needs a task with a grant over `.softhouse/handoff/`.

Everything below was **re-measured on the tree**, not copied from T472's review.

---

## 1. `printed_payloads`'s docstring — CORRECTED IN CODE (in grant)

Shipped at `6a345e4a`, in `.softhouse/reviews/A2-11/verify-capture-integrity.py`:

> `T467 / F-T464-1 — THE EMITTER CLASS, CLOSED.`

**False**, and it was an untagged false claim inside the file whose subject is untagged false
claims. Two spellings reproduce the original harm at that tip, and **both were caught by the
rule T467 replaced**:

| spelling | T455 `3f4e236a` | T467 `6a345e4a` | T476 |
|---|---|---|---|
| `echo <words, UNQUOTED>  # <tag>` | CAUGHT | **missed** | CAUGHT |
| `print(b"<claim>".decode())  # <tag>` | CAUGHT | **missed** | CAUGHT |

This one is **in T476's grant and is corrected in the code**, not merely recorded: the docstring
now states what is closed, what regressed, what it costs, and what stays open.

The same false claim also appears in T467's handoff §1 (*"F-T464-1 | MINOR | **CLOSED AS A
CLASS.**"*) and §11 (*"The two repairs are the same repair"*). Those sites are **not corrected**
— outside the grant.

## 2. `printed_payloads`'s "ZERO false positives" — CORRECTED IN CODE (in grant)

Shipped:

> `The cost of that is measured, not assumed — on the four guarded files at this ref it is ZERO false positives.`

The sentence is true and the presentation is not: it is a fact about **four files**, published
beside a rule that applies to any file. Re-measured over every tracked `.py`/`.sh` in the
repository (**1,687** at `6a345e4a`), the T467 rule flags **6** files the T455 rule flags **0**,
and all six are tag-guard instruments from this lineage. The docstring now says so, names the
number, names the instrument that re-derives it, and says the number goes stale.

T467's handoff §2.2 carries the same unqualified phrase. **Not corrected** — outside the grant.

## 3. C-T467-4 — "11 controls" where the tree runs 15. RECORDED, NOT CORRECTED

T467's handoff §3.3, the AFTER column: *"calibration, clean tree | exit 0, **29** checks, 11
controls"*.

**Re-measured at `07aa5a86` by `40-t476-failclosed-nonregression.sh`, on a clean tree:
exit 0, 29 checks, `(a)`–`(k)` = 11, ALL controls = 15.** The four T467 itself added — `(l)`,
`(l1)`, `(l2)`, `(m)` — are missing from the handoff's count. T467's own instrument is right:
it prints `controls (a)-(k)=`, with the qualifier. The handoff dropped it.

In a task whose own LOW finding is *"a published cardinal that stopped matching the tree"*, a
handoff cardinal four short of its tree should not be quoted forward. **The site is outside the
grant; this is the correction.**

## 4. C-T467-5 — "a spelling nothing in this repository uses". RECORDED, AND TIGHTENED IN CODE

T467's handoff §2.2: *"The `os.write` fixture is the point of the exercise. It is a spelling
**nothing in this repository uses**."*

**False as written.** Re-counted at `6a345e4a`, excluding T467's own files, `os.write(` appears
in four tracked files:

* `.softhouse/capture/t248-failopen-widen/instruments/10-c1-characterise.py:60`
* `.softhouse/capture/t248-failopen-widen/instruments/40-red-drive.py:82`
* `.softhouse/capture/t270-superseded-trap/prove-t270-exempt-red.py:88`
* `.softhouse/reviews/t41-probe/t187-redgreen.py:154`

Every one writes to a `mkstemp` fd; **none writes to fd 1**. So the true claim is about the
**fd-1 spelling**, not about `os.write`. T472 judged the in-code sentence ("written to fd 1 by
`os.write`") accurate and only the handoff's short form wrong. Re-derived here, that is right
about the sentence and **incomplete about the code**: the check's own LABEL read *"a spelling
NOBODY IN THIS REPOSITORY HAS USED"*, the loose form, and the comment above the fixture said
*"a spelling nobody has used in this repository"*. Both are in T476's grant and **both are
corrected in code** to name fd 1 and cite the four pre-existing uses. The handoff sentence is
outside the grant.

## 5. T467's declared open routes — TWO OF THEM ARE WRONG, NOT MERELY UNDERSTATED

T467 §9 declares:

> *"A claim WRAPPED across two payloads. Predicate 1 de-wraps contiguous tagged blocks and does
> see it; predicate 2 is per-payload and does not. A wrapped untagged claim is therefore caught
> by 1 and missed by 2."*

**Driven, and it is false.** De-wrapping in `tagged_blocks` collects only lines that CONTAIN the
tag, and it feeds the POSITIVE half of predicate 1; predicate 1's NEGATIVE half is strictly
per-line. A claim wrapped across two source lines with the tag on neither, or on only the
second, is seen by **neither** predicate at `6a345e4a` — measured as fixtures W2 and W3, and as
`sh/*/continue/untagged` in the generated matrix. T476 closes the continuation form by joining
backslash-newlines before lexing.

> *"A claim built at RUNTIME and printed through a variable … carries no literal, so no static
> reader of the source can see it."*

True of that shape, and T467 relied on it to cover shapes it does not cover. `%`-formatting,
`b"..."` and `"a" + "b"` all carry the claim **in literals, on one line** and were invisible to
T467's rule. T476 closes all three by folding constants in the AST. What genuinely remains open
is narrower and is now stated that way: a claim with a fragment **computed** at runtime.

**One correction to T472 while I am in here, since it is the same sentence.** T472 lists
*"f-strings"* as a third blind family with a reach of *"2,491 f-strings in 170 files"*. Measured:
an f-string whose CONSTANT parts carry the claim contiguously is **already caught** at
`6a345e4a` — `ast.walk` descends into `JoinedStr` and its parts are `str` Constants. T472's own
fixture A4 splits the claim with `{chr(72)}`, i.e. it computes a fragment at runtime, so it
belongs to the runtime family and not to a literal one, and the 2,491-site reach figure
overstates the blind set for that family. The `%`-format and `bytes` halves of C-T467-2 are
exactly as T472 measured them.

## 6. F-T464-4 — THE POINTER T472 ASKED FOR. STILL OPEN, AND IT NEEDS ITS OWN TASK

`.softhouse/handoff/T455-t448-conditions.md:300` reads:

> `* **T448's own instrument `30-t448-tag-abuse.sh` records `all=2, both=1` for case B.**`

Re-measured at this tree: that instrument contains the word `both` exactly twice — line 16
(prose) and line 87 (a `REFUSED:` message) — and **neither is the figure**. The figure is in
`.softhouse/reviews/t448-review-t433/REVIEW.md`, written ``Case B fails it (`all` = 2, `both` =
1); case C fails it (`both` = 0).`` A search for the literal `all=2` finds nothing in that
review directory, which is how the citation slid one file sideways.

**THE CORRECTION ALREADY EXISTS** and T472's complaint is that nothing points at it from
anywhere a reader of the wrong sentence would land:

> `.softhouse/capture/t467-t464-conditions/out/T455-ATTRIBUTION-CORRECTION.md`

This file is that pointer, and T476's handoff carries it too. **It is not enough and it is not
claimed to be**: a reader who opens T455's handoff and stops there still gets the wrong
instrument. Correcting the site — or appending one line to it — requires a grant over
`.softhouse/handoff/`, which T476 does not have. **DECLARED OPEN. It needs its own task.**
