# `.softhouse/hooks/` — what is here, and the one thing you must not re-attempt

**T336, 2026-08-28.** Read this before writing any git hook for this pipeline.

## THE MEASUREMENT THAT DECIDES IT

> **The agent harness creates worker worktrees WITHOUT RUNNING GIT HOOKS.**
> Not `post-checkout`. Not `reference-transaction`. None.

Five real worker spawns through the real route (`Agent` tool, `isolation: worktree`) on
2026-08-28 between 11:57 and 12:03, with an always-`exit 0` logging `post-checkout` and a
logging wrapper around T312's `reference-transaction` installed in
`/Users/buv/gerege-nbfi/.git/hooks/`, produced **zero invocations of either hook**
[VERIFIED: `../capture/t336-post-checkout-decision/out/real-route-POSTCHECKOUT-FIRED.log`,
`…/real-route-REFTXN-FIRED.log`].

The control that makes that a measurement rather than a broken instrument: in the same
minute, from the same `.git/hooks` directory, **both hooks fired for a worker's own git
commands** — `post-checkout` at 12:03:18 with `$3=1` for
`git checkout -b softhouse/T270-superseded-trap`, and `reference-transaction` at 12:01:38
for `refs/heads/softhouse/T323-wire-unwired-guards`. The harness spawn at 12:03:00, between
those two, logged nothing. `core.hooksPath` is unset at every level and no `GIT_*` hook
variable is set in a worker's environment [VERIFIED: worker probe, `git config --list
--show-origin`].

The spawn is nonetheless done by git: the branch `refs/heads/worktree-agent-<id>` gets a
real reflog entry, `branch: Created from origin/main`, and the worktree's `logs/HEAD` is
byte-shape-identical to what `git worktree add -b <branch> <path> origin/main` writes
[VERIFIED: `…/out/reflog-signature.txt`]. So git ran; its hooks were suppressed.

### What that kills

* **A `post-checkout` push-before-spawn gate.** T279 built one
  (`../capture/t279-lock-partition/post-checkout`); it is **not installed and must not be**.
  T280's F-C — that it exits 1 and git creates the worktree anyway — reproduces exactly
  (`…/out/fc-reproduce.txt`: `rc=1`, branch created, files checked out, and a worker
  committed inside the "refused" worktree). But F-C *understates* the problem: on the real
  route the hook does not run at all, so it cannot even warn.
* **A `reference-transaction` gate.** This one **genuinely can veto** a `git worktree add`
  — in the `prepared` state it produces `fatal: ref updates aborted by hook`, rc 255, **no
  branch, no directory, no admin dir, nothing to work in**
  (`…/out/refuse-candidates.txt`, cases B1a/B1d, with B1c/B1e as the permitting controls).
  It is a real precondition, and it is **useless here anyway**, because the harness does not
  invoke it for the spawn.

**Do not file another task to install a git hook at the spawn instant.** Re-measure this
first if you believe the harness changed; the probes are checked in.

## What IS here

* `push-before-spawn-audit.py` — a **detector**, not a guard. It reconstructs what
  `origin/main` said at the instant each live worker worktree was created, and fails if
  origin was still lying about the fire. Nothing calls it automatically; until something in
  the driver's exit path does, the obligation is a **convention**. Driven red and green:
  `…/out/audit-red-green.txt`.

### The driver push gate — T412, repaired by T453

`pre-push`, engaging only for `refs/heads/main`. **Every file below is part of one unit and
the installer copies all of them into the install-time snapshot** — the list lives once, in
`install-driver-push-gate.sh`'s `GATE_PARTS`, because T412 wrote it twice (checked three,
copied two), the omitted file was `bar-attest.sh`, and the gate's own refusal message names
it. The driver of fire 20260829-080002 followed that message, found nothing, and lost a
merge to it.

| file | what it is |
|---|---|
| `driver-push-gate.sh` | the gate: C1 gitlinks (tip **and every commit in the pushed range**), C2 driver write-path allowlist, C3 grade identity + the STATE set |
| `cheap-subset.sh` | the P-number citation checker, run against a **named tree**, not the working tree |
| `bar-attest.sh` | materialises a commit's tree in scratch, runs the full bar there, writes the ledger row. The **only** way to satisfy C3 |
| `added-path-hazard.py` | **[T453]** does ADDING these paths make a **pinned dead literal resolve**? Read out of the *pushed tree's own pin*. `--selftest` drives both polarities |
| `install-driver-push-gate.sh` | installs / `--status` / `--uninstall`. **`--status` exits 1 when the gate is absent or incomplete** |
| `reconcile-pushed-trees.sh` | **[T453, FU-T412-4]** post-hoc: every tip in `origin/main`'s reflog reconciled against the ledger, scanned for gitlinks, and `bypass.log` finally read |

**Two things about this gate that must not be forgotten.**

1. **`pre-push` is client-side. `--no-verify` turns it off.** C1 says "THERE IS NO BYPASS";
   that is true about the gate and false about git — T450 drove a gitlink onto `main` with
   zero gate output. `reconcile-pushed-trees.sh` is the answer: it cannot *prevent* the
   bypass, it makes it **countable**, one fire later. Do not read C1's sentence as a
   guarantee about the ref.
2. **The STATE set is not a list of files the guards read.** Three of the fifteen guards
   resolve against the tree's **inventory** and never open the file you touched, which is
   why T412's read-oriented table let four bar-red trees through. Anything that widens the
   STATE set must answer the inventory question too, and clause (k) answers it by
   *measurement against the pin*, deliberately, because the table is what rotted.

Installed by `.softhouse/bin/fire-program.sh` at every fire, beside T312's `refguard` lines
— **not** by a human remembering. If you move that call, `--status`'s exit code is what any
replacement must keep testing.

## The candidate nobody has tested yet

A Claude Code **`PreToolUse` hook on the `Agent`/`Task` tool** is the only remaining place
that could actually refuse a spawn: it runs in the harness, at dispatch, and a `deny`
decision stops the tool call before any worktree exists. It is **[UNVERIFIED]** here —
T336 did not test it, because it requires creating `.claude/settings.json` (there is none:
no `settings.json`, no `settings.local.json`, and the user-level file has no `hooks` key
[VERIFIED]), and a worker may not change harness configuration. Whoever picks this up must
drive it **red** first — a spawn that is actually refused — before any prose calls it
enforcement.
