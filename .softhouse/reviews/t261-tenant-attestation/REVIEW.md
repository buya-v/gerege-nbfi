# T261 — independent review of T250 (`softhouse/T250-tenant-attestation` @ `d2b5772`)

Reviewer: T261, isolated worktree `agent-aa1570a5ac5acb88a`, branch
`softhouse/T261-review-tenant-attestation`. I did not write what is reviewed.
Reference oracle (Fineract) **REACHABLE** at `https://localhost:8443` throughout —
`actuator/health` → `{"status":"UP"}`; every capture below is a real exchange with it.
curl 8.7.1 (x86_64-apple-darwin25.0), go1.26.6.

**VERDICT: MICRO-FIX.**
The claim set is substantially TRUE and the load-bearing measurements reproduce
exactly. Four tamper shapes T250 did not design around get past its verifier, one
of them a fail-open in the module that sells itself on default-deny; and one of the
two library files still carries a claim its sibling explicitly measured FALSE. None
of that is reachable today — **nothing calls the new code** — which is why this is
a micro-fix and not a rejection. The ruling on merging an uncalled successor is in
§9.

---

## 0. Scope of MY search, and what I did not do (P-66/P-70/P-40)

**Engine.** `python3` `re` only for every sweep. **No `grep`, no `rg`, no `git grep`**
in any instrument I wrote (P-75). Population always from `git ls-tree -r --name-only <tree>`
or `git ls-files`; a non-zero git exit **ABORTS (exit 5)** in every instrument, so an
error can never be reported as a zero. Every sweep instrument calibrates on a
POSITIVE *and* a NEGATIVE arm and **ABORTS (exit 4)** if either disagrees. My
population instrument did abort once, on a badly-written calibration fixture of my
own; the fixture was repaired and the abort is what caught it.

**Where I looked.** `git ls-tree -r a71c140` (T250's base) — 5,215 tracked files, 918
`.sh`/`.py`; and `git ls-tree -r d2b5772` — 5,345 files, 927 `.sh`/`.py`. Trees
materialised to disk and read byte-for-byte.

**Counted skips.** Untracked files; other checkouts; `/Users/buv/fineract`; non-`.sh`/`.py`
suffixes except where explicitly widened below; `nexus/**` beyond `admit.go`/`vector.go`;
the 8 `.status`/`.sha256` sidecars of T250's own arms.

**A contamination I caused and am reporting rather than hiding.** I first extracted
both trees *inside* the worktree, under `.softhouse/reviews/.../scratch/`. The BAR's
narrow-catch guard walks the whole repository for `.java` and refused on the extracted
`Capture*.java` copies — **my** fault, not T250's. Trees were moved to `/tmp` and the
BAR re-run. Do not extract a repo tree inside this repo.

---

## 1. THE POPULATION — independently re-derived. T250 is RIGHT: it is FOUR.

I wrote my own sweep (`instruments/t261-population.py`) **deliberately wider** than
T250's on both axes, so an undercount would surface:

* emitters — `echo` / `printf` / `print` **and also** `<obj>.write(` **and heredoc
  body lines**. T250's `ATTEST_RE` matches only `echo|printf|print`, so a sidecar
  written by `cat <<EOF` or `fh.write("Key: value\n")` is invisible to it.
* oracle contact — `curl` | `psql` | a literal `localhost:8443`.

Calibration: 5 arms (echo-literal +1, echo-from-var 0, heredoc +1, py-write +1,
py-write-from-var 0) — all agreed; instrument discriminates.

| term | T250 | T261 (wider selector) | verdict |
|---|---|---|---|
| TERM 1 — oracle-talking scripts writing a `Key: value` attestation | 29 | **45** | see F-8b |
| **TERM 2 — of those, a LITERAL while a variable held the value** | **4** | **4** | **CONFIRMED, identical rosters and identical line numbers** |

My TERM 2, produced by different code:

```
.softhouse/capture/tierA-a2/cap.sh    :97  Fineract-Platform-TenantId: gerege  <- $T  (full-header)
.softhouse/capture/tierA-a2/cap.sh    :100 Content-Type: application/json      <- $CT (full-header)
.softhouse/capture/tierA-a2/cap8.sh   :116 / :119   (same two)
.softhouse/capture/tierA-a2/cap9.sh   :95  / :99    (same two)
.softhouse/capture/tierA-a2/cap10.sh  :113 / :117   (same two)
```
[`evidence/10-t261-population-base.txt`]

I also re-ran T250's own instrument 10 against the same tree with only its population
source repointed: **RATE 4 / 29**, byte-identical roster. [`evidence/11-repro-t250-inst10-base.txt`]

**`cap10.sh` is real and it is the newest link.** Read directly:
`cap10.sh:79,82` sends `-H "$A" -H "$T" -H "$CT"`; `cap10.sh:113/114/117` echoes the
three values as literals. `env.sh:5-7` defines `A`, `T`, `CT` with exactly those values.
[`evidence/12-cap-defect-lines.txt`]. `git log --diff-filter=A`: `cap10.sh` was added by
**`994905c` — "T236: cap9.sh:49's P-40 residual closed by minting cap10.sh, not editing
in place"**, and `cap9.sh` by `d1a9587` (T163). So the defect was **minted after the
audits that walked the chain**, into a file created specifically to close an audit
residual.

**The redaction class is also exactly 4**, one line per file:
`cap.sh:98`, `cap8.sh:117`, `cap9.sh:96`, `cap10.sh:114` — all
`echo "Authorization: Basic <mifos:password>"` while `$A` holds
`Basic bWlmb3M6cGFzc3dvcmQ=`. Confirmed.

### F-1 (MEDIUM) — a pattern worth naming in its own right

A defect **added after two audits**, by a task whose stated purpose was closing an
audit residual, in a file minted rather than edited *precisely so the audit trail
stayed clean*. `cap.sh → cap8.sh → cap9.sh → cap10.sh` is four generations of
copy-forward, and the literal attestation survived every one. The remedy is not
another audit of the same chain: it is that **the chain must not be extended again
without adopting a derived attestation**, because minting `capN+1.sh` from `capN.sh`
demonstrably carries the defect forward intact. T250's B-5 half-says this; it should
be said outright to the driver.

---

## 2. THE TENANT SPLIT — verified, and it is the bigger half. Say so plainly.

T250's instrument 12, repointed only at the tree: **A=50, B=5, literal=5, DERIVED=0,
D(silent)=45** — reproduced exactly. [`evidence/14-repro-t250-inst12-base.txt`]

My independent, wider instrument (`instruments/t261-tenant-term.py`, 5 calibration
arms including a heredoc positive): **A=52, B=6, literal=6, DERIVED=0, D(silent)=46**,
with the arithmetic check `B + D == A` asserted. [`evidence/13-t261-tenant-term-base.txt`]

**The load-bearing figure is confirmed twice by different code: `DERIVED = 0`.**
Not one capture script in the tree recovers the tenant from the value that was in
force. And the silent class is an order of magnitude larger than the literal class.

**My answer to the framing question, for the driver, not for a handoff appendix:**
> **The literal that cannot disagree was the SMALLER half of the problem.**
> Four scripts write a tenant line that is always `gerege`. **Forty-five to
> forty-six send a tenant and write no tenant line at all** — and for those there is
> no artefact to be wrong, no line to grep, and nothing that could ever be driven
> red. T245's F-2 named the visible 4. The invisible 45 is the finding, and T250
> filed it as backlog item **B-2 (MEDIUM)**, which under-weights it. It should be a
> task, and it should be scheduled ahead of any further work on the four.

### F-2 (MEDIUM) — instrument 12 is uncalibrated and has a measured blind spot

`12-tenant-term.py` has **no calibration arm at all** (see §8), and its emitter regex
is `(?:echo|printf|print)`, so a Python `.write()` attestation is invisible. A real
instance exists in the tree it swept:

```
.softhouse/reviews/A2-10-probe/poison-d2-transport-modes.py:30-31
    open(d + "/out/POISON.http", "w").write(
        "POST /glaccounts\nFineract-Platform-TenantId: gerege\n" ...)
```

T250's instrument classifies that file as **SILENT (bucket D)**. Within *T250's own
50-file sender population*, the honest split is therefore **6 attesters / 44 silent,
not 5 / 45.** The headline number in the handoff was produced by the one instrument
in the set that calibrates on nothing. T250 disclosed a *different* limitation of
instrument 12 (§8b B-6: it cannot see a derived attestation); it did not disclose
this one.

### F-3 (MEDIUM) — the "5th attester", filed as backlog B-3, is a poison fixture

T250 files `.softhouse/reviews/A2-10-probe/adjudicate-rmf-counterfactual.sh:27,34` as
"literal tenant attestation, backlog B-3". Read in place, line 27 is
`echo "T='Fineract-Platform-TenantId: gerege'"` — it is **writing an `env.sh` line for
a temp fixture**, not attesting a capture — and line 34 seeds a deliberately-poisoned
`POISON.http` in `$(mktemp -d)` so that a *detector* can be driven red against it.
Same for `poison-d2-transport-modes.py`. Neither is a capture rig and neither produces
committed evidence.

**Consequence:** the count of capture rigs that attest a real tenant into committed
evidence is **4, not 5**, and B-3 as filed points a future task at a red-drive
fixture. Both classifiers — T250's and mine — over-count here; mine over-counts by
two. The number to carry forward is 4.

---

## 3. RED-DRIVE A — reproduced against the live oracle, independently

Not a re-run of `20-redA` (P-76). I reconstructed the legacy writer from the frozen
source lines I read myself and wrote the comparison from scratch
(`instruments/t261-redA-independent.sh`), with a P-22 refusal arm: if the legacy arm
*tracks* the tenant, the script exits 3 and certifies nothing.

```
legacy   arm: SENT gerege    HTTP 200   SIDECAR SAYS gerege    -> TRUE
legacy   arm: SENT default   HTTP 200   SIDECAR SAYS gerege    -> FALSE
derived  arm: SENT gerege    HTTP 200   SIDECAR SAYS gerege    -> TRUE
derived  arm: SENT default   HTTP 200   SIDECAR SAYS default   -> TRUE
```
[`evidence/20-redA.txt`]

**The defect reproduces on this host, live, at HTTP 200 on both arms** — both tenants
are real and both requests genuinely completed. The derived writer tracks the send on
both. T250's Arm A is TRUE.

T250's *committed* redA/redB artefacts are also real, not synthesised: their
`.json` bodies are byte-identical to what the oracle returned to me
(`[{"id":1,"name":"Head Office",...}]`), and their sidecars verify `rc=0` against
their own records when I run the verifier over them.

---

## 4. RED-DRIVE B — I attacked the detector. It misses four shapes.

`instruments/t261-redB-attack.sh`. Eleven attacks, none of them in T250's arm set.
Every attack starts from a **fresh live capture taken in this run**. The harness
calibrates: an untouched positive control must verify `rc=0` or the run ABORTS (exit 4)
rather than scoring against a broken baseline. It did verify.

```
[DETECTED] A1  duplicated header (different values): one copy removed from sidecar   rc=1
[MISSED  ] A2  body swapped (same length) + `body-sha256:` line deleted              rc=0  <-- GAP
[DETECTED] A3  body truncated + all three body assertions deleted                    rc=1
[MISSED  ] A4  sidecar header lines REORDERED vs the wire                            rc=0  <-- GAP
[DETECTED] A5  wire header literally named `body-bytes` tampered in sidecar          rc=1
[MISSED  ] A6  invented `content-length-crosscheck: MATCH (99999 bytes)` appended    rc=0  <-- GAP
[DETECTED] A7  colon-bearing header value (`X-…: alpha: beta; gamma`) tampered       rc=1
[DETECTED] A8  sidecar header name case-folded                                       rc=1
[DETECTED] A9  record swapped for a DIFFERENT real request's record                  rc=1
[MISSED  ] A10 RESPONSE body swapped for another capture's response                  rc=0  <-- GAP
[DETECTED] A11 `request-headers-sha256:` line deleted from sidecar                   rc=1
SCORE: 7 detected / 4 missed of 11
```
[`evidence/30-redB-attack.txt`]

Plus, from red-drive C, a twelfth:
```
[MISSED] duplicated IDENTICAL header, one of the two copies deleted from the sidecar rc=0  <-- GAP
```
[`evidence/40-redC-wrap.txt`]

### F-4 (HIGH) — `verify` checks only the assertions that are PRESENT

`cmd_verify` requires exactly two things: the `attestation-derivation:` tag, and a
`request-headers-sha256:` line. **Everything else is checked only if it happens to be
there.** `body-sha256:` and `body-bytes:` are matched with
`for line in side_lines: if line.startswith("body-sha256: ")` — delete the line and the
loop body never runs, and nothing notices the absence.

Measured (A2): delete `body-sha256:` from the sidecar, replace `post.req` with
different bytes **of the same length**. `body-bytes` still matches, `Content-Length`
still matches, the header record is untouched → **`VERIFIED`, exit 0.** The committed
request body is now a forgery and the module says the artefact set is sound.

This is a fail-open, and it sits inside the module whose own docstring says
*"Default-deny: absence of evidence is not evidence."* For the header record that is
true; for the body it is exactly inverted — absence of the assertion is treated as
absence of anything to check. **This is the same shape T250 exists to remove**, one
artefact down.

*Repair (mechanical):* when `--req` is supplied, `body-sha256:` and `body-bytes:` must
be REQUIRED and their absence must be a `Refuse`; likewise
`content-length-crosscheck:` when the record carried a `Content-Length`.

### F-5 (MEDIUM) — multiplicity and order are not checked

Check (2) is set membership in both directions (`if line not in side_lines`,
`if line not in rec_lines`). So:

* **A4** — swap two header lines in the sidecar → `rc=0`. The sidecar can state a
  header order the wire did not have.
* **dupid** — send `Fineract-Platform-TenantId: default` **twice**; the record and the
  sidecar each carry it twice; delete one copy from the sidecar → `rc=0`. The sidecar
  now says one tenant header went out where two did.

This is not academic. **T250's own red-drive C shape 1 is the discovery that curl
sends both copies and the server picks** — I reproduced it (§6). Which tenant headers
went out, how many, and in what order is precisely the fact this sidecar exists to
record, and the verifier cannot detect a sidecar that misreports it.

*Repair:* compare `rec_lines` against the sidecar's header lines as an **ordered
sequence**, not as sets.

### F-6 (MEDIUM) — the RESPONSE is entirely unattested, and that limit is not stated

`verify` never opens `NAME.json` or `NAME.status`. Swap the response body for another
real capture's (A10) → `rc=0`. The sidecar carries no response digest and
`oracle_send` computes none.

For a *capture* rig this is the material half: a golden vector is graded on the
oracle's answer, not on the request. The module's "WHAT IS AND IS NOT CLAIMED" block
enumerates request-side tampering only and never says the response is out of scope;
the handoff §2 lists `.json`/`.status` among the artefacts without saying they are
unattested. **A reader meeting this module will reasonably think the capture is
attested. Only the request is.**

*Repair (documentation at minimum):* add the response to the NOT CLAIMED block; better,
have `derive` emit `response-sha256:` / `response-status:` and have `verify` check them.

### F-7 (LOW–MEDIUM) — `known_keys` is an exemption list, and invented lines ride it

Any sidecar line whose key is one of the ten `known_keys` is `continue`d past the
"ASSERTS a line that was NOT sent" check. A6 appends
`content-length-crosscheck: MATCH (99999 bytes)` → `rc=0`. A reader of the sidecar is
told a crosscheck matched at a byte count that is fiction. (Conversely A5 shows a
*real* wire header named `body-bytes` is still caught, because it is in the record.)

*Repair:* every known key that is present must be *validated*, not merely skipped.

### Arm B7 — the honest negative. Adequately disclosed. No finding.

The whole-set consistent forgery is stated in **two** places a reader actually meets:
the module docstring's *"Tamper both consistently → you have forged a matched
artefact set … this module does not and cannot claim unforgeability"*, and handoff
§3 arm 7. That is disclosure at the point of use, not buried in a transcript. **I
accept it.** Contrast F-6, which is a limit of the same kind and is stated nowhere.

---

## 5. THE WRAP BUG — genuinely fixed, and checked where it could break

The most dangerous thing in the diff is a corrupt record that still looks like
evidence. T250 tested at 300 bytes. I swept the **wrap boundary itself**, because a
64-byte chunking bug is most likely to be wrong at 63/64/65 and 127/128/129, not at 300.
Ground truth is the exact bytes handed to `-H`. Seventeen live captures:

```
len   1   10   60   61   62   63   64   65   66  127  128  129  200  300 1000 4000
      EXACT for every one; verify rc=0 for every one
plus a 360-byte value full of colons and spaces ('x: y; ' x60) -> EXACT
```
[`evidence/40-redC-wrap.txt`]

**The offset-chaining reassembly is correct across the boundary.** I traced why: curl's
trace-ascii writer emits `i += c + 2` when it consumes a CRLF and `i += 64` when it
wraps, which is exactly the `o2 == o1 + len(c1)` / `o2 == o1 + len(c1) + 2`
discrimination in `reassemble()`, and the `total != declared` check closes the case
where the chain is plausible but wrong. This is the strongest work in the task and it
holds. T250's own note — *a fix tested only on the value that motivated it is
untested* — is the right lesson and it earned it.

Two adjacent checks, both clean:
* **multibyte body** — 58 bytes / 35 characters; `Content-Length: 58`,
  `content-length-crosscheck: MATCH (58 bytes)`, committed `.req` 58 bytes. Byte-exact,
  not character-counted. Truncating it mid-multibyte **with all assertions intact** is
  caught three ways (sha, byte count, Content-Length). It is only missed when the
  assertion is deleted — F-4, not a separate defect.
* **CRLF injected into a header value** — no header smuggling; the record shows one
  line, `X-T261-Inj: safe.X-T261-Evil: injected`, with the control byte rendered as
  `.`. The attestation is faithful to what went out.
* **empty tenant** (`-H "Name;"` alongside a valued one) — capture succeeds, sidecar
  records what actually went. No warning is emitted, but nothing false is asserted.

**T245's `echo "$T"` is genuinely driven red.** Two `-H` for the same header, live:
```
Fineract-Platform-TenantId: default
Content-Type: application/json
Fineract-Platform-TenantId: gerege        <- both on the wire, HTTP 200
```
`$T` holds one value; the wire carried two. T250's refusal of item 2 taken alone is
correct and measured.

---

## 6. F-8 (MEDIUM) — the two library files contradict each other on a measured fact

`wire_attestation.py`, docstring, item 1 — **corrected**:
> "the SAME header given twice is sent TWICE. Curl **does not de-duplicate and does not
> let the later value win**"

`oracle_send.sh`, header comment — **uncorrected**:
> "Curl's argument grammar has at least two shapes where that is false — **a later
> `-H` for the same header wins**, and `-H "Name:"` REMOVES the header rather than
> sending an empty one."

My live capture (above) proves `oracle_send.sh` wrong: both values went out, in
argument order. The second clause is also the one `wire_attestation.py` explicitly
corrects — *"It does NOT remove an earlier user-supplied header of the same name — this
file claimed it did, and the measurement said otherwise."* — stated flatly in
`oracle_send.sh` without the qualification.

**T250's claim that two docstring assertions were measured false and corrected in
place, marked as corrections, is TRUE of `wire_attestation.py`.** [verified: the
"this file claimed it did, and the measurement said otherwise" clause is present, and
handoff §3 shape 2a records the assertion as wrong rather than deleting it — good
practice.] **The correction was not carried to the sibling file that ships with it.**
A committed library header that is read, is authoritative-looking, and is false is the
P-45 class in miniature, inside the task that exists to remove it.

---

## 7. THE `OracleStamp` REFUSAL — re-derived, and I uphold it

I re-derived both facts rather than reading them.

**FACT 1 — both pins are inside the pinned tree.** `git ls-tree -r d2b5772
.softhouse/vectors` → **62 entries**: 59 vector `.json`, `README.md`, `PIN.json`,
`PIN-ledger.json`. Blob-hash mutation reproduced exactly:

```
orig  PIN-ledger.json                      30595a7364db38f3ac55f1a1a1f6ed50f2260c82
mut   dec2_revision 5 -> 6                 b865732ccb4e3528b5f4962eb918885adfe0a123
```
Matching T250's `30595a73… → b865732c…` to the stated prefixes. A tree hash is computed
over its members' hashes, so a pin that names a tenant moves `13b8342e…`. **FACT 1 holds.**

**FACT 2 — 59 / 0.** My census (`instruments/t261-vector-tenant-census.py`, parsing every
document with `parse_float=str` so no monetary literal ever becomes a binary float, and
calibrated on a positive and a negative fixture): **59 vector files, 0 carrying a
`tenant` field at any depth, 0 unparseable.** Both PIN files also carry none.
[`evidence/50-vector-census.txt`]

**The `Seam` citation is accurate to the line.** `ledger/conformance/admit.go:118-123`:
```go
switch v.Oracle.Seam {
case "ledger_rest_admin", "ledger_rest_posting", "ledger_db_readback":
default:
    add("oracle.seam %q is not one of G-01's three (…). ABSENT REFUSES: default-deny, DEC-2 §4.10", …)
```
An empty string falls to `default:` and refuses. `type OracleStamp struct` in
`vector.go` carries `FineractCommit`, `Seam`, `CapturedAt` — **no tenant field**, as
stated.

**Verdict on the refusal: UPHELD.** Route A moves the digest (59 blobs change); Route B
makes all 59 inadmissible; Route C ships a field that grades nothing, which is a new
P-45 artefact — and the task exists to remove one. There is no route satisfying both
constraints, and T250 measured that instead of asserting it, including a self-abort in
its instrument if the mutation *failed* to move the blob hash ("instrument is broken").
That is the right shape for a refusal. A well-argued NOT-DONE with a stated cost was
permitted, and this one is evidenced.

### F-9 (LOW) — the §4 table contradicts the prose two lines below it

The table says Route C: store digest **"unmoved"**. The prose says *"even C moves the
digest the moment it names a tenant."* Both cannot be read off the same row, and the
table is what a reader skims. Fix one.

---

## 8. NO RETRO-EDITING — verified. Purely additive.

`git diff --name-status main...softhouse/T250-tenant-attestation`:
**130 files, all `A`. 0 `M`, 0 `D`.**

The T114-frozen files are byte-identical at every revision that matters:

| file | a71c140 | HEAD | d2b5772 | main | |
|---|---|---|---|---|---|
| `tierA-a2/cap.sh` | `6bfddf8d…` | same | same | same | IDENTICAL |
| `tierA-a2/cap8.sh` | `585c3eb8…` | same | same | same | IDENTICAL |
| `tierA-a2/cap9.sh` | `e0a4d322…` | same | same | same | IDENTICAL |
| `tierA-a2/cap10.sh` | `9e9361293…` | same | same | same | IDENTICAL |
| `tierA-a2/env.sh` | `1d4d01fe…` | same | same | same | IDENTICAL |

`.softhouse/capture/tierA-a2/MANIFEST.sha256` differs at `main` only, because **T164
(`f084819`) landed there after T250 branched** — which independently confirms T250's
stated reason for not touching the directory. T250 adds no file under `tierA-a2/`, so
there is no MANIFEST conflict.

**Vector-store digest — read live at four points:**

| ref | `git rev-parse <ref>:.softhouse/vectors` |
|---|---|
| `a71c140` (T250 base) | `13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d` |
| `d2b5772` (T250 tip) | `13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d` |
| `main` | `13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d` |
| my HEAD | `13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d` |

**UNMOVED.** The §6 reasoning against re-stamping historical sidecars is right on the
merits: a `.reqhdr` for an exchange whose wire record does not exist cannot be
manufactured, and replacing a weak-honest record with a strong-looking invented one is
strictly worse. The four conditions filed as G-T250-2 are the right conditions, and
condition 1 (re-CAPTURE, never re-stamp) is the load-bearing one.

---

## 9. THE MALFORMED FIXTURE, AND THE BAR

### The fixture: genuinely outside the graded population — and I checked both ways

The wire-float round-trip guard's population is **derived**, not named:
`derive(root)` recursively walks `.softhouse/capture/` and takes (a) any `*.json` under a
directory named `req`, (b) any `*.req`.

* **The guard is byte-identical to `main`:** blob `6d67ea828f997db1c5d4bc58b35fa1f0a8ea2087`
  at both `main` and `d2b5772`. **Not weakened, not exempted, not edited.**
* **Where the fixture ended up:**
  `.softhouse/capture/t250-tenant-attestation/evidence/redC/out/inject.req.NOT-JSON-BY-DESIGN.txt`
  — `derive()` says `in-population=False`. Its sibling
  `evidence/redC/req/injection.txt` sits *in* a `req/` dir but is `.txt`, also outside.
* **Counter-check, because "renamed out" means nothing unless the rename mattered:**
  I copied the fixture back to `…/out/T261PROBE.req` and asked the guard's own
  `derive()` again → **reached it**, and it **does not parse** (`JSONDecodeError`).
  So the guard genuinely would have refused it, and the rename genuinely moved it out.
  Probe removed; population back to 393.
* **All 10 T250 files that ARE inside the population parse as JSON** — the nine
  `redB/**/probe.req` and `redB/req/bad-office.json` (which is bad to Fineract, not
  malformed).
* Running the guard over T250's tree: **exit 0, clean**, 408 documents / 9,549 tokens.

[`evidence/60-guard-on-t250-tree.txt`, `evidence/61-fixture-location.txt`]

**T250's account of this is honest and its choice was the right one** — it moved the
fixture rather than working around the guard, and it named the tension in the
instrument itself (`40-redC…sh:198-200` states that the guard REFUSES and that this
produces `a HARD guard failed. EXIT 2` on this host).

#### F-10 (LOW) — the mitigation is a filename, and the fixture still lives in `capture/`

A file whose whole purpose is to be malformed still sits under `.softhouse/capture/`,
excluded only by its suffix. Any future guard that selects by directory rather than by
suffix, or any rig that copies `*.txt` bodies, re-arms it. Its sibling
`inject.req.sha256.txt` names a `.req` artefact that no longer exists under that name.
Structural fix: move deliberately-malformed fixtures out of `.softhouse/capture/`
entirely. (T250 filed the naming/population tension as B-1; the *location* is the part
still open.)

### The BAR — probe PRESENCE first, then value (P-83)

Run by me, on **my worktree + T250's 130 files materialised** — i.e. the tree that
would exist if this merged. `instruments/t261-bar.sh` tests the probe line's PRESENCE
before reading any value and exits 5 if it is absent, so a missing probe can never be
read as a value.

```
STEP 1  lines containing 'probe = ' : 1   -> PRESENT
STEP 2  conformance: reference oracle (https://localhost:8443/…/actuator/health) probe = up
STEP 3  VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle,
        7884 cells compared.
        fail-open frontier 11, pinned at 11; frontier == pinned (all 11 rows, by path)
        refused 0 | inadmissible 0 (+ ledger 0) | harness errors 0 (+ ledger 0)
        invariant violations 0 | invariant assertions NOT RUN 0
conformance.sh EXIT = 0
```

**Exemption census, all nine pins, zero mismatches:**
```
exempted assertions (graded)     = 4 == pinned 4
declared exemptions (loaded)     = 4 == pinned 4
GROUNDED                         = 4 == pinned 4
UNDETERMINED-ON-THE-RECORD       = 0 == pinned 0
UNGROUNDED                       = 0 == pinned 0
LEDGER declared exemptions       = 0 == pinned 0
LEDGER parity vectors            = 4 == pinned 4
LEDGER oracle-refusal vector     = 2 == pinned 2
LEDGER money cells compared      = 21 == pinned 21
```
[`evidence/92-bar-merged-T250.txt`, full log `evidence/90-bar.txt`]

Store digest at finish: `13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d` — **UNMOVED.**

### F-11 (HIGH, **NOT T250's** — escalate to the driver as its own task)

**The BAR's verdict depends on a file in shared `/tmp`, and I hit it.**

One of my BAR runs on exactly this diff exited **2**, with:
```
THE FAIL-OPEN FRONTIER IS NOT THE PINNED FRONTIER (- pinned, + measured):
+TIER1 .softhouse/capture/t234-sweep-instrument-audit/instruments/02-escape-matrix-fix.sh
-TIER2 .softhouse/capture/t234-sweep-instrument-audit/instruments/02-escape-matrix-fix.sh
```
A later, otherwise identical run passed. I attributed it rather than shrugging:

`50-failopen-lint.py` classifies TIER1 as *"C1 dead absolute path AND C2 reassuring
failure arm"*, and `_dead_paths` decides deadness with `os.path.exists(p)`.
`02-escape-matrix-fix.sh:5` contains `C=/tmp/t234_matrix2.txt`. **Controlled test:**

```
/tmp/t234_matrix2.txt present  -> TIER2 (frontier == pinned, BAR exit 0)
/tmp/t234_matrix2.txt removed  -> TIER1 (frontier != pinned, BAR exit 2)
```
(removed, re-linted, restored — the file is scratch the instrument regenerates.)

`/tmp` is shared by every worktree in the fire and is reaped by the OS. So **the BAR's
pass/fail on an unrelated diff turns on whether some other agent has recently run
`02-escape-matrix-fix.sh`.** A verdict guard that is non-deterministic and
cross-worktree coupled is worse than no guard: it produces both false rejections and,
symmetrically, a green that was bought by an unrelated process's side effect. My own
green above is contingent on that file existing. **This predates T250 and blocks
nothing here, but it should be a task.**

---

## 10. INSTRUMENTS AND NON-NEGOTIABLES

**Engine purity — CONFIRMED.** Stripping docstrings and comments, **zero live uses of
`grep`, `rg` or `git grep` across all seven of T250's instruments.** The only
occurrences are the docstring sentences claiming their absence. The BAR's own probe
check used `/usr/bin/grep` by absolute path, which is the correct way around the
ugrep shell function. [`evidence/70-instrument-audit.txt`]

**Money — CLEAN.** `wire_attestation.py`, `oracle_send.sh` and all seven instruments:
**no `float(`, no `json.load(s)`, no float formatting, in any executable line.** The
module reads header text and integer byte counts only; `Content-Length` is compared as
an integer. **No new unguarded site against the T145 census.** T207's ruling does not
bite: there is no float-derived predicate here to repair.

**Database — CLEAN.** One `mysql` token across all 130 files, inside
`transcripts/90-bar.txt` quoting the harness quoting Fineract's own
`GLAccountReadPlatformServiceImpl.java`. No driver, no dialect, no `:1521`.

**No synthesised captures.** T250's committed responses match, byte for byte, what the
live oracle returned to me independently, and its sidecars verify `rc=0`.

### F-12 (MEDIUM) — the calibration claim is overstated

Claimed: *every* instrument calibrates on a positive AND a negative and aborts (4/5)
rather than reporting an error as a zero. Measured, per file:

| instrument | calibration | pos+neg arms | abort |
|---|---|---|---|
| `10-population.py` | yes | yes | exit 4 and 5 | ✅ |
| `11-selector-check.py` | **none** | **none** | exit 5 | ❌ |
| `12-tenant-term.py` | **none** | **none** | exit 5 | ❌ **produced the headline number** |
| `20-redA-….sh` | P-22 refusal arm | effectively | exit 3 | acceptable |
| `30-redB-….sh` | positive control + honest negative | yes | scored | acceptable |
| `40-redC-….sh` | per-shape asserts | partial | exit 1 | acceptable |
| `50-oraclestamp-….py` | self-abort if the mutation fails to move the hash | — | exit 5 ×3 | good |

Two of seven calibrate on nothing, and one of those two is the instrument whose output
T250 calls "the finding that matters" — and whose blind spot I demonstrated in F-2.
Given last fire's three fail-opens-inside-fail-open-detectors, a blanket "every
instrument" claim that is false for 2/7 is a finding, not a quibble. (Note in T250's
favour: instrument 50's *"ABORT: mutation did not change the blob hash; instrument is
broken"* is precisely the right instinct, and instrument 10's calibration is textbook.)

### F-13 (LOW) — a regex that is committed, read, and grades nothing

`12-tenant-term.py:44` defines `WRITES_RECORD = re.compile(...)` with a docstring
comment. **It is never referenced.** A P-45 artefact inside the task that exists to
remove P-45 artefacts. Delete it or wire it.

### F-14 (LOW) — the library clobbers the caller's traps while arguing it must not

`oracle_send.sh`'s header argues at length that a sourced library must not mutate the
caller's shell, and therefore sets no shell options. It then runs
`trap '…' EXIT HUP INT TERM QUIT` and, on every return path, `trap - EXIT`.

Driven red **with a control arm** (`instruments/t261-caller-and-trap.sh`) — the two
arms differ by exactly the `. oracle_send.sh` line:
```
CONTROL   (library NOT sourced) : BODY-FINISHED / CALLER-CLEANUP-RAN   <- control OK
TREATMENT (library sourced)     : BODY-FINISHED                        <- cleanup GONE
```
A caller's `trap cleanup EXIT` does not survive one `oracle_send` call. The argument in
the header is correct; the code does the thing the argument forbids, via a different
mechanism. *Repair:* save and restore the caller's EXIT trap (`trap -p EXIT`) rather
than clearing it, or scope the cleanup to the function's own return paths.

### F-15 (LOW) — a placeholder timestamp committed under `capture/`

`evidence/redA/legacy/*.http` carry `captured-at-utc: <fixed-for-diff>`. Deliberate and
self-labelling, and these are fixtures rather than evidence — but they live under
`.softhouse/capture/` where a later reader may meet them as capture records. A one-line
`README` in `redA/legacy/` would close it.

---

## 11. THE UNCALLED SUCCESSOR — the ruling

**Measured, not assumed.** Over T250's own committed tree, **12 files mention
`oracle_send` / `wire_attestation`; every one of them is the library itself, T250's own
instruments, T250's own transcripts, or T250's handoff. External callers: 0.**
[`evidence/71-caller-and-trap.txt`]

**Is the labelling honest?** Yes. T250 files it as backlog **B-5** — *"Nothing is WIRED
to `oracle_send.sh` yet. It is a proven successor shape with no caller."* — in the
backlog section, under its own heading, in the same words a critic would use. It does
**not** claim a migration, does not claim the four files are fixed, and states in §5
with a count that the four files were NOT edited, NOT run, NOT superseded in place, and
why. Compare the shape this program has been burned by: `manifest.py verify`,
`t44_float_roundtrip_v3`, T173's float guard, `guard_ledger_invariants`. Each of those
was a *silent* orphan. This one is a *declared* one, and the declaration is the
difference.

### RULING: an uncalled successor MAY merge — with conditions

**May it merge?** Yes.
1. It is purely additive: 130 `A`, 0 `M`, 0 `D`. It changes no verdict, no pin, no
   graded population beyond ten JSON-clean `.req` files, and moves no digest.
2. Its verdicts are reachable only by explicit invocation. F-4 through F-7 are latent,
   not live — no committed evidence today rests on `verify`.
3. It is proven against the live oracle at the boundary that mattered (§5), which is
   more than the four incumbent files can say.
4. Refusing it leaves the literal-attestation shape as the **only** shape in the tree,
   and the chain has already demonstrated (F-1) that the next `capN+1.sh` copies it.

**But it may NOT acquire a caller until F-4 and F-5 are repaired.** An uncalled
successor with a fail-open is safe; a *called* one is a fail-open in the evidence path,
and the first adopter would inherit it silently — which is how every prior instance of
this class started.

**And the conditions must be written where the next reader meets them — in the module
— not only in this review.** That is the entire lesson of the class.

### What must be FILED to wire it

1. **Repair F-4 and F-5 in `wire_attestation.py`** (require the body assertions when
   `--req` is given; compare header lines as an ordered sequence). Small, mechanical,
   testable against the artefacts already in `evidence/redB/`.
2. **State F-6 in the module's NOT-CLAIMED block** — the response is unattested — or
   attest it. Until then no vector may cite an `oracle_send` capture's `capture_sha256`
   as evidence about the *response*.
3. **Correct `oracle_send.sh`'s header** (F-8) so the pair stops contradicting itself.
4. **Reconcile B-1 before any non-JSON body is captured** — `oracle_send` names every
   body `NAME.req` and the wire-float guard requires every `*.req` under
   `.softhouse/capture/` to parse as JSON. A form-encoded, CSV or multipart body trips a
   HARD guard. Neither side is wrong; the naming convention and the guard's derived
   population need one owner.
5. **Assign the first caller.** T250 says minting `cap11.sh` inside `tierA-a2/` is
   T164's call. **T164 has since landed on `main` (`f084819`)**, so that blocker is
   gone and the task can now be scheduled — with the MANIFEST.sha256 re-derived in the
   same commit as the first real capture.
6. **Schedule B-2 (the 45-46 silent scripts) ahead of further work on the four.** §2.

---

## 12. FINDINGS SUMMARY

| # | sev | finding |
|---|---|---|
| F-4 | **HIGH** | `verify` checks only assertions that are PRESENT; deleting `body-sha256:` + swapping the body for same-length bytes → `VERIFIED` rc=0. Fail-open in a default-deny module. |
| F-11 | **HIGH** | **NOT T250's.** The BAR's fail-open frontier flips on the existence of `/tmp/t234_matrix2.txt`; verdict is non-deterministic and cross-worktree coupled. Own task. |
| F-5 | MED | Header comparison is set membership: reordering, and dropping one of two identical duplicated headers, both verify clean — the exact fact redC shape 1 proved matters. |
| F-6 | MED | The RESPONSE (`.json`/`.status`) is entirely unattested and that limit is stated nowhere. |
| F-8 | MED | `oracle_send.sh` states "a later `-H` … wins"; `wire_attestation.py` measured that FALSE and corrected it. Correction landed in one file of a shipped pair. |
| F-2 | MED | Instrument 12 (uncalibrated) is blind to `.write(` emitters; on T250's own 50-file population the split is 6/44, not 5/45. |
| F-3 | MED | The "5th attester" (backlog B-3) is a poison fixture, not a capture attester. Honest count is 4. |
| F-12 | MED | "Every instrument calibrates on a positive and a negative" is false for 2 of 7 — including the one that produced the headline number. |
| F-1 | MED | Pattern: the defect was ADDED after two audits, by a task closing an audit residual, via copy-forward. The chain must not be extended again without a derived attestation. |
| F-7 | LOW-MED | `known_keys` exempts invented sidecar lines from the "asserts what was not sent" check. |
| F-9 | LOW | §4 Route C: table says digest "unmoved", prose says it moves. |
| F-10 | LOW | The malformed fixture still lives under `.softhouse/capture/`, excluded only by suffix; its `.sha256.txt` sibling names a vanished `.req`. |
| F-13 | LOW | `12-tenant-term.py:44` `WRITES_RECORD` — defined, never used. A P-45 regex inside the anti-P-45 task. |
| F-14 | LOW | `oracle_send.sh` destroys the caller's EXIT trap while arguing a sourced library must not mutate the caller's shell (driven red with a control arm). |
| F-15 | LOW | `captured-at-utc: <fixed-for-diff>` placeholder committed under `.softhouse/capture/`. |

## 13. WHAT I COULD NOT VERIFY

* **The BAR was run at my worktree HEAD `7c29273`, which is NOT a descendant of `main`
  (`607252a`)** — the two lines diverged in the concurrent cloud fire. `conformance.sh`,
  `.softhouse/vectors`, `nexus/` and `.softhouse/capture/lib` are byte-identical between
  `a71c140` and my HEAD, so the graded surface is the same; but `main` carries T164's
  MANIFEST change that my line does not. **A merge-time BAR on `main` is still owed by
  whoever merges.**
* My green BAR is contingent on `/tmp/t234_matrix2.txt` existing (F-11). I restored that
  file after testing; I cannot guarantee its state at merge time.
* "The sixth time in this program" for the P-45 uncalled-successor class — I verified
  this instance has 0 external callers and took the prior five on report.
* Whether **T216** specifically audited the `cap*.sh` chain. I verified the stronger,
  load-bearing half: `cap10.sh` is the newest link, was minted by T236 (`994905c`),
  and carries the defect; `cap9.sh` came from T163 (`d1a9587`).
* Prior-art claims about T245's leg 2 (database contents) — out of scope here; I did not
  re-derive T245.
