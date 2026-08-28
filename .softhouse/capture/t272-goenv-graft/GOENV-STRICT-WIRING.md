# FU-T272-1 — wiring `GEREGE_GO_STRICT` at the three call sites

**Filed by T272, which grafted the strict arm into `.softhouse/bin/go-env.sh` but does NOT own the
call sites.** `.softhouse/conformance.sh` belongs to **T326** this batch and `.softhouse/bin/fire-program.sh`
to **T324**; the two guards are outside T272's `files_hint` as well. So this is written the way T319 wrote
`CONFORMANCE-WIRING.md`: the exact patch, the reasoning, and the per-site fail-closed direction, filed rather
than applied.

## The problem, stated as a measurement and not as a worry

`GEREGE_GO_STRICT=1` with the pinned toolchain absent now makes `. go-env.sh` **return 2** and set
`GEREGE_GO_SOURCE=refused`, exporting nothing. **It does not remove `go` from `PATH`** — deliberately; a
sourced env file must not hide a compiler it did not install.

**None of the three call sites checks either signal.** [VERIFIED by reading them at this commit:
`.softhouse/conformance.sh:650-654`, `.softhouse/guards/check-ledger-invariants.sh:55-60`,
`.softhouse/guards/drive-red-ledger-invariants.sh:27-31` — every one is
`if [ -f "$env_script" ]; then . "$env_script"; fi` followed by an unconditional `command -v go` test, and no
reference to `$?` or `GEREGE_GO_SOURCE` appears in any of them.]

**Driven, not argued:** `.softhouse/capture/t272-goenv-graft/evidence/20-strict-drive.txt`, arm **A9**. With
`GEREGE_GO_STRICT=1`, no pinned toolchain, and a shim `go` on `PATH`, `check-ledger-invariants.sh` sourced
go-env.sh, read the refusal banner on its stderr, **ignored it, built the guard with the shim compiler and ran
it** (`ledger-invariants: selftest OK — 15 cases, 13 RED, 2 GREEN`). Its final `rc=1` is its own
population-floor refusal about the scratch checkout and has nothing to do with strict; the load-bearing fact is
that it *got that far at all*.

**So today strict is LOUD BUT ADVISORY.** The banner says so in the transcript, which is the honest interim
position, but it is an interim position.

## THE FAIL-CLOSED DIRECTION, PER CALL SITE — read this before writing the patch

T292 identified the root of a five-fix losing streak as **widening one predicate to serve two purposes whose
fail-closed directions are opposite.** That hazard is live here, because two different questions are being
asked within four lines of each other:

| predicate | question | fails closed by | must NOT be merged with |
|---|---|---|---|
| **P-env** — status of `. go-env.sh`, or `GEREGE_GO_SOURCE = refused` | *did the toolchain seam refuse to supply a toolchain?* | treating **non-zero / `refused`** as STOP | P-go |
| **P-go** — `command -v go` | *is there any compiler at all?* | treating **absence** as STOP | P-env |

They point opposite ways. P-env fails closed on a **positive** signal (a refusal was issued); P-go fails closed
on an **absence** (nothing was found). A single widened test — e.g. `if ! command -v go || [ "$rc" -ne 0 ]` —
would read as one predicate and would be maintained as one, and the first person to relax either half relaxes
both. **Keep them as two separate `if` blocks with two separate messages.** The patch below does exactly that,
and the new block goes **BEFORE** the existing one so a refusal is reported as a refusal rather than being
re-described as "no Go toolchain", which would be false whenever a `go` is sitting on `PATH`.

## The patch — `.softhouse/guards/check-ledger-invariants.sh` (T272 does not own this file)

Replace lines 55-60:

```sh
  local env_script="$REPO_ROOT/.softhouse/bin/go-env.sh"
  if [ -f "$env_script" ]; then
    # shellcheck disable=SC1090
    . "$env_script"
  fi
  if ! command -v go >/dev/null 2>&1; then
```

with:

```sh
  local env_script="$REPO_ROOT/.softhouse/bin/go-env.sh"
  local env_rc=0
  if [ -f "$env_script" ]; then
    # shellcheck disable=SC1090
    . "$env_script" || env_rc=$?
  fi
  # P-env. A DIFFERENT QUESTION FROM THE ONE BELOW, AND IT FAILS CLOSED IN THE OPPOSITE
  # DIRECTION (T292): this refuses on a POSITIVE signal — go-env.sh issued a refusal —
  # whereas the next block refuses on an ABSENCE. Do not merge them into one condition.
  # go-env.sh returns non-zero in exactly one arm: GEREGE_GO_STRICT set and the pinned
  # toolchain absent. It does NOT remove the PATH `go`, so without this block the guard
  # would build with the very compiler the operator just said to refuse.
  if [ "$env_rc" -ne 0 ] || [ "${GEREGE_GO_SOURCE:-}" = refused ]; then
    warn "ledger-invariants: $env_script REFUSED (rc=$env_rc, GEREGE_GO_SOURCE=${GEREGE_GO_SOURCE:-unset})."
    warn "ledger-invariants: GEREGE_GO_STRICT is set and the PINNED toolchain is not on this host, so"
    warn "ledger-invariants: substituting an unpinned compiler was declined by configuration. A \`go\` may"
    warn "ledger-invariants: still be on PATH; it is NOT being used. EXIT 2 — NOT a pass."
    exit "$EXIT_UNUSABLE"
  fi
  # P-go. Absence of any compiler. Unchanged.
  if ! command -v go >/dev/null 2>&1; then
```

`drive-red-ledger-invariants.sh:27-31` takes the same shape with `say`/`exit 2` instead of `warn`/`exit
"$EXIT_UNUSABLE"`, and `conformance.sh:load_toolchain` the same with `warn`/`exit "$EXIT_UNUSABLE"`.

**Why `|| env_rc=$?` and not `set -e`.** All three consumers run `set -u -o pipefail` and none sets `-e`
[VERIFIED: `conformance.sh:396`, `check-ledger-invariants.sh:39`, `drive-red-ledger-invariants.sh:18`]. Under
`set -u` an uninitialised `env_rc` would abort, so it is initialised to 0 on the line above. **Do not "fix"
this by adding `set -e`** to any consumer: a strict refusal would then kill the script before it printed its
probe line, which is P-84 ("*exit 2 with NO probe line PRINTED is a FAILED HARD GUARD, not an oracle outage —
test for the line's PRESENCE before its value*") manufactured on purpose. The explicit `exit` above prints
first and exits second.

**Why `[ "${GEREGE_GO_SOURCE:-}" = refused ]` is ORed in rather than trusted alone.** Two independent signals
for one condition, because each can be lost on its own: a future consumer might wrap the `.` in a construct
that swallows the status, and a stale exported `GEREGE_GO_SOURCE` from an earlier sourcing could survive in a
long-lived shell. Neither is a reason to drop the other. They are two witnesses to **one** predicate (P-env),
which is not the same thing as merging two predicates.

## Order of landing, and the one thing that must be true first

**This wiring must NOT land before something sets `GEREGE_GO_STRICT`, and it must not land after it either —
it must land BEFORE.** As of T272 **neither fire sets the variable** [VERIFIED:
`evidence/10-locate-cloud-arm.txt` §6 — no occurrence in `.softhouse/bin`, `.softhouse/launchd` or `.claude`],
so this patch is a **no-op on both hosts today** and can land safely at any time. If it landed *after* a fire
started setting strict, there would be a window in which the harness announced a refusal and then built anyway.

## The related, still-undispatched finding this sits next to

**T267** — the toolchain-substitution notice goes to **stderr only**, so a reader of the graded transcript
never learns which Go compiled the money guard. T272 could not take T267's fix (it names `conformance.sh`).
Two things T267 gets from this work:

1. **Print the TOKEN, not the path.** `GEREGE_GO_SOURCE` is now one of `pinned` | `fallback-path` | `absent` |
   `refused` — four bare tokens, host-independent by construction, safe to compare across the two fires and
   safe to put in a graded verdict block. `GEREGE_GO_BIN` carries the absolute path and is **host state**;
   print it as detail on its own line, never grade on it, never diff it across hosts. This is why T272 declined
   T254b's literal `substituted:/abs/path` form, which would have folded a `/Users/buv/...` string into the
   exact variable T267 wants rendered into the verdict.
2. **`refused` is a fourth value T267 must render**, and it is the one where the verdict block matters most.
