# T239 — r11's hygiene check re-run with a sound instrument

Branch `softhouse/T239-r11-hygiene-rerun`. No shipped code touched. No vector touched. Reference
oracle read only (by the harness, for the BAR).

**Headline.** T234 reported that `r11-hygiene.sh:35` lost **95.3 %** of its hits (3 of 64) to the
literal-`b` escape. Re-run over the population the check **actually searched** — the `T115` tree,
not the working tree — the original instrument returned **0 hit lines where a sound instrument
returns 38**. The recall loss is **100 %, not 95.3 %**. The check did not see 95 % of its
population; it saw **none of it**. T234's figure was measured over the wrong population, because
its own instrument dropped the commit argument that the line under audit passes.

And the classified answer to "what did it never see": **zero hygiene violations**. The check's
*conclusion* was right. Its *instrument* was void. Those are independent facts and this handoff
keeps them apart.

---

## 0. Provenance, and a fork point that moved under me

| | |
|---|---|
| fork point (`git merge-base HEAD origin/main`) | `477dc2da0f9edf3922e7d29e689bc6473289befc` |
| `origin/main` **at dispatch**, measured | `477dc2da0f9edf3922e7d29e689bc6473289befc` |
| `origin/main` **at BAR time**, measured | `8275f8b4ca49ea62b46c4d3d34e98b145f817414` |
| my HEAD at BAR | `fad76630eee565bd4ef21980ba82b2783e7ca6f3` |
| vector store digest | `8968c559fa613e8642ab030bd0a029c17d147054` — **unchanged by me** |

I measured the fork point rather than asserting it, and at dispatch it matched expectation exactly
(merge-base == origin/main == HEAD == `477dc2d`). **P-71 was not falsified this time** — reported
because a measurement that *confirms* is still a measurement, and this program has had it go the
other way twice.

**But `origin/main` moved during my run**, `477dc2d` → `8275f8b4`, between my first measurement and
the BAR. I did not rebase onto it: my evidence is all keyed to trees (`T115`) that are immutable, so
nothing in the finding depends on the tip. Flagging it under **P-69**: every number below is stamped
to the commit it was measured at, and the ones that matter are stamped to
`bd59187cf83c7c7161db23668e91d45bd46be2a8`, which cannot move.

**Predictions were registered in `f747a46` BEFORE any probe** —
`.softhouse/capture/t239-r11-rerun/PREDICTIONS.md`. Outcomes in §6.

---

## 1. FINDING (filing): the instrument is not at the path T239 says it is

T239's `description` and `note` both locate the instrument at
`.softhouse/capture/t138-evidence/r11-hygiene.sh:35`.

**Where I looked, and my scope (P-66/P-70):** `ls .softhouse/capture/` in this worktree;
`find . -name 'r11*' -not -path './.git/*'`; `find . -iname '*t138*'`;
`git log --all -- '.softhouse/capture/t138-evidence/'`;
`git log --all --diff-filter=A -- '*r11-hygiene*'`. Scope: this worktree at `477dc2d`, all refs.

- `.softhouse/capture/t138-evidence/` **does not exist and has never existed** on any ref.
- The instrument is at **`.softhouse/reviews/T138-evidence/r11-hygiene.sh`**, added in `477d1c3`.

T234's own HANDOFF (line 258, 410) gives the **correct** path. The error was introduced when the
driver raised T239 from T234's L-2. Low severity — I found it in one `find` — but it is the same
filing-vs-knowledge failure the task itself flags: *the correct path was already written down*.
A worker who trusted the task text and ran `ls` on the stated path would have got "no such file"
and had to decide whether that meant "already fixed" or "never existed".

---

## 2. THE POPULATION, and how I enumerated it

`r11-hygiene.sh:35-37`, verbatim:

```
git grep -n -a -E 'merge-base|main:|origin/main|rev-parse main|\bmain\b' "$T115" -- \
  .softhouse/capture/t91/ .softhouse/capture/charges/bin/preconditions.sh \
  .softhouse/capture/audit-t44/charges/bin/preconditions-COPY.sh
```

The `"$T115"` argument is load-bearing. The population is the **T115 tree**
(`bd59187cf83c7c7161db23668e91d45bd46be2a8`, "T115: record the second scratch merge — main moved
mid-run", 2026-08-21T09:08:08+08:00) restricted to those three pathspecs — **not** the working tree.

Enumerated with `git ls-tree -r --name-only $T115 -- <3 pathspecs>`, line counts via
`git show $T115:<file> | wc -l`, in `instruments/10-population.sh`, transcript
`transcripts/10-population.txt`.

| population | files | lines | what it is |
|---|---:|---:|---|
| **A** — `T115` tree, 3 pathspecs | **200** | **8,170** | what `:35` actually searched |
| **B** — working tree, same 3 pathspecs | **207** | **8,984** | what T234's `21-r11-recall-loss.sh` searched |

A ⊂ B: **0** files only in A, **7** only in B, 200 shared, of which **4** differ in content.
The 7 extras are all `T151` additions made *after* `T115`:
`out/T151-G4-CELLS.txt`, `out/T151-G67-RED-GREEN.txt`, `out/T151-VB-LEGS.txt`,
`t151-drive-g4.sh`, `t151-drive-g67.sh`, `t151-drive-vb.sh`, `t151-merge-check.sh`.

**T234's instrument omits the commit argument.** Its command is
`git grep $f -c -a -- '<pattern>' -- $P` — no revision. So it measured population B. This is not a
transcription slip in T234's prose; it is in the committed instrument, and it is why its numerator
and denominator are both wrong for the question asked.

---

## 3. ORIGINAL vs SOUND — the ratio, both terms named and both counted in the live artefact

Engines are stated in §5 and calibrated **before** any of these negatives were believed.

### Over population A — the tree `:35` actually searched

| | hit lines |
|---|---:|
| **ORIGINAL** instrument, `git grep -E`, five alternatives | **0** |
| **SOUND** instrument, `git grep -P`, five alternatives | **38** |
| same, BSD `/usr/bin/grep -E` (independent engine) | **38** |
| same, `python3 re` (independent engine) | **38** |

- **NUMERATOR** — hit lines the sound instrument found that the original did not: **38**.
  Counted in `evidence/delta-unseen.txt` (38 lines, committed).
- **DENOMINATOR** — hit lines the sound instrument found in total: **38**.
  Counted in `evidence/hits-sound-P-five.txt` (38 lines, committed).
- **Recall of the original instrument: 0 / 38 = 0.0 %. Recall loss: 38 / 38 = 100.0 %.**

Both terms are `wc -l` of two committed files in this branch, not derived from prose (**P-67**).

### Why the original returned 0 and not T234's 3 — per-alternative, both populations

| alternative | @T115 (pop. A) | @HEAD (pop. B) |
|---|---:|---:|
| `merge-base` | 0 | 0 |
| `main:` | 0 | **2** |
| `origin/main` | 0 | 0 |
| `rev-parse main` | 0 | **1** |
| `\bmain\b` (engine `-P`, sound) | **38** | **64** |

T234's "four-alternative = 3" is `2 + 1`, and **both come from the seven `T151` files that did not
exist at `T115`**. Over the real population all four literal alternatives are zero, so the original
instrument's total is zero. T234's 64 is likewise population B's number, not the check's.

**This means T234 understated the damage.** Its 95.3 % is arithmetically fine for the population it
used; the population was the wrong one. Corrected: **100 %**.

### Positive control, because the above are negatives (P-72)

Reporting `0` for a sweep is a claim that a route ran and found nothing. Through the identical route
— same engine, same tree, same pathspecs — substring `main` returns **43 hit lines across 36
files**. The route is live; the zeros are findings, not a dead rig.
[`instruments/21-crosscheck.sh` §1, `transcripts/21-crosscheck.txt`]

### Nothing was lost in the other direction

`evidence/delta-original-only.txt` is **empty** (0 lines): the original found nothing the sound one
misses. Worth stating because it need not have been zero — see the false-positive limb in §5.

---

## 4. WHAT THE CHECK NEVER SAW — all 38, classified

`instruments/30-classify.py`, transcript `transcripts/30-classify.txt`, machine-readable
`evidence/classified.json`. **Every one of the 38 is classified; none skipped (P-40).**

| class | n | disposition |
|---|---:|---|
| `VIOLATION` — a baseline computed from the moving ref `main` | **0** | — |
| `COMPLIANT` — literal sha baseline, `main` only in an attached comment | 1 | leave |
| `PROSE` — `main` inside a comment or an `echo` label | 7 | leave |
| `JVM-LOG` — `main` as the Spring Boot **thread name** in a captured JVM transcript | **29** | leave |
| `OTHER` | 1 | leave (transcript echo of a label; benign) |
| **TOTAL** | **38** | equals the delta |

**The 29 JVM-LOG hits are the interesting class.** They are captured Fineract startup lines of the
form `... INFO 1 --- [           main] o.a.f.o.monetary.dom...`. `main` there is the JVM thread
name. These are **true regex matches** — `\b` is doing exactly what it should — but they are
**false positives of the *check***: a thread name in a frozen transcript is not a git ref and never
could be a baseline. So 29 of 38 (**76 %**) of everything the sound instrument recovers is noise
generated by the pathspec including `out/` transcripts, when the check's own §2 title scopes it to
"T115's **scripts**".

The one `COMPLIANT` hit is the most on-point line in the set —
`t91/t115-rerun-attacks.sh:22`: `PRE_SHIM_BLOB=e6c1795a172168105d788321a71ee4ca62b73e36   # main's
pre-hardening charges/bin twin`. A literal blob id with `main` only in the comment: precisely the
thing the check wanted to confirm, and it confirms it.

The 7 `PROSE` hits are comments in `preconditions.sh:87`, `t115-drive-mf1.sh:12`,
`t115-drive-mf2.sh:{17,30,150}`, `t115-rerun-attacks.sh:{2,34}`. `t115-drive-mf2.sh:30` reads
*"Pre-MF-2 bytes pinned to a LITERAL IMMUTABLE SHA, never a ref computed from `main` (P-24)"* — an
assertion of compliance, not a breach.

### The check's real predicate, evaluated without the regex

"Every baseline must be a LITERAL sha" is not a question about the word `main`. I evaluated it
directly over all 10 `.sh` files in the population: parse every
`git (rev-parse|merge-base|rev-list|show|archive|cat-file|ls-tree|diff|log)` invocation outside
comments and inspect what revision it resolves.

- 15 revision-resolving invocations found.
- **0 resolve `main` or `origin/main`.**
- 7 resolve **`HEAD`** (`prove-guards.sh:45,58`; `t115-drive-mf2.sh:40,54`;
  `t115-rerun-attacks.sh:30,31,47`) — all of them deliberate "export the tree as it stands now"
  calls, all of them in files r11's *other* sub-check (`:43-47`) does enumerate.

**So: the population is clean of the defect the check was hunting. r11's verdict was correct — by
luck, not by measurement.** That distinction is the whole point of the task and I want it stated
plainly: a void instrument that happens to sit over a clean population still tells you nothing, and
the next population it is pointed at will not be clean.

---

## 5. Engines, flags, calibration — and a correction to the brief

`instruments/00-engines.sh`, transcript `transcripts/00-engines.txt`. Fixture is four lines chosen
so three failure modes are distinguishable: `main` (true match), `bmainb` (literal-`b` degradation),
`domain` (left trap), `maintain` (right trap / P-72 Mechanism 1).

| engine + flags | `\bmain\b` on the fixture | verdict |
|---|---|---|
| `git grep -E` | rc=0, **matches line 2 — `bmainb`** | **DEFECTIVE**, reads `\b` as literal `b` |
| `git grep -P` | rc=0, matches line 1 | SOUND |
| `/usr/bin/grep -E` (BSD grep 2.6.0-FreeBSD) | rc=0, matches line 1 | SOUND — honours `\b` |
| `/usr/bin/grep -P` | **rc=2**, `invalid option -- P` | **DOES NOT EXIST** |
| `python3 re` (3.9.6) | matches line 1 | SOUND |
| `ugrep` | — | **ABSENT** |
| `rg` (ripgrep) | — | **ABSENT** |

### FINDING: there are not five engines here, there are three

My dispatch brief states *"On this machine there are **FIVE** engines… ugrep honours them; ripgrep
14.1.1 is present."* **Measured: ugrep and ripgrep are not installed at all.**

Where I looked, and my scope: every one of the 9 directories on `PATH`
(`/usr/local/bin`, `/System/Cryptexes/App/usr/bin`, `/usr/bin`, `/bin`, `/usr/sbin`, `/sbin`, the
three cryptex bootstrap dirs, `/pkg/env/global/bin`, `/Users/buv/.local/bin`, `/opt/homebrew/bin`,
`/Applications/Docker.app/Contents/Resources/bin`); `zsh -i -c 'type rg; type ugrep'` (interactive
resolution, to rule out the "interactive-only" hypothesis); `/opt/homebrew/Cellar/{ugrep,ripgrep}`
and `/usr/local/Cellar/{ugrep,ripgrep}`; `brew list | grep -i -e ugrep -e ripgrep`; and
`find /opt/homebrew /usr/local /usr/bin /bin /pkg -maxdepth 3 -name ugrep -o -name rg`. All empty.
Measured 2026-08-22 at `f747a46`. **Not a statement about the world — a statement about this
machine, today, in both script and interactive contexts.**

Two consequences the program should absorb:

1. **T234's framing "`BASH_FUNC_grep` is not exported, so ugrep is interactive-only" is wrong on
   this machine** — `grep` resolves to `/usr/bin/grep` in an interactive `zsh` too, and there is no
   ugrep to resolve to. The useful half of T234's finding survives and is confirmed: **BSD grep
   DOES honour `\b\d\s\w`**, so a script that reaches for BSD grep is fine.
2. **T224's exoneration rests on a premise I cannot reproduce.** T234 corrected the lore to say
   T224's sweep "ran under ugrep, where `\b` works". If ugrep is not installed, that sweep did not
   run under ugrep. I am **not** claiming T224 is therefore engine-killed — the tool may have been
   removed since, and T224's own mechanism (right-anchoring an inflected stem) is independently
   sufficient to explain its zero. But the *evidential basis* for "it was NOT the engine" is now
   `[UNVERIFIED]`, and it is cited as settled. **Backlog item, outside my scope.**

### Which mechanism killed r11 — both were checked

**P-72 Mechanism 2 (engine), CONFIRMED.** `git grep -E` matches `bmainb`, and `\bmain\b` under `-E`
contributes 0 lines over the population while `-P` contributes 38.

**P-72 Mechanism 1 (right-anchored inflected stem), ABSENT.** `main` is not a stem being inflected;
the check wants the bare word and `\bmain\b` is the correct expression of that. Control on the
fixture: `\bmaintain\b` hits line 4, `\bmaint\b` hits nothing — the trap exists and this pattern
does not fall into it. Over the population, `main[a-z]+` (main as a prefix) = 0, so there is no
inflected form being wrongly excluded. **One mechanism, not two.**

**A third mechanism, which neither T234 nor the task names.** The degradation is not always a zero:
`git grep -E`'s `\bmain\b` **matches the literal string `bmainb`**, demonstrated on fixture line 2.
Over this population that string happens not to occur, so the result was a clean zero. In a
population containing `bmainb`, `abmainbc`, or any `b…main…b` substring, the defective instrument
would return a **false positive** and read as a *finding*. `evidence/delta-original-only.txt` is
empty here; it is not guaranteed to be empty elsewhere. Worth a pattern line: *this defect can
fabricate a hit as well as suppress one.*

---

## 6. Predictions registered before probing — outcomes

Registered in `f747a46`, before any measurement.

| | prediction | outcome |
|---|---|---|
| **P1** | sound count at `$T115` ≠ 64, because T234 measured a different population | **CONFIRMED** — 38 at T115 vs 64 at HEAD; 200 files vs 207 |
| **P2** | `git grep -E` compiles `\bmain\b` to literal `bmainb`; other 4 alternatives unaffected | **CONFIRMED** |
| **P3** | only the engine mechanism is present, not the inflected-stem one | **CONFIRMED** |
| **P4** | `/usr/bin/grep -P` exits 2; `git grep -P` works; BSD grep and ugrep honour `\b` | **PARTLY FALSIFIED** — first three confirmed; **ugrep does not exist**, so the clause about it was unfalsifiable-as-stated and its premise is wrong |
| **P5** | a multi-line matcher finds ≥1 newline-spanning hit the line-oriented run could never see | **FALSIFIED — 0 found** |
| **P6** | `/tmp/T138-merge` is absent, so §4 fails open while printing its reassurance | **CONFIRMED** |

**P5 in full, because a falsified prediction is worth more than a confirmed one.** I predicted
newline-spanning hits and found **none**. `instruments/40-multiline.py` reads all 200 files whole
and matches across newlines for the multi-token alternatives (`rev-parse\s*\\?\s*\n\s*main`,
`origin…/main`, `merge…-base`, `main…:`). Result: **0**. The route is not dead — it is calibrated on
a synthetic `rev-parse \` + newline + `main`, which the line-oriented pattern misses (0 matches) and
the multi-line one finds (1). The same script's line-oriented control reproduces **38** for
`\bmain\b`, agreeing with both grep engines. So: this population contains no continuation-split git
invocation, and **T234's 743-multi-line-hits result does not generalise to this pattern**. Line
orientation was not a defect here.

---

## 7. Driving it RED (P-22)

Two red drives, both through the route that actually runs, not by hand.

### 7a. The guard is red-blind to the exact violation it was written for

`instruments/50-red-drive.sh`, transcript `transcripts/50-red-drive.txt`.

Planted `BASE=$(git rev-list -1 main)` — a bare-word `main` used as a baseline, matching **none** of
the four literal alternatives, so only the fifth term could ever catch it. The tree is built with
plumbing (`hash-object` → temporary `GIT_INDEX_FILE` → `write-tree` → `commit-tree`), so nothing
enters my branch, my working tree, or any path outside my scope.

- planted blob `0acb5786c64b9f8ed5379e30867b7c4c8876e6d6`
- scratch commit `aecf337ed68366f5af8c6e21b341975a94145dd7`, parent `bd59187c…`, unreachable
- plant verified present in the scratch tree before grading

| | total hit lines | plant detected |
|---|---:|---:|
| original `git grep -E` | **0** (exit 1) | **0** |
| sound `git grep -P` | 39 | **1** |

**The guard passes a tree containing a baseline computed from `main`.** Fail-open, silently.

### 7b. The whole frozen script, unmodified — and a SECOND void instrument

`instruments/51-run-r11-verbatim.sh` runs
`.softhouse/reviews/T138-evidence/r11-hygiene.sh` **unedited** (the file is frozen review evidence,
T114/T176, and T239 is report-don't-fix). Transcript `transcripts/51-run-r11-verbatim.txt`.
**Script exit code 0.** What an operator reads:

```
--- any use of a ref computed from main (P-24's exact trap):
   (nothing above, or only prose, = clean)
```

Nothing printed, then the script's own reassurance. That is the fail-open shape in one screenful.

**And section 4 is a second, independent void instrument that no task has flagged.**
`r11-hygiene.sh:77-79`:

```
cd /tmp/T138-merge 2>/dev/null && \
  git grep -n -a -E '17 capture scripts|17 callers|seventeen capture' -- . | sed 's/^/   /'
echo "   (searched the MERGED tree)"
```

`/tmp/T138-merge` does not exist (checked directly; `ls` → No such file or directory). The `cd`
fails, `&&` short-circuits, the `git grep` never runs — and the `echo` on the next line is
**unconditional**, so the transcript reads `(searched the MERGED tree)` having searched nothing.
Exit status 0. This is exactly the **fail-OPEN dead-`cd` class**, live, in the same file as L-2, and
it is **not** covered by T234's L-2 (which is only about `:35`). T234 explicitly notes r11 §4 "fails
the focused sweep predicate", i.e. it was out of its scope — so this is new. **Reported, not fixed.**

Note it is unauditable in a second way too: even if `/tmp/T138-merge` still existed, it is a scratch
path outside the repo with no recorded provenance, so the section can never be re-run to the same
state. Prose-only closure (T234 §5) with a `cd` in front of it.

---

## 8. FINDING: a coverage gap the `\b` defect was hiding behind

`instruments/31-coverage.sh`, transcript `transcripts/31-coverage.txt`.

1. **`HEAD` is not in r11 §2's alternation at all.** The pattern is
   `merge-base|main:|origin/main|rev-parse main|\bmain\b`. `HEAD` is a moving ref too, and the
   population contains **8** `\bHEAD\b` lines and 7 invocations resolving it. **A fully sound engine
   running this exact pattern still reports none of them.** That is a *pattern-design* gap,
   orthogonal to the engine defect — fixing the engine alone would not have surfaced them.
   Mitigating: all 7 sites fall inside the 5 files r11's `:43-47` sub-check enumerates, so a reader
   of the full transcript would have seen them listed.
2. **That sub-check iterates a hard-coded list of 5 filenames; the population holds 10 `.sh`
   files.** Uncovered: `preconditions.sh`, `preconditions-COPY.sh`, `run-attacks.sh`,
   `shell-invariance.sh`, `verdict.sh`. Two contain a revision-resolving invocation. I opened both:
   each is a **comment** citing the literal blob `e6c1795a172168105d788321a71ee4ca62b73e36`
   (`preconditions.sh:49`, `preconditions-COPY.sh:33`) — **compliant, not violations**. So the gap
   is real but cost nothing here.

---

## 9. THE BAR

`instruments/90-bar.sh`, full transcripts `transcripts/90-bar.txt` and
`transcripts/90-conformance-full.txt`. Harness invoked with **`bash`**, never `sh`.

```
probe line               PRESENT (tested for presence first) and reading:
                         conformance: reference oracle (https://localhost:8443/...) probe = up
                         oracle probe    UP
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.

loanschedule   parity vectors    PASS 46   FAIL 0
               cells compared    7884 graded, 93 ungraded
               inadmissible      0
               harness errors    0
               invariant violations  0
ledger         parity            PASS 4    FAIL 0
               oracle-refusal    PASS 2    FAIL 0
               inadmissible      0
               harness errors    0

exemption census READ: exempted assertions (graded) = 4 == pinned 4
exemption census READ: declared exemptions (loaded) = 4 == pinned 4
exemption census READ: GROUNDED                     = 4 == pinned 4
exemption census READ: UNDETERMINED-ON-THE-RECORD   = 0 == pinned 0
exemption census READ: UNGROUNDED                   = 0 == pinned 0
exemption census READ: LEDGER declared exemptions   = 0 == pinned 0
exemption census READ: LEDGER parity vectors        = 4 == pinned 4
exemption census READ: LEDGER oracle-refusal vector = 2 == pinned 2
exemption census READ: LEDGER money cells compared  = 21 == pinned 21

go build ./...        rc=0
go vet ./...          rc=0
go test -count=1 ./...  rc=0   (ledger, ledger/conformance, loanschedule, loanschedule/conformance all ok)
gofmt -l .            internal/apps/loanschedule/contract/contract.go   (exactly one; NOT gofmt -w'd, G-3)

vector store digest   8968c559fa613e8642ab030bd0a029c17d147054  — UNCHANGED BY ME
```

All census pins `4/4/4/0/0` and ledger pins `0/4/2/21` read `== pinned`. **BAR: PASS.**

---

## 10. What is still unchecked, and its scope

Scope of everything above: the **T115 tree restricted to r11's three pathspecs** — 200 files,
8,170 lines — plus the `r11-hygiene.sh` file itself. Nothing else was swept.

1. **r11 sections 1 and 3 were not audited as instruments.** I ran them (they are in the verbatim
   transcript) but did not re-derive their populations. §3's bare-`grep` sub-check at `:61-64`
   pipes `grep 'grep' | grep -v 'LC_ALL=C'` — no `\b`, so not engine-affected, but its predicate is
   untested by me. **UNVERIFIED.**
2. **The other nine `git grep -E` + escape sites T234 lists** (`RESUME.md:86`, `A2-33.md:66`,
   `T232.md:89/92/184`, `patterns.md:1307/2100/2103`, `a2-33-dec2-rev5/REVIEW.md:168`) — I did not
   re-verify T234's claim that eight are prose documenting the defect. Out of my scope.
3. **The `/tmp/T138-merge` sweep (§4) has not been re-run soundly.** I proved it is dead; I did not
   reconstruct the merged tree and answer its question ("other restatements of '17 capture
   scripts'"). That needs the merged tree, which no longer exists. **Backlog.**
4. **Whether other instruments in the repo `cd` into scratch paths.** I found this one by reading
   r11 end to end. I did **not** sweep the repo for the dead-`cd` class. Given it produced a
   fail-open in the very first instrument audited closely, **this is the highest-value follow-up I
   can name**, and it is outside T239's scope.
5. **T224's ugrep premise** (§5) — `[UNVERIFIED]` and currently cited as settled.

## Backlog raised (all outside my scope — reported, not diffed)

| # | item | where |
|---|---|---|
| B-1 | **`r11-hygiene.sh:77-79` fails OPEN via dead `cd /tmp/T138-merge` and prints "(searched the MERGED tree)" regardless.** New; not covered by T234's L-2. | `.softhouse/reviews/T138-evidence/r11-hygiene.sh:77` |
| B-2 | Sweep the repo for the **dead-`cd` fail-open class** — `cd X 2>/dev/null && <sweep>` followed by an unconditional reassurance echo. | repo-wide |
| B-3 | T234's `instruments/21-r11-recall-loss.sh` **omits the commit argument**, so its 61/64 and 95.3 % are over the wrong population. Correct figures: 0/38, 100 %. | `.softhouse/capture/t234-sweep-instrument-audit/instruments/21-r11-recall-loss.sh` |
| B-4 | **ugrep and ripgrep are not installed**; the "five engines" lore and T234's "ugrep is interactive-only" both need correcting, and T224's exoneration re-grounded. | `.softhouse/patterns.md` (driver files patterns) |
| B-5 | T239's own task text points at a **non-existent path** for the instrument. | `.softhouse/tasks.json` T239 |
| B-6 | Candidate pattern: **the literal-`b` defect can FABRICATE a hit** (`\bmain\b` matches `bmainb`), not only suppress one. Existing lore treats it as recall-only. | `.softhouse/patterns.md` |
| B-7 | r11 §2's alternation **contains no `HEAD` term**, and its `:43-47` sub-check covers **5 of 10** `.sh` files. | `.softhouse/reviews/T138-evidence/r11-hygiene.sh:35,44` |

## Artefacts, all committed on this branch

```
.softhouse/capture/t239-r11-rerun/
  PREDICTIONS.md                     registered in f747a46, BEFORE probing
  instruments/00-engines.sh          engine matrix + calibration (carries its own v1 bug as a lesson)
  instruments/10-population.sh       population A vs B enumeration
  instruments/20-rerun.sh            the re-run, the ratio, the delta
  instruments/21-crosscheck.sh       positive control, per-alternative split, 3rd engine (BSD grep)
  instruments/30-classify.py         classification of all 38 + the check's real predicate
  instruments/31-coverage.sh         HEAD gap + sub-check file coverage
  instruments/40-multiline.py        multi-line matcher (P5)
  instruments/50-red-drive.sh        planted violation, scratch tree, guard blind
  instruments/51-run-r11-verbatim.sh the frozen script run unmodified
  instruments/90-bar.sh              the BAR
  transcripts/*.txt                  one per instrument, plus 90-conformance-full.txt
  evidence/hits-original-E-five.txt  0 lines   <- ratio denominator's counterpart
  evidence/hits-sound-P-five.txt     38 lines  <- ratio denominator
  evidence/delta-unseen.txt          38 lines  <- ratio numerator
  evidence/delta-original-only.txt   0 lines
  evidence/classified.json           all 38 with class, file, line, context
  evidence/multiline-hits.json       [] (empty — P5 falsified)
  evidence/calibration-fixture.txt   the 4-line fixture, tracked so git grep can see it
```
