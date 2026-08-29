# T445 — `softhouse/T445-case-route`

**Subject:** T444's `M-1` (MAJOR, live on `main`) plus `C-1`, `C-2`, `C-3`, `C-4` and the five LOW.
**Grant:** `.softhouse/conformance.sh` (sole writer this wave), `.softhouse/capture/t445-case-route/`,
this handoff. Nothing else is touched — verified by `git diff --name-only main...HEAD`.

Honesty rule: every material claim below carries `[VERIFIED: <path>]` or is marked `[UNVERIFIED]`.

---

## THE HEADLINE

**T444's M-1 was one instance of a class, and the class had at least three more live members on
`main`. All of them are the same confusion: a test that reads the WORKING TREE deciding a
question about what is COMMITTED.** I re-derived M-1 rather than inheriting it, drove it RED with
my own instrument, then asked T444's own closing question — *which read looks at the index, which
at the working tree, and what happens when the two disagree?* — of **every remaining read in
`guard_guards_dir_registration`**. Three more fail-opens fell out, each driven through the whole
bar at `EXIT 0 / probe PRESENT / VERDICT: PASS` before a character was changed.

**After this change `guard_guards_dir_registration` performs ZERO filesystem reads of any member,
witness or declared-witness path.** The only file it still reads from this host is
`.softhouse/conformance.sh` itself, which is correct and is argued below.

---

## WHAT WAS DRIVEN RED, THEN GREEN

Instrument: `.softhouse/capture/t445-case-route/instruments/drive-t445.sh`, **FROZEN**
`sha256 = 9adf98c4900e81fe79023fbf865d1130543a8136a0889685bed408e8276a764c`, `chmod a-w` before the
runs. It takes its work root and its source repository **as arguments**, so it binds no literal
shared-temp path to a name and adds no row to `HOSTSTATE_PIN_TEMP_ASSIGN_LIST`.

Each arm: clone the tree under test → mutate + commit → **RE-CLONE** (so a case collision
materialises exactly as a fresh checkout would) → apply any working-tree-only mutation → run the
**whole bar** from a cwd outside the repo → record the exit code, then the probe **PRESENCE**,
then its value (P-84 — absence is not `down`), then the census line and the decisive sentences.

`RED` = `eb795f1d` (this branch before any change to `conformance.sh`; the file is byte-identical
to `main`). `GREEN` = `b2c49ca9`. The instrument DETECTS which tree it is grading from the tree's
own text and prints it on every arm; the mode is not passable in.

*(table filled in from the transcripts — see EVIDENCE below)*

---

## EVIDENCE

*(paths filled in below)*
