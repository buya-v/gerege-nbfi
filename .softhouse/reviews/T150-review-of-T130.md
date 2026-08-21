# T150 — independent review of T130 (`softhouse/T130-t113-microfixes`)

**Verdict: MICRO-FIX.**
**Is the interpreter-guard stream mergeable? YES — merge it, and land the two prose
corrections below as a follow-on.** Holding the branch is strictly worse than merging it:
`main` today carries T113's *false* `read` rule in `conformance.sh` and no token invariant
at all, and this branch replaces both.

Reviewer: T150, fire `20260821-080001`. Branch reviewed at
`softhouse/T130-t113-microfixes`, 4 commits on the T97 → T113 stack. Base for the P-24
merge: **current `main` = `2f3d7d2`** ("MERGE the G-8 stream"), which is three commits
ahead of where T130 ran its second scratch merge (`bcf2c55`).

**Headline.** I was told to assume I am the sixth worker to find the previous one's central
claim false. **T130's two central claims are TRUE**, and I verified both from first
principles rather than re-running its scripts:

- **The inherited-`IFS` null-control finding HOLDS.** bash resets `IFS` at startup and
  ignores an inherited one, on 3.2.57, 4.4.0 and 5.3.9, in plain mode, `--posix`,
  `argv[0]=sh` and `POSIXLY_CORRECT=1` alike. Four rounds of `env IFS=…` rows were null
  controls. `BASH_ENV` and sourcing do deliver.
- **The fourth statement of the `read` rule is RIGHT where it is used and WRONG where it is
  stated.** It is correct for every IFS containing no whitespace (960 cases of my own
  brute force + T130's 3,282 reproduced on three majors, 0 disagreements). It is **false as
  written** once IFS mixes whitespace and non-whitespace. That is F-T150-2.
- A **new** defect that neither T121 nor T130 caught: `conformance.sh`'s brand-new exit-2
  paragraph asserts the `probe = up|down` line is printed **"unconditionally"**. It is not —
  four exit-2 paths print no probe line at all, and on every one of them the driver's park
  rule fires the wrong way. That is F-T150-1, and it is the one finding in this review that
  can cost a fire.

Everything reproduced. Every number T130 published, I got — with one benign row-count
difference on bash 4.4 explained below.

---

## 0. What I ran, and with which binaries (P-33)

| tool | which one | how invoked |
|---|---|---|
| `bash` 3.2.57(1) arm64-apple-darwin25 | `/bin/bash`, host | direct |
| `bash` 5.3.9(1) aarch64-alpine-linux-musl | throwaway `alpine:3` + `apk add bash`, `docker run --rm --network none` | direct |
| `bash` 4.4.0(1) aarch64 | **built by me** from `bash-4.4.tar.gz`, sha256 `d86b3392…dfcb` verified before extraction, in a throwaway alpine container | direct |
| `grep` | **`/usr/bin/grep` (BSD grep) with `LC_ALL=C` and `-a`**, called by absolute path from a script, for every sweep in this review | never the Bash-tool `grep` shell function, which is ugrep-with-`-I` and honours `.gitignore` (P-33) |
| `gofmt`, `go` | `/Users/buv/gerege-nbfi/.softhouse/toolchain/go/bin/…` (P-30) | absolute path; **`gofmt -w` never run** (G-3) |
| `docker` | server 29.6.2 | only `docker run --rm` on `alpine:3` / `eclipse-temurin:21-jdk` and one local `docker build` of an alpine+bash image. **No `docker compose`. The Fineract stack was never started, stopped, rebuilt or re-seeded.** The reference oracle was contacted only by the harness's own `curl -sk` health probe during two graded runs (`probe = up`). |

**P-25.** Every script I wrote for this review uses integer counters (`$((n+1))`) and string
comparison only. There is no money quantity in this task and no floating-point operation
anywhere in it. No vector JSON, `PIN.json`, `capabilities.json`, `nexus/`, `tasks.json`,
`patterns.md` or `gates.md` was read-modified by me; my branch adds exactly two files.

---

## 1. THE LOAD-BEARING CLAIM — the inherited-`IFS` null control. **CONFIRMED.**

I did not run `ifs-routes.sh` first. I wrote my own probe (`show-ifs.sh` printing
`"$IFS"` and `${#IFS}`) and drove it through every route by hand.

**bash 3.2.57 (host) and bash 5.3.9 (alpine), identical:**

```
== exported IFS=z in the parent ==
route: bash script                  -> IFS=[ \t\n] len=3     DELIVERS NOTHING
route: bash --posix script          -> IFS=[ \t\n] len=3     DELIVERS NOTHING
route: bash -c                      -> IFS=[ \t\n] len=3     DELIVERS NOTHING
route: argv[0]=sh (symlink)         -> IFS=[ \t\n] len=3     DELIVERS NOTHING
route: POSIXLY_CORRECT=1            -> IFS=[ \t\n] len=3     DELIVERS NOTHING
route: BASH_ENV=<file: IFS=z>       -> IFS=[z]     len=1     DELIVERS
route: sourced into a shell with IFS=z -> IFS=[z]  len=1     DELIVERS
route: parent sets IFS=z but does NOT export -> IFS=[ \t\n]  DELIVERS NOTHING
```

Same on **bash 4.4.0**, via `ifs-routes.sh` under the binary I built: `6 passed, 0 failed`.

**Ruling: T130 is right, and the consequence is right.** Every `IFS=…` row in T97's matrix,
T106's review, T113's refutation and T121's 448-value brute force was run through the
environment, so **none of them could have failed whatever the token was spelled**. Four
rounds of argument about the `IFS=` prefix were conducted entirely over a null control.
T130's relabelling of those rows, and its `[SUPERSEDES:]` note retiring T97's and T113's
env-route evidence, are correct.

### 1a. Two route facts T130's table does not state (neither weakens it)

I checked the *non*-delivering claims as hard as the delivering ones, and pushed past
T130's seven routes:

```
ENV=<file>  bash --posix script   -> IFS=[ \t\n]   does NOT deliver
ENV=<file>  bash script           -> IFS=[ \t\n]   does NOT deliver
BASH_ENV=<file> bash --posix script    -> IFS=[ \t\n]   does NOT deliver   <-- note
BASH_ENV=<file> argv[0]=sh script      -> IFS=[ \t\n]   does NOT deliver   <-- note
bash --rcfile <file: IFS=z> -i script  -> IFS=[z]       DELIVERS           <-- 8th route
```
(identical on 3.2.57 and 5.3.9)

So **`BASH_ENV` delivers only to a non-interactive, non-POSIX-mode bash** — a POSIX-mode
non-interactive bash reads neither `BASH_ENV` nor `ENV`. T130's table lists `BASH_ENV` as
delivering without that qualification. It does not matter for any conclusion in the branch:
the crossproduct's one refusing cell and `[6b]`'s end-to-end leg both use plain mode, where
it does deliver, and `interpreter-matrix.sh:216-225` **asserts the route before relying on
it** rather than assuming it. Recorded for completeness, not as a finding.

---

## 2. THE CORRECTED STRIPPING RULE — third-party re-derivation, and where it breaks

I did not transcribe T130's predicate either. I implemented **the sentence as it is written
in `conformance.sh:208-215`**, literally, including the whitespace clause it inherits, and
brute-forced `read` against my implementation.

### 2a. Inside the domain T130 swept: the rule is RIGHT

```
$ bash /tmp/t150/mypredicate.sh abc 4 a b c ab bc abc : a:
bash 3.2.57(1)-release alphabet=[abc] maxlen=4 ifs={a b c ab bc abc : a:}
T150 PREDICATE: 960 cases, 960 agree, 0 DISAGREE
```

and T130's own rig, re-run by me on all three majors:

```
3.2.57 : PREDICATE CHECK: 378 cases, 378 agree, 0 DISAGREE
         PREDICATE CHECK: 2904 cases, 2904 agree, 0 DISAGREE
4.4.0  : 378/378/0   and   2904/2904/0
5.3.9  : 378/378/0   and   2904/2904/0
```
378 + 2904 = **3,282**, exactly as published, on all three.

**T130's sharpening of T121 is a real correction, not a rewording.** T121 wrote *"that
delimiter occurs exactly once in the line and is its last character"*. On `abcze` with
`IFS=ze` the last character `e` occurs exactly once and is last, so T121's rule predicts
`abcz`. Measured, on all three majors:

```
D IFS=[ze] line=[abcze] read=[abcze]   INTACT
```
T121's phrasing is wrong there; T130's *"the ONLY position holding ANY IFS delimiter"* is
right. **Third statement wrong, fourth better.**

### 2b. Outside it: the rule as written in `conformance.sh` is FALSE — F-T150-2

T130's rig header honestly scopes the predicate: *"**With IFS containing no whitespace**, a
single-variable `read -r` returns the line unchanged UNLESS…"*
(`T130-evidence/read-ifs-predicate.sh:19-22`). **`conformance.sh:208-215` and
`interpreter-matrix.sh:186-193` drop that scope** and state the rule unconditionally, with
a `[VERIFIED: T130 … 3,282 cases]` tag whose sweep never contained a whitespace IFS and
never contained a whitespace character in a line.

Counterexamples, measured on **3.2.57, 4.4.0 and 5.3.9, identical**:

```
bash 3.2.57 / 4.4.0 / 5.3.9
A  IFS=[ a]  line=[bb a]  read=[bb]   -- conformance.sh's rule predicts [bb a]
B  IFS=[ a]  line=[a ]    read=[]     -- conformance.sh's rule predicts [a]
C  IFS=[z]   line=[abcz]  read=[abc]  -- control, rule predicts [abc]    AGREES
D  IFS=[ze]  line=[abcze] read=[abcze]-- control, rule predicts [abcze]  AGREES
```

In case A the final `a` **is** stripped although the line holds two delimiter positions
(the space and the `a`), and the intervening space goes with it. My literal implementation
of the shipped sentence disagrees with `read` in **81 of 960** cases once the alphabet and
the IFS set are allowed to contain a space or a tab.

This is the **fourth** statement of this rule in this file, and it is the fourth to be
over-scoped. It is materially better than its three predecessors and it is right in the
domain that governs the guard — but P-11 applies exactly here: *the reason is what the next
contributor checks*, and the next contributor may well be reasoning about an IFS that
contains a space, because the **default** IFS contains a space. → **F-T150-2, P3,
MICRO-FIX. Prose only.**

T130's `[UNVERIFIED]` list names "IFS values outside printable ASCII" and "any locale other
than the host default". It does **not** name the blind spot that actually bites — *IFS
containing whitespace, and lines containing whitespace, were not swept*. P-23: scope every
claim to the family it holds for.

### 2c. The `[6b]` implication — I attacked it, and it SURVIVES

The claim under test: *(i) the token has no whitespace and (ii) its last character occurs
earlier in it ⟹ the token round-trips through a single-variable `read` under **every**
IFS.* Because §2b shows the rule the implication is derived from is not generally true, I
tested the implication **directly**, as a property, over a domain including whitespace-bearing
IFS.

**Property test** — every string of length 1..5 over `{a,b,z}`, 21 IFS candidates including
`" a"`, `"a "`, `"\ta"`, `"\na"`, `"\t \n a"`, `" ab"`, `" :z"`:

```
bash 3.2.57 / 4.4.0 / 5.3.9 — identical
INVARIANT-SATISFYING tokens: 270, of which round-trip under EVERY swept IFS: 270, violations: 0
INVARIANT-VIOLATING tokens:   93, of which truncatable by some swept IFS:    93
```

The second line is the discrimination control (P-22): the invariant is **tight**, not merely
sufficient — every token that violates it really is truncatable, so `[6b]`'s assertion is
not a check that cannot fail.

**Real-token sweep** — `conformance-psub-live` against **9,799** IFS values (every printable
ASCII character, plus space/tab/newline, plus every 2- and 3-character combination over the
token's own alphabet ∪ {space, tab, newline, `:`, `z`}):

```
bash 3.2.57  token=[conformance-psub-live]  IFS values swept=9799
T150 TOKEN SWEEP: 0 truncations of the real token; control token
                  [conformance-psub-livz] truncated by 71 of them
bash 5.3.9   identical
```

**Ruling: the implication `[6b]` rests on is TRUE, verified over a domain ~3× larger than
T130's and containing the whitespace cases T130's did not.** The guard is sound; only the
*derivation printed next to it* is over-scoped.

---

## 3. THE ACCIDENT OF SPELLING — the judgement call. **T130's reasoning is SOUND, and I measured both of its reasons rather than accepting them.**

T130 rejected the structural fix and asserted the invariant instead. I was asked to rule on
that reasoning. It gave two reasons; both are correct, and both were arguments in T130's
write-up. I converted them into measurements.

**Reason 1 — a structural change to the probe's SHAPE makes T106's rig INERT.**
T106's rig greps the harness for the literal
`< <(builtin printf "%s\n" "$CONFORMANCE_PSUB_TOKEN")` (`prove-token-forgeable.sh:32`) and
for `      IFS= builtin read -r _conformance_psub_line` (`:33`). I applied the doubling
option (`printf "%s%s\n"`) to a copy of the harness and ran the **unmodified** rig against it:

```
T106 proof: the probe redirection is not in …/conformance.sh any more.
T106 proof: this script tests a shape that no longer exists — INERT, so exit 1.
RC=1
```
The brief requires that rig to produce 7/1 unmodified. Reason 1 **holds** — and it is
stronger than T130 said: the doubling would also require the comparison
`[ "$conformance_psub_seen" != "$CONFORMANCE_PSUB_TOKEN" ]` to change, so the blast radius
is larger still.

**Reason 2 — a change to the token's VALUE destroys the discrimination T121 verified.**
T106's rig hard-codes `TOKEN="conformance-psub-live"` (`:31`) and seeds it. I ran the
unmodified rig against a post-fix harness whose token had been renamed to
`conformance-psub-livz`:

```
[1] the harness AS SHIPPED, with the probe's redirection failing at run time
  ok    clean environment -> REFUSED (exit 3)
  FAIL  _conformance_psub_line pre-seeded -> ADMITTED (F1)   expected exit 0, got 3
T106 FORGE PROOF: 7 passed, 1 failed
```
**Numerically identical to the correct post-fix result** (7/1, same row). So after a rename
the rig's one red row no longer distinguishes "the F1 fix closed the forge" from "the seed
no longer matches the token" — which is precisely the discrimination T121 checked row by
row. Reason 2 **holds**, and is now measured.

**Reason 3** — not going through `read` needs `cat` (external, breaks self-containment) or
`read -N` (bash 4.1+, and the host is 3.2.57). Correct by construction.

**RULING: uphold.** "Assert the invariant" was the right call, and it catches strictly more
than a structurally-immune token would (it also fires on whitespace in the token and on any
future rename, whatever the reason). I found no fourth option T130 should have costed.

### 3a. Red proof — reproduced exactly

Token renamed to `conformance-psub-livz` at `conformance.sh:312` in a copy of the tree
(the copy is itself healthy: `--help` → exit 0).

**T113's own matrix bytes** (`git show softhouse/T113-close-forgeable-token:…`, sha256
`0168dac4f44e0971d9168eb1e5afb43cf8450d4bfc8802add9039072fe7de4ea`), against that renamed
harness:

```
[6] the probe's `IFS=` prefix is INSURANCE, not a measured save (T113 finding)
  ok    IFS= prefix removed from a copy of the harness
  ok    no IFS= prefix, IFS=[oc] (exit 0)   ok IFS=[e]   ok IFS=[c]   ok IFS=[ ]   ok IFS=[-]
T113 INTERPRETER MATRIX: 26 passed, 0 failed        RC=0
```
**Silently admitted**, exit 0 — exactly as T130 reported.

**T130's matrix, same renamed harness:**

```
[6b] THE TOKEN MUST ROUND-TRIP THROUGH `read` — asserted, not narrated (T130)
  token read from the harness: [conformance-psub-livz]  (last character [z])
  ok    (i) token contains no whitespace
  FAIL  (ii) the token's last character [z] occurs NOWHERE ELSE in the token
  FAIL  read round-trip, IFS=[z]
  FAIL  read round-trip, IFS=[zz]
  FAIL  no IFS= prefix, BASH_ENV IFS=[z] (from the token's own alphabet)
        expected exit 0, got 3
T113 INTERPRETER MATRIX: 67 passed, 4 failed        RC=1
```
**67/4**, red at three levels of abstraction, the last row a genuine **false refusal of a
healthy bash at exit 3**. Green again on the real harness: **69 passed, 0 failed**.

**The 12-cell crossproduct**, run by me on all three majors — `12 passed, 0 failed` on each,
with exactly one refusing cell:

```
token=conformance-psub-livz prefix=drop route=bashenv -> exit 3
  (the one false refusal — renamed token AND no prefix AND a delivering route)
```
Eleven of twelve admit. The published table is exact.

---

## 4. F-T150-1 — **P2. `conformance.sh`'s new exit-2 paragraph says "unconditionally", and it is false on four paths. The driver parks on all four.**

This is the finding of this review, and it is inside the very correction T130 was sent to
make (F-T121-3).

`conformance.sh:65-74` (branch) now reads:

> … so the driver's park condition is now BOTH `exit 2` AND `probe != up`, taken from the
> `reference oracle (…) probe = up|down` line **this harness prints unconditionally before
> the graded binary runs** …

and `:1085` repeats it, and `T113.md`'s new erratum repeats it a third time, citing
`conformance.sh:512`.

**It is not unconditional.** The probe line is printed at `conformance.sh:595` (`:512` on
the branch), inside `main_grade`, **after** four earlier exits:

| line (branch) | path | prints a `probe =` line? |
|---|---|---|
| `:466` | `load_toolchain` — no Go toolchain | **no** |
| `:545` | `run_guards` — **a failed HARD guard** | **no** |
| `:583` | `mktemp` failure | **no** |
| `:573` | `build_binary` — the harness does not build | **no** |

Driven red by me, on the P-24 scratch merge, by making a harness-owned Go file
non-gofmt-clean:

```
$ bash .softhouse/conformance.sh
conformance: not gofmt-clean:
/tmp/…/nexus/internal/apps/loanschedule/conformance/vector.go
conformance: a HARD guard failed. EXIT 2 — no verdict is available. This is NOT a pass.
EXIT=2
=== does a probe line appear? ===  0        (LC_ALL=C /usr/bin/grep -ac "probe = ")
```

**Why it matters.** `.claude/skills/softhouse-program/SKILL.md:108-120` gives the driver two
rows and one rule: park on `exit 2` AND `probe != up`. There is **no row for "exit 2 with no
probe line at all"**, and `probe != up` is trivially true when no probe line was printed.
So on a hard-guard failure — which T130's own new sentence lists, by name, as one of the
*corpus*-unusable meanings of exit 2 — the driver parks every vector task on an oracle
outage that did not happen. That is the exact defect T76/T77 found, the exact defect T119
raised, and the exact defect this paragraph was written to close, surviving inside the
paragraph that closes it.

**How it got here.** T130 wrote *"Verified rather than assumed: … `main`'s SKILL.md already
carries the 'Exit 2 with `probe = up` … NOT an oracle outage' row"*. It verified the row
**exists**. It did not verify the **claim the row makes**. `"unconditionally"` is T119's
word, on `main`, in `SKILL.md`, and T130 propagated it into the file that decides PASS —
in a task whose entire subject is propagated unverified sentences.

**Disposition: MICRO-FIX, prose in `conformance.sh` plus one row in `SKILL.md`.** Suggested
wording, no behaviour change:

> The `probe = up|down` line is printed on every path that **reaches the grader**. Four
> exit-2 paths precede it and print **no probe line at all**: no Go toolchain, a failed
> HARD guard, `mktemp` failure, and a build failure. **Exit 2 with NO probe line is a
> harness/corpus defect, never an outage — treat it exactly like `probe = up`.** The park
> condition is therefore `exit 2` AND a printed `probe = down`, not `exit 2` AND `probe !=
> up`.

(The stronger fix — move `probe_oracle` above `run_guards` so the line really is
unconditional — changes the order in which the harness contacts the reference oracle, which
is outside a prose micro-fix and should be its own task.)

**Note for the merge decision:** this defect is **inherited from `main`**, not introduced by
this branch. `SKILL.md:116` already says "unconditionally" on `main` today. Merging T130
does not make it worse; it adds a second and third copy of a sentence that is already
wrong. So it is a follow-on, not a blocker.

---

## 5. F-T121-2 — the three print-without-asserting rigs. All three armed, all three driven red by me.

### `readonly-sourced-edge.sh`

On the branch harness: **5 passed, 0 failed**.
Against the **real pre-fix bytes** (`git show f2813c8:.softhouse/conformance.sh`, sha256
`c69e30ff6617debbd2e013cefd903479dcab0f8c9b0c4e3ea273e88b1907951a` — I re-hashed it, it
matches, and the F1 assignment is absent):

```
  FAIL  [1] the F1 assignment is NOT in /tmp/t150/pre.sh
  ok    [2] control: sourced WITHOUT the readonly -> ADMITTED (exit 0)
  FAIL  [3] sourced WITH _conformance_psub_line readonly   expected exit 3, got 0
  FAIL  [3b] verdict tokens on the refusal path   1 found
  FAIL  [4] refusal text
T113/T130 READONLY-SOURCED EDGE: 1 passed, 4 failed        RC=1
```

**1/4 exactly**, and — the point of the control — row **[2] is green in both legs**, so the
refusal in [3] is demonstrably caused by the `readonly` and not by sourcing. That is the
control T121 asked for and it does its job.

One P-35 note: row **[3b]** (`tokens -eq 0`) is a *negative* assertion and would pass on an
empty `$out`. It is not vacuous **in combination**, because [4] asserts positively that the
same `$out` contains a specific sentence — an empty `$out` reddens [4]. Acceptable as
shipped; worth knowing that [3b] alone is the P-35 shape.

### `psub-dead-container.sh` — **3 passed, 0 failed** on the scratch merge (real bash 5.3.9, `/dev/fd` removed)

Driven red by deleting the one line `rm -f /dev/fd` (line 84) from its generated inner script:

```
psub after removing /dev/fd: [CAP]  (empty = dead)
  FAIL  psub-dead precondition   capability is [CAP], expected empty …
  FAIL  PRE-FIX  clean=0 forged=0   expected clean=3 forged=0
  FAIL  POST-FIX clean=0 forged=0   expected clean=3 forged=3
T113/T130 PSUB-DEAD CONTAINER: 0 passed, 3 failed        RC=1
```
**0/3 exactly.**

I also attacked the host-side "absent result" guard, which is the P-35 half of it — I pointed
`IMAGE` at `alpine:3`, which has no bash, so the container dies producing no summary line:

```
docker: … exec: "bash": executable file not found in $PATH
T113: the container printed no summary line (docker rc=127) — it did not finish.
T113: a run with no result is a FAILURE, not a pass. exit 1.
RC=1
```
**A dead container is an error, not a pass.** Correct.

### `bash5-matrix-container.sh` — **19 passed, 0 failed**; red at **9 passed, 10 failed**

Same one-line deletion (line 145):

```
  FAIL  F precondition: psub capability = yes, expected no
  FAIL  PRE-FIX  psub-dead clean = 0, expected 3        (+ 5 more PRE/POST rows)
  FAIL  POST-FIX psub-dead forged = 0, expected 3
T113/T130 BASH5 MATRIX: 9 passed, 10 failed
```
**9/10 exactly.** Worth naming: the row `PRE-FIX psub-dead forged = 0` does **not** go red,
because its expected value (0) is also what a healthy shell produces. It is the
**precondition row** that catches the broken container — which is exactly why T130 added it,
and why an unarmed version of this script printed four zeros and exited 0.

### The honest scoping — checked, and it is honest

T130 claims these three additions are **not** new standing regression coverage for the F1
fix, and that the standing coverage lives in **row [7] of T97's rig**. I opened
`T97-evidence/prove-interpreter-guard.sh:213-228`: row [7] is asserted **and** carries a
second row whose sole purpose is to stop the first from becoming green-either-way. That is
real regression coverage with its own discrimination check, and T130's narrower claim for
what the three additions buy — a revert caught in three more places, a broken container
precondition caught **at all**, and a control for the sourced-readonly change — is accurate.
`T97 GUARD PROOF: 16 passed, 0 failed` on the scratch merge.

### `hostile-env-matrix.sh`

Unchanged in behaviour; the "this is a PROBE, not a rig, it exits 0 whatever it observes"
disclosure now lives **in the file** rather than only in T113's handoff, along with the
null-control note. Correct call — a probe with a stated blind spot is honest (P-26).

---

## 6. F-T121-3 — the exit-code sentence vs today's `SKILL.md`. **Matches, except for §4.**

`.claude/skills/softhouse-program/SKILL.md` on current `main`:

- `:108` — *Oracle unreachable — `conformance.sh` prints `probe = down` AND exits 2* → park.
- `:109` — *Exit 2 with `probe = up`* → **NOT an oracle outage — park nothing on it.**
  Names `ZERO VECTORS FOUND`, an inadmissible vector, and *"since T110 a duplicate
  `case_id`"*.
- `:110` — exit 3 → not an outage, do not park.
- `:116-120` — the park condition is *`exit 2` AND `probe != up`*, both of them.

`conformance.sh:65-74` now says the same thing in the same words. T110 **is** on `main`
(`DuplicateCaseIDs` at `nexus/internal/apps/loanschedule/conformance/vector.go:912,944`,
plus a compile-on-main integrity test). The `--help` dispatch comment at `:1085` carries the
same qualification and the 1→2 move is still right.

**Consistent — and both documents share the single false word, F-T150-1.**

---

## 7. N-T113-5 — bash 4.4 closure, independently reproduced

I built GNU bash **4.4.0** myself rather than take T130's word:
`bash-4.4.tar.gz`, sha256 `d86b3392c1202e8ff5a423b302e6284db7f8f435ea9f39b5b1b20fd3ac36dfcb`
**verified before extraction** (`sha256sum -c` → `OK`), configured with T130's published
`CFLAGS` workaround (which is necessary — the tarball does not build on a modern GCC
without it), `--network none` for every run afterwards.

**T121's datum reproduced independently.** On bash 4.4, POSIX mode does not merely disable
process substitution, it makes it a **parse error**:

```
$ bash44 --posix -c 'IFS= read -r v < <(printf "%s\n" CAP); …'
/bin/bash: -c: line 0: syntax error near unexpected token `<'
$ bash44 -c '…'   ->  plain cap=[CAP]
```
and the matrix grades all four POSIX-mode shapes as `psub dead -> REFUSED (exit 3)` on 4.4
while 5.3.9 gives `psub works -> ADMITTED (exit 0)` for all four. **The `5.1+` attribution in
the harness is confirmed and the boundary is bracketed to `(4.4, 5.3.9]`.**

**Matrix results, mine:**

| interpreter | T130 published | T150 measured |
|---|---|---|
| bash 3.2.57 (host, macOS) | 69 / 0 | **69 passed, 0 failed** |
| bash 4.4.0 (built from source) | 67 / 0 | **68 passed, 0 failed** |
| bash 5.3.9 (alpine, musl) | 68 / 0 | **68 passed, 0 failed** |

The 67-vs-68 difference on 4.4 is **not** a discrepancy in behaviour: **zero failures either
way**, and the row count is a function of which shells exist in the image (`[1b]` iterates
`/bin/dash /bin/zsh /bin/ksh /bin/ksh93 /bin/mksh /bin/busybox /bin/yash /bin/ash` and skips
absent ones). T130 built 4.4 in a different base image than my alpine. T130 states this cause
explicitly in its handoff. Accepted.

---

## 8. §6 — the Alpine false failure. **Real, and the fix grades both branches.**

T130 claims `interpreter-matrix.sh` asserted `agree "/bin/sh" /bin/sh` unconditionally and
produced a FALSE FAILURE on Alpine. Reproduced with T113's own pre-fix matrix bytes, in the
alpine container, against a **correctly behaving** harness:

```
[1a] bash, and shells that MIGHT be bash — decision must track capability
  ok    /bin/bash: psub works -> ADMITTED (exit 0)
  FAIL  /bin/sh
        psub capability=yes but guard exit=3 — the decision does not track the capability
```

Alpine's `/bin/sh` is busybox ash and it **has** process substitution, while the guard
correctly refuses it at 3 on `BASH_VERSION` being unset, before capability is consulted.

T130's fix (`interpreter-matrix.sh:92-107`) asks `bashver` first and routes a non-bash
`/bin/sh` to the `[1b]` "not bash → must be refused at 3" rule. Both branches are **graded**:

```
alpine (busybox /bin/sh):
  ok    /bin/sh (NOT bash — refused whatever it can do; psub capability=yes) (exit 3)
macOS (/bin/sh IS bash 3.2.57):
  ok    /bin/sh (IS bash 3.2.57(1)-release): psub dead -> REFUSED (exit 3)
```

**Neither branch is skipped, and neither is weakened.** The non-bash branch uses `want …
3`, a positive assertion on an exact exit code; it does not become a `skip`. Confirmed.

One residual: if `/bin/sh` does not exist at all (`[ -x /bin/sh ]`), the row vanishes
silently. Not reachable on any host this program meets.

---

## 9. Attacking the additions (P-22 / P-35) — starvation tests

*"What is the observation, and could it be produced by the check never running?"* — applied
to every new rig, with **zero input, absent tool, empty file set, absent subject**:

| attack | result |
|---|---|
| `interpreter-matrix.sh <empty file>` | `no CONFORMANCE_PSUB_TOKEN line … INERT, so exit 1 rather than pass quietly` — **rc=1** |
| `interpreter-matrix.sh <nonexistent>` | `no harness at … — refusing to report anything` — **rc=1** |
| `token-spelling-crossproduct.sh … <empty file>` | `no CONFORMANCE_PSUB_TOKEN … INERT, exit 1` — **rc=1** |
| `readonly-sourced-edge.sh <empty file>` | `no CONFORMANCE_PSUB_TOKEN … INERT, exit 1` — **rc=1** |
| `read-ifs-predicate.sh "" 0 a` (zero cases) | `zero cases generated — a sweep that inspects nothing is an error, not a pass (P-22)` — **rc=1** |
| `read-ifs-predicate.sh` (no args) | usage — **rc=2** |
| `ifs-routes.sh /nonexistent/bash` | **0 passed, 6 failed, rc=1** — every route row is a positive equality against an exact expected `$IFS`, so an absent interpreter reddens all six |
| `psub-dead-container.sh` with an image that cannot run bash | `the container printed no summary line … a run with no result is a FAILURE, not a pass. exit 1` — **rc=1** |

**Every new check is phrased positively and every starvation input is an error, not a pass.**
This branch is the first in the T97→T130 chain that passes P-35 cleanly on its own additions.

Two attacks that could have produced a false green and do not:
- `TOKEN` is extracted with `sed -n 's/^CONFORMANCE_PSUB_TOKEN="\(.*\)"$/\1/p'`. If someone
  writes `CONFORMANCE_PSUB_TOKEN='single-quoted'`, the sed finds nothing → INERT exit 1
  (fails closed). If someone writes `CONFORMANCE_PSUB_TOKEN="$X"`, `TOKEN` becomes the
  literal `$X`, whose last character `X` occurs nowhere earlier → `[6b](ii)` goes **red**,
  not green.
- `token-spelling-crossproduct.sh` **derives** the truncatable counterpart from the live
  token instead of pinning `conformance-psub-livz`, and refuses if either mutation fails to
  bite (`:105-113`). It keeps testing the right thing after a rename.

### Residual vacuities in the file T130 armed (advisory, both pre-existing)

- **N-T150-1 / already recorded as N-T113-4.** `interpreter-matrix.sh:115` —
  `[ -x "$s" ] || continue`. Section `[1b]` silently skips absent shells and never asserts a
  minimum, so on a host with none of the eight it prints nothing and still passes. This is
  the P-35 shape inside the rig T130 armed, and it is why the headline number moves 67/68/69
  between hosts. T113 itself recorded it as N-T113-4 and T130 did not close it. **Not a
  regression, but it is the one negative assertion left in this file and it should be closed
  by whoever next touches the matrix**, with a positive `N interpreters inspected, N ≥ 1` row.
- **N-T150-2.** `interpreter-matrix.sh:205-207` writes `.T113-matrix-noifs.sh`,
  `.T113-matrix-benv.sh` and `.T113-matrix-seeifs.sh` into the **live** `$REPO_ROOT/.softhouse/`
  under **fixed** names, and none of the five `.T113-*` scratch names is in `.gitignore`. They
  are trap-removed, but two agents running the matrix in the same checkout will delete each
  other's files mid-run and produce false reds, and an interrupted run leaves untracked
  dotfiles in `.softhouse/`. T106's own rig avoids this with `mktemp -u`. T130 added two of
  the three. Cosmetic today; worth one `mktemp -d` when convenient.

### F-T150-3 (P3, advisory) — the new invariant is asserted where nothing runs it

`[6b]` is excellent, and it lives in
`.softhouse/handoff/2026-08-17-run1-harness-schedule-poc/T113-evidence/interpreter-matrix.sh`
— a rig in a handoff directory that **no automated surface invokes**. I checked the harness's
own asserted surface: `conformance.sh --prove` is **21 rows, all about grading semantics**
(exit codes, perturbations, transcription, invariants); it contains **no row about the
interpreter guard at all**, and T130 states plainly that it added none.

So the sequence "someone renames `CONFORMANCE_PSUB_TOKEN`; `conformance.sh` keeps working
because of the `IFS=` prefix; the invariant is now false and nothing says so" is caught only
if a human remembers to run a handoff-directory script. Given that this whole chain exists
because guards were believed without being reached, the invariant belongs in `--prove` (or
`--self-test`), not only in a rig. **Not a blocker and arguably outside T130's brief** ("do
not touch grading"; a `--prove` row is not grading, but it is a change to the harness's
executable surface). Recommend it as the follow-on task.

---

## 10. Verification demanded by the brief — every line

### T106's rig — byte-unmodified, both legs, control green in both

```
sha256 cb11a2be18c692d32ef5100066364a4d6da33086a029bf82b1a75aa3a3bc0005   (= T113's, = T121's)
git diff softhouse/T113-close-forgeable-token softhouse/T130-t113-microfixes -- <that file>   EMPTY

LEG 1  PRE-FIX  (git archive f2813c8 -> clean tree; harness sha256 c69e30ff…951a; F1 ABSENT)
  [1] clean -> REFUSED (3)   pre-seeded -> ADMITTED (F1) (0)
  [2] +fix: clean -> 3       pre-seeded -> 3
  [3] control: unmutated clean -> 0    unmutated pre-seeded -> 0
  T106 FORGE PROOF: 8 passed, 0 failed        RC=0

LEG 2  POST-FIX (branch tip)
  [1]b FAIL  _conformance_psub_line pre-seeded -> ADMITTED (F1)   expected 0, got 3
  [3] control: unmutated clean -> 0    unmutated pre-seeded -> 0
  T106 FORGE PROOF: 7 passed, 1 failed        RC=1
```
**8/0 and 7/1 exactly, section [3] green in both legs.**

### Matrix on three bash majors

3.2.57 **69/0** · 4.4.0 **68/0** (T130: 67/0; row-count only, 0 failures either way — §7) ·
5.3.9 **68/0**.

### `conformance.sh` — the executable delta is ZERO

```
git diff softhouse/T113-close-forgeable-token softhouse/T130-t113-microfixes -- .softhouse/conformance.sh
  -> 168 diff lines; every added/removed line is a comment or blank.
```
Filtered with `/usr/bin/grep -E` for any changed line that is not `^[+-]\s*#` and not blank:
**none**. T130's claim of "no behaviour change, no grading change, no exit-code meaning
changed" is **exact**, mechanically checked, not read.

### P-24 — scratch merge into **current** `main` (`2f3d7d2`), throwaway clone, deleted after

| required | measured |
|---|---|
| merge | **clean, 0 conflicts** |
| `bash .softhouse/conformance.sh` | **VERDICT: PASS (exit 0)** |
| parity vectors | **42** PASS, 0 FAIL |
| graded cells | **5576** graded, 84 ungraded |
| invariant violations | **0** |
| invariant assertions NOT RUN | **0** |
| refused / inadmissible / harness errors | 0 / 0 / 0 |
| `--prove` | **PROOFS: 21 passed, 0 failed** |
| `sh conformance.sh` | **exit 3**, **0 verdict tokens** (`LC_ALL=C /usr/bin/grep -acE 'VERDICT\|PASS\|FAIL'` → `0`) |
| `gofmt -l .` | **exactly** `internal/apps/loanschedule/contract/contract.go` (G-3) |
| `contract.go` sha256 | `0db73d4af996737d2f1a33c6d6aa4ac6cc35a33fbae57afbeb0d81e67e37f139` — **identical to `origin/main`'s**; never `gofmt -w`'d |
| `git diff origin/main..HEAD -- .softhouse/vectors/` | **EMPTY** |
| `git diff origin/main..HEAD -- nexus/` | **EMPTY** |
| `go build ./...` / `go test ./... -count=1` | rc=0 / rc=0 (`ok loanschedule 9.927s`, `ok …/conformance 27.802s`) |
| oracle probe | `probe = up`, read-only health check only |
| working tree afterwards | clean |

### Rigs on the scratch merge

```
T97 GUARD PROOF                    16 passed, 0 failed
T113 INTERPRETER MATRIX            69 passed, 0 failed
T106 FORGE PROOF                    7 passed, 1 failed   (the forge row, by design)
T113/T130 READONLY-SOURCED EDGE     5 passed, 0 failed
T113/T130 PSUB-DEAD CONTAINER       3 passed, 0 failed
T113/T130 BASH5 MATRIX             19 passed, 0 failed
T130 IFS ROUTES                     6 passed, 0 failed
T130 PREDICATE                    378/378/0  and  2904/2904/0
T130 TOKEN-SPELLING CROSSPRODUCT   12 passed, 0 failed
```

### Scope and known-bad patterns

15 files touched vs `main`; 11 of them by T130 itself. **Nothing** matching
`vectors/|PIN.json|capabilities.json|^nexus/|tasks.json|patterns.md|gates.md`.
Known-bad sweep over the **3,764-line merged diff, added lines only** (3,590 lines), with
`/usr/bin/grep -acE` under `LC_ALL=C` and `-a`:

```
float(32|64)                            0
[^a-zA-Z]float[^a-zA-Z]                 6   all prose / the identifier guard_no_float_in_vectors
[0-9]\.[0-9]                          160   all bash version numbers (3.2.57, 4.4.0, 5.2.37, 5.3.9)
first_name|last_name                    2   the two handoff sentences that LIST the token to report the grep
ojdbc|oracle.jdbc|OracleDialect|:1521   2   same two sentences
com.mysql|mariadb|mysql                 3   same
\+08:00|\+07:00                         2   same
5000000                                 2   same
Stripe|Plaid|Lithic|Persona             2   same
gofmt -w|go fmt                         3   all "never gofmt -w'd (G-3)" attestations
```
**Zero real hits.** Every match is a report *about* the forbidden tokens. No money path, no
vector, no schema, no Go. T130's own sweep result is confirmed.

**What my sweep could not have found:** a violation expressed as a *number* rather than a
token (a hard-coded threshold written `5_000_000` or as an expression); a float introduced
by an identifier my patterns do not name; anything in the 174 lines the diff *removes*;
anything outside the merged diff (I did not re-audit unchanged files); and any claim in
`T86.md`, `reviews/T86-review-t81.md` or `.softhouse/vectors/README.md`, which this branch
does not touch and which T113 §8 correctly parks on T93.

---

## 11. Findings, ranked

### F-T150-1 — **P2, MICRO-FIX.** "unconditionally" is false; four exit-2 paths print no probe line, and the driver parks on all four
`conformance.sh:70-71` and `:1085` (branch); `T113.md` erratum; `SKILL.md:116` on `main`.
Driven red on the scratch merge with a HARD-guard failure: exit 2, **zero** `probe =` lines.
Prose fix given in §4. **Inherited from `main`, propagated by T130 — a follow-on, not a
blocker.**

### F-T150-2 — **P3, MICRO-FIX.** The fourth statement of the `read` rule is over-scoped
`conformance.sh:208-215`; `interpreter-matrix.sh:186-193`. The rule is right for every
whitespace-free IFS (960 of my cases + 3,282 of T130's, 0 disagreements, three majors) and
**false** once IFS mixes whitespace and non-whitespace: `IFS=" a"`, line `bb a` → `bb`, not
`bb a`; `IFS=" a"`, line `a ` → empty, not `a`. T130's *rig* scopes the predicate correctly
("with IFS containing no whitespace"); the *harness comment* drops the scope while carrying
a `[VERIFIED]` tag for a narrower sweep. **The `[6b]` implication is unaffected — I verified
it independently over 9,799 IFS values including whitespace, 0 truncations, control
truncated by 71.** Fix: restore the scope, or state the whitespace case, and add "IFS
containing whitespace was not swept" to the UNVERIFIED list.

### F-T150-3 — **P3, advisory.** The token invariant is asserted only in a handoff rig
`--prove` has 21 rows and none of them concerns the interpreter guard. A rename is caught
only by a human running `interpreter-matrix.sh`. Recommend a `--prove` row as the follow-on.

### N-T150-1 — advisory, **already open as N-T113-4.** `interpreter-matrix.sh:115` silently skips absent shells; `[1b]` can inspect zero interpreters and pass. The last negative assertion in the file.

### N-T150-2 — advisory. The matrix's three scratch files use fixed names in the live `.softhouse/` and are not gitignored; concurrent runs collide. Use `mktemp -d`.

### Upheld without qualification

- The inherited-`IFS` null-control finding, on three bash majors, by my own probe.
- The 12-cell crossproduct, exactly as published, on three bash majors.
- The red proofs: 26/0-silently-admitted vs 67/4 with a genuine exit-3 false refusal; 69/0
  green on restore; 1/4 against real pre-fix bytes with the control green; 0/3 and 9/10 for
  the two container rigs; exit 1 when the container produces nothing.
- T106's rig byte-unmodified, 8/0 and 7/1, control green in both legs.
- The §6 Alpine false failure and its fix — both branches graded, neither skipped.
- N-T113-5 closed: bash 4.4.0 built and measured independently; POSIX-mode psub is a parse
  error on 4.4; boundary `(4.4, 5.3.9]`.
- The judgement call: **assert rather than restructure was right**, and both stated reasons
  are now measured rather than argued.
- F-T121-3: `conformance.sh` and `SKILL.md` agree, modulo F-T150-1.
- Every new rig is a positive assertion and errors on starved input (P-35).

---

## 12. `[UNVERIFIED]` — my honest list

- **bash 5.0, 5.1 and 5.2.37.** I bracketed the POSIX-mode psub boundary to `(4.4, 5.3.9]`
  with my own 4.4 build; I did not locate it. The T97 tags about 5.2.37 in
  `conformance.sh` and `softhouse-uat/SKILL.md` remain open.
- **A complete graded conformance run under any bash 5.x.** Still none. My PASS, like every
  one on record, is macOS bash 3.2.57.
- **Locale.** Every `read`/IFS measurement in this review ran under the host default locale.
  I did not sweep locale × IFS, and neither did T130 or T121.
- **Non-ASCII / multibyte IFS.** My 9,799-value sweep is printable ASCII plus space, tab and
  newline. A multibyte IFS character cannot appear in the ASCII token, so I do not expect a
  surprise, but I did not measure it.
- **T121's N-T121-2** (`/dev/fd` present at mode 000 on 5.3.9) and four of the six exotic
  shells in **N-T121-3**. Recorded on T121's authority; I re-measured only busybox `sh` and
  `/bin/ash` (both exit 3), as ordinary matrix rows in my alpine run.
- **Whether a `BASH_ENV` that assigns `IFS` can arise in any environment this program
  meets.** I proved the route delivers on three bash majors. I have no evidence of
  occurrence, and neither does T130.
- **The `readonly`-sourced refusal outside this repo.** Not swept by me.
- **`T97.md`, `T86.md`, `reviews/T86-review-t81.md`, `.softhouse/vectors/README.md`.** Not
  re-audited line by line; the last is correctly parked on T93.
- **`main` after `2f3d7d2`.** `main` moved twice while I worked (`3bc6d5d` → `2f3d7d2`). My
  P-24 battery is against `2f3d7d2`. A merge against a later `main` should be re-run, per
  P-24 itself.

---

## 13. Mergeable ruling

**MERGE THE INTERPRETER-GUARD STREAM.**

- The executable delta of this branch over `main` is the T97/T113 guard plus the F1 fix,
  already reviewed by T106, T113 and T121. **T130 adds not one executable line to
  `conformance.sh`** — mechanically verified, not asserted.
- The scratch merge into **current** `main` is clean, PASSes at exit 0 with 42 vectors and
  5,576 cells, `--prove` 21/0, `sh` → exit 3 with zero verdict tokens, `gofmt -l` names only
  the ratified `contract.go`, and `vectors/` and `nexus/` diffs are empty.
- The one thing on this branch that decides PASS — the interpreter guard — is now defended
  by an invariant that is **asserted, spelling-independent, and driven red at three levels
  of abstraction**, where four previous rounds defended it with prose over a null control.
- The two prose defects (F-T150-1, F-T150-2) are strictly less dangerous than what `main`
  carries today: `main`'s `conformance.sh` still states T113's **false** `read` rule and has
  no token invariant at all, and `main`'s `SKILL.md` already carries the "unconditionally"
  word that F-T150-1 is about. **Holding this branch preserves worse sentences than merging
  it.**

Follow-on task, in this order: **F-T150-1** (the exit-2 park condition, `conformance.sh` +
`SKILL.md`), then **F-T150-2** (re-scope the `read` rule and extend the UNVERIFIED list),
then **F-T150-3** (a `--prove` row for the token invariant) and **N-T150-1** (close
N-T113-4). None of them blocks the merge.
