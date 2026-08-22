# T250 — the capture sidecar's tenant attestation is a hard-coded literal (T245 F-2)

Branch `softhouse/T250-tenant-attestation`. Worktree-isolated, opus, local fire 20260822-140002.
Reference oracle REACHABLE at `https://localhost:8443` throughout; every capture in this task's
evidence is a real exchange with it. Nothing synthesised.

**Vector-store digest — read LIVE, `git rev-parse HEAD:.softhouse/vectors`**

| when | value |
|---|---|
| at start, HEAD `a71c140` | `13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d` |
| at finish | `13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d` — UNMOVED |

---

## 0. T245's reason, re-derived before it was accepted

T245 rested claim (5) on **database contents** (leg 2), not on the capture sidecars (leg 1), and
said why: `cap.sh`/`cap8.sh`/`cap9.sh` "send `-H \"$T\"` but write the sidecar line as a hard-coded
literal … the sidecar is a constant, not an echo of the value in force. **So I did not rest the
claim on it.**"

**Re-derived, and it holds — but I did not take it on report.** RED-DRIVE A below reproduces the
legacy writer verbatim and runs it against the LIVE oracle under two different tenants. The
sidecar it produces for a request genuinely sent to tenant `default` says `gerege`. That is not an
argument that the sidecar *could* be wrong; it is a committed artefact in which it *is* wrong:

```
  legacy  arm: SENT gerege    SIDECAR SAYS gerege    -> TRUE
  legacy  arm: SENT default   SIDECAR SAYS gerege    -> FALSE
```

T245 was right to route around leg 1. A sidecar that cannot disagree is decoration.

---

## 1. Population — BOTH TERMS, with the scope stated (P-66/P-67/P-70)

**Where I looked.** Every path in `git ls-files` of this worktree — 5,215 tracked files, of which
**918** end `.sh` or `.py`. Untracked files, other checkouts and `/Users/buv/fineract` were NOT
searched. Engine: `python3` `re` only. No bare `grep`, no `rg`, no `git grep` (P-75); `type grep`
confirmed a shell function wrapping ugrep, and it was not used for any sweep. Every instrument
calibrates on a known POSITIVE **and** a known NEGATIVE differing by exactly the defect, and
**aborts** (exit 4) if either arm disagrees; `git ls-files` failure aborts (exit 5) — an error is
never reported as a zero (P-80).

### The general shape — instrument `10-population.py`

| term | count |
|---|---|
| **TERM 1** — scripts that talk to the oracle (`curl`/`psql`) AND write ≥1 `Key: value` attestation line | **29** |
| **TERM 2** — of those, writing ≥1 attestation line as a LITERAL while a variable carrying that same value was IN SCOPE | **4** |

**The reported population of three was wrong, and this is the selector error the program keeps
re-finding.** The defect is in **four** files, not three — `cap10.sh` has it too, and it is the
*newest* link in the chain (`cap.sh` → `cap8.sh` → `cap9.sh` → `cap10.sh`). It was minted by T236
*after* T163 and T216 had each audited the chain. Each carries **two** such lines, not one:

```
cap.sh:97    Fineract-Platform-TenantId: gerege        <- shadowed by $T  (full-header)
cap.sh:100   Content-Type: application/json            <- shadowed by $CT (full-header)
cap8.sh:116  / :119    (same two)
cap9.sh:95   / :99     (same two)
cap10.sh:113 / :117    (same two)   <-- NOT named in the F-2 report
```

### The selector, checked before the conditions (P-76 addendum) — instrument `11-selector-check.py`

Instrument 10 narrows three times. Each narrowing was measured rather than assumed empty:

| narrowing | what it could hide | measured |
|---|---|---|
| A — suffix `.sh`/`.py` | an attestation writer with another suffix | 152 files of ANY suffix emit a literal `Key: value`; **14** are not `.sh`/`.py` — inspected, **all 14 are transcripts or markdown records OF output**, not writers. Real miss: 0. |
| B — file must contain `curl`/`psql` | a driver that writes the sidecar while a helper transports | **109** `.sh`/`.py` attestation writers have no `curl`/`psql`; **10** of them call a known transport helper. Named in the transcript; none writes a tenant line. |
| C — exact value match | a REDACTED literal, equally unfalsifiable | **4** — `Authorization: Basic <mifos:password>` in the same four files, while `$A` holds `Basic bWlmb3M6cGFzc3dvcmQ=`. Same defect, one header down. |

12 binary tracked files skipped; 0 tracked-but-absent.

### The tenant term specifically — instrument `12-tenant-term.py`, and the finding that matters

F-2 asks about scripts that attest the tenant **as a literal**. The more useful question is how many
capture scripts let you recover the tenant from their artefacts **at all**:

| | count |
|---|---|
| A. scripts that SEND a tenant selector to the oracle (header, `tenantIdentifier=`, or `psql -d fineract_*`) | **50** |
| B. of those, that ATTEST the tenant into a record at all | **5** |
| C. of those attesters, attesting it as a LITERAL (F-2 proper) | **5** |
| — attesting it DERIVED from the value in force | **0** |
| D. SEND a tenant and attest NO tenant line anywhere | **45** |

**Zero of fifty** tenant-sending capture scripts produce a tenant attestation derived from what was
sent. F-2 named the 4-file literal class; the 45-file **silent** class is strictly worse, because
there is no line to be wrong. The fifth attester is
`.softhouse/reviews/A2-10-probe/adjudicate-rmf-counterfactual.sh:27,34` — outside my scope, filed
as backlog B-3.

---

## 2. The fix

`.softhouse/capture/lib/wire_attestation.py` (new) and `.softhouse/capture/lib/oracle_send.sh` (new).

**The one rule: nothing writes an attestation line.** The attestation is DERIVED from curl's own
`--trace-ascii` record of the bytes it actually put on the wire. `oracle_send` passes the derivation
step no method, no path, no tenant, no auth, no content type — there is no argument it could be
given that would make it attest something unsent, because no value is typed twice.

Artefacts per capture: `NAME.reqhdr` (the redacted wire record) + `NAME.http` (the sidecar, derived
from it, carrying `request-headers-sha256:`) + the existing `.json` / `.status` / `.req` /
`.req.sha256`. A `verify` subcommand re-derives and compares.

**Why not T245's proposed `echo "$T"`.** Because `$T` is what the author *believed* would be sent.
Driven red in RED-DRIVE C, on the live oracle, curl 8.7.1 — with `-H "$T"` and a second `-H` for the
same header, **the wire carried BOTH** (`gerege` AND `default`); `echo "$T"` attests one value of
two. T245's item 2, taken alone, is insufficient, and the measurement says so.

**Redaction is derivable, not a placeholder.** `Authorization` becomes
`Basic <redacted sha256:2614d66f727c25bb>` over the exact sent bytes, so a changed credential
changes the sidecar. The legacy `Basic <mifos:password>` cannot.

**Money.** Neither file parses a monetary value. No `json.load`, no `float(` anywhere in either —
the T145 census stands at 224 unguarded sites and this task adds none. `Content-Length` is compared
as an integer byte count.

**Semantics carried over verbatim** from the `cap*.sh` chain because they are right: a non-2xx is an
observation not an error; a transport failure writes NOTHING under `out/` and NAMES pre-existing
artefacts (A2-5's D-2 fix); `--data-binary` not `-d` (T163); body snapshotted before the send;
`QUIT` in the trap (T216). The library is SOURCED and therefore sets **no** shell options — mutating
a caller's shell is its own fail-open — and contains **no pipeline at all**, so `pipefail` is moot
and every exit status is checked explicitly.

### Two defects the red-drives found in MY OWN work

1. **The capture-time self-check caught my verifier.** `oracle_send` verifies every sidecar against
   the header record written in the same breath. On the first run it FAILED — `send-header-block 1
   of 1` has no colon and my key matcher assumed one. The self-check is not decorative; it went red
   on its first real use.
2. **`--trace-ascii` WRAPS payload lines at 64 bytes.** Found by RED-DRIVE C shape 4: a 300-byte
   header value was attested as 51 bytes. Every chunk was being read as a separate header line, so
   the record was **corrupt for any header longer than ~64 bytes** — a long bearer token, for
   instance. Fixed by reassembling on the trace's OWN byte offsets: `o2 == o1 + len(c1)` is a
   continuation, `o2 == o1 + len(c1) + 2` is a new line (the CRLF), anything else REFUSES; the
   reassembled block is then checked against the byte count curl itself declared. Had I only tested
   the tenant header — 34 bytes — I would have shipped this.

---

## 3. Red-drive evidence

All under `.softhouse/capture/t250-tenant-attestation/`; instruments in `instruments/`, transcripts
in `transcripts/`, captured artefacts in `evidence/`.

### RED-DRIVE A — the sidecar TRACKS the send (`20-redA-…`, rc 0)
Same request, two tenants, live oracle, two writers.

| arm | tenant SENT | sidecar SAYS | |
|---|---|---|---|
| legacy | gerege | gerege | TRUE |
| legacy | **default** | **gerege** | **FALSE** |
| derived | gerege | gerege | TRUE |
| derived | default | default | TRUE |

The script FAILS if the legacy arm tracks the tenant — i.e. it refuses to certify a fix for a defect
it could not reproduce (P-22).

### RED-DRIVE B — a MISMATCH is DETECTED (`30-redB-…`, rc 0, 8/8 arms as expected)
Real capture (tenant `default`, POST /offices, HTTP 400), then the artefacts attacked:

| arm | attack | expected | got |
|---|---|---|---|
| 0 | positive control, untouched | 0 VERIFIED | 0 |
| 1 | sidecar edited to claim `gerege` when `default` was sent | 1 MISMATCH | 1 |
| 2 | header record edited, sidecar untouched | 1 MISMATCH | 1 |
| 3 | header record DELETED | 2 REFUSED | 2 |
| 4 | legacy literal sidecar, no derivation provenance | 2 REFUSED | 2 |
| 5 | body artefact swapped under a sidecar that hashed the original | 1 MISMATCH | 1 |
| 6 | Content-Length sent ≠ committed body byte count | 1 MISMATCH | 1 |
| 7 | **HONEST NEGATIVE** — whole set forged consistently | **0, NOT caught** | 0 |

Arm 7 is in the transcript deliberately. This module does **not** claim unforgeability: a consistent
forgery of the entire artefact set is caught by `MANIFEST.sha256` and the vectors' `capture_sha256`
pins, or not at all. Arm 4 is the load-bearing one — a legacy-shaped sidecar is REFUSED as
UNVERIFIABLE, never quietly passed. Default-deny.

### RED-DRIVE C — shapes the fix was NOT designed around (`40-redC-…`, rc 0)

| shape | result |
|---|---|
| 1 — same header twice | wire carried BOTH values; sidecar == an independent re-read of the wire. **Drives T245's `echo "$T"` red.** |
| 2a — `-H "Name:"` after a valued user header | **This shape corrected the file.** I asserted removal; MEASURED, the user's value SURVIVES. The assertion was wrong and is recorded as wrong, not deleted. |
| 2b — `-H "Accept:"` / `-H "User-Agent:"` | curl-generated headers vanish from the wire; the attestation correctly omits them. A rig printing its own belief about curl's defaults would attest two headers never sent. |
| 3 — body forged to look like a `=> Send header` block | did NOT reach the attestation; 1 block recorded. |
| 4 — 300-byte header value | initially attested as **51 bytes** — a real defect, now fixed and green at 300. |

---

## 4. VERDICT on T245's `OracleStamp.tenant` proposal — **NOT IMPLEMENTED**

T250's constraint: implement only if it can be done **without moving the store digest** AND
**without making any existing vector inadmissible**. T250 calls this "a gate, not a judgement call".
Measured by `50-oraclestamp-tenant-gate.py`, not argued.

**FACT 1 — both pins live INSIDE the pinned tree.** `git ls-tree -r HEAD .softhouse/vectors` = 62
files, of which `PIN.json` and `PIN-ledger.json` are two. Demonstrated, not asserted: mutating
`dec2_revision: 5 → 6` moves `PIN-ledger.json`'s blob hash
`30595a73…` → `b865732c…`, and a tree hash is computed over its members' hashes.

**FACT 2 — the corpus.** 59 vector files; **0** carry a `tenant` field; **59** do not. `Seam` is the
model T245 says to copy and it reads *"ABSENT REFUSES: default-deny, DEC-2 §4.10"*
[`admit.go:118–123`]. A `tenant` graded that way refuses all 59.

| route | store digest | admissibility | verdict |
|---|---|---|---|
| A. add field, default-deny, re-stamp all vectors | **MOVES** (59 blobs change) | clean | violates (i) |
| B. add field, default-deny, no re-stamp | unmoved | **all 59 REFUSE** | violates (ii) |
| C. add field, grade permissively | unmoved | clean | **violates the point** |

**There is no route that satisfies both.** Route C is not a loophole: the pin must carry the
permitted value, and both pins are inside the tree, so even C moves the digest the moment it names a
tenant. And T245's own words apply — *item 1 without item 2 is COSMETIC*. A field graded permissively
would be a **new P-45 artefact**: committed, read, grading nothing. Shipping that under the banner of
fixing a fail-open would be the defect re-committed.

**What would be required to do it** (all three, in one commit, as a task that owns the store):
1. authority to move `13b8342e…` — every BAR pins it, so the pin and its consumers move together;
2. a single commit re-stamping all 59 vectors with `tenant`, both pins with the permitted value, and
   the `OracleStamp` field + default-deny grading in `admit.go` — `PIN-ledger.json`'s own `_note`
   already contemplates exactly this shape of one-commit re-stamp;
3. **item 2 first, or it is cosmetic** — the field must be fed by a capture rig that derives the
   tenant from the wire. That rig now exists (`oracle_send.sh`); nothing is wired to it yet.

Filed as gate **G-T250-1**.

---

## 5. What I did NOT touch, and why (P-40 — counted, not implied)

| skipped | count | why |
|---|---|---|
| `.softhouse/capture/tierA-a2/cap.sh`, `cap8.sh`, `cap9.sh`, `cap10.sh` | **4 files, 8 defective lines** | T164 owns the directory this fire, AND T114 binds: all four produced committed evidence and are pinned byte-for-byte in `MANIFEST.sha256`. NOT edited, NOT run, NOT superseded in place. |
| committed `.http` sidecars under `tierA-a2/out/` | ~450 | **Deliberately NOT retro-stamped.** See §6. |
| `.softhouse/conformance.sh` | 1 | T253 owns it. Read only. |
| `.softhouse/capture/t229-g8-site3/` | 1 dir | T259 owns it. |
| `.softhouse/vectors/**` | 62 files | Digest must not move. Read only. |
| `nexus/**` | — | The `OracleStamp` change is refused above; nothing edited. |
| `reviews/A2-10-probe/adjudicate-rmf-counterfactual.sh` | 1 file, 2 lines | Literal tenant attestation, outside `files_hint`. Backlog B-3. |
| non-`.sh`/`.py` regex matches | 14 | Inspected: all transcripts/markdown, not writers. |
| attestation writers with no `curl`/`psql` | 109 (10 helper-calling) | Named in the transcript; none writes a tenant line. |
| binary tracked files | 12 | Not text. |

---

## 6. Historical sidecars: NOT re-stamped, and what would authorise it

**They must NOT be re-stamped, and I did not.** The existing sidecars are weak-but-honest: they say
`gerege`, they were produced by a writer that would have said `gerege` regardless, and T245
established by three independent routes — decisively by database contents — that `gerege` is in fact
what those captures ran against. Rewriting them now to *look* derived would replace a weak honest
record with a strong-looking invented one, which is strictly worse: it would assert wire-derivation
for exchanges whose wire records **do not exist and cannot be recovered**. `T114` binds
independently: a file that produced committed evidence stays byte-identical.

**What would authorise a re-stamp — all four, and nothing less:**
1. **RE-CAPTURE, not re-stamp.** The only honest way to give those observations a derived
   attestation is to take them again through a rig that records the wire. A `.reqhdr` for a 2026-08
   exchange cannot be manufactured in 2026-08-22 from anything but the exchange itself.
2. The oracle at the **pinned commit** `426a2354…` with the tenant state those captures assumed —
   otherwise the re-capture is a different observation wearing the old name.
3. A task that **owns the vector store**, because 12 `capture_sha256` / `request_capture_sha256`
   values across the six ledger vectors pin the current bytes; re-capturing moves them and therefore
   moves `13b8342e…`.
4. `MANIFEST.sha256` re-derived in the same commit, and the superseded artefacts kept, not deleted —
   the old capture is still the evidence for every claim already made from it.

Absent all four: **leave them alone and cite T245's leg 2.** Filed as gate **G-T250-2**.

---

## 7. BAR — this host, presence before value (P-83)

Invoked `bash .softhouse/conformance.sh` (exit 3 = wrong interpreter; not seen) with the go-env
exported. Transcript: `transcripts/90-bar.txt`.

1. **PROBE LINE PRESENCE, tested FIRST** — `/usr/bin/grep -c 'probe = '` → **1**, exit 0. PRESENT.
2. **Probe VALUE** — `reference oracle (https://localhost:8443/…/actuator/health) probe = up`.
3. **VERDICT: PASS (exit 0)** — 46 parity vectors, 7884 cells compared.

| assertion | required | measured |
|---|---|---|
| loanschedule parity | 46 | **46** PASS / 0 FAIL |
| loanschedule cells graded | 7884 | **7884** |
| ledger parity | 4 | **4** PASS / 0 FAIL |
| ledger oracle-refusal | 2 | **2** PASS / 0 FAIL |
| ledger money cells | 21 | **21** |
| refused | 0 | **0** |
| inadmissible | 0 | **0** (+ ledger inadmissible 0) |
| harness errors | 0 | **0** (+ ledger harness errors 0) |
| invariant violations | 0 | **0** |
| invariant assertions NOT RUN | 0 | **0** |
| census pins == pinned | all 9 | **9/9**, zero mismatches (+ fail-open frontier 11 == pinned 11) |

**An earlier BAR run on this branch exited 2, and it was my fault.** RED-DRIVE C shape 3 writes a
deliberately malformed request body; `oracle_send` names every body artefact `NAME.req`; the
wire-float round-trip guard sweeps every `*.req` under `.softhouse/capture/` and REFUSED it as
unparseable. **The guard is right** — a request body that is not a request body cannot be certified
clean — so the fixture was renamed out of the graded population (kept, not deleted, with the reason
in the instrument) rather than the guard being worked around. Baseline
`bar-baseline-20260822-060013.log` exits 0, confirming this was mine and not pre-existing.

---

## 8. Backlog

- **B-1 (MEDIUM).** `oracle_send` names every body artefact `NAME.req`, and the wire-float guard
  requires every `*.req` under `.softhouse/capture/` to parse as JSON. Any future capture with a
  legitimately non-JSON body (form-encoded, CSV upload, multipart) will trip a HARD guard. Neither
  side is wrong; the naming convention and the guard's population need reconciling.
- **B-2 (MEDIUM).** 45 scripts send a tenant to the oracle and attest no tenant at all (§1 term D).
  The literal class is 4; the silent class is 45. Worth a task.
- **B-3 (LOW).** `reviews/A2-10-probe/adjudicate-rmf-counterfactual.sh:27,34` — literal tenant
  attestation, outside T250's scope.
- **B-4 (LOW).** The redaction class: `Authorization: Basic <mifos:password>` is hard-coded in all
  four `cap*.sh`. `oracle_send` fixes the shape going forward; the legacy files are T114-frozen.
- **B-5.** Nothing is WIRED to `oracle_send.sh` yet. It is a proven successor shape with no caller.
  The next capture task in a directory not frozen by T114 should adopt it; adopting it inside
  `tierA-a2/` means minting `cap11.sh`, which is T164's call, not mine.

## 8b. Re-measurement at finish (P-69)

Instruments re-run after commit, so they now measure a population that includes T250's own files.
Every delta is this task's own artefacts; full accounting in
`.softhouse/capture/t250-tenant-attestation/transcripts/99-FINAL-REMEASURE-NOTE.md`.

| measure | start `a71c140` | finish `b4d170d` |
|---|---|---|
| TERM 1 | 29 | 33 |
| TERM 2 | 4 | **5** — instrument `10-population.py` matches its OWN calibration fixture |
| tenant senders / literal / derived | 50 / 5 / 0 | 56 / 9 / 0 |

The self-match was **not** excluded. A self-exclusion would give the instrument a blind spot aimed at
itself, which is the shape this task removes; the honest report is "5, of which 1 is the positive
control". The +4 literal attesters are RED-DRIVE A's verbatim reproduction of the defective writer —
a detector that failed to flag it would be failing at its job.

**Instrument 12 UNDERSTATES the fix, stated plainly.** It detects attestation *by emission*;
`oracle_send.sh` emits nothing and derives instead, so it is invisible to that instrument and sits in
bucket D. "Attested DERIVED = 0" is a statement about what instrument 12 can see (P-66), not about
the world. The derived sidecars exist under `evidence/`, each carrying `attestation-derivation:`.
Backlog B-6: count derived attestations from that marker in the produced `.http` artefacts, not from
emission sites in scripts.

- **B-6 (LOW).** Instrument 12 cannot see a derived attestation; see above.

## 9. Pattern candidate

**"Deriving an attestation from the variable you *sent* is not the same as deriving it from what
went on the wire."** T245 proposed `echo "$T"`; measured, that still attests a belief — curl sent
two tenant headers where `$T` held one, and dropped generated headers `$T` knew nothing about. The
weaker fix would have passed every test written for it. Corollary, from shape 4: **a fix tested only
on the value that motivated it is untested** — the 34-byte tenant header hid a parser bug that a
300-byte header exposed immediately.
