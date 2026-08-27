# T121 — independent review of T113 (`softhouse/T113-close-forgeable-token`)

**Verdict: MICRO-FIX.** One paragraph of prose in the shipped harness, plus its two
restatements. **No behaviour change is required and none is recommended.** The
one-line fix is correct, minimal, and I drove it red and green myself against the real
pre-fix bytes on three different major versions of bash. Every number T113 reports
reproduces — the rig legs, the matrix, the exit-code surface, and the whole acceptance
battery on a scratch merge into a `main` that has moved **twice** since T113 measured.

The MICRO-FIX is this: T113 correctly withdrew T106's `IFS=` claim, and then wrote a
**false statement of bash `read` semantics** in its place — in `conformance.sh`, in
`interpreter-matrix.sh`, and in its own handoff. The disposition it defends is right;
the reason it gives is wrong, and it is exactly the reason a future worker would cite
to delete the prefix.

Reviewer: T121, fresh, no part in planning T97, T106 or T113. Host: macOS 26.5.1 /
Darwin 25.5.0 arm64, GNU bash 3.2.57. Interpreters exercised by me:
bash **3.2.57**, bash **4.4.0** (built from source — see N-T121-1), bash **5.3.9**
(glibc and musl), `/bin/sh` 3.2.57, `dash`, `zsh`, `ksh93`, `mksh`, `yash`,
busybox `ash`, busybox `sh`, `bash -r`, `bash --posix`, `bash --posix -r`,
`argv[0]=sh`, `argv[0]=sh --posix`, `POSIXLY_CORRECT=1`, bash with `/dev/fd`
**removed**, and bash with `/dev/fd` **present but mode 000**.

Reference oracle (Fineract): contacted **read-only**, only by the harness's own
`curl -sk` health probe during two graded runs, plus one health check (HTTP 200).
**No `docker compose` command of any kind** — nothing restarted, rebuilt, re-seeded
or written. Throwaway containers were `eclipse-temurin:21-jdk` and `alpine:3`,
`docker run --rm`, unrelated to the Fineract compose project. "The oracle" here always
means the Fineract reference implementation; Oracle Database appears nowhere.

---

## 0. What I checked, and how — so silence is distinguishable from not looking

| # | Required by the brief | Done | Where |
|---|---|---|---|
| 1 | **F-T113-1** — adjudicate T113 vs T106 on the `IFS=` prefix, from the manual AND by experiment | yes — **SPLIT RULING**, and a new finding | §1, §2 |
| 2 | **F-T113-2** — re-open the cited line 53 myself | yes — **T113 UPHELD in full** | §3 |
| 3 | T106's rig, bytes verified unmodified, **both legs run by me** | yes — 8/0 and 7/1 reproduced exactly | §4 |
| 4 | Interpreter matrix; hunt a FALSE REFUSAL; close the bash 4.x gap | yes — **none found**; **gap CLOSED** | §5, §6 |
| 5 | The `readonly`-sourced behaviour change; caller sweep | yes — fail-closed, one-directional, **zero callers** | §7 |
| 6 | Exit-code surface 0/1/2/3 | yes, one qualification | §8 |
| 7 | The killed worker's residue — every `[VERIFIED` tag | yes — 14 sites, all re-measured or listed | §9 |
| 8 | Attack the rigs, not just the fix (P-22) | yes — **N-T113-3 confirmed and EXTENDED to 3 more scripts** | §10 |
| 9 | P-24 scratch merge into **current** main, throwaway clone | yes — all seven required numbers hit | §11 |

---

## 1. RULING on F-T113-1 — **SPLIT. T113's disposition upheld; T113's derivation refuted.**

### 1a. T106's claim is FALSE. T113 is right to withdraw it.

T106's review says:

> `IFS=e` is worth naming: `e` occurs in the token, so without the `IFS=` prefix in the
> probe this would have been a false refusal — **that prefix earns its place**.

Measured, with the prefix **deleted** from a copy of the harness
[VERIFIED: T121, bash 3.2.57, 4.4.0 and 5.3.9]:

```
IFS=[e   ] in=[conformance-psub-live] -> [conformance-psub-live]  INTACT
no-prefix harness, IFS=[e] -> exit 0   (ADMITTED)
```

Not a false refusal, on any of three bash major versions. **T106's claim does not
survive measurement, and T113's withdrawal of it is correct.**

I went further than T113's nine IFS values, because "nine values did not break it" is
not the same claim as "nothing can break it". Brute force, prefix deleted, against the
real token:

| sweep | values tried | mangled the token |
|---|---|---|
| every printable single char as IFS, bash 3.2.57 (+ space, tab, newline) | 97 | **0** |
| every printable single char as IFS, bash 5.3.9 | 94 | **0** |
| every printable single char as IFS, bash 4.4.0 | 94 | **0** |
| every **pair** drawn from the token's own alphabet, bash 3.2.57 | 256 | **0** |
| **all 94 printable chars at once** as IFS | 1 | **0** |

**No false refusal from `IFS` is reachable today, with or without the prefix.**

### 1b. But T113's REASON is false, and it is shipped in the harness.

`.softhouse/conformance.sh:171-174` (and two more sites, §2) now says:

> T113 tested that by DELETING the prefix and it is not so: `read` with a SINGLE
> variable assigns the whole line **and strips only leading/trailing IFS *whitespace*,
> so a non-whitespace delimiter — even one occurring in the token, even as its first or
> last character — changes nothing.**

**That is not what bash does.** Re-derived from the bash manual's `read` description
("*any leftover words **and their intervening delimiters** assigned to the last name*"
— *intervening*, not *trailing*) and then measured. A trailing non-whitespace IFS
delimiter **is** removed when it is the only delimiter occurrence in the line:

```
IFS=[z ] in=[abcz                 ] -> [abc                 ]  MANGLED   <- counterexample
IFS=[e ] in=[abce                 ] -> [abc                 ]  MANGLED
IFS=[: ] in=[abc:                 ] -> [abc                 ]  MANGLED
IFS=[z ] in=[zabc                 ] -> [zabc                ]  INTACT  (leading — kept)
IFS=[z ] in=[abzc                 ] -> [abzc                ]  INTACT  (middle  — kept)
IFS=[z ] in=[abczz                ] -> [abczz               ]  INTACT  (two     — kept)
```

[VERIFIED: T121, identical on bash **3.2.57**, **4.4.0** and **5.3.9**.]

**The measured rule is:** with a single variable, `read` strips leading/trailing IFS
*whitespace*, **and additionally strips one trailing non-whitespace IFS delimiter when
that delimiter occurs exactly once in the line and is its final character.**

And the counterexample lands directly on the probe's own subject. A token of the
*same shape*, differing only in its last character:

```
token=[conformance-psub-livz] IFS=[z] -> [conformance-psub-liv]  MANGLED
token=[conformanc-psub-liv3 ] IFS=[3] -> [conformanc-psub-liv ]  MANGLED
```

### 1c. Why the real token survives — and why that matters

`conformance-psub-live` ends in `e`, and `e` occurs **twice** (`conformanc**e**` and the
final `**e**`). The single-occurrence-at-the-end shape therefore never arises, for any
single character, because the token's last character is not unique within it.

**The probe survives by an accident of how the token is spelled, not by the semantics
T113 states.** That inverts the risk the paragraph is trying to manage. The file's own
list of reasons to keep the prefix reads:

> it is the difference between "cannot break today" and "cannot break if someone later
> **reads two variables** or **puts whitespace in the token**".

The most likely third case is missing, and it is the one an editor would actually do:
**someone changes the token.** Rename it to `conformance-psub-livz`, or `…-probe`, or
anything whose final character is unique, and `IFS=<that char>` becomes a genuine false
refusal the moment the prefix is gone. A worker reading the shipped sentence — *"a
non-whitespace delimiter, even as its first or last character, changes nothing"* — has
been told, in the harness's own voice, that deleting the prefix is safe. It is not.

**This is the P-22 shape one remove: not a guard that cannot fail, but a true guard
carrying a false certificate.** T113 names that risk itself — *"a guard that is credited
with a save it never made is the P-22 failure in miniature"* — and then commits the
mirror image of it.

**Ruling.** Withdraw the claim: correct. Keep the prefix: correct. **Replace the
derivation** with the measured rule and add the token-change case to the list. Prose
only; the code is right as it stands. → **F-T121-1, below.**

**Was this REJECTED-class?** No. The brief's REJECTED test was *"T113 deleted a true
justification"*. It did not: it kept the prefix, and T106's justification was genuinely
false. What it deleted was a false reason and what it wrote was a different false
reason. That is MICRO-FIX.

---

## 2. F-T121-1 (P2, MICRO-FIX) — the false `read` rule, at three sites

P-26 sweep for the **concept**, not the sentence. T113 swept its *withdrawal* to every
site correctly; the *replacement* is wrong at every one of them.

| site | text |
|---|---|
| `.softhouse/conformance.sh:171-174` | **the shipped harness** — "strips only leading/trailing IFS *whitespace*, so a non-whitespace delimiter — even one occurring in the token, even as its first or last character — changes nothing" |
| `.softhouse/handoff/…/T113-evidence/interpreter-matrix.sh:142-145` | the rig's own comment, same sentence |
| `.softhouse/handoff/…/T113.md:346-348` | the handoff, same sentence |

Suggested replacement (docs only, no behaviour change):

> `read` with a SINGLE variable assigns the whole line, stripping leading/trailing IFS
> **whitespace** — **and one trailing non-whitespace IFS delimiter, when that delimiter
> occurs exactly once in the line and is its last character** (`IFS=z`, line `abcz` →
> `abc`) [VERIFIED: T121, bash 3.2.57 / 4.4.0 / 5.3.9]. `conformance-psub-live` escapes
> that shape only because its final `e` also occurs in `conformance`; a token whose last
> character is unique within it — `conformance-psub-livz` — **is** truncated by
> `IFS=z`. So the prefix is not a measured save **for today's token**, but it is not
> merely stylistic either: it is what makes the probe robust to **renaming the token**,
> as well as to reading two variables or putting whitespace in it.

**What this sweep could not have found:** IFS values containing non-ASCII or multibyte
characters; IFS strings of three or more characters other than the all-printable case;
any locale other than the host default (I did not sweep locale × IFS); a restatement of
the rule as a chart, a count, or a silence where a qualification belongs; and any site
outside the eleven files this branch touches.

---

## 3. RULING on F-T113-2 — **T113 UPHELD in full. T106's citation is false.**

I re-opened the line rather than accepting either party's description of it.
`git show f2813c8:.softhouse/conformance.sh`, the bytes T106 was reading, lines 51-60:

```
51  # WHY IT EXISTS (T76 and T77 found this independently in the same fire).
52  # `sh .softhouse/conformance.sh` used to die at the first process substitution
53  # (the `done < <(find …)` in guard_no_float_in_vectors) with a bash syntax error
54  # and **exit 2** — and 2 is this harness's "unusable / oracle unreachable" code AND
55  # the /softhouse-program driver's oracle-is-down stop condition.
```

T106 wrote that F1's vacuous-pass hazard is *"precisely the P-22 failure mode the
harness's own comment at **line 53** cites"*. Line 53 sits inside `WHY IT EXISTS`, and
it describes the process substitution **dying** with a syntax error and being mistaken
for an oracle outage. That is the **opposite** failure from a guard `return`ing 0 having
inspected an empty file set. It is a loud death, not a silent pass.

I also checked T113's second, sharper claim — that the only P-22 sentence anywhere in
T97's file is elsewhere:

```
$ git show f2813c8:.softhouse/conformance.sh | grep -n 'P-22\|cannot fail is worse'
872:  # produce. (P-22 — a check that cannot fail is worse than no check.)
```

**Exactly one hit, at line 872, the `--help` comment.** T113's statement is correct to
the line number. And T113's remedy is the right one: the replacement **names the block**
(`WHY IT EXISTS`) instead of numbering it, because the number is precisely what drifted
— the same block is line 51 in T97's bytes and line 56 in today's. A citation nobody
re-opens is a claim, not a fact; this one was a claim, and it was wrong.

---

## 4. T106's acceptance rig — bytes verified, both legs run by me

**Bytes first.** Extracted from both branches and compared:

```
cb11a2be18c692d32ef5100066364a4d6da33086a029bf82b1a75aa3a3bc0005  T106-review-t97:…/T106-evidence/prove-token-forgeable.sh
cb11a2be18c692d32ef5100066364a4d6da33086a029bf82b1a75aa3a3bc0005  T113-close-forgeable-token:…/T113-evidence/prove-token-forgeable.sh
BYTE-IDENTICAL: T113 did not modify T106's rig
```

Matches T113's reported sha exactly. **T113 did not touch the rig it is graded by.**

**LEG 1 — PRE-FIX**, `git archive f2813c8` to a clean tree, T106's canonical rig dropped
in at the identical relative path (not a hand-edited copy of the fixed file):

```
### harness sha256: c69e30ff6617debbd2e013cefd903479dcab0f8c9b0c4e3ea273e88b1907951a
### does this harness contain the F1 assignment?  absent — this is PRE-fix
[1] the harness AS SHIPPED, with the probe's redirection failing at run time
  ok    clean environment -> REFUSED (exit 3)
  ok    _conformance_psub_line pre-seeded -> ADMITTED (F1) (exit 0)
[2] the same harness plus the one-line fix
  ok    clean environment -> still REFUSED (exit 3)
  ok    _conformance_psub_line pre-seeded -> REFUSED (exit 3)
[3] control: a HEALTHY bash is still admitted, fix or no fix
  ok    unmutated harness, clean (exit 0)
  ok    unmutated harness, pre-seeded (exit 0)
T106 FORGE PROOF: 8 passed, 0 failed
RIG-EXIT=0
```

**LEG 2 — POST-FIX**, tip of `softhouse/T113-close-forgeable-token`:

```
### harness sha256: ee46aadf97eca96190a2189dce8ae3121e156382c4e9ced22fa050d5bd8239ab
234:      _conformance_psub_line=     ^^ PRESENT — this is POST-fix
[1]b  FAIL  _conformance_psub_line pre-seeded -> ADMITTED (F1)
            expected exit 0, got 3
T106 FORGE PROOF: 7 passed, 1 failed
RIG-EXIT=1
```

**8/0 and 7/1 exactly as T113 reports, and the pre-fix sha256 `c69e30ff…951a` matches
T113's figure to the character.** No residue left in `.softhouse/` on either leg.

**Is T113's reading of the post-fix red row right? Yes, and I checked it rather than
accepting it.** Row [1]b is written as `row "…-> ADMITTED (F1)" 0` — it **asserts that
the forge works**. It is a defect detector, not a regression test, so closing the forge
is *required* to redden it. Three things confirm the row went red for the right reason:

- the rig's own two anti-vacuity rows are green (`mutation applied`, `candidate fix
  applied to a second copy`), so the mutation still bites;
- row [1]**a** — same mutant, clean environment — is still `3`, so the mutant is still
  psub-broken and the guard still refuses it;
- **section [3], the healthy-bash control, is green in BOTH legs** (`exit 0` clean and
  `exit 0` pre-seeded). That is the discriminator between "a fix" and "a blanket
  refusal", and it holds.

**One degradation in the rig worth recording** (not a T113 defect): post-fix, `$ORIG` is
derived from the *live* harness, which already carries the fix, so `$FIXED` receives a
**second** `_conformance_psub_line=` line and rows [1] and [2] now test nearly the same
thing. That is exactly why T106's rig cannot serve as the standing regression test —
and exactly why T113 was right to reject T106's literal F5 text and add an asserting row
[7] to T97's rig instead. See §10.

---

## 5. The hunt for a FALSE REFUSAL — none found, across 17 interpreters

This is the failure mode T86 hit in its own draft and the way this fix could be wrong.
Every row below was run by me.

**Host, `interpreter-matrix.sh`: 26 passed, 0 failed** — reproduced.

**bash 5.3.9 container**, PRE-FIX and POST-FIX side by side so a change in admission
would show. Every shape **admitted (0) on both**: plain, `--posix`, `argv[0]=sh`,
`argv[0]=sh --posix`, `POSIXLY_CORRECT=1`, `env -i`, `BASH_ENV=/dev/null`,
`IFS ∈ {oc, e, c, ' ', -, l, v, i}`, and all three pre-seeded probe variables including
the forge itself. `bash -r` → 3 on both.

**bash 4.4.0** — first measurement in this program, §6.

**Exotic interpreters T113 did not try** (alpine:3, extra shells installed). Its matrix
skips absent shells silently, so on this host these had never been asked:

| interpreter | POST-FIX | verdict tokens | PRE-FIX |
|---|---|---|---|
| busybox `ash` | **3** | 0 | 3 |
| busybox `sh` | **3** | 0 | — |
| `/bin/ash` | **3** | 0 | — |
| `mksh` | **3** | 0 | 3 |
| `yash` | **3** | 0 | 3 |
| alpine `/bin/sh` (busybox) | **3** | 0 | — |

**Every one refused correctly, at the right code, with zero verdict tokens, and the fix
moved none of them.**

**A `/dev/fd` that is present but restricted** — the brief's last exotic case, and a
psub-failure shape nobody in this chain had measured. `/dev/fd` replaced with an empty
directory at mode `000`, on bash 5.3.9/musl:

```
psub capability now : []                      (dead, but /dev/fd EXISTS)
POST : clean=3  forged=3      <- closed
PRE  : clean=3  forged=0      <- THE FORGE, on a second real interpreter shape
```

**This is an independent second real-interpreter reproduction of T106's F1**, distinct
from `/dev/fd` removed. The defect and the fix both hold in it.

**Total across every refusal shape I could produce on the merge — `sh`, `dash`, `zsh`,
`ksh`, `bash --posix`, `bash -r`, `bash --posix -r`: 0 verdict tokens.**

---

## 6. N-T121-1 — **the bash 4.x gap is CLOSED**, and it produced a new datum

`docker pull bash:4.4` stalled for me exactly as it did for T97, T106 and T113 — no
output, no image, had to be killed. But the block is **daemon-side, not network-side**:

```
gnu.org      rc=200  time=1.53
dockerhub    rc=401  time=0.71     (401 is the normal unauthenticated response)
```

So I built one instead. GNU bash **4.4.0** from the official tarball
(`sha256 d86b3392c1202e8ff5a423b302e6284db7f8f435ea9f39b5b1b20fd3ac36dfcb`), compiled
inside a throwaway `eclipse-temurin:21-jdk` container (Ubuntu/glibc, aarch64). The
guard matrix then ran under it with `--network none`.

**Result: the guard behaves on bash 4.4 exactly as it does on 3.2.57 and 5.3.9. Zero
false refusals; the forge exists and the fix closes it.**

```
=== 1. FALSE-REFUSAL HUNT on bash 4.4 — every shape must be ADMITTED ===
  plain / env -i / BASH_ENV / -u -e -C -f -p            POST=0  PRE=0
  IFS ∈ {oc,e,c,' ',-,l,v,i,z}                          POST=0  PRE=0
  the forge env on a healthy shell                      POST=0  PRE=0
=== 2. bash 4.4 -r ===                                  POST=3  PRE=3   tokens=0
=== 6. /dev/fd REMOVED — psub genuinely dead ===
  PRE-FIX   clean=3   forged=0        <- the forge, on bash 4.4
  POST-FIX  clean=3   forged=3        <- closed, on bash 4.4
```

**And a fact nobody in this chain had:** bash 4.4 **kills process substitution in POSIX
mode**, like 3.2 and unlike 5.x.

```
plain: [CAP]   --posix: []   argv[0]=sh: []   POSIXLY_CORRECT=1: []
```

All three POSIX-mode shapes are correctly refused at exit 3. This **confirms** the
harness's `5.1+` attribution at `conformance.sh:75-78` rather than refuting it — 4.4 is
on the dying side of the boundary — and it **brackets** the boundary to `(4.4, 5.3.9]`.
It also widens the practical population: the "`sh conformance.sh` is fine on Fedora/RHEL"
framing is true only of bash **5.x**; every RHEL 7 / CentOS 7 / Debian 8-9 /
Ubuntu 14.04-18.04 bash is 4.x and is **correctly refused**. Worth a sentence in the
harness some day; not a defect, and not blocking.

*Still [UNVERIFIED]:* bash 5.0 and 5.1 themselves — I bracketed the boundary, I did not
locate it.

---

## 7. The disclosed behaviour change — fail-closed, one-directional, zero callers

Sourcing the harness into a shell where `_conformance_psub_line` is already `readonly`
now refuses, where pre-fix it was admitted. Reproduced by me on three bash versions:

| | PRE-FIX | POST-FIX |
|---|---|---|
| healthy bash 3.2.57 | 0 (admitted **by forgery**) | **3** |
| healthy bash 4.4.0 | 0 | **3** |
| healthy bash 5.3.9 | 0 | **3** |
| psub-**dead** bash 5.3.9 | 0 | **3** |

**Fail-closed:** every cell moves toward refusal; none moves toward admission.
**One-directional:** the new outcome is exit 3, which prints zero verdict tokens and
cannot turn a red run green — while the outcome it replaces was an *admission produced
by forgery rather than by evidence*, which can. The trade is correct.

**Callers.** I swept for it rather than restating T113:

- `.claude/skills/softhouse-uat/SKILL.md:23` → `bash .softhouse/conformance.sh`
- `.claude/skills/softhouse-program/SKILL.md:109` → discusses exit codes only
- `.softhouse/bin/` → four scripts; **not one of them references `conformance.sh` at
  all**, and the only `.`/`source` in the directory is `go-env.sh` sourcing itself into
  a caller.
- A regex sweep for `source`/`.` applied to any path ending `conformance.sh`, across
  `*.sh`, `*.bash`, `*.py`, `*.go`, `*.md`: **zero hits.**

**No caller sources the harness.** T113's claim confirmed.

---

## 8. Exit-code surface — 0/1/2/3 intact, with one qualification

Complete census on the merge: `exit "$EXIT_WRONG_INTERPRETER"` (3, one site),
`exit "$EXIT_UNUSABLE"` (2, **eight** sites vs seven on main — the eighth is the new
`--help` arm), and `exit $?` / `exit 0`. `EXIT_WRONG_INTERPRETER=3` at :228,
`EXIT_UNUSABLE=2` at :327. **No new numeric exit.** `git diff main…HEAD -- nexus/` is
empty, so `Summary.ExitCode()`'s 1/2/2/0 could not have moved. Measured on the merge:

```
--help (healthy)        -> 0     unknown option --zzz  -> 2
sh (wrong interpreter)  -> 3     graded run            -> 0 (VERDICT: PASS)
--help, sentinel deleted-> 2     verdict tokens on that path: 0
```

**Is the `--help` 1→2 move an improvement? Yes — and T113's framing is true but
incomplete.** Driven red by deleting the sentinel: exit **2**, the correct diagnostic
text, zero verdict tokens. Exit 1 is this file's "at least one graded vector FAILED", so
a damaged header reported as 1 would have been indistinguishable from a real port defect
to any caller reading exit codes. Moving it out of that bucket is right, and 2 is the
code the file's own EXIT CODES table assigns to "the harness is unusable", which a file
with a damaged header is. The adjacent `--*` arm already used it.

**The qualification T113 does not state.** `conformance.sh:59` — 935 lines above the
change, in this same file — says 2 is *"this harness's 'unusable / oracle unreachable'
code **AND** the /softhouse-program driver's oracle-is-down stop condition."* So the new
exit 2 does join a bucket that a driver can read as an outage. I rule this **not a new
collision and not blocking**: exit 2 already carries six other non-oracle causes, so this
is a seventh member of an existing polysemy rather than a new one; no grading caller
passes `--help`; and the stderr text names the sentinel explicitly. T113's sentence
"*removes a collision with the graded-FAIL code rather than creating one*" is accurate;
it is just not the whole sentence. → **F-T121-3, P3.**

**Note for the record:** relative to **main**, `--help` cannot fail at all (main has no
sentinel logic), so the 1→2 move is entirely internal to the unmerged T97+T113 chain.
No pre-existing `main` exit path was renumbered. That is the invariant that matters and
it holds.

*Cosmetic (P4, not counted as a finding):* with the sentinel absent, `usage()` prints
`(or is at line )` with an empty number, because `end` is empty on that branch.
Inherited from T97, harmless.

---

## 9. The killed worker's residue — all 14 `[VERIFIED` tags accounted for

T113 reports that the rescued commit `b9f9ab3` carried five `[VERIFIED: T113]` tags
standing for measurements no T113 had made, and says it re-measured every one. I did not
take that on report. Grepping the branch gives **14** `[VERIFIED` sites; here is each,
with who I could confirm it:

| site | claim | re-measured by me? |
|---|---|---|
| `conformance.sh:118-121` | psub-dead 5.3.9: pre-fix 3/0, post-fix 3/3 | **YES** — §4, §5, and on 4.4 |
| `:153` | readonly-sourced refusal, 3.2.57 and 5.3.9 | **YES** — §7, plus 4.4 |
| `:164` (T97) + `:177` (T113) | IFS rows admitted, both directions | **YES** — §1, brute-forced far wider |
| `:189` | `builtin eval` shields a false refusal from an exported `eval()` | **YES** — bare `eval` + exported `eval()` → **3**; `builtin eval` → **0**. Driven red. |
| `:203` | `[() { return 1; }` → guard skipped, psub-dead 5.3.9 **admitted** | **YES** — container, PRE and POST both 0 |
| `:205` | `[() { return 0; }` → **healthy** bash refused, text says "BASH_VERSION is unset" when it is not | **YES** — 3.2.57 exit 3 with that exact line; 5.3.9 exit 3 |
| `:209` | `builtin() { echo …-live; }` forges the token, psub-dead 5.3.9 admitted | **YES** — container, 0 |
| `:214` | no fixed point: `\builtin` / `\command` do not bypass function lookup | **YES** — all four print `HIJACKED`, 3.2.57 and 5.3.9 |
| `:96` (T97) | the pre-fix defect from `main`'s own bytes → exit 2, fabricated toolchain line | **YES** — see below |
| `:255` (T97) | `$-` contains `r` under `bash -r`: `hrB` / `hrBc` | **YES** — `hrB` script, `hrBc` under `-c` |
| `:30`, `:78`, `SKILL.md:41` (T97) | bash **5.2.37** admitted in four shapes | **NO** — 5.2.37 not available to me. I measured 5.3.9 in all four shapes. **[UNVERIFIED by T121]** |

**The motivating defect, re-run by me against `main`'s ACTUAL bytes on the merge**
(P-22: a proof that only shows the "after" cannot distinguish a fix from a no-op):

```
main harness sha256: 225181baeff9a0f5df51646157a7f93174e05859e80df8fd032cb06725a70000
$ bash -r <main's bytes>
  line 107: cd: restricted
  line 164: /dev/null: restricted: cannot redirect output
conformance: no Go toolchain. Expected /.softhouse/bin/go-env.sh to put one on PATH.
conformance: EXIT 2 — the harness is unusable. This is NOT a pass.
exit=2
$ bash -r <today's bytes>     exit=3, verdict tokens=0
```

Same invocation, same host, **2 → 3**, blaming a path that exists nowhere before and
naming the real cause after. **This is a fix, not a no-op**, and `main`'s sha matches
T106's independently recorded figure.

**Conclusion: I found no inherited-but-unmeasured claim surviving on this branch.**
Every `[VERIFIED: T113]` tag is now backed by a measurement I made myself, and the one
site I could not reach is a **T97** tag about bash 5.2.37 that T106 also did not close.

**The F4 leak is fixed and did not re-leak.** `SKILL.md:38` now reads *"admitted, and
the harness starts normally"* with the reason stated. A grep for `and works` across
`.claude/`, `conformance.sh` and `vectors/README.md` returns exactly one hit — the
sentence that *quotes* the retracted wording in order to retract it. Correct.

**F5 was applied, and I drove row [7] red myself** — see §10.

---

## 10. F-T121-2 (P3) — N-T113-3 is real, and it is **three scripts wider** than T113 says

T113 discloses `hostile-env-matrix.sh` as "a probe advertised as a rig" (N-T113-3) and
`interpreter-matrix.sh`'s silent skipping (N-T113-4). **Both confirmed.** The matrix's
`[1b]` printed three rows on my host and passed; five shells were absent and it said
nothing about them.

But N-T113-3 names one file. Sweeping every script the branch touches for the shape —
*what is the observation, and could it be produced by the check never running?* —
finds **four**:

| script | fail counter | exit depends on the observation | disclosed by T113? |
|---|---|---|---|
| `hostile-env-matrix.sh` | **no** | **no** (always 0) | yes — N-T113-3 |
| `readonly-sourced-edge.sh` | **no** | **no** (always 0) | **NO** |
| `psub-dead-container.sh` | **no** | only for INERT guards | **NO** |
| `bash5-matrix-container.sh` | **no** | only for INERT guards | **NO** |
| `interpreter-matrix.sh` | yes | yes | n/a |
| `prove-token-forgeable.sh` (T106's) | yes | yes | n/a |
| `prove-interpreter-guard.sh` (T97's) | yes | yes | n/a |
| `conformance.sh` | yes | yes | n/a |

The last two container scripts are the interesting ones. Both carry **strong INERT
guards** — a pinned immutable sha, an asserted sha256, a refusal if the baseline already
contains the fix, a refusal if the live harness does not — and T113 deserves credit for
all of that; it is the P-24 lesson applied correctly. But those guards protect against
the **subject being absent**. Neither script asserts its **observation**. Their
expectations live in comments:

```
psub-dead-container.sh:16   #   PRE-FIX   clean=3  forged=0
psub-dead-container.sh:17   #   POST-FIX  clean=3  forged=3
bash5-matrix-container.sh   echo "psub capability now: $(cap)   (must be 'no')"
bash5-matrix-container.sh   echo "  the same shape under --posix and argv[0]=sh (all must refuse):"
```

*"must be no"* and *"all must refuse"* are written in prose and nowhere in code. If the
fix regressed and `forged` came back `0`, `psub-dead-container.sh` would print it and
**exit 0**. That is the flagship claim of the whole task, carried by a script that
cannot fail on it.

**Severity: P3, not blocking**, for a reason I checked rather than assumed: the standing
regression coverage does not live in these scripts. It lives in **row [7] of T97's rig**,
which T113 added over the rescued WIP's decision to skip F5 — and row [7] *is* asserted.
I drove it red two ways on the merge:

```
### the F1 assignment line deleted from the live harness
[7]  FAIL  run-time open failure + inherited _conformance_psub_line -> REFUSED
           expected exit 3 / 0 verdict tokens; got exit 0 / 1.
     FAIL  F1 assignment
           no '      _conformance_psub_line=' line in the harness — the fix is GONE,
           and the row above cannot fail
T97 GUARD PROOF: 12 passed, 3 failed
### probe mutated to emit the token unconditionally
[5]  FAIL  probe reads /dev/null instead of the psub — got exit 0 / 52 tokens
[7]  FAIL  run-time open failure + inherited … -> REFUSED
T97 GUARD PROOF: 12 passed, 3 failed
### restored
harness restored byte-identical;  16 passed, 0 failed
```

**A revert of the one-line fix is caught, twice, with the second row explaining why the
first can no longer discriminate.** T106's F5 gap is genuinely closed, and T113's reason
for rejecting T106's literal text — a second pinned sha could be made unreachable by a
squash merge and would then redden the rig on `main` for an unrelated reason — is sound
P-24 reasoning that I agree with.

**Recommendation (not blocking):** rename `hostile-env-matrix.sh` and
`readonly-sourced-edge.sh` to `*-probe.sh`, or give all four expectations. This fire has
now found this shape **six** times, and **four of the six were inside the task sent to
fix the previous one.**

---

## 11. P-24 — verified on a scratch merge into CURRENT `main`, in a throwaway clone

`main` moved **again** while I worked: T113 measured against `6d2a1e9`; current `main`
is **`9027f00`** ("T119 approves T110"), two commits later. Everything below is a fresh
`git clone` of the repo, `main` at `9027f00`, T113 merged in (clean, **0 conflicts**,
merge `e39a4b9`), Go toolchain symlinked in. The clone was deleted afterwards; nothing
was merged anywhere real.

| required | measured |
|---|---|
| `bash .softhouse/conformance.sh` | **VERDICT: PASS (exit 0)** |
| parity vectors | **42** PASS, 0 FAIL |
| graded cells | **5576** graded, 84 ungraded |
| invariant violations | **0** |
| invariant assertions NOT RUN | **0** |
| `--prove` | **PROOFS: 21 passed, 0 failed** |
| `sh conformance.sh` | **exit 3**, **0 verdict tokens** |
| `gofmt -l .` | **exactly** `internal/apps/loanschedule/contract/contract.go` (G-3) |
| refused / inadmissible / harness errors | 0 / 0 / 0 |

Plus, on the same merge:

```
go build ./...   rc=0        go vet ./...   rc=0
go test ./... -count=1   ok loanschedule 9.004s · ok …/conformance 8.778s
contract.go sha256   0db73d4af996737d…f139   IDENTICAL to main:  never gofmt -w'd
git diff main..HEAD -- .softhouse/vectors/   EMPTY
git diff main..HEAD -- nexus/                EMPTY
T97's rig            16 passed, 0 failed
T113 matrix          26 passed, 0 failed
T106's rig           7 passed, 1 failed   (the forge row, by design)
working tree clean afterwards
```

**Scope:** 11 files, all inside the brief. Nothing in `nexus/`, `.softhouse/vectors/`,
`PIN.json` or `capabilities.json`. Known-bad-pattern grep over the 2,265-line merged
diff, added lines only — float type or literal, `first_name`/`last_name`,
`ojdbc`/`oracle.jdbc`/`OracleDialect`/`:1521`/`com.mysql`/`mariadb`, hard-coded
`+08:00`/`+07:00`, a literal `5000000` threshold, Stripe/Plaid/Lithic/Persona:
**zero real hits.** The only matches are the two handoff sentences that *list* the
forbidden tokens in order to report the grep. Every "oracle" in the diff is the Fineract
reference implementation. No money path, no vector, no schema, no Go.

**P-25:** my own analysis scripts use integer arithmetic (`$((n+1))`) and string
comparison only. There is no money quantity anywhere in this task and no floating-point
operation in anything I wrote.

*One difference from T113's numbers, and it is mine not theirs:* running T97's rig
inside a plain `git archive` extraction gives **14/1**, because row [1] pins the
immutable baseline `ab2de89` and cannot `git show` it outside a checkout. The rig
**refuses rather than passing quietly** — `cannot read ab2de89…:.softhouse/conformance.sh
from this checkout` — which is correct P-22 behaviour. In a real checkout it is 16/0, as
T113 reports.

---

## Findings, ranked

### F-T121-1 — **P2, MICRO-FIX.** A false statement of bash `read` semantics, shipped in the harness, at three sites

`conformance.sh:171-174`, `interpreter-matrix.sh:142-145`, `T113.md:346-348`.
`read` with a single variable **does** strip a trailing non-whitespace IFS delimiter when
it occurs exactly once and is the last character (`IFS=z`, `abcz` → `abc`), on bash
3.2.57, 4.4.0 and 5.3.9 alike. The probe's token survives only because its final `e`
also appears in `conformance`; `conformance-psub-livz` would not. Replace the derivation
with the measured rule and add **"someone renames the token"** to the list of futures the
prefix insures against. §1, §2. Prose only; no code change.

### F-T121-2 — **P3.** N-T113-3 was swept for the sentence, not the concept (P-26)

Three further scripts on this branch print without asserting: `readonly-sourced-edge.sh`
(no assertions at all), and `psub-dead-container.sh` / `bash5-matrix-container.sh`,
whose strong INERT guards protect the *subject* but never the *observation* — their
`clean=3 forged=3` expectations live in comments. Standing regression coverage is safe
because it lives in T97's asserted row [7], which I drove red. §10.

### F-T121-3 — **P3.** The `--help` 1→2 move is right, but its justification is half-stated

Moving off 1 removes a collision with the graded-FAIL code — correct, and I drove it
red. But `conformance.sh:59`, in this same file, says 2 is also the `/softhouse-program`
driver's oracle-is-down stop condition. Exit 2 is already a seven-cause bucket, no
grading caller passes `--help`, and the text is explicit, so this is not blocking — but
the sentence should say so. §8.

### N-T121-1 — **the bash 4.x gap is CLOSED.** Three tasks declared it; it is now measured

GNU bash 4.4.0 built from the official tarball and run under `--network none`. Guard
behaviour identical to 3.2.57 and 5.3.9: **zero false refusals**, forge present pre-fix
(`clean=3 forged=0`) and closed post-fix (`clean=3 forged=3`). New datum: **bash 4.4
kills process substitution in POSIX mode**, confirming the `5.1+` attribution and
bracketing the boundary to `(4.4, 5.3.9]`. Retire N-T113-5. §6.

### N-T121-2 — a second real-interpreter reproduction of F1

`/dev/fd` **present but mode 000** (rather than removed): PRE `clean=3 forged=0`,
POST `clean=3 forged=3`. A distinct psub-failure shape, unmeasured until now. §5.

### N-T121-3 — six exotic interpreters closed

busybox `ash`, busybox `sh`, `/bin/ash`, `mksh`, `yash`, alpine `/bin/sh`: all exit 3,
zero verdict tokens, PRE and POST identical. These are the shells `interpreter-matrix.sh`
skips silently (N-T113-4). §5.

---

## [UNVERIFIED] — the honest list

- **bash 5.2.37**, tagged at `conformance.sh:30`, `:78` and `SKILL.md:41`. A **T97** tag;
  I measured 5.3.9 in all four shapes instead. T106 did not close it either.
- **bash 5.0 and 5.1.** I bracketed the POSIX-mode process-substitution boundary to
  `(4.4, 5.3.9]`; I did not locate it. The harness's literal "5.1+" is consistent with
  everything I measured and is not directly confirmed.
- **A complete graded run under any bash 5.x.** Still nothing. Every green conformance
  run on record, including mine, is macOS bash 3.2.57. The harness and `SKILL.md` both
  say so, correctly.
- **IFS values outside printable ASCII**, IFS strings of 3+ characters other than
  all-printable, and any locale other than the host default. My brute force was
  ASCII-only and single-locale.
- **Whether an exported `builtin()` or `[()` can arise in any environment this program
  meets.** I reproduced the mechanism on three bash versions; I have no evidence of
  occurrence. F2 is documentation for exactly that reason.
- **The `readonly`-sourced refusal outside this repo.** I swept this repo exhaustively
  and found zero callers that source the harness; I did not search outside it.
- **T97's and T106's own handoff prose** beyond the sentences T113 lists. I re-ran their
  rigs and re-measured their claims; I did not re-audit their documents line by line.
- **`.softhouse/vectors/README.md:727-730`** still over-generalises ("`sh`, `bash --posix`,
  `dash` and `zsh` are all refused") — confirmed present, correctly outside T113's brief,
  correctly parked on **T93** as N-T113-1.
- **`T86.md:85` and `T86-review-t81.md:228`** still say "admitted and works" — confirmed
  present. T113 left them deliberately as historical review records. **I agree**: a
  reviewer's timestamped record should not be rewritten after the fact, and this file is
  its erratum.

---

## Verdict

**MICRO-FIX** — required before merge:

1. **F-T121-1**, prose only, three sites: replace the false `read`/IFS derivation with
   the measured rule, and add "someone renames the token" to the prefix's list of
   futures. No code change; the `IFS=` prefix stays exactly as it is.

Recommended, not blocking: **F-T121-2** (rename or arm the four non-asserting probes),
**F-T121-3** (one clause about exit 2's other meaning).

Everything else in T113 stands up, and stands up well. **F-T113-2 is upheld in full** —
I re-opened line 53 and T106's citation is false. **F-T113-1's disposition is upheld** —
T106's `IFS=e` claim is false, withdrawing it was right, keeping the prefix was right,
and I confirmed it over 448 IFS values instead of nine. The one-line fix is correct and
proven from the real pre-fix bytes; the forge is closed on **four** interpreter shapes
(mutant, `/dev/fd` removed, `/dev/fd` at mode 000, and now bash 4.4); no interpreter that
was admitted before is refused now across 17 shells; the one behaviour change is
disclosed, fail-closed, one-directional and has zero callers; the exit-code contract is
intact with 0 verdict tokens on every refusal; the rescued worker's five unmeasured tags
are now all measured; T106's rig is byte-identical and both legs reproduce exactly; and
the whole battery passes on a scratch merge into a `main` that moved twice underneath it
— **PASS, exit 0, 42 parity vectors, 5576 graded cells, 0 invariant violations, 0
assertions NOT RUN.**
