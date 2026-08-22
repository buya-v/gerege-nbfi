# T228 — sweeping THREE dead concepts outside the G-8 section

**Branch** `softhouse/T228-dead-concept-sweep` · **fork point MEASURED** `2d41838` · **swept and measured at**
`f8436b4` · role `spec_writer` · target `docs` · local fire `20260822-060013`, wave 2.

Every measured claim below is stamped `f8436b4` (P-69) unless it says otherwise. Anything I did not verify is
marked `[UNVERIFIED]`.

---

## 0. THREE THINGS THAT CONTRADICT MY OWN BRIEF — reported, not reconciled

The brief told me to say so loudly rather than smooth it over. Three of its statements did not survive
measurement.

### 0.1 My fork point was NOT what any rule predicts, and `main` MOVED UNDER ME MID-TASK

```
git rev-parse HEAD          -> 2d41838cdbbe5332bd62deb5cdec9f52f3df91f3
git merge-base HEAD main    -> 2d41838   (i.e. HEAD was a STRICT ANCESTOR of main)
git rev-list --count HEAD..main -> 17
```

My worktree forked at **`2d41838`** — the session-start commit — **17 commits behind `main`**, and therefore
**before `99c031d`**, exactly as the brief warned. I read *nothing* before merging. So far, so predicted.

**What was not predicted:** between my first `git log main` and my `git merge main`, **`main` advanced by one
commit**, from `d039d29` to **`f8436b4`** (*"wave 2 dispatched (A2-34, T228); program.json records the first
ledger vectors"*) — the commit that dispatched **me**. My merge therefore fast-forwarded to `f8436b4`, not to
the `d039d29` I had measured seconds earlier. **A fork-point measurement is stale the moment it is taken**;
P-71 has now been falsified twice as a *rule*, and this fire shows the underlying reason is that `main` is not
quiescent during a wave. **Report the sha you MERGED, never the sha you LOOKED AT.**

### 0.2 The BAR's store commit `d1f74ae` IS NOT ON `main`

The brief pins the BAR to *"merged `main` at `d1f74ae`"*. Measured:

```
git merge-base --is-ancestor d1f74ae main  -> NO
git branch -a --contains d1f74ae           -> (nothing)
git log -1 --format='%H %P' d1f74ae -> d1f74ae  a072ecd 1325e8b
git log -1 --format='%H %P' d76594a -> d76594a  a072ecd 1325e8b   <- this one IS on main
```

**`d1f74ae` and `d76594a` are two DISTINCT merge commits with IDENTICAL parents and an IDENTICAL subject**,
created **15 seconds apart** (`16:40:04` vs `16:40:19`). Their **trees are byte-identical**
(`90514b2f66697e8b5edee41995d35c51efaaeafc` both; `git diff d1f74ae d76594a` is empty).

**Consequence: none for content, some for provenance.** The A2-15 merge was performed twice and the orphan is
the one the brief and `program.json` cite. Nothing I checked depends on it, and the vector-store digest is
unaffected. But *"driver-verified on merged main at `d1f74ae`"* is **not verifiable from `main`** — the sha
resolves only because the object survives unreferenced. **Recommend the driver re-stamp that BAR to
`d76594a`.** `[UNVERIFIED: why the merge ran twice.]`

### 0.3 The engine warning is RIGHT about the trap and UNDERCOUNTS THE ENGINES — there are FIVE

The brief says four engines. **There are five reachable here**, and I add ripgrep. Full discriminating table,
measured directly at `f8436b4` on `.softhouse/gates.md` (see §2.2 for why this test and not `\bMNT` alone).

### 0.4 …and my OWN first calibration script produced a FALSE engine finding, which I caught and am reporting

My first-pass engine probe ran the engines through `subprocess.run(..., executable="/bin/zsh")` and coded the
result as `"0"` **whenever stdout was empty and the exit code was not 2**. Two lies came straight out of it:

- it reported **`rg` as a silent-zero engine returning 0 on a literal `MNT` that BSD grep finds 154 times** —
  false; `rg` was simply **not defined as a function in a fresh non-interactive zsh** and the `command not
  found` (rc 127) was swallowed by my fallback and re-printed as *"0 matches"*;
- it labelled a row **"ugrep (the `grep` shell function)"** when in that same fresh shell `grep` had resolved
  to **BSD `/usr/bin/grep`** — so I measured one engine twice and called it two.

I caught both only by cross-checking against a direct Bash call. **This is P-72 firing on the instrument
written to satisfy P-72**, and it is the same shape as everything else in this task: *a result presented with a
domain that names the wrong thing*. The corrected table in §2.2 is measured by **direct shell invocation
only**. **No conclusion anywhere in this handoff rests on the grep engines** — see §2.1.

---

## 1. VERDICT

Population = the **1310 claim-bearing files** (`.md` + `.sh` + `.py` + `tasks.json` + `program.json` +
`.softhouse/vectors/**`). Counts are **files with ≥ 1 hit**, measured, not estimated:

| concept | claim-bearing files with ≥1 hit | **LIVE CLAIM SITES** | files left untouched | of those, the big benign class |
|---|---|---|---|---|
| **C1** — *"600 % only"* / family B stated in RATES AND TERMS | **61** | **3** (`patterns.md` ×2, `program.json` ×1) | **57** | — |
| **C2** — the falsified `~n/2` / `MNT n/200` / `MNT 1.80` ceiling | **74** | **2** (`program.json`, `tasks.json`) | **71** | **~40 files: `floor(n/2)`, a DIFFERENT mechanism — §4** |
| **C3** — the superseded **MNT 10.01** residual record | **22** | **3** (`gates-proposed-answers.md`, `program.json`, `tasks.json`) | **19** | — |

Plus **one live defect that is none of the three concepts** and is the one I would escalate first (§3.4,
LIVE #5). **Six correction sites across four files.** (File counts are taken *after* my edits, so a file I
corrected still counts as a hit — the correction text necessarily quotes the concept.)

**Four files carry the six correction sites** (`patterns.md` and `program.json` carry two each):

1. `.softhouse/patterns.md:471` — **C1** — P-23's illustrative parenthetical.
2. `.softhouse/patterns.md:546` — **C1** — P-26's *"the rate that defines family B"*.
3. `.softhouse/gates-proposed-answers.md:207` — **C3** — P-6's *"It is frozen: MNT 10.01 at n=3000"*.
4. `.softhouse/program.json` `gates_pending[G-8].measured_region` — **C2 + C1** — the sentence the file itself
   labels **DECISION-RELEVANT**.
5. `.softhouse/program.json` `gates_pending[G-8].state` **and** `.blocks` — **a live prohibition that had
   silently expired.** See §3.4; this is the finding I would escalate first.
6. `.softhouse/tasks.json` T223 `note` — **C2 + C3** — *"DECISION-RELEVANT RESTATEMENT FOR BUYAN"*.

**Zero corrections to `.softhouse/vectors/`** — and see §5, because the brief called vector reason strings the
dangerous population and my scope forbade me from touching them. They turned out to be **clean**, but that was
luck of the draw, not a boundary that was safe to draw.

**`.softhouse/obligations.md`: ZERO hits on all three concepts** — measured, not assumed (§2.3).
**`docs/` (10 files), `.claude/skills/` (4 files), `CLAUDE.md`: ZERO live instances** — this closes the `docs/`
population **T231 explicitly declared it had not looked at**, as *measured-absent* rather than *assumed-absent*.

---

## 2. THE INSTRUMENT, AND ITS CALIBRATION BEFORE ANY NEGATIVE (P-72)

### 2.1 Primary instrument: Python `re` over `git ls-files`, NOT grep

Every population count and every negative in this handoff was produced by **Python 3.9.6 `re`**, reading each
file's **whole text** (so newline-spanning matches are structurally possible), over the file list from
`git ls-files -z`. I chose it over all five grep engines deliberately:

- it has **one** regex dialect, so T232/T234's `\b` trap cannot arise — and in fact **no net I ran contains
  `\b` at all**; I used explicit `(?<![.\d])` / `(?![.\d])` lookarounds instead, which no engine can silently
  reinterpret;
- it does **no ignore-file filtering**. The `grep` shell function on this machine re-execs with
  `--ignore-files`, which honours `.gitignore` — **a fail-open I did not want under a sweep whose whole job is
  to prove absence**;
- it reports **file, line, matched text, and whether the match spanned a newline**, so the multi-line result is
  measured rather than asserted.

**Flags/dialect:** `re.IGNORECASE` and `re.DOTALL` only where the net's name says so; `\s` is used deliberately
in phrase nets **because `\s` matches `\n`**, which is what makes those nets multi-line.

### 2.2 The five engines, discriminating test, measured directly at `f8436b4`

`MNT` in `gates.md` is always preceded by a non-word character; `NT` is always preceded by `M`. So
`\bMNT` alone **cannot** distinguish a working `\b` from an ignored one — **both give 154.** `\bNT` is the
discriminator. This is why the brief's phrasing (*"which does honour `\b\d\s\w`"*) is right but was, as stated,
not yet checkable.

| engine | `MNT` | `\bMNT` | `\bNT` | verdict |
|---|---|---|---|---|
| BSD `/usr/bin/grep -E` (what scripts get) | 154 | **154** | **0** | **REAL word boundary** — brief CONFIRMED |
| ugrep 7.5.0 (the interactive `grep` function) | 154 | **154** | **0** | **REAL word boundary** |
| ripgrep 14.1.1 (the interactive `rg` function) | 154 | **154** | **0** (rc 1) | **REAL word boundary** — **the FIFTH engine, absent from T234's audit** |
| `git grep -E` | 154 | **0, rc 1** | 0 | **`\b` READ AS LITERAL `b` — SILENT ZERO.** T232/T234 CONFIRMED |
| `git grep -P` | 154 | **154** | **0** | REAL word boundary |
| `/usr/bin/grep -P` | — | — | — | **DOES NOT EXIST — `invalid option -- P`, rc 2.** T234 CONFIRMED |

`git version 2.50.1 (Apple Git-155)`, darwin/arm64. `[UNVERIFIED on GNU/Linux]`, per P-72's own caveat.

### 2.3 RECALL ON KNOWN POSITIVES — measured BEFORE any negative was written down

| # | concept | known positive | result |
|---|---|---|---|
| 1 | C3 | `gates.md:3385` — G-8-NOTICE table row `MNT 10.01` | **HIT** (28 in file) |
| 2 | C3 | `gates-proposed-answers.md:207` — *"frozen: MNT 10.01 at n=3000"* | **HIT** |
| 3 | C2 | `program.json` — *"~MNT n/200 WHATEVER THE RATE"* | **HIT** (lines 657–658) |
| 4 | C2 | `RESUME.md:67` — the headline **the driver had already fixed** (control) | **HIT** |
| 5 | C1 | `patterns.md:471` — *"600 % p.a., MNT 0.01, n ≥ 104"* | **HIT** |

**RECALL 5/5.** Row 4 is the T232-shaped control: a sweep must find the positive somebody already holds. Rows
2, 3 and 5 are known positives only *in hindsight* — they were unknown when the nets were written and are the
sweep's actual yield.

### 2.4 The nets

21 nets over the claim-bearing population, 18 over the full population, 10 over the bulk capture payloads.
Concept nets, not sentence nets (P-26): `10\.01`, `1001\s*minor`, `n\s*/\s*2(?![0-9])`, `n\s*/\s*200`,
`(?<![.\d])1\.80(?![\d])`, `2\s*[·*x×]\s*B(_minor)?\s*(>=|≥)\s*n`, `half\s+(a\s+|one\s+)?minor\s+unit`,
`(bounded|ceiling|cap|limit)\s+(\w+\s+){0,6}n\s*/\s*2`, `600(\.0)?\s*%`, `n\s*(>=|≥)\s*104`,
`no\s+other\s+(annual\s+)?rate`, `600\s*%\s*(\w+\s+){0,6}\bonly\b` and its mirror,
`famil(y|ies)[\s\-]*A\s+(\w+\s+){0,12}(analog|same\s+(way|shape|mechanism)|likewise|mirror|resembl)` and its
mirror, `(largest|biggest|record|greatest|max)\s+(\w+\s+){0,4}(residual|unamortized|failing disbursement)`,
`19\s*/\s*log`, `⌊\s*n\s*/\s*2\s*⌋`, `\(\s*(δ|delta)\s*\+\s*(½|1/2|0\.5)\s*\)`.

### 2.5 MULTI-LINE RESULT — measured, and the honest answer is "almost nothing"

T234 found 743 newline-spanning matches across 161 files repo-wide. **On these three concepts the number is
small**, because the load-bearing tokens are numerals, which do not wrap:

| net | multi-line matches |
|---|---|
| `C3 largest…residual` | **3** |
| `C2 ceiling…minor unit` | **2** |
| `C1 600 %…only`, `C1 always/every 600 %`, `C2 half a minor unit`, `C2 famA analogy`, `C3 10.01 at n` | **1 each** |
| every purely numeric net (`10\.01`, `1001`, `n/2`, `n/200`, `1\.80`, `104`) | **0** |

**None of the multi-line matches was a live claim** — all fell inside handoffs or the live G-8 section. But the
count is **not zero**, so a line-oriented sweep of these concepts would have been running with an unmeasured
blind spot, and I would not have known which of the 9 it lost.

---

## 3. THE POPULATION, AND THE TRIAGE

### 3.1 Denominator, and WHAT I SKIPPED (P-40)

| | count |
|---|---|
| tracked files at `f8436b4` | **4954** |
| read as text | **4942** |
| **SKIPPED — binary (NUL in first 8 KiB)** | **12**, enumerated below |
| **SKIPPED — unreadable** | **0** |
| of which: `.md` files scanned | **409** |
| `.md` with ≥1 hit on any concept | **70** |
| `.md` with **0** hits | **339** |

**The 12 skipped files, named**: seven `.gz` raw oracle captures
(`t117-familyb` ×2, `t159-review-t117`, `t219-g8-residual` ×3, `t223-g8-region-predicate`, `t229-g8-site3`),
two NUL-corpus grep fixtures (`t108-grep/corpus/s09-nul-other-line.txt`, `s10-nul-same-line.txt`), and three
further capture blobs. **I did not decompress the `.gz` captures.** They are machine-emitted oracle payloads,
not prose, and G-8's STANDING RULE 5 exists to make people *analyse* them, not to make them carry claims.
`[UNVERIFIED: whether any `.gz` contains a prose field. I assert only that I did not look.]`

**Second declared split.** I ran the two backtracking proximity net families over a **PROSE tier of 4891 files
/ 47 MB** and only the cheap linear nets over a **BULK tier of 51 files / 122 MB** (capture payloads
> 200 KB under `capture/*/out/`). The first attempt at running everything over everything did not terminate.
**BULK-tier hits: 881 × `104`, 163 × `10.01`, 99 × `1001`, 21 × `600 %`, 18 × `1.80`, 1 × `n/2` — every one an
oracle-emitted balance or a period index, none a claim.** `[UNVERIFIED: the proximity nets over the BULK tier.]`

### 3.2 By role — the full 70-file `.md` population

| role | files with hits | disposition |
|---|---|---|
| handoff (`.softhouse/handoff/**`) | **31** | **EVIDENCE — left byte-identical.** A handoff is a dated, attributed record of what one task measured; every C3 hit in T116/T117/T159/T170/T177/T182/T219/T220 is past-tense and correctly attributed. |
| review (`.softhouse/reviews/**`) | **19** | **EVIDENCE — left.** |
| capture note (`.softhouse/capture/**`) | **15** | **EVIDENCE — left.** Includes all four `PREDICTION.md` pre-registrations, which are load-bearing *because* they record what was believed before probing. |
| `docs/` | **1** | `DEC-1` ×15 — **all `floor(n/2)`, the EmiAdjustment guard. FALSE POSITIVE by concept (§4). Left.** |
| **softhouse LIVE DOC** | **4** | `gates.md`, `patterns.md`, `RESUME.md`, `gates-proposed-answers.md` — **triaged individually below.** |

Plus, outside `.md`: `program.json`, `tasks.json`, `.softhouse/vectors/**` (§5).

### 3.3 `gates.md` — hits OUTSIDE the live G-8 section (lines 1033–3120 excluded by scope)

| bucket | hits | disposition |
|---|---|---|
| **PRE (1–1032)** | **2** | `:30` the G-8 summary-table row — **ALREADY CARRIES T219's AND T229's CORRECTIONS in full** (`(δ+½)·n` not `n/2`; `MNT 10.01 → MNT 30.00`; largest failing disbursement `MNT 44.99`; *"600 % only" is still dead*). **CLEAN, left.** `:477` — `floor(n/2)`, the EmiAdjustment guard. **False positive, left.** |
| **`## G-8-NOTICE` (3293–3466)** | **13** | **HONOURED T219's DECISION — NOT TOUCHED.** See §6. |
| **POST-other (3467–3735)** | **0** | — |

### 3.4 The six live claims, and why each is one

**LIVE #1 — `patterns.md:471` (P-23) — CONCEPT 1.**
> *"A second family (600 % p.a., MNT 0.01, n ≥ 104, 22 cells) fails to sum at all…"*

Every figure is **correct over T84's domain**, so **not one digit was changed** — the T101 F-8 shape. The
parenthetical has no domain on it, so it reads as **the definition of family B**, on precisely the axis T223
killed. **The pattern's own rule is what it violates**: P-23 says *"every sentence must name the domain it was
measured over"*. **An example inside a pattern is a claim carrying that pattern's authority.** Correction added
naming T223's 36.0 % and 300.0 % observations, `n* ≈ 19/log10(1+r)` as a property of the **rate**, and T219's
principals to 4499.

**LIVE #2 — `patterns.md:546` (P-26) — CONCEPT 1.**
> *"the missing rate being 600.0 %, **the rate that defines family B**"*

Present tense, live pattern. The incident's numbers (family A at 11 of 12, absent at 600.0 %) are **T101's
measurement and are untouched**. Only the word *defines* is wrong. Correction supplies the substitution:
*"the only rate at which family B had then been observed"*.

**LIVE #3 — `gates-proposed-answers.md:207` (P-6) — CONCEPT 3.**
> *"It is **frozen**: MNT 10.01 at n=3000, not a bound, two phenomena, family-B exemption clean at 761 cells /
> 0 diffs."*

The strongest form of the seventh mechanism: a figure **declared settled**, carrying a domain, on the wrong
axis. I corrected it **clause by clause, and left two clauses alone because they are right**:
*"not a bound"* is **correct** — it is exactly what T117 warned and T219 demonstrated a second time — and
*"761 cells / 0 diffs"* is **correct over T100's named domain**. Only *"frozen"* and the axis are wrong.
Recorded that P-6's own exemption (*"a new task is justified only by a new MEASUREMENT"*) **covered all five
subsequent moves**, so the rule was never violated — only its illustration went stale. **Read P-6 as freezing
prose churn, never as freezing a number.**

**LIVE #4 — `program.json` `gates_pending[G-8].measured_region` — CONCEPTS 2 AND 1.**
> *"…and as a rescue ceiling **B_minor <~ n/2**. **DECISION-RELEVANT: the failing disbursement is bounded by
> ~MNT n/200 WHATEVER THE RATE; at n <= 360 that is ~MNT 1.80. WHAT KEEPS THIS OUT OF A REAL PRODUCT IS THE
> TERM, NOT THE RATE.**"*

**This is the RESUME.md headline the driver already fixed, still standing in the machine-readable registry** —
proof the concept travelled, and the *worse* copy of the two, because (a) the file **labels it
DECISION-RELEVANT**, (b) *"WHATEVER THE RATE"* is an unconditional universal, and (c) it ends in a
**product-safety conclusion derived from the falsified ceiling** — the false mechanism the brief warned a
reader would still be able to reason from. It also carries *"all 20 family-B principals are odd"*, **which
T231 had already struck from `gates.md`** (T223's own new principals 50 and 2 are even).

**Shape of the fix:** T223's text is **kept verbatim** (T114/T176 — evidence gets a labelled correction, never
a silent edit). I prefixed the field with `[SUPERSEDED IN PART — SEE measured_region_correction ABOVE…]` and
added a sibling `measured_region_correction` key **placed BEFORE it in key order**, so the correction is read
first. It enumerates what falls (three claims) **and what stands** (the 7-for-7 predicate, the `c2771fb`
strict-ancestor discipline, the death of *"600 % only"*, the band structure, `n* ≈ 19/log10(1+r)`, the T220
correction, the 971/1035 pre-registered miss count).

**LIVE #5 — `program.json` `gates_pending[G-8].state` and `.blocks` — A PROHIBITION THAT HAD SILENTLY EXPIRED.
THIS IS THE ONE I WOULD ESCALATE FIRST, AND IT IS NOT ANY OF MY THREE CONCEPTS.**

```
"state" : "…Options (b)/(c) MUST NOT be put to Buyan UNTIL T229 CHARACTERISES SITE 3."
"blocks": "Options (b) and (c) are BLOCKED ON T229 (characterise site 3)…"
```

**`T229` is `done`.** Read literally today, both fields say **the block has lifted**. It has not — and the
truth is the opposite of what the wording implies: T229 characterised site 3 **and in doing so falsified the
ceiling by 3×**, and T219 then tripled the residual record at a term already declared measured. **The failing
region got THREE TIMES WIDER, so the prohibition is STRENGTHENED.** A `user`-gate prohibition written with an
expiry condition, whose expiry condition then completed, is a **new failure shape** — the brief's boundary
("options (b) and (c) must NOT be put to Buyan") was one stale JSON string away from reading as satisfied.
Both fields corrected in place with a labelled `[T228 CORRECTION at f8436b4: …]` that restates the prohibition
unconditionally and names the *real* blocker: **not "site 3 is uncharacterised" but "the characterised law has
an UNMEASURED INPUT"** — `δ = I₁q − E` depends on the pre-rescue instalment `E`, which nothing in this program
measures, so `(δ+½)·n` cannot be evaluated, only bounded by `B_minor < 1.5·n` **conditional on the unproven
`δ ≤ 1`**.

**LIVE #6 — `tasks.json` T223 `note` — CONCEPTS 2 AND 3.**
> *"**DECISION-RELEVANT RESTATEMENT FOR BUYAN**, which is what this task existed to produce: the failing
> disbursement is bounded by ~n/2 minor units = MNT n/200 WHATEVER THE RATE. At n <= 360 that is ~MNT 1.80.
> WHAT KEEPS THIS OUT OF A REAL PRODUCT IS THE TERM, NOT THE RATE."*

The third copy of the same sentence. **`tasks.json` dispositions are a NAMED fossil site in G-8's own STANDING
RULE** (mechanism four: *"a `tasks.json` disposition that the author had already reversed and never swept"*),
which is why I read every one rather than trusting `status: done`. The same note also says
*"MNT 0.23 / 2.91 / **10.01** LEFT UNTOUCHED — all correct over their named domains"* — **10.01's named domain
is exactly what T219 falsified**, and T219's own note already reads `0.23 / 2.91 / 5.01`. Labelled correction
appended; T223's wording untouched.

### 3.5 What I read and deliberately LEFT

- **31 handoffs, 19 reviews, 15 capture notes** — evidence. Includes `T117.note`'s *"the residual DOUBLED to
  MNT 10.01 at n=3000"* (a true statement about what T159 did), `T170.note`'s *"says TWICE that the MNT 10.01
  headline is not in doubt"*, and `T177.note`'s cell-identity correction — all attributed and past-tense.
- **`tasks.json` T228 (my own) and T241** — both quote the falsified claims **as the thing to be swept**, with
  attribution. **Correctly-attributed quotation → leave.**
- **`RESUME.md:67–73`** — the driver's already-fixed labelled-historical text. **CLEAN.** (`:161` still says
  T228 sweeps *"BOTH dead concepts"*; there are now **three**. Cosmetic, driver's file, **not edited** — §7.)
- **`capture/t100-g8-rescope/g8-section.md`** — P-27's tombstoned duplicate. Header reads *"(removed) — this
  was a duplicate copy"*. **Correctly disposed of; left.**
- **`gates.md` lines 1033–3120** — the live G-8 section, **out of scope by the brief**, and rebuilt by T219 and
  T231 this fire. I read it to derive the law; **I changed nothing in it.**

---

## 4. THE FALSE-POSITIVE CLASS I DID NOT "FIX" — and it is the biggest population in the task

**~40 hits across ~20 files match `n/2` and are NOT the G-8 ceiling.** They are
`EmiAdjustment.shouldBeAdjusted`'s threshold — `|ΔEMI| × 100 > floor(n/2)` whole currency units
`[EmiAdjustment.java:31-36, Money.java:216-222]` — a **source-cited Fineract constant**, correct, load-bearing
in DEC-1 §8, and **a completely different mechanism**. Files: `DEC-1` (×15), `T64-ZP-A/B/C/D` vector notes,
`T9`/`T11`/`T18`/`T21`/`T23`/`T26`/`T27`/`T29`/`T43`/`T49`/`T57`/`T61`, `patterns.md:1147` (P-2), `gates.md:477`.

**The trap is genuinely sharp, and I nearly fell in it.** `B > floor(n/2)` appears verbatim in the T64-ZP
notes — and `B_minor > ⌊n/2⌋` is **the FIRST CONJUNCT of the corrected rescue law** in `gates.md:2084`. The
identical expression is *right* in both places. What was falsified is **not `⌊n/2⌋`** but the claim that
`⌊n/2⌋` **bounds the failing disbursement from above**; in the corrected law it is a **necessary condition for
RESCUE**, and the ceiling is `(δ+½)·n`, coinciding with `n/2` **only at δ = 0** — a value never observed on a
family-B cell. **A sweeper matching the token instead of the mechanism would have "corrected" forty correct,
source-cited sentences.** This is the brief's *"do not fix a correct figure"* with teeth on it.

---

## 5. THE VECTOR STORE — clean, but I want the boundary itself on the record

The brief calls vector reason strings *"the dangerous population… a false claim with a machine repeating it"*
and my scope forbids me from touching the promoted payloads. **Both were true at once, and that is a gap.**

**Measured** (62 hits over all `.softhouse/vectors/**` strings, walked as parsed JSON at every depth, including
the six new `ledger/` vectors from A2-15):

- **C3 (`10.01` / `1001 minor`): ZERO hits. Nothing in the store carries the superseded residual record.**
- **C2: 42 hits — every one the `floor(n/2)` EMI guard** (T64-ZP ×4, P-EMI ×2) **plus one
  `principal_major_text` of `1.80`, an oracle-emitted money value.** No ceiling claim. Correct as written.
- **C1: 20 hits — every one a description of the vector's OWN cell** (its rate 600.0 %, its term 104/108/103).
  **T116-G8-FAMB's exemption reason argues the RIGHT way**: *"It is NOT a statement that 600.0 % p.a. is
  exempt: the sibling vector T116-G8-CLEAN-N103, one repayment shorter at the same rate and the same
  principal, amortizes normally and carries NO exemption at all."*

**One borderline call I am flagging rather than burying.** `T116-G8-FAMB-…-108x600pct.json` `_note` says
*"**n = 104 is the region's lower boundary**"*. `gates.md` says whether family B exists below n = 104 at
600.0 % is **`[UNVERIFIED]`**, and T223's `n* ≈ 19/log10(1+r)` makes the lower edge **rate-dependent**, so
*"the region's lower boundary"* is true only at 600.0 % and false as a statement about family B. It is **one
word short** of the C1 defect. **I did not correct it: the store is read-only to me and the pinned digest
forbids it.** Registering it as the sole vector-store residual. Recommend a task with `.softhouse/vectors/`
writable and a re-pin; suggested wording *"the lowest family-B cell ever observed, and the region's lower edge
**at 600.0 %**"*.

**Store digest UNCHANGED, verified both ways**: `git rev-parse HEAD:.softhouse/vectors` =
**`8968c559fa613e8642ab030bd0a029c17d147054`**, and `git diff -- .softhouse/vectors` is **empty**.

---

## 6. `## G-8-NOTICE` — T219's DECISION HONOURED, AND ONE LINE HANDED TO T241

13 hits, lines 3293–3466, all C3. **I did not touch the block.** Its heading already reads
*"(SUPERSEDED — historical record; the LIVE G-8 section is above)"*, which is a correct label, and **T219 read
it and left it deliberately.** T241 is registered to resolve exactly this and its description already says
*"if T228 already handled it, say so and leave it"* — **I have not handled it; it is T241's.**

**One line for T241 to weigh, because it is the single most dangerous line in the block and it is not a
figure — it is an IMPERATIVE:**

> `gates.md:3396` — *"**Any disclosure of G-8 must state the residual WITH ITS TERM — "MNT 10.01 at n = 3000"
> — and must still…**"*

**That instruction is the seventh mechanism in its purest form.** It does not merely *carry* the wrong-axis
label; it **commands future readers to reproduce it**, and every restatement in this program *obeyed it
correctly*. A `must` inside a block headed SUPERSEDED still reads as live guidance to someone who lands on it
by search. **My recommendation to T241** (offered, not applied): leave the block's measurements untouched and
add **one pointer directly under `:3396`** saying the axis is the **principal**, not the term. Adding a pointer
does not corrupt a historical record; leaving a live imperative does. `:3398` (*"Writing 'MNT 10.01' without
its term would repeat…"*) has the same property.

---

## 7. GAPS I LEAVE BEHIND — stated so nobody reads this sweep as exhaustive (P-26, P-40, P-70)

1. **`.gz` raw captures (7 files) not decompressed.** Machine payloads; I did not look. `[UNVERIFIED]`
2. **Proximity/backtracking nets not run over the 51-file / 122 MB BULK capture tier** — only the linear
   numeric nets were. A *phrase* asserting a dead concept inside a large capture payload would be missed.
   `[UNVERIFIED]` I judge this near-zero: those files are oracle JSON.
3. **The vector-store borderline in §5** is **left uncorrected by scope**, not by judgement.
4. **`RESUME.md:161`** still says T228 sweeps *"BOTH dead concepts"* when there are three. **Driver's file, not
   edited.**
5. **The `d1f74ae` / `d76594a` duplicate merge (§0.2) is unexplained** and the BAR sha in T228's and T241's
   briefs points at the orphan. `[UNVERIFIED: cause.]`
6. **I did NOT rebuild G-8's 117-row scope table** (STANDING RULE 1). I made **no edit inside the G-8 section**,
   so I read the rule as not triggered — but **T219 faced this same question and T241 is registered to settle
   it**, so I record my reading rather than assert it. `[UNVERIFIED: that rule 1 does not bind an
   outside-the-section sweep.]`
7. **A concept can be restated as a CHART, a COUNT IN A SUMMARY TABLE, or a SILENCE where a qualification
   should be** — P-26's own list of what a sweep cannot find. I found the summary-table instance
   (`gates.md:30`, already clean). **I cannot claim to have found a silence.**
8. **Neither `600` nor `104` nor `1001` was swept as a bare number outside claim-bearing files** — 1109 and 653
   hits respectively, overwhelmingly period indices and oracle balances. I triaged the `.md`/`.sh`/`.py`/
   registry population (**1249 files**) and sampled, not exhausted, the rest.

---

## 8. BAR — OBSERVED BY ME on this branch at `f8436b4` + my four edits

| item | required | **observed** |
|---|---|---|
| probe line PRESENT (tested first) | present, `up` | **PRESENT**, `conformance.sh` output line 85: `reference oracle (https://localhost:8443/…/health) probe = up` |
| VERDICT | PASS exit 0 | **PASS, exit 0** |
| loanschedule parity | 46 / 7884 cells | **46 PASS / 0 FAIL, 7884 graded** |
| ledger | 4 parity / 2 oracle-refusal / 21 money cells | **4 / 2 / 21** |
| inadmissible | 0 | **0** |
| harness errors | 0 | **0** |
| invariant violations | 0 | **0** |
| original census pins | 4/4/4/0/0 `== pinned` | **exempted 4, declared 4, GROUNDED 4, UNDETERMINED 0, UNGROUNDED 0 — all `== pinned`** |
| new ledger pins | 0/4/2/21 `== pinned` | **0 / 4 / 2 / 21 — all `== pinned`** |
| `--prove` | 23/0 | **PROOFS: 23 passed, 0 failed** |
| `go build ./...` | 0 | **exit 0** |
| `go vet ./...` | 0 | **exit 0** |
| `go test -count=1 ./...` | ok | **ok** — ledger 0.652s, ledger/conformance 3.170s, loanschedule 8.453s, loanschedule/conformance 68.587s |
| `gofmt -l` | exactly `contract.go` | **exactly `nexus/internal/apps/loanschedule/contract/contract.go`** (never `-w`, G-3) |
| **vector store digest** | `8968c559…` UNCHANGED | **`8968c559fa613e8642ab030bd0a029c17d147054` — UNCHANGED; `git diff -- .softhouse/vectors` empty** |

Toolchain: repo-local, `.softhouse/bin/go-env.sh`, `GOROOT=/Users/buv/gerege-nbfi/.softhouse/toolchain/go`.
A bare `go` is `command not found` here **by design** — that is the expected state, not a broken environment.

## 9. Files changed

```
.softhouse/gates-proposed-answers.md | 26 ++++++++++
.softhouse/patterns.md               | 22 ++++++++
.softhouse/program.json              |  7 ++--
.softhouse/tasks.json                |  2 +-
```

**Docs only.** Nothing under `nexus/`, nothing in `.softhouse/conformance.sh`, nothing in
`.softhouse/vectors/`. No measurement was edited to agree with a document; every correction is **additive and
labelled**, and every superseded sentence is still readable in full next to what supersedes it.
