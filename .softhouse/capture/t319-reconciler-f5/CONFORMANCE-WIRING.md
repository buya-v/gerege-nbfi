# T319 — the exact wiring for `conformance.sh`, which I could not take

**I did not edit `.softhouse/conformance.sh`.** It is not in T319's edit set and it is
contended this fire — T305, then T313/T315/T317. This file is the patch, specified to the
line, for whoever holds that file next.

## The finding, restated with its measurement

```
$ grep -c 'fire-program\|ready-tasks\|reconcile\|in_progress' .softhouse/conformance.sh
0
```

[VERIFIED: this checkout, 3,101 lines, T319 re-ran it.] Raised by T302 as item (c) and
upheld here.

Nothing automated grades any of it. T309 built an 8-cell ownership matrix and a 3-cell
SIGTERM matrix, both good harnesses, both under `.softhouse/capture/`, and **nothing runs
them** — so T309 shipped 8/8 green with a discriminator that would have destroyed seven
live workers, and the code that decides whether to demote live work has zero automated
coverage.

The standard the repo holds itself to is in that same file, at `conformance.sh:909-915`:

> *"EACH GUARD RUNS ITS OWN SELFTEST FIRST, IN THE SAME INVOCATION. A wired guard that has
> been quietly neutered is worse than an unwired one, because it is believed (P-22). So the
> selftest — which drives the guard RED on a planted defect AND requires it to stay GREEN
> on a clean tree (P-50) — runs on every conformance run, **not on the day someone
> remembers**."*

**P-22** — *"A guard, a canary, or a control that cannot fail is worse than none — because
it is believed"* [VERIFIED: `.softhouse/patterns.md`, P-22].
**P-45** — *"a guard that only works when someone remembers to run it enforces nothing"*
[VERIFIED: `.softhouse/patterns.md`, P-45]. This is P-45 moved one level out: the *guards*
are wired to the signal path; their *tests* are wired to nothing.
**P-89** — *"THREE ARTEFACTS SHIPPED WIRED TO NOTHING IN ONE FIRE … THE FIX IS A FILED
TASK, NOT A SENTENCE"* [VERIFIED: `.softhouse/patterns.md`, P-89, restated as *"prose does
not fire on the next fire"*]. So this is a specification, not a recommendation.

## The patch

### 1. Add the guard function, beside the other HARD guards

Insert after `guard_no_host_state_in_lint_corpus()` (currently ends before `run_guards()`
at `conformance.sh:1996`):

```sh
# ---------------------------------------------------------------------------
# guard_reconciler_ownership: the reconciler's ownership predicate is GRADED.
# ---------------------------------------------------------------------------
# WHY THIS IS HERE AT ALL. `.softhouse/bin/ready-tasks.py --reconcile` decides whether to
# rewrite `in_progress` tasks to `needs_retry`. Getting that wrong in the demoting
# direction DESTROYS LIVE WORK AND CANNOT BE UNDONE. Until T319 not one line of
# conformance.sh mentioned `fire-program`, `ready-tasks`, `reconcile` or `in_progress`
# (measured: grep -c => 0, over 3,101 lines), so three consecutive attempts at that
# predicate shipped with no automated coverage and the third would have demoted seven live
# workers of the fire that was holding the lock.
#
# THE GUARD IS THE MATRIX, AND THE MATRIX CARRIES ITS OWN RED/GREEN. `--selftest` plants
# T309's shipped single-term predicate into a COPY of ready-tasks.py and REQUIRES cell B'
# — the cell whose clock advances across a re-dispatch — to go red against it, and green
# against the shipped tool. It also refuses to run at all if no cell in its table advances
# the clock across a re-dispatch, so deleting the cell that catches this class is a red
# run rather than a smaller green one.
#
# HARD GUARD. A non-zero exit means the ownership predicate is UNGRADED, which is not a
# FAIL verdict and is not an oracle outage: it exits 2 through run_guards, BEFORE the
# `reference oracle (…) probe = …` line is printed, so the driver's park condition
# (`exit 2` AND a probe line PRESENT reading `down`) is not met. P-84 — "'EXIT 2 WITH NO
# PROBE LINE' IS THE GUARD WORKING. READ THE ABSENCE, NOT THE VALUE."
#
# COST, MEASURED on this host [T319, .softhouse/capture/t319-reconciler-f5/]:
#   green leg only          14.7 s real   (13 cells)
#   with --selftest         29.9 s real   (26 cells, both legs)
# It is the most expensive guard in this file and it is the only one standing between a
# broken predicate and destroyed work. `--selftest` is NOT optional here: the RED leg is
# the only thing that distinguishes this guard from one that cannot fail (P-22), and
# making it a flag somebody sets on good days is P-45 by another name.
#
# IT NEEDS A C COMPILER, AND FAILS RATHER THAN DEGRADING WITHOUT ONE. The matrix compiles
# a four-line exec shim so each cell can CONSTRUCT the `claude` / non-`claude` ancestry
# that selects `in_session` vs `wrapper` mode. Without it every cell would silently run in
# whatever mode the ambient process tree gave — green in one hand, meaningless in another.
# cc/clang/gcc are present on this host [VERIFIED: /usr/bin/cc, T319].
guard_reconciler_ownership() {
  local rig="$REPO_ROOT/.softhouse/capture/t319-reconciler-f5/run-ownership-matrix.py"
  if [ ! -f "$rig" ]; then
    warn "conformance: guard_reconciler_ownership: $rig is MISSING. The reconciler's"
    warn "conformance: ownership predicate is UNGRADED. This is a HARD failure, not a"
    warn "conformance: pass: the last three versions of that predicate each shipped able"
    warn "conformance: to demote live workers, and the rig is what catches it."
    return 1
  fi
  local out rc
  out=$(/usr/bin/python3 "$rig" --repo "$REPO_ROOT" \
          --tool "$REPO_ROOT/.softhouse/bin/ready-tasks.py" --selftest 2>&1)
  rc=$?
  if [ "$rc" -ne 0 ]; then
    printf '%s\n' "$out" >&2
    warn "conformance: guard_reconciler_ownership FAILED (rc=$rc). Full transcript above."
    return 1
  fi
  printf '  %-24s%s\n' "reconciler ownership" \
    "$(printf '%s\n' "$out" | sed -n 's/^GREEN LEG.*: \(.*\)$/\1/p') (RED/GREEN selftest OK)"
  return 0
}
```

### 2. Register it in `run_guards()`

`conformance.sh:2018`, after `guard_no_host_state_in_lint_corpus`:

```sh
  guard_no_host_state_in_lint_corpus  || failed=1
  guard_reconciler_ownership          || failed=1        # T319
```

It joins the `failed=1` tally rather than short-circuiting, because unlike
`guard_graded_root_is_this_tree` it does not invalidate the other guards' answers — one
bad guard must not hide another.

### 3. Add the permanent cell to the matrix's own contract, not to prose

Already done, in the rig: `_assert_matrix_can_see_a_redispatch()` raises `SystemExit` when
no cell in the table has both `redispatch=True` and more than one commit. Cell B′ is
therefore not a cell somebody has to remember to keep — removing it fails the run.

## What this does NOT cover, stated so the gap is visible

- **`fire-program.sh` itself is still ungraded.** This guard drives `ready-tasks.py`
  through a real subprocess and constructs the ancestry, but the wrapper's signal path,
  the worktree sweep and `foreign_live_session_in_repo` are exercised only by
  `.softhouse/capture/t319-reconciler-f5/drive-wrapper-fixes.zsh`, which nothing runs.
  **That should be a second filed task**, same shape: give it a `--selftest`, wire it in.
  T319 did not do it because a zsh harness that fakes `/bin/ps` and reparents processes
  needs the same construction work the matrix needed and the budget went to F5.
- **Gap A, the process gap, is still not closed and cannot be.** A killed real `claude`
  and a never-started fake are byte-identical to `ps` name/stat, `kill -0` and
  `lsof -d cwd`. T302 established this and I have not pretended otherwise.
