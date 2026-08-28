# T398 — a measured remedy can be measured and still be backwards

**Branch.** `softhouse/T398-measured-but-backwards`.
**Grant.** `.softhouse/patterns.md` and `.softhouse/capture/t398-measured-but-backwards/`.
**One file outside the grant was changed** — one line plus its comment in
`.softhouse/capture/t282-pnumber-drift/bin/check-pnumber-citations.py`. It was **not optional**: §3
below shows the register could not grow past 98 without it, and the bar was already red on `main`
because of it. Driven three ways before landing.

---

## 1. P-NUMBERS TAKEN: **`P-100`** and **`P-101`**. Two patterns, not one.

### How each was verified free — before writing, and stated as the method rather than the conclusion

1. **Enumerated every `P-n` token in `patterns.md`**, sorted numerically:
   `git grep -oE 'P-[0-9]+' | sort -u -t- -k2 -n` → the tail is `…P-96, P-97, P-98, P-99, P-131, P-261`.
   `P-98` is the high-water **definition** (`patterns.md:3411`, taken by `T392`, merged to `main` at
   `2f4c3378`). `P-131` and `P-261` are the two declared-dangling *citations* that resolve to nothing —
   they are in the `PNUMBER-DANGLING-CITED-IDS: 131, 261` marker at `patterns.md:3251` and are not
   definitions.
2. **`P-99` confirmed permanently reserved**, at both of the sites the brief named and by reading them:
   `patterns.md:3253` (*"`P-99` is NOT in that list and must never be… a deliberate absence used as a
   negative control by three instruments"*) and `check-pnumber-citations.py:61` plus the
   `NEGATIVE_CONTROL_IDS` dict at `:203`, which names `15-p5-probe.py:59,73` as the instrument that
   depends on it. **`P-99` is not a usable id and was not used.**
3. **Enumerated `P-n` across the WHOLE TREE**, not just `patterns.md`, because a rival could have been
   minted in a task record: the only pre-existing occurrences of the literal `P-100` anywhere were three
   *instructions to take it* — `.softhouse/RESUME.md:42`, `.softhouse/tasks.json:5837`, and
   `.softhouse/handoff/T392-vacuous-pass-pattern.md:31-32` (`T392`'s note about its own near-miss).
   **No definition anywhere.** `P-101`: **zero occurrences of any kind, anywhere in the tree.**
4. **The checker confirms it mechanically after the fact**, which is the check that does not depend on my
   greps being right: `register=.softhouse/patterns.md ids=100 gaps=none` — 100 ids for P-1…P-98 plus
   P-100 and P-101, minus nothing, with `P-99` correctly excluded as a reserved absence.

### The one-or-two decision, and the argument

**Two.** They were dispatched together and they rhyme — both are about a measurement that is sound from
the only vantage point its author occupied — but they are filed separately because:

- their **populations** differ: implementations under grade, versus documents in a corpus;
- their **remedies** differ, and neither remedy helps the other: "add a deliberately wrong implementation
  to the same pass" does nothing for a self-referential census, and "exclude the program's own record"
  does nothing for an inverted comparator;
- a merged entry would be **cited for one half and read for the other**, which is precisely the hazard
  `P-86` records (*the pattern ids themselves rotted, in the file that names the rot*);
- merging them would force the shared rule up to an altitude — "controls can be wrong in ways one
  vantage point cannot see" — at which it becomes a restatement of `P-98`, which the brief explicitly
  said not to produce.

---

## 2. RE-VERIFIED CARDINALS

### 2a. `P-100` — read out of `T387`'s committed transcripts, not out of its prose

Both logs read from `main` at `4cf77a42`. Line numbers are into the transcript, so a later reader can
re-derive them without trusting this file.

| figure | `ledger-go` (CORRECT) `DRIVE-A2-…-FULL.log` | `ledger-wrong-residue-rounding` (WRONG) `DRIVE-B2-…-FULL.log` |
|---|---|---|
| candidate vector row | `:273` `FAIL 1 cells (0 money)` | `:276` `PASS 11 cells (4 money)` |
| ledger parity | `:276` `PASS 7  FAIL 1` | `:279` `PASS 8  FAIL 0` |
| ledger cells / MONEY | `:281` `143 graded … 39 are MONEY cells` | `:284` `153 graded … 43 are MONEY cells` |
| top-line verdict | tail: `VERDICT: FAIL (exit 1)`, `RC_ledger_go=1` | `:479` `VERDICT: PASS (exit 0) — 46 parity vectors … 7884 cells`, `RC_wrongimpl=0` |
| the fabricated value | — | `:277` `debits 10013 == credits 10013 (minor units), over 2 legs` |

The wrong-implementation banner at `DRIVE-B2:246` confirms the implementation is the deliberately wrong
one and that a RED below it is the expected result. **The review's §1.2 table is exact; I found no
discrepancy between `T387`'s prose and its transcripts.**

Everything here is integer minor units. `10013` is compared as **bytes**, never parsed; the port's
`hasResidueBeyondMinorUnit` finds `'.'` by index and compares fraction bytes with `'0'` — no `strconv`,
no division, no exponent — and `T387` §3.1 records the repo's own no-float census running clean over the
branch. **No float is anywhere near this defect.** The defect is that a fabricated integer entered the
graded money census and moved a pinned figure by four.

One thing worth passing on that neither the brief nor the review's §1.2 dwells on: the correct-port drive
prints `VERDICT: FAIL (exit 1) — 0 mismatched vector(s), 0 invariant violation(s)`. **A red verdict whose
own summary line reports zero mismatches** — the same shape as `T387`'s `F-T387-1`, and worth a look if
anyone touches `report.go:592`.

### 2b. `P-101` — re-measured with `T386`'s own instrument, unmodified

`T386`'s `t386-r3-measure.sh` was extracted from `main` byte-for-byte and run against this worktree.
Transcripts: `.softhouse/capture/t398-measured-but-backwards/out/T398-r3-remeasure.txt` (head
`4cf77a42`, before my commits) and `…-AFTER-COMMIT.txt` (after the `patterns.md` commit). Scope
`-- .softhouse`, `git grep -c` summed, `git version 2.50.1 (Apple Git-155)`.

| term | `T234` | `T386` @ `9eedfe4d` | **`T398` @ `4cf77a42`** | **`T398` one commit later** |
|---|---|---|---|---|
| `-E '\bmain\b'` | 0 | 114 | **138** | **147** |
| `-E 'bmainb'` | 0 | 114 | **138** | **147** |
| `-F 'bmainb'` | not run | 114 | **138** | **147** |
| `-E 'ma(in\|ni)'` | not run | 33,751 | **35,633** | **35,653** |
| `-F 'ma(in\|ni)'` (control) | not run | **0** | **7** | **11** |
| `-P '\bmain\b'` | 17,646 repo-wide | 22,524 | **23,111** (23,324 repo-wide) | 23,113 |
| `-E 'bzzqabsenttermb'` (negative control) | not run | **0** | **3** | **5** |

**The brief's `114` and `22,524` are both stale, exactly as the brief warned they would be.** The three
byte-identical outputs share sha256 `f4f1f727bd97a7ecb72fefc0e66a2d02cfbc62c8972016da00236f15b40f2445`.

**The finding I did not expect and which sharpened the pattern:** *both* of `T386`'s controls have been
contaminated by `T386` publishing them, within one day. The ERE-interpretation control's literal half
went `0 → 7 → 11`, and **`T386`'s deliberately-absent negative control went `0 → 3 → 5`** — its
instrument now prints the hardcoded gloss *"both 0, they AGREE"* over a measurement that reads 5 and 5.
All the new hits are `T386`'s own review, instrument and transcript, the `tasks.json` description written
to dispatch me, and now this handoff and `P-101` itself. **A negative control built from a literal search
term is destroyed by the act of publishing it**, and that is now duty 4 of the pattern.

`T234`'s prior art is confirmed: `.softhouse/capture/t234-sweep-instrument-audit/HANDOFF.md:266-276` had
already run the `-P` control and already called it *"a 95.3 % recall loss (61/64)"*, with
`-E 'bmainb' repo-wide = 0` and `-P '\bmain\b' repo-wide = 17646`.

---

## 3. THE ONE OUT-OF-GRANT LINE, AND WHY IT WAS FORCED

**`main` was already red before I touched anything.** The dispatch commit `4cf77a42` added
`RESUME.md:42`, which cites `P-100` in prose. `RESUME.md` is a **directive** file, `P-100` was undefined,
and undefined ids are fatal in directive files — so the baseline run of the checker on my worktree before
any edit printed `FATAL UNDEFINED .softhouse/RESUME.md:42 P-100` and `VERDICT FAIL -- 1 fatal (register
0, directive-file 1)`. That is `T392`'s recorded near-miss reproduced one level up: the *driver* wrote a
not-yet-defined id into a directive file. **Defining `P-100` is the repair.**

**But defining `P-100` armed a second, latent fatal.** `check-pnumber-citations.py:860` scanned
`range(1, max(reg) + 1)` for holes. While the register topped out at 98, `P-99` sat *beyond* the register
and was never scanned. The moment any pattern is filed at 100 or above, `P-99` becomes an **interior**
gap and the loop goes fatal — on the very absence the same file declares 650 lines earlier as deliberate
and permanent, with three committed instruments depending on it, and with the reason printed as *"cited
ids may resolve to nothing"* when the truth is the opposite. **The P-register would have been frozen at
98 forever, by a guard, silently.** Latent since `T282`; it detonated on the first entry filed above 99
(`P-4`: latent harness defects detonate on first real use).

**The fix is one line plus its reasoning:** the gap scan now consults `NEGATIVE_CONTROL_IDS`, a dict the
same file already carries and which already requires every entry to name the instrument that relies on
it. It is not a widening — an id can only be excused from the gap scan if it is already excused from the
citation scan, by the same declaration, on the same evidence. **An undeclared hole is still fatal.**

**Driven three ways, because `P-100` — which I had just written — demands exactly that of a grading
change.** `instruments/drive-gap-exemption.sh`, transcript `out/T398-gap-exemption-drive.txt`:

| arm | input | result | want |
|---|---|---|---|
| **A — CORRECT** | the real tree: `P-99` reserved-absent, `P-100`/`P-101` defined | `gaps=none`, `VERDICT PASS`, **rc 0** | 0 |
| **B — WRONG** | an **undeclared** hole (`P-97`'s definition deleted, its citations left) | `gaps=[97]`, `FATAL REGISTER GAP P-97` + 5 directive UNDEFINED, **rc 1** | 1 |
| **C — CONTROL ON THE FIX** | ARM A's input, exemption neutralised in a throwaway copy of the checker | `gaps=[99]`, `FATAL REGISTER GAP P-99`, **rc 1** | 1 |

`ALL THREE AS EXPECTED.` ARM C is the one that matters: it proves the exemption is **load-bearing** —
ARM A is green *because of* the exemption and not for some unrelated reason — and ARM B proves it is
**narrow**. This is the P-100 discipline applied to P-100's own landing.

The checker's `--selftest` passes (`SELFTEST: PASS`, rc 0). The edited file is in the checker's
`SELF_SOURCE_EXACT` skip list, so editing it cannot move any citation count.

**If a reviewer wants this line moved out of `t282-pnumber-drift/`,** the right home is a follow-up that
lifts the whole checker into `.softhouse/guards/` — but that is a bigger change than this fire can
absorb, and leaving the register frozen at 98 in the meantime is not an option.

---

## 4. `T359`'s REMEDY IS MARKED `DO-NOT-APPLY`

Recorded inside `P-100` (`patterns.md`, section headed **`T359`'S REMEDY IS `DO-NOT-APPLY`**), not in a
separate note, so that it travels with the rule. The marking is in `patterns.md` rather than beside
`T359`'s review because `T359`'s review is **committed evidence that may not be rewritten in place** —
the program's standing practice is to correct forward. The entry names the exact patch
(`impl.go:276-279`, returning `(*Refusal, nil)` with `422` instead of a Go `error`) and the four
consequences of applying it, and it is explicit that `T359`'s **diagnosis stands** and only the patch is
condemned. A later reader who greps `patterns.md` for `T359` now finds the warning.

---

## 5. CHECKER AND BAR

- **`check-pnumber-citations.py --selftest`** → `SELFTEST: PASS`, **rc 0**.
- **`check-pnumber-citations.py`** (live, clean tree, after everything) →
  `register=.softhouse/patterns.md ids=100 gaps=none in-file-collisions=2`,
  `VERDICT PASS -- 0 fatal; 98 report-only findings in committed evidence`, **rc 0**.
  Directive-zone MISDIRECTING stayed at **2** and directive-zone fatal at **0** — my two new entries
  introduced no misdirecting citation, and they cleared the `RESUME.md:42` fatal that `main` was
  carrying.
- **`bash .softhouse/conformance.sh`** from a clean tree after `git add -A` and commit — output in §6.

---

## 6. FINAL BAR

<!-- BAR-OUTPUT -->

---

## 7. FOLLOW-UPS FOR THE DRIVER

1. **`T386`'s instrument now lies in its own narration.** `t386-r3-measure.sh` ARM E prints the hardcoded
   sentence *"both 0, they AGREE"* over a measurement that now reads 5 and 5. It is committed evidence,
   so the correction is forward — `P-101` records it — but the instrument should grow a **computed**
   expectation so it goes red when it rots instead of printing a stale gloss. That is `P-101` duty 4
   applied to the artefact that taught it.
2. **The `P-99`-shaped trap is a class, not an instance.** Any other guard that reasons over
   `range(1, max(...))` on the P-register, or over any series with a reserved absence, has the same
   latent fatal. I checked `check-pnumber-citations.py` only; a sweep of `.softhouse/bin/`,
   `.softhouse/guards/` and `conformance.sh` for the pattern would be cheap.
3. **`report.go:592`** — the correct-port drive prints `VERDICT: FAIL (exit 1) — 0 mismatched vector(s)`.
   `T387` filed this as `F-T387-1` (MINOR) against a different symptom; the "red verdict, zero
   mismatches" phrasing is the same defect seen from the other side.
4. **The driver reddened its own bar by dispatching me.** `RESUME.md:42` cited `P-100` before `P-100`
   existed. `T392` recorded this exact hazard about itself; the dispatch template should either define
   the id or refer to it without writing the token (e.g. "the next free cardinal above `P-98`").
