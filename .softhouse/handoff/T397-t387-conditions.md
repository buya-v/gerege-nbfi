# T397 — T387's two MINOR conditions on T360, closed

**Branch.** `softhouse/T397-t387-conditions`, three commits on top of `main` (`1eacb63e`).
**Grant.** `nexus/internal/apps/ledger/conformance/`, `.softhouse/capture/t397-t387-conditions/`,
plus `nexus/internal/apps/loanschedule/conformance/report.go` — which the task assigns explicitly
("`report.go` was outside T360's grant, which is why this is yours") and which is the only file
touched outside the literal grant list. `.softhouse/conformance.sh` was **NOT** touched (T404 holds
it); `git diff main...HEAD -- .softhouse/conformance.sh` is empty.

Condition (a), the `EXEMPTION_PIN_LEDGER_WRONGIMPLS` 13 → 14 bump, is the driver's and is already
on `main` at `d8ea93b8`. It is not in this diff.

| commit | what |
|---|---|
| `d35e5b44` | F-T387-2 — `verbatimInCapture` matches on a TOKEN BOUNDARY, not a bare substring |
| `f952b5d2` | F-T387-1 — the exit-0 verdict names the recorded divergences |
| `199b6e1f` | re-drive of T387's 16 authoring attacks + A17 before/after |

---

# 1. NO FLOAT AND NO PARSE WAS INTRODUCED. Explicitly.

**Not one number is formed anywhere in this diff.** No `float`, `float64`, `strconv`,
`ParseFloat`, `ParseInt`, `json.Number`, `big.Float`, `big.Rat`, `math.*`, `%f`, no division, no
exponent, and no arithmetic on any captured amount — not in production code, not in a test, not in
a fixture, not as an intermediate.

```
$ git diff main...HEAD -- 'nexus/***' | grep '^+' |
    grep -iE 'float|strconv|ParseFloat|json\.Number|big\.(Float|Rat)|%[0-9.]*f|math\.|complex'
+// class: no int64 holds 100.125, no float may touch it, and a parse would be the
+// NOT ONE NUMBER IS FORMED IN THIS FILE OR IN THE CODE IT EXERCISES. No strconv,
+// no float, no arithmetic on any captured amount, no exponent — the boundary is
+		// 19 significant digits — past float64 entirely. A parsing implementation
```

**Four hits, all four inside comments**, and all four are the prohibition being stated rather than
broken. The repo's own `no-float guard` and `no-float census` ran inside `.softhouse/conformance.sh`
on the committed tree and passed (`out/BAR-clean-tree.log`).

**The tempting wrong fix, named so nobody re-proposes it.** The obvious "proper" repair for
F-T387-2 is to parse both sides and compare them as numbers. That is an instant REJECT here: no
`int64` holds `100.125`, a float would destroy the very digit the divergence class exists to
record, and the parse would be the defect this file exists to prevent wearing the costume of a fix.
The boundary is therefore decided by **classifying a single neighbouring byte** — the same
discipline `hasResidueBeyondMinorUnit` already uses to find a residue without ever holding the
amount as a number.

---

# 2. F-T387-2 — the numeric PREFIX, closed at admission

## 2.1 The change

`nexus/internal/apps/ledger/conformance/admit.go`. `verbatimInCapture` was
`bytes.Contains(raw, []byte(t))` and nothing else, so `"100.12"` satisfied it against a capture
holding `"100.125"`. It now requires a **token-bounded** occurrence:

- new `tokenBoundedIndex(raw, needle []byte) int` — walks occurrences by byte offset and returns
  the first one whose neighbours do not continue a numeric token, or `-1`;
- `numericLeftNeighbour(b byte)` — digit, `.`, `-`, `+`. The signs are included because they change
  the value, not because any arithmetic was done to find that out;
- `numericRightNeighbour(b byte)` — digit, `.`, `e`, `E`. `e`/`E` closes the exponent form
  (`"100.12"` against `"100.12e3"`); recognising the marker is a character test and forms no
  exponent.

**Two distinct diagnostics, deliberately.** "Those bytes DO NOT OCCUR" (the pre-existing message,
unchanged) and the new "…occur … ONLY GLUED TO A LONGER NUMBER". A transcription from nowhere and a
truncation of the artefact's own number are different mistakes and a reader has to be able to tell
them apart; one arm of the test suite asserts the two never collapse into each other.

**ANY bounded occurrence is enough.** Both legs of a balanced entry carry the same characters — that
is literally the artefact this rule guards — so one honest occurrence is the whole of the claim.

## 2.2 RED before, GREEN after — driven, not asserted

Instrument: `.softhouse/capture/t397-t387-conditions/instruments/red-before-green.sh`.
Transcripts: `out/RED-bare-bytes-Contains.log`, `out/GREEN-token-bounded.log`.

**What RED means here, because the obvious reading is wrong.** The true pre-T397 tree does not fail
the new tests, it does not *compile* them — `tokenBoundedIndex` does not exist on `main`, so `go
test` there reports a build error and no test result at all, which is evidence about a symbol and
not about a defect. RED is therefore driven by **neutralising the new call site**
(`if tokenBoundedIndex(...)` → `if false && tokenBoundedIndex(...)`), which leaves the helper
compiled and restores `verbatimInCapture` to *exactly* its pre-T397 semantics.

```
RED exit = 1
  --- FAIL: TestANumericPrefixOfTheCapturedAmountIsNotVerbatim
      --- PASS: …/control_the_unmutated_vector_still_admits
      --- FAIL: …/request_side_prefix_A17            <- "100.12" vs captured "100.125"
      --- FAIL: …/oracle_side_prefix                 <- "100.12500" vs captured "100.125000"
      --- FAIL: …/oracle_side_tail                   <- "00.125000" vs captured "100.125000"
      --- PASS: …/absent_text_keeps_the_original_diagnostic
  --- PASS: TestTheBoundaryRuleFormsNoNumber                          (16 sub-tests)
  --- PASS: TestThePrefixIsStillCaughtDownstreamIfAdmissionIsBypassed
  --- PASS: TestObservedCharactersMustBeInTheCitedCapture             (T360's, unchanged)

GREEN exit = 0   (every one of the above PASS)
RED-before-GREEN CONFIRMED
```

The RED **discriminates**: exactly the three boundary arms fail, the anti-vacuity control passes,
T360's own verbatim tests pass, and the retained downstream control passes. A bare build failure
could not have shown any of that.

## 2.3 A17 end to end, on both sides of the change

Instrument: `instruments/a17-before-after.sh` (drives `instruments/a17.py` against a binary built
from the neutralised tree and then from the fixed tree). Transcripts:
`out/attacks/A17-BEFORE-bare-contains.log`, `out/attacks/A17-AFTER-token-bounded.log`.

| tree | LDG-DIV-01 | ledger parity | ledger inadmissible | exit |
|---|---|---|---|---|
| **BEFORE** (bare `bytes.Contains`) | **FAIL 2 cells (0 money)** | PASS 7 **FAIL 1** | 0 | **1** |
| **AFTER** (token-bounded) | **INADMISSIBLE 0 cells** | PASS 7 FAIL 0 | **1** | **2** |

The AFTER run prints, per leg:

```
request.legs[].amount_major_text[0] is "100.12" and those bytes occur in
provenance.request_capture_ref (…/T352-A01-residue-3dp.req) ONLY GLUED TO A LONGER NUMBER …
```

This is T387's own measurement reproduced rather than quoted, and it is also the record that the
**second layer still exists**: BEFORE, the class caught itself downstream exactly as T387 described.

## 2.4 The self-correction is RETAINED as a control (P-45)

`TestThePrefixIsStillCaughtDownstreamIfAdmissionIsBypassed`
(`nexus/internal/apps/ledger/conformance/verbatimboundary_test.go`) plants the A17 mutation and
grades it the way `gradeOne` would **after** `Admit` — deliberately skipping `Admit`, because after
T397 the vector never reaches the comparator and the downstream check would otherwise become
unobservable and then, silently, removable. It asserts:

- `divergence.port_outcome: want "REFUSED", got "ACCEPTED"` is still produced;
- `THE DIVERGENCE HAS MOVED` is still said;
- the comparator graded **0 money cells** (the class has none and must never acquire one);
- **control for the control**: the unmutated vector still passes the same comparator, so the FAIL
  above is caused by the mutation and not by a comparator that fails everything.

Two independent layers now refuse the prefix, and exactly one test goes red if either is lost.

## 2.5 The boundary rule's own table

`TestTheBoundaryRuleFormsNoNumber` — 16 rows chosen so that any implementation that parsed either
side would answer differently: 19 significant digits (`1234567890123456.001`, past `float64`
entirely) and its prefix; the exponent form; a leading sign; `"100.120"` against a capture holding
`"100.12"` (numerically equal, textually different — the rule is about characters and must not
"helpfully" find it); and the two-occurrence case where the first is glued and the second is not.

---

# 3. F-T387-1 — the unqualified verdict sentence, qualified

`nexus/internal/apps/loanschedule/conformance/report.go`. The exit-0 block printed
`This means "matches the reference oracle on captured vectors, within the graded domain".` with
nothing beside it, over a corpus that since T360 contains a captured vector on which the port
demonstrably does **not** match the oracle. It now prints, from the committed store:

```
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
         This means "matches the reference oracle on captured vectors, within the graded domain".
         IT EXCLUDES 1 RECORDED DIVERGENCE(S) — see THE DIVERGENCE CENSUS above. On those
         captured vectors this port does NOT match the reference oracle: the oracle ACCEPTED
         a request this port REFUSES. Each is an OPEN disagreement held at the gate named on
         its row, and a green line there means only "the disagreement is still exactly as
         recorded" — never that it has been fixed, and never that the port is right.
         IT DOES NOT MEAN SAFE TO CUT OVER. Cutover is a user gate.
```

- The count comes from `(*Summary).recordedDivergences()`, which reads the **ledger Summary's own
  census fields** (`DivergencePass + DivergenceFail`). It composes nothing, so the verdict qualifier
  and the divergence census can never disagree about how many there are — the defect A2-34 found in
  the hand-written not-graded block.
- **Both directions are counted**, because the sentence being qualified is "this port matches the
  oracle on the captured vectors" and a divergence is a captured vector on which it does not,
  whether the disagreement is still behaving as recorded (PASS) or has moved (FAIL). A FAIL folds
  into ledger `ParityFail` and turns the run red, so exit 0 sees only the PASS half in practice; the
  sum is written anyway so the sentence stays true if that fold is ever changed.
- **The zero case is printed too** — `NO DIVERGENCE IS RECORDED in this store … That is a fact about
  the CORPUS, not a fact about the port` — because "there are none" and "nobody looked" must stay
  distinguishable, which is the discipline every other empty state in this report already keeps.
- **A nil ledger half claims nothing in either direction** (self-test, `-context` filter, or an
  empty ledger store), because the report has already said the ledger half did not run.

Asserted by `nexus/internal/apps/loanschedule/conformance/verdict_divergence_test.go`, five arms:
the qualifier appears; the count tracks the ledger (driven with 3, so a hard-coded `1` would fail);
the zero case says so; the nil case says nothing; the cutover line survives. Plus a table over
`recordedDivergences()` in both directions. A claim limit nothing asserts is prose.

---

# 4. T387'S 16 AUTHORING ATTACKS — ALL 16 STILL REFUSED

Instrument: `instruments/redrive16.py`, reconstructed from T387's own committed
`attack{,2,3,4,_capture}.py` and re-pointed at this worktree. Each attack is planted on the **real
committed store**, driven through the **real conformance binary at full store**, then reverted with
`git checkout --` before the next plant. Per-attack transcripts in `out/attacks/`.

**The pass criterion is stricter than "the run went red":** the run must not exit 0, **and** the
vector must be reported `INADMISSIBLE` (or trip the divergence-population FATAL), **and** the reason
T387 recorded must still be among the reasons printed. A vector that FAILED grading instead of being
REFUSED ADMISSION would mean the default-deny had been lost and the corpus was relying on the
comparator — the exact P-45 shape this task removes from one place.

```
A1-expect-legs-10013                           exit=2  refused=True  REFUSED
A2-totals-minor                                exit=2  refused=True  REFUSED
A3-expect-refusal                              exit=2  refused=True  REFUSED
A4-expect-http-status                          exit=2  refused=True  REFUSED
A5-oracle-accepted-on-parity                   exit=2  refused=True  REFUSED
A6-one-digit-mutated                           exit=2  refused=True  REFUSED
A7-representable                               exit=2  refused=True  REFUSED
A8-short-marker                                exit=2  refused=True  REFUSED
A9-capture-digit-mutated-sha-refreshed         exit=2  refused=True  REFUSED
A10-divergence-relabelled-parity               exit=2  refused=True  REFUSED
A11-divergence-relabelled-oracle-refusal       exit=2  refused=True  REFUSED
A12-divergence-with-journal-entry-kind         exit=2  refused=True  REFUSED
A13-marker-not-in-observed-text                exit=2  refused=True  REFUSED
A14-gate-empty                                 exit=2  refused=True  REFUSED
A15-refusal-for-an-unrelated-reason            exit=2  refused=True  REFUSED
A16-graded-on-an-unrelated-refusal             exit=2  refused=True  REFUSED

16 of 16 attacks REFUSED
store clean after the drive: YES     (git status --porcelain over the store, checked by the script)
```

**A16 GAINS A REASON, and that is the closure showing up.** T387 built A16 **on top of** the
F-T387-2 hole — it truncates the request legs to `"100.12"` precisely because `bytes.Contains`
accepted the prefix — so after T397 it is refused by the **new boundary rule as well as** by the
pre-existing date/outcome conflict rule. Both are asserted by the driver.

`A9` is the isolation case: one digit mutated **inside the cited capture artefact** with the
vector's `capture_sha256` refreshed to the new hash, so the digest pin cannot be what catches it.
The verbatim check still fires on its own.

---

# 5. VERIFICATION — from a CLEAN tree, after `git add -A` and commit

```
$ git status --porcelain
(empty)

$ cd nexus && go build ./...
EXIT = 0                                out/go-build.log

$ cd nexus && go test -count=1 ./...
ok  github.com/gerege/nexus/internal/apps/ledger                     0.462s
ok  github.com/gerege/nexus/internal/apps/ledger/conformance         5.200s
ok  github.com/gerege/nexus/internal/apps/loanschedule               4.283s
ok  github.com/gerege/nexus/internal/apps/loanschedule/conformance  32.072s
EXIT = 0                                out/go-test-count1.log

$ bash .softhouse/conformance.sh          # bash, never sh
EXIT = 0                                out/BAR-clean-tree.log

$ grep -c 'probe = ' out/BAR-clean-tree.log
1                                       # P-84: PRESENCE tested before value
conformance: reference oracle (https://localhost:8443/…/actuator/health) probe = up
```

Baseline reconciliation, every figure read off the committed bar log:

| figure | measured | pinned |
|---|---|---|
| parity vectors / cells | **46 / 7884** | 46 / 7884 |
| ledger parity | **PASS 7 FAIL 0** | 7 / 0 |
| `LEDGER parity vectors` | **7 == pinned 7** | 7 |
| `LEDGER money cells compared` | **39 == pinned 39** | 39 |
| `LEDGER oracle-refusal vector` | **6 == pinned 6** | 6 |
| `LEDGER declared exemptions` | **0 == pinned 0** | 0 |
| divergence vectors | **PASS 1 FAIL 0 (pinned 1)** | 1 |
| ledger cells compared | 144 graded, 39 money | — |
| wrong ledger implementations | **14 discovered, all 14 KILLED** | 14 |
| dead-path frontier | GREEN, `deadOccurrences 108` | 108 |
| exemption censuses | all 9 read `== pinned` | — |

`ledger inadmissible 0`, `ledger harness errors 0`, no `LEDGER FATAL`, no `warn`-level line, one
`EXIT` line and it is 0.

---

# 6. WHAT THIS DOES NOT SETTLE

- **G-19 remains OPEN.** Nothing here decides whether the port or the oracle is right about a
  sub-minor-unit residue. The verdict line now *says* so; it does not close it. That is still a
  `user` gate.
- **The corpus still cannot grade the oracle's over-scale value against anything.** T360's printed
  limit is untouched: a port that refused for the right reason and a port that refused for the right
  reason *while also being wrong about what the oracle's amount was* remain indistinguishable.
  Closing that needs a decided rule for over-scale money, not a wider schema.
- **T387's OBS-1 and OBS-2 are untouched.** OBS-1 (a pre-existing conflict diagnostic calls
  `expect.kind "port-refusal"` "a POSTED ENTRY") and OBS-2 (`-context ledger` prints a mislabelled
  empty-store fatal) are both pre-existing, both cosmetic, and neither is in this task's brief. All
  drives here are **full-store**, so OBS-2 does not touch any figure above.
- **T359's F-T359-5** (the `t305`/`t327` rigs pinning `60/64` and `26` by string equality) is still
  open and still nobody's.
- **`.softhouse/conformance.sh` was not edited** — T404 holds it this wave. Nothing in T397 needs a
  pin moved: no census figure changed.
