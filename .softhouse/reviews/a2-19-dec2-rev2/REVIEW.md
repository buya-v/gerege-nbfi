# A2-19 — INDEPENDENT REVIEW of DEC-2 revision 2 (post-A2-17 micro-fix)

**Task:** `A2-19`, run `2026-08-21-run2-tierA-gl-accounting-A2`
**Subject:** `docs/adr/DEC-2-gl-accounting-adapter.md`, 1,678 lines, DRAFT revision 2,
as it stands after A2-17's applied micro-fix (merge `0e610ba`, feature `f39a65d`).
**Date:** 22 August 2026

---

## VERDICT: **REJECTED**

One rejection-grade finding (**A2-19-F1**), two substantive (**F2**, **F3**), four minor
(**F4**–**F6**, plus one citation miscount at §6).

The rejection is narrow and repairable. **The document's central conclusions are correct and I
reproduced them**: option (b) really is a memo, P-1…P-5 really are required, the §5.4 sequencing
rule is right, and the §4.10 micro-fix is correctly placed and factually right on its load-bearing
clause. What is rejection-grade is a **single claim, asserted in three places and now propagated
into the micro-fix, that I falsified by measurement** — and it fails in the unsafe direction, by
producing a green `PASS` line naming the `ledger` context at exit 0.

This is the same defect class `A2-14` rejected revision 1 for ("an empty `ledger/` passes"), one
notch worse: **a populated `ledger/` passes, and affirmatively reports a passing ledger vector.**

---

## 0. Fork point, and the P-59 trap

```
HEAD                     1672d857f42c7bfe20beec2c8f07e62484c7b469
git merge-base HEAD main 1672d857f42c7bfe20beec2c8f07e62484c7b469   (identical — forked at main)
docs/adr/DEC-2-gl-accounting-adapter.md   present, 1678 lines
0e610ba (A2-17 merge)    is an ancestor of HEAD
```

Every artefact named in my brief is present. No STOP.

**P-59 asserted, not assumed.** Both upstream branches are already merged, so the three-dot form
reads clean:

```
git diff main...softhouse/A2-17-review-dec2-rev2   ->  0 lines
git diff main...softhouse/A2-16-dec2-rev2          ->  0 lines
```

Both **empty**. I therefore used `git show f39a65d` (A2-17's feature commit) and
`git show softhouse/A2-16-dec2-rev2` for the subject matter, and read the handoffs from git rather
than from disk. The A2-17 micro-fix diff so obtained is **non-empty**: 2 files, +439 lines, of which
`docs/adr/DEC-2-gl-accounting-adapter.md` is **+7** (A2-17's own commit message says "8 added
lines"; the diff is 7 — six blockquote lines and one blank. Immaterial, noted for accuracy).

---

## 1. Method, and the programs I ran

Harness invoked with **`bash`**, never `sh`. Toolchain exported from
`.softhouse/bin/go-env.sh`'s variables (the sandbox refuses `.`-sourcing in this worktree, so the
five exports were set directly and `go version` confirmed **go1.26.6 darwin/arm64**).

**Oracle probe tested for presence, not assumed** (per brief): the baseline run printed
`conformance: reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up`
and `oracle probe UP`. **The probe line was actually printed and reads `up`.** Every exit 2 below is
therefore a real refusal, not oracle-down.

**Tool provenance (P-58 / P-33).** `grep` invoked as **`/usr/bin/grep`**, BSD grep **2.6.0-FreeBSD**,
with `LC_ALL=C` on every expression and `-a` where the input is harness output, so the shell-function
ugrep (which re-execs with `-I`) cannot be silently substituted. Input shape: plain ASCII text
files. `sed` is BSD `/usr/bin/sed`. Extraction only — **no source line in this review was retyped**
(P-46).

**No file under `.softhouse/vectors/`, `nexus/`, `.softhouse/conformance.sh`,
`.softhouse/bin/fire-program.sh` or `.softhouse/handoff/*promote-vectors.py` was modified.** Every
experiment ran against a **temp copy** of the store under `/tmp/a219-*`, with a binary built to
`/tmp/a219-conf` and `-store=` / `-repo-root=` pointed at it. Raw outputs are committed beside this
review.

---

## 2. Baseline and control — P-35, so nothing here inspects zero items

| # | run | result |
|---|---|---|
| **E0** | `bash .softhouse/conformance.sh`, my tree, unmodified | **exit 0**, `VERDICT: PASS`, **43 parity, 5664 cells** |
| **C0** | same via the built binary against a pristine temp store copy | **exit 0**, `PASS 43`, **5664 cells** |

The document's stated baseline reproduces **exactly** on a later `main` than A2-16 forked from.
The control establishes that the temp-store rig itself is neutral, so every delta below is caused
by the perturbation and not by the rig.

---

## 3. Findings

### A2-19-F1 — **REJECTION-GRADE.** "No `ledger` vector CAN exist" is FALSE. A `ledger` vector is admitted, graded, and reports **PASS** at exit 0.

**Where the claim is made** (three places, one of them the unreviewed micro-fix):

- **Banner, item 2** — *"**No `ledger` vector CAN exist.**"*
- **§8.1, fact 2** — *"**Zero `ledger` vectors CAN exist**"*
- **§4.10, A2-17's micro-fix** — *"because §5.1 establishes that no `ledger` vector can be admitted
  **at all** until §5.3's P-1…P-5 exist."*

**§5.1's own heading is careful and correct** — *"No `ledger` vector is **expressible** against the
frozen vector schema"*. Expression-impossibility is what the five legs actually establish, and I
verified all five (§4 below). **Admission-impossibility is a strictly stronger claim, and it is
false.**

**The false negative that produced it.** The strong claim rests on §5.1's positive control **PC-3**,
"the same case filed as `class: "contract-refusal"` — the only other class outside `_selftest/`",
reported INADMISSIBLE. But read PC-3's own quoted refusals: it failed on **two author-correctable
defects**, not on a structural wall —

```
class "contract-refusal" requires oracle.seam "none": nothing was captured
expect.sentinel: "ErrGLAccountMappingNotFound" is not one of ErrInvalidRequest,
  ErrUnsupportedConfiguration, ErrNoDiscriminatingVector
```

Both are things the *author* chose. **P-50: the prover was never made falsifiable toward the fix.**
A2-16 built a control that failed and read it as a wall; A2-17 re-derived the *argument* but did not
re-run the *corrected* control. So nobody corrected the two defects and retried. I did.

**E4 — MEASURED.** I took the repository's own `REFUSE-01-actual-actual-ungraded.json`, changed
`case_id`, set `context: "ledger"`, filed it at `ledger/LEDGER-REFUSE-A219.json`, and supplied a
citation. Everything else — including `oracle.seam: "none"` and the legal sentinel
`ErrNoDiscriminatingVector` — is what the schema already requires. Unfiltered run against the temp
store:

```
LEDGER-REFUSE-A219           contract-refusal none        PASS              1        0
    contract-refusal        PASS 5    FAIL 0   (derived from the ratified contract, NOT oracle-observed)
    cells compared          5665 graded, 87 ungraded (never recorded by the capture)
VERDICT: PASS (exit 0) — 43 parity vectors match the pinned reference oracle, 5665 cells compared.
```

**Exit 0.** The vector is **admitted**, **graded**, and **passes**. The contract-refusal tally moves
**4 → 5** and the headline cell count moves **5664 → 5665**. A `ledger`-context row is printed in the
per-vector table with the word `PASS` on it.

**E8 — and this is the severe form. A `ledger` PARITY vector is admitted and COUNTED IN THE 43.**

I then closed the harder case. I took `P-00-baseline-6x7pct.json` — a real promoted parity capture —
changed **only** its `case_id` (to clear the duplicate-id check) and its `context` to `"ledger"`,
and filed it at `ledger/`. Its `capabilities_required`, its `graded_against` capability, its seam and
its whole `provenance` block are **untouched**, so `admitParityProvenance` passes against the real
committed capture and its real `sha256`. Unfiltered:

```
LEDGER-PARITY-PURE-A219      parity           path_a_e... PASS             47        2
    parity vectors          PASS 44   FAIL 0
    cells compared          5711 graded, 89 ungraded (never recorded by the capture)
VERDICT: PASS (exit 0) — 44 parity vectors match the pinned reference oracle, 5711 cells compared.
```

**`parity vectors PASS 44`.** Exit 0. **The headline number this entire program quotes is inflatable
by copying a loanschedule capture into `ledger/` and editing two strings**, and the verdict line then
reads "44 parity vectors match the pinned reference oracle" over a corpus containing a ledger-context
vector that grades nothing about the ledger.

This falsifies two further statements the document makes as structural guarantees:

- **§8.2**: *"**"PASS 43" remains the only thing anyone can say about the ledger, and what it says is
  "this is about a different context"**"* — false; the ledger context can contribute to the parity
  count today.
- **Banner fact 4 / §8.1 fact 4**: *"All 43 promoted parity vectors are in the `loanschedule/`
  directory"* — true as a statement of **fact today**, but the document leans on it as though the
  directory boundary were **enforced**. It is not. Nothing ties `context` to a schema, a comparator,
  a capability or a count.

**The structural cause, and it is one line.** `context` is a free-text field constrained *only* to be
non-empty and to equal its own directory name — `admit.go:115` and `admit.go:119-120`:

```go
	if v.Context == "" {
	if v.Context != dirOfFile {
		bad("context %q does not match the directory %q the file lives in", v.Context, dirOfFile)
```

I grepped the conformance package for any allowlist of context names. **There is none** — the only
occurrences of the literal `"loanschedule"` are in `_test.go` files. So *any* directory name is a
legal context, and its contents are graded by the loanschedule machinery regardless of what the
directory is called.

**Why this is rejection-grade and not a follow-up.**

1. **It is believed, and it is load-bearing (P-22).** The banner is the document's most-read
   paragraph and offers four *measured* facts. Fact 2 is false. §8.1 — "what a ratifier reads last"
   — repeats it. The micro-fix propagates it into **§4.10, the table a grader copies from**.
2. **It fails green.** A reader who believes ledger vectors cannot be admitted has no reason to
   guard against a `ledger/` directory filling with relabelled loanschedule content that reports
   `PASS`. The whole program exists to prevent a false green.
3. **It falsifies §8.2 directly.** §8.2 promises `ledger/` "**stays unusable** until the §5.3
   machinery lands". It does not. It is usable enough *today* to print a green ledger line.
4. **It is precedent.** `A2-14` rejected revision 1 because "an empty `ledger/` passes". Revision 2
   fixed the *empty* case honestly (§5.4, which I reproduced — see E1). It did not notice the
   *populated* case, which is worse: the empty directory is merely invisible; this one affirmatively
   asserts a pass.
5. **The repair is not ≤10 mechanical lines**, and it touches an admissibility predicate — which my
   brief forbids a MICRO-FIX from doing.

**What would fix it.**

- Restate the claim in **all three** places as **expression**-impossibility, matching §5.1's own
  heading: *no `ledger` vector can carry a ledger input or express a ledger output.* That statement
  is true, I verified it, and it fully supports §5.2's rejection of option (b).
- **Correct PC-3 in §5.1**: show the corrected vector, show that it IS admitted and passes, and say
  what that means — the class wall is a wall against *meaning*, not against *admission*.
- **Record the hole** beside §5.4's existing empty-directory hole, with the same "DEC-2 records it,
  does not fix it" discipline. The natural home for the guard is **P-6** (below): the store-level
  files are the chokepoint where a context/schema/capability mismatch can be refused.
- **Add a ninth precondition, P-9**: *the store must refuse a vector whose `context` is not the
  context its schema, comparator and capabilities belong to.* E8 shows this is not a theoretical
  tidiness point — without it, the parity count itself is not context-safe, and §8.2's promise that
  "PASS 43 … is about a different context" cannot be kept.
- **Correct §8.2 and banner/§8.1 fact 4** to say the directory separation is a *convention presently
  observed*, not a boundary the harness enforces.

**What this finding does NOT touch.** §5.2's conclusion, §5.3's P-1…P-8, and §5.4's sequencing rule
all stand. My vector grades **nothing** about the ledger — it is a loanschedule refusal in a ledger
costume. The document's *substantive* position is correct; its *statement* of the wall is
overstated in the unsafe direction.

---

### A2-19-F2 — §5.2's five requirements are pure non-regression, and are satisfied by an extension that does nothing

My brief asks whether the demonstration §5.2 requires is *sufficient*, since those five numbered
requirements are the specification `A2-15` will be graded against.

They are not sufficient. All five are **regression guards on `loanschedule`**:

1. before/after digests of the 43 vector files — unchanged;
2. unfiltered `PASS 43` at the **same cell count** (5664);
3. `conformance.sh loanschedule` identical but for timestamps;
4. no diff to `contract.go`, no DEC-1 amendment;
5. `bash` not `sh`, no `gofmt -w`.

**Every one of these is satisfied by a builder who adds nothing at all.** A dead second schema that
no vector uses, or an empty file, passes all five perfectly. There is **no requirement that the new
machinery be demonstrated to work**, and in particular **no required RED demonstration** that the
new `ledger` comparator can *fail* — no positive control that a ledger vector is now admissible, and
no red/green pair proving the comparator detects a wrong implementation.

That is squarely against this program's own standard: **P-35** (a check that inspects zero items is
an ERROR, not a pass) and **P-22** (a guard that cannot fail is worse than none). The program has
already paid for this lesson twice — `T9-F1b` (nine capabilities printed as killed at exit 0 over a
garbage store) and `T156`'s red/green exit trap. §5.2 reintroduces the shape at the level of the
acceptance criteria.

**Severity.** Substantive, and I would normally call it rejection-grade on its own; here it is
subsumed. **Fix:** add a sixth and seventh requirement — (6) a positive control showing a `ledger`
vector is admitted and graded *after* the extension, and (7) a red/green pair showing the new
comparator goes RED on a perturbed expectation and GREEN on the pristine one.

---

### A2-19-F3 — `CounterfactualCoverage` counts kills from vectors the harness REFUSED, silencing the very fatal §5.4 calls "a strong leg"

§5.4's strongest leg is that the capability fatal is registry-wide. I verified that claim exactly
(`capability.go:243-244`, `for _, v := range vectors` / `r.GradedCapabilities()`, no context scoping
anywhere in it). **The document's stated claim is true.**

But the loop filters on **class only** — `if v.Class != ClassParity { continue }` — and **not on
whether the vector was admitted**. So a vector the harness *refused* still contributes coverage.

**E7 — MEASURED.** With a probe row `ledger.probe.a219` marked `in_graded_domain: true`, I added a
relabelled parity vector naming that capability. The harness **REFUSED** it —

```
LEDGER-PARITY-A219  parity  path_a_e...  REFUSED  0  0  UNKNOWN_CAPABILITY
    seam "path_a_embeddable" has no recorded status for capability "ledger.probe.a219"
    (default-deny: an unaudited input is assumed invisible, never assumed wired)
    ledger.probe.a219                          killed by LEDGER-A219-RELABELLED-KILL
```

— and yet `UNBACKED` **disappeared from the output entirely** (`grep -c UNBACKED` = **0**, against 1
in E2/E3), and `kills named` rose **103 → 104 money**. A refused vector both silenced the unbacked-
capability fatal and inflated the headline kill tally.

**Not exploitable to green today**: the refusal itself forces exit 2 (`refused 1`). So the run stays
red — but **for a different reason than the document believes**, and the specific enforcement §5.4
leans on is weaker than stated.

**This is a harness defect, not DEC-2's to fix**, and I raise rather than make. But it **qualifies**
§5.4's claim, and it belongs in the document as a recorded caveat, because §5.4 presents that leg as
the thing that makes Disposition 3 safe.

---

### A2-19-F4 (minor, DRIFT not WRONG) — the `run_guards` citation has moved ~95 lines

Cited as `.softhouse/conformance.sh:843-849` in the **banner (item 3)**, **§4.4.1** and **§8.1
(item 3)**. In my tree `run_guards()` is at **938-949**; line 843 is mid-comment inside
`guard_no_float_in_capture_requests`.

**The fact is correct and I verified it by extraction** — exactly five guards, and all five are about
float, `gofmt` and exception scope:

```
run_guards() {
  local failed=0
  guard_no_float_in_vectors           || failed=1
  guard_no_float_in_harness           || failed=1
  guard_gofmt                         || failed=1
  guard_no_float_in_capture_requests  || failed=1
  guard_no_narrow_catch_in_capture_rigs || failed=1
```

This is **drift**, and the document's header discloses drift as a known hazard. Two mitigations
apply and one does not: the header says harness citations "may be stale by a few lines" — 95 is not
a few — and it specifically claims **§4.4.1's citations were re-taken by A2-16**. They were, and then
`main` moved (T190/T194/T196/T199 all touched `conformance.sh`). Honest drift, not a wrong claim.
Worth a re-take at ratification.

---

### A2-19-F5 (minor) — the micro-fix attributes P-1…P-5 to §5.1; they are §5.3

*"…because **§5.1** establishes that no `ledger` vector can be admitted at all until **§5.3's**
P-1…P-5 exist."* §5.1 never mentions P-1…P-5. The composite claim is §5.1 + §5.4. Immaterial on its
own; noted because the same sentence carries F-1.

### A2-19-F6 (minor, errs safe) — "no legal way to clear it" has a legal way

The harness's own remediation text offers **two** outs:

```
Either promote a vector with a graded_against entry, or set in_graded_domain false in capabilities.json.
```

§5.1 closes the first. **The second is legal, immediate, and is exactly step 2 of §5.4's own
sequencing rule.** So the accurate statement is *"no way to clear it while keeping the claim; the
only remedy is to withdraw the row to `false`"*. The document (and the micro-fix, which mirrors its
parent text faithfully) overstates the hazard in the **fail-loud** direction, which is the safe
direction. Not a defect under P-22 — recorded for precision only.

---

## 4. What I re-derived and CONFIRMED — so silence is distinguishable from not looking

### 4.1 The A2-17 micro-fix itself (nobody had reviewed it)

| aspect | verdict |
|---|---|
| **Placement** | **Correct.** Head of §4.10, immediately above the table, after the "specification for the registry" line. It is where a grader lands before copying rows. |
| **Does §5.4 contain what it points at?** | **Yes.** §5.4 carries a heading literally reading **NORMATIVE SEQUENCING RULE** with the three-step order the block describes. |
| **"six rows `in_graded_domain: true`"** | **Correct, I counted them**: `gl.account.model`, `mapping.core.row`, `mapping.paymenttype.override`, `mapping.duplicate.rows`, `financialactivity.model`, `posting.resolution.cash.loan`. |
| **Does it neutralise A2-17-M1?** | **Yes.** M1 was that §4.10's table carried no pointer to §5.4, whose only pointers were 330+ lines later. The block supplies it in the first thing a reader of §4.10 sees. |
| **"turns every run red — including `-context=loanschedule`"** | **RE-MEASURED, TRUE** (E2/E3 below). |
| **Trailing clause** | **FALSE** — carries F-1, and mis-attributes P-1…P-5 (F-5). |

**E2 / E3 — I re-measured A2-17's decisive measurement myself.** Probe row `ledger.probe.a219`,
`in_graded_domain: true`, no covering kill, appended to a **temp copy** of `capabilities.json`:

| run | result |
|---|---|
| **E2** unfiltered | **exit 2**, `VERDICT: UNUSABLE`, `UNBACKED in_graded_domain claims: ledger.probe.a219` |
| **E3** `-context=loanschedule` | **exit 2**, `VERDICT: UNUSABLE`, identical `UNBACKED` line |

**Confirmed.** Following §4.10's table literally *does* make every run in the repository exit 2
UNUSABLE, including the loanschedule-filtered run. **The micro-fix's load-bearing claim is true, and
the hazard it warns about is real.** On its central purpose the micro-fix is sound.

### 4.2 §5.1's five legs — all opened at the exact cited lines, by extraction

| leg | citation | verdict |
|---|---|---|
| (1) schema string is the only accepted value | `vector.go:16-18`, `admit.go:109-110` | **HIT, exact** |
| (2) `Request` is thirteen loanschedule fields | `vector.go:279-293` | **HIT** — thirteen fields at 279-291; the range overshoots by the closing brace and a blank line. Substance exact. |
| — strict decode | `vector.go:771-772` | **HIT, exact** — `dec.DisallowUnknownFields()` is line 772 |
| (3) `Expect.Kind` closed set; sentinel one of three | `admit.go:180-194`, `enums.go:92-103` | **HIT** — switch at 181, default at 194, `sentinelByName` at 93 |
| (4) three classes jointly closed | `admit.go:130-176`, `:154-171`, `:517-519` | **HIT** — class switch 132; contract-refusal case 153, its `oracle.seam` predicate at **171**, inside the cited range; parity's "must expect a schedule" `bad()` at **518** |
| (5) `StructuralCellFields()` whitelist of three | `vector.go:571-583` | **HIT, exact** — comment 571-580, func 581-583, returns `{"kind","from_date","due_date"}` |

**The five legs are all true.** My F-1 does not touch any of them — it touches the *conclusion drawn
from them*, which is stronger than the legs support.

### 4.3 §5.4's retraction and its measurement — reproduced

**E1.** Empty `ledger/` directory added to a temp store, unfiltered run:

```
EXIT=0
VERDICT: PASS (exit 0) — 43 parity vectors match the pinned reference oracle, 5664 cells compared.
```

and the string `ledger` occurs **exactly once** in the whole 160-line output:

```
150:                            covered: nexus/internal/apps/ledger
```

— the no-float census line about the **Go source tree**, not about a vector. **Reproduced exactly.**
Revision 1's claim was indeed false; revision 2's retraction is correct and honestly stated; the
"remaining hole" §5.4 records and declines to close is real.

### 4.4 §5.3 P-8's independence — **the claim is TRUE**

The driver dispatched `A2-18` this fire on exactly this claim, so I checked it directly.

**P-8 is the `I-3`/`I-4` source guard.** P-1…P-5 are all *vector-schema* machinery. P-8 is a guard
over the **Go source tree** — it looks for a write path to a balance column and for `UPDATE`/`DELETE`
against `acc_gl_journal_entry`. **It consumes no vector, no schema, no comparator and no capability
row.** There is therefore no dependency.

And the target it would guard **exists today**: `nexus/internal/apps/ledger/` holds **18 `.go` files**
(`find nexus -name '*.go' | grep -c ledger` = **18**, which independently confirms §4.4.1's own "18"
claim), 12 of them non-test, ~3,400 non-test lines. My baseline run's census prints
`covered: nexus/internal/apps/ledger` and reports 5 packages / 44 Go files inspected.

**P-8 is independent of P-1…P-5 and is dispatchable today. A2-18 is correctly founded.** This is the
one piece of §5.3 that needs nothing else first, and I confirm A2-17's endorsement of it.

### 4.5 The banner and §8.1 — do they prevent the named misreading?

**Yes.** The specific hazard is a reader taking *"the guards cover the ledger tree"* to mean I-3/I-4
are enforced. Three mechanisms, and the third is the one that earns it:

1. The **banner** states it before any other sentence, and pre-emptively contradicts §8.
2. **§4.4.1** is a dedicated subsection whose title is `THE GUARD I-3 AND I-4 REQUIRE DOES NOT EXIST`,
   sitting exactly where §4.4's reader lands.
3. **§8.3 contradicts the misleading sentence at the point of the claim** — in the same bullet that
   states the true fact: *"DO cover … **FOR FLOATING POINT AND `gofmt`, AND FOR NOTHING ELSE**"*, then
   quotes revision 1's own wording and says it is *"certain to be read as saying the invariants are
   checked. They are not checked."*

I verified the underlying fact by extraction: `run_guards` invokes exactly five guards, all five
about float / `gofmt` / exception scope (F-4 for the drifted line number), and my own unfiltered run
printed `covered: nexus/internal/apps/ledger` — so the hazard is genuinely live and genuinely
defused. **This is the document at its best**, and it is the technique F-1's three sites should have
used.

---

## 5. Adjudication — A2-17's "decide P-6/P-7 BEFORE P-1…P-5"

My brief requires me to **adjudicate** this, not note it. **A2-17 is directionally right, but it
bundles two unlike things, and the bundle should be SPLIT.**

**Facts, verified by extraction, not taken from A2-17:**

- `capabilities.json` line 2: `"schema": "gerege.loanschedule.capabilities/v1"`, and
  `"dec1_revision": 12` — singular.
- `PIN.json` line 2: `"schema": "gerege.loanschedule.pin/v1"`, with singular `"contract_file"` and
  `"contract_sha256"`. The schema check is at `admit.go:65-66`, exactly as §5.3 P-7 cites — **HIT**.
- `dec1_revision` is checked **per vector against the pin** (`admit.go:122`,
  `if v.DEC1Revision != pin.DEC1Revision`).

**P-6 (`capabilities.json`) — YES, decide it BEFORE P-1…P-5. Strongly.**

Three reasons, and the third is decisive:

1. **The file is shared by design.** §5.2's adopted disposition says the second schema shares "the
   store root, the file census, the duplicate-case-id check, the raw-token float scan and **the
   capability registry**". So the registry is *not* separable from the extension — it is explicitly
   the shared part.
2. **DEC-2 itself declines to decide it.** §4.10's closing paragraph refuses to add a fifth status
   precisely because "`capabilities.json`'s schema is shared with the `loanschedule` context and
   adding a status is a change to that file's contract, **which is not DEC-2's to make**". The
   document has already identified this as an undecided, blocking, out-of-scope question.
3. **§5.4's sequencing rule cannot be obeyed without it.** Step 2 says rows are authored
   `in_graded_domain: false` **first**, carrying their reason in `evidence`. A builder cannot author
   a single row — not even a `false` one — without knowing whether ledger rows live in this file or
   another. **P-6 blocks step 1 of the rule that is itself supposed to come first.** That is a real
   ordering inversion, and it is A2-17's best point.

My **F-1** strengthens this further: the store-level files are the only natural chokepoint at which a
`ledger`-context file carrying the loanschedule schema could be refused. Deciding P-6 first is what
makes F-1's hole closable.

**P-7 (`PIN.json`) — NO, not as stated. A2-17 overreaches by bundling it with P-6.**

P-7's stated rationale is *"a second context implies a second pinned contract file, and the pin has
one slot."* **That premise does not hold for DEC-2.** §1.1 establishes — and the status block
repeats — that **DEC-2 does not create or freeze a Go file and carries no PIN digest at all**, unlike
DEC-1. There is no second contract file to pin, and there will not be one until a ledger contract is
frozen, which is a separate future gate.

What *does* need deciding is **narrower and different**: what `dec1_revision` a `ledger` vector
declares, given that `admit.go:122` checks it per-vector against the single store pin. A ledger
vector asserting `dec1_revision: 12` is asserting a *loanschedule* contract revision, which is
semantically wrong. **But that question is only answerable once P-1 fixes the ledger vector's
shape** — it depends on the extension rather than blocking it.

**Adjudicated sequencing:**

```
P-6  ->  P-1…P-5  ->  P-7(narrowed to the dec1_revision question)
P-8  ->  independent, dispatchable now, in parallel with all of the above
```

**Recommendation to the driver:** adopt A2-17's ordering **for P-6 only**; re-scope P-7 in the
document from "a second pinned contract file" (a premise §1.1 contradicts) to "what contract
revision a non-loanschedule vector declares", and move it after P-1. This is a correction to §5.3
that should be made as part of repairing F-1.

---

## 6. `[VERIFIED]` spot-check — **62/64 = 96.9%**

Full sample, per-citation evidence and method in **`CITATIONS.md`** beside this file.

| population | checked | HIT | DRIFT | WRONG |
|---|---|---|---|---|
| Fineract Java (25 named + 22 relative) | 47 | **47** | 0 | 0 |
| Harness / Go, opened by me personally | 15 | **15** | 0 | 0 |
| In-repo non-Go (`conformance.sh`, changelog XML) | 2 | 0 | **1** | **1** |
| **TOTAL** | **64** | **62** | **1** | **1** |

**Every one of the 47 Fineract citations traced to the pinned checkout at the exact cited line**, on
a fresh sample deliberately spread across §2.1, §2.2, §4.2, §4.3, §4.5, §4.7, §4.8, §4.9, §6 and §9
— including citations A2-14 and A2-17 did not open. The pinned commit was re-confirmed by
`git rev-parse`.

**Both misses are in-repo, non-Fineract, and neither is a money claim:**

- **DRIFT** — `.softhouse/conformance.sh:843-849` (= **F-4**). Substance correct; `run_guards` is at
  938-949. **Cause traced**: it was at 843 exactly at commit `dd53e87` (T191) and was shifted +95 by
  `9ef1c93` (T194). Accurate when written.
- **WRONG (minor, inherited)** — §2.2 **B-4**, DEC-2 line 264: *"three columns plus id"*.
  `0001_initial_schema.xml:99-109` declares **two** columns plus id (`gl_account_id`,
  `financial_activity_type`), which I extracted and confirmed myself. The **load-bearing claim — no
  office dimension — is TRUE**, the line range is right, and two things soften it: the claim is
  flagged `[VERIFIED BY A2-1 AND A2-2 …, NOT RE-OPENED HERE]`, the document's own weakest tier — **so
  the tier caught precisely the one wrong claim in 64**, which is evidence *for* the convention — and
  the same sentence's own corroboration lists `id, financial_activity_type, gl_account_id`,
  refuting the count from inside the bracket. **A one-word MICRO-FIX**, correctly outside the
  forbidden categories.

**Distinguishing drift from wrong, as my brief requires:** one drift, one wrong, and the wrong one is
a miscount in the honestly-hedged tier rather than an overstated verification. **The document's
`[VERIFIED]` discipline is sound and its citation-tier convention demonstrably works.**

---

## 7. Non-negotiables sweep

Run over the document and over every file I touched:

- **Money is integer minor units** — the document's money cells are `int64` minor-unit **strings**
  (P-5, §4.3); no float in any monetary path it specifies. The harness's own no-float guards report
  `0 floating-point or imaginary LITERALS` across 5 packages / 44 files / 86,653 tokens.
- **Never insured / protected / guaranteed** — zero occurrences.
- **Deposit-taking** — correctly held as a `user` activation gate; DEC-2 does not activate anything.
- **No US rails / vendors** — none present.
- **PostgreSQL only** — no MySQL, MariaDB or Oracle Database driver, dialect or port. The document
  uses "oracle" exclusively in the **reference-oracle (Fineract)** sense and says so explicitly in
  its own Terminology block.
- **Frozen artefacts unmodified** — `contract.go` and DEC-1 untouched by me; I edited **no** file
  under `nexus/`, `.softhouse/vectors/`, `.softhouse/conformance.sh`,
  `.softhouse/bin/fire-program.sh` or `.softhouse/handoff/*promote-vectors.py`.
- **No gate crossed.** I did not ratify, did not amend DEC-1 or the contract, and did not edit
  DEC-2 — including no micro-fix (see §8).

---

## 8. Why I applied NO micro-fix

My brief permits a MICRO-FIX of ≤10 mechanical lines, but **never a graded-domain predicate**.

F-1 is precisely an admissibility predicate — what the harness will and will not admit — asserted in
three separate places, and repairing it requires correcting a positive control (PC-3) and recording a
new hole. That is neither ≤10 lines nor mechanical, and it is explicitly the forbidden category.

So **`docs/adr/DEC-2-gl-accounting-adapter.md` is unmodified by A2-19.** The document the driver
holds is exactly the document I reviewed, and this verdict applies to it without qualification —
which is the property A2-17's self-merged fix cost the previous round.

---

## 9. What I could not close

1. ~~Whether F-1 is exploitable to a *parity* green.~~ **CLOSED — see E8 under F-1. It is.** A
   `ledger` parity vector naming only loanschedule capabilities is admitted and counted:
   `parity vectors PASS 44`, exit 0. This is the severe form and it is now measured, not flagged.
2. **F-3's blast radius.** I established that a refused vector's kills count toward coverage and the
   kill tally. I did not determine whether any *currently committed* vector is affected — the
   baseline shows `refused 0`, so today the answer is almost certainly no, but I did not prove it
   across all classes.
3. **G-10** remains OPEN and undecided; I neither re-litigated nor crossed it.
4. **§4.2's eleven predicates and §4.6's A-1…A-4** I read but did not independently re-derive
   against Fineract source; A2-14 opened 30+ citations and A2-17 re-opened Q5's set. My own sample
   is in `CITATIONS.md`.

---

## 10. Summary for the driver

**Do not ratify DEC-2 revision 2 as it stands.**

The document is good — better than revision 1 by a wide margin, honest about its own gaps, and
correct in every conclusion I tested. Its §5.4 measurement, its §8.3 technique, and A2-17's
micro-fix all survive independent re-measurement.

But **the banner's second fact is false**, §8.1 repeats it, and the micro-fix has now carried it into
the table a grader copies from. A `ledger` vector can be admitted, graded, and reported as `PASS` at
exit 0 today — and in its parity form it **raises the headline count to `PASS 44`**, which is the one
number this program has been most careful about.

Fixing it is a well-specified edit and not a redesign: restate the three
admission-vs-expression claims, correct PC-3, correct §8.2 and fact 4, record the hole, add **P-9**
(context/schema binding), and re-scope **P-7**. Revision 3 should then pass cleanly.

**Two things the driver can act on immediately, regardless of the rejection:**

- **`A2-18` is correctly founded** — P-8 really is independent of P-1…P-5, and its target tree
  exists (18 files). Let it run.
- **`A2-15` must stay blocked**, and A2-17's endorsement of that is confirmed: with E8 in hand, a
  promotion task pointed at `ledger/` today would produce a green `PASS 44` over a corpus that grades
  nothing about the ledger.
