# T284 — the three FROZEN `verify` call sites T274 broke: decision record

Branch `softhouse/t284-schema2-callsites`. This file is authoritative for **which instrument
answers which question** about `wire_attestation.py verify`. The machine-checked version of
the same table is `instruments/callsite_registry.json`, graded by
`instruments/10-callsite-registry.py`.

---

## 1. What "FROZEN" turned out to bind

**T114's standing ruling**, as it is stated in the place this program keeps restating it —
`.softhouse/capture/audit-t44/analysis/T207/RULING-float-derived-predicate.md:247`:

> *"Anything that produced COMMITTED EVIDENCE is superseded by a scratch copy, NEVER edited in
> place."*

It binds the **bytes** of a script that produced committed evidence, and the bytes of the
evidence it produced. It does **not** forbid a successor, and it does **not** forbid an
additive notice placed beside the frozen file. The remedy the ruling itself prescribes is a
supersession: a scratch copy plus a record of which one is authoritative (the shape of
`.softhouse/capture/leapboundary/analysis/T175-SUPERSEDES.md` and
`.softhouse/capture/audit-t44/analysis/T207/T207-SUPERSEDES.md`).

All three sites are caught by it — each produced committed evidence, and in each case the
evidence includes the **verify transcripts themselves**:

| site | committed files it produced | which of them are the output of the broken call |
|---|---|---|
| `t250-…/instruments/30-redB-mismatch-detected.sh` | 127 under `t250-tenant-attestation/` | `evidence/redB/arm-*/verify.out`, `verify.err` |
| `t261-…/instruments/t261-redB-attack.sh` | 265 under `reviews/t261-tenant-attestation/` (shared with redC) | `evidence/redB/a*/…vout`, `…verr` |
| `t261-…/instruments/t261-redC-wrap.sh` | *(same tree)* | `evidence/redC/dupid/verr`, `mbtrunc/verr` |

**So: nothing was rewritten.** `git diff --name-status` over this branch shows **zero `M`** on
any pre-existing file. What was done instead is an **explicit, justified re-freeze**: each
site is declared, its schema scope is stated, a successor carries its coverage, and a pin
fails if any of that moves.

Two files were **added** next to frozen ones —
`t250-tenant-attestation/instruments/SCHEMA2-STATUS.md` and
`reviews/t261-tenant-attestation/instruments/SCHEMA2-STATUS.md`. That is a deliberate,
declared extension beyond this task's `files_hint`, taken because the reader who is about to
run one of these scripts looks in **that directory**, not in a handoff. Both are additive,
both are pinned as `required_files`, and neither changes a byte of anything that existed.

---

## 2. What was actually broken — measured, not inherited

All three measurements were taken on this branch against the live reference oracle (Fineract)
at `https://localhost:8443`, in a scratch copy of the tree so no committed evidence was
touched. Transcripts: `evidence/RED-site1.txt`, `RED-site2.txt`, `RED-site3.txt`.

| site | line | what happens now | how loud |
|---|---|---|---|
| `30-redB-mismatch-detected.sh` | **:74** | 2 of 8 arms as expected, **6 schema refusals**, `exit 1` | loud |
| `t261-redB-attack.sh` | **:47, :49** | calibration refuses → **ABORT `exit 4`, 0 of 11 attacks scored** | loud |
| `t261-redC-wrap.sh` | **:54, :104, :168** | all 17 sweep verifies fail, and it still **`exit 0`**; `dupid` and `mbtrunc` print **`DETECTED`** on a schema refusal | **silent, and worse than silent** |

Three findings the brief did not anticipate, each measured:

**F-1 — the population is not three files.** The tracked tree carries **13 files with 24
`verify` invocations**, of which **11 are REQUEST_ONLY**. Six are the T284 defect (the three
sites). **Five more are correct by design** and would have been "repaired" by anyone who
treated REQUEST_ONLY as a defect class: T274's `P1` control (a deliberate schema-1 call over
T250's committed corpus), T274's `P3` control (a deliberate REQUEST_ONLY call asserting the
*refusal*), T283's `verify_request_only()` helper, and the **frozen specimen**
`t274-attestation-failopen/baseline/oracle_send.sh`, which must never be repaired because
repairing it would destroy T274's RED arm. T283's "exactly three files invoke `verify`" is
true of the **pre-T274 frozen** instruments and false as a statement about the tree.

**F-2 — site 3 scores a refusal as a detection.** `rc=2` means *no verdict is available*.
`t261-redC-wrap.sh:104` prints `verify rc=2 DETECTED` and `:168` reports the truncated
multibyte body as caught. Neither attack was ever looked at. A refusal read as a win is a
fail-open with a green tick on it.

**F-3 — site 1 has one arm that passes while testing nothing.** Arm 3's stated test is
"header record DELETED → must refuse". It gets `rc=2` — from the *schema* check, not from the
missing record. Arm 4 is unaffected (its refusal is genuinely the derivation-tag one).

---

## 3. The three decisions

They are not the same answer, and the reasons differ.

### Site 1 — `t250-…/30-redB-mismatch-detected.sh` → **(b) RE-FROZEN, SCOPED TO SCHEMA 1**

*Not (a) taught*, because a schema-2-native version of these exact eight arms **already
exists**: `t274-attestation-failopen/instruments/30-t250-arms-still-hold.sh`, arm for arm,
expectation for expectation, plus 7a/7b. Writing a second one would create two instruments
that can disagree.

*Not (c) retired*, because retirement would have thrown away a question nobody had asked:
**is T250's committed evidence still admissible under today's verifier?** T283 measured the
live-recapture path (2/8). Nobody measured the committed path.

**Successor:** `instruments/20-site1-schema1-replay.sh` — oracle-free, replays the eight arms
against T250's **committed schema 1** corpus, pinned by a digest over all 70 files.
**Result: 8 of 8 arms reproduce T250's original expected exit statuses** (0,1,1,2,2,1,1,0),
and arm 3's refusal is now for the *right* reason. T250's 127 committed evidence files remain
admissible. Transcript: `evidence/GREEN-site1.txt`.

**The scope gate, which is the part the task asks for.** The successor REFUSES (exit 2) if any
input sidecar declares an `attestation-schema:` line, and it **drives that gate red on every
run** via a built-in selftest that plants such a line in a scratch copy. It does not skip an
out-of-scope input; it refuses it and grades nothing.

### Site 2 — `t261-redB-attack.sh` → **(a) TAUGHT SCHEMA 2**

**Six of its eleven attack shapes appear in no other instrument in the tree** — A3 (body
truncated + all three body assertions deleted), A5 (a wire header whose *name* collides with a
sidecar assertion key), A7 (a colon-bearing value tampered after the colon), A8 (header name
case-folded), A9 (record swapped for another real request's), A11 (`request-headers-sha256:`
deleted). T274 covers only A1, A2, A4, A6, A10. Retirement would drop six live attack shapes.

**Successor:** `successors/t284-redB-attack-v2.sh`. All eleven, schema-2 complete, plus **A12
— the response *header* record swapped**, which could not be written before T274 because the
response leg did not exist. **Result: 12 caught / 0 accepted**, positive control clean.
Transcript: `evidence/GREEN-site2.txt`.

### Site 3 — `t261-redC-wrap.sh` → **SPLIT: wrap sweep (c) RETIRED, residual legs (a) TAUGHT**

The 17-length wrap sweep is the *identical* experiment T274 instrument 20 runs
(`1 10 60 61 62 63 64 65 66 127 128 129 200 300 1000 4000` plus a 360-byte colon-laden value),
schema-2-natively, with the extra check that the `.reqhdr` wire record is byte-identical to
the T250 rig's. Seventeen more live captures buy nothing.

The other legs are reproduced nowhere. **Successor:** `successors/t284-redC-residual-v2.sh` —
duplicate-identical-header multiplicity, CRLF injection, multibyte `Content-Length`
byte-exactness, and a body truncated **mid-character** with every assertion left intact.
**Result: all legs as required.** Header multiplicity is now a **detection (rc=1)** — T250's
redC recorded it as a GAP and the frozen original scores the schema refusal as the catch.
Transcript: `evidence/GREEN-site3.txt`.

**The retirement is asserted, not cited.** `LEG 0` reads T274 instrument 20 and refuses if it
is gone *or if its length list has moved*. Coverage claimed by citation is coverage that
evaporates the day the cited file changes; arms `S5` and `S6` of the red drive prove both
directions.

**And the discrimination the original lacks:** for the legs under attack the successor requires
`rc=1` specifically. `rc=2` is reported as *"a REFUSAL, not a detection — the verifier never
reached the shape under test, so this arm measured NOTHING"* and **fails**.

---

## 4. What makes it bite — and the honest limit on that

The decisions above are a document, and a document is `P-45`'s exact shape one layer out:
**a guard that only works when someone remembers to read it enforces nothing.** So the
decisions are also a **pin**.

`instruments/10-callsite-registry.py` enumerates every `verify` call site in the tracked tree,
classifies each by the response artefacts it presents, and grades the result against
`callsite_registry.json`. It is **default-deny** in five directions: an undeclared site fails,
a vanished site fails, a class change fails, a frozen file whose digest moved fails, and a
missing successor or missing notice fails. No pin, an empty corpus, or a failed calibration
**REFUSES (exit 2)** rather than reporting a clean tree.

**THE LIMIT, STATED HERE RATHER THAN DISCOVERED LATER: it is not wired into
`.softhouse/conformance.sh`, because that file is partitioned to two other tasks this fire and
T284 may not touch it.** Until it is wired, this instrument is itself an unwired guard —
the very shape it was built to close — and **nobody may cite it as an enforced control.** The
exact wiring line is in the handoff, ready to paste, and the recommendation is HARD.

---

## 5. Which file is authoritative for what

| question | authoritative instrument |
|---|---|
| do T250's eight redB arms hold on a **fresh schema 2** capture? | `t274-attestation-failopen/instruments/30-t250-arms-still-hold.sh` |
| do they hold against T250's **committed schema 1** corpus? | `t284-schema2-callsites/instruments/20-site1-schema1-replay.sh` |
| is the 64-byte `--trace-ascii` wrap reassembly exact? | `t274-attestation-failopen/instruments/20-wrap-boundary-and-derivation-unchanged.sh` |
| do T261's eleven attack shapes still get caught? | `t284-schema2-callsites/successors/t284-redB-attack-v2.sh` |
| multiplicity / CRLF / multibyte body? | `t284-schema2-callsites/successors/t284-redC-residual-v2.sh` |
| are all four T261 fail-open routes still closed? | `t274-attestation-failopen/instruments/10-four-routes-red-green.sh` |
| can a forgery survive re-derivation? | `reviews/t283-review-t274/instruments/10-forgery-arms.sh` |
| **is every call site declared and correctly scoped?** | `t284-schema2-callsites/instruments/10-callsite-registry.py` |

---

## 6. A hazard in the successors themselves, disclosed rather than left to be found

Site 1's live half (`t274-…/instruments/30-t250-arms-still-hold.sh`) and the wrap-sweep owner
(`t274-…/instruments/20-wrap-boundary-and-derivation-unchanged.sh`) **both `rm -rf` a committed
evidence directory when they run** — `evidence/t250arms` (**91 tracked files**) and
`evidence/wrap` (**145 tracked files**) respectively [measured: `git ls-files | wc -l` on each
path].

So `F-T283-6` is not a property of the T250 instrument. It is a property of at least **four**
instruments in this chain, including two that T284 relies on. **Neither was run for this
task's evidence**, and that is why the site 1 GREEN transcript is the *committed-corpus*
replay rather than the live one. Anyone who runs either T274 instrument to check T284's claims
should expect a dirty tree afterwards and should `git checkout --` those paths.

The T284 instruments do not have this shape: they write only to `mktemp -d` under `$TMPDIR`,
and the red drive proves the real tree is still green (`Z0`) after sixteen deliberate breaks.

Filed as backlog **FU-T284-3**.

---

**RETAINED, BYTE-IDENTICAL, DO NOT RUN FOR A NEW ANSWER:**
`t250-…/instruments/30-redB-mismatch-detected.sh` (and it destroys committed evidence if you
do), `t261-…/instruments/t261-redB-attack.sh`, `t261-…/instruments/t261-redC-wrap.sh`.
**RETAINED, NEVER RUN, NEVER REPAIRED:** `t274-attestation-failopen/baseline/oracle_send.sh`.
