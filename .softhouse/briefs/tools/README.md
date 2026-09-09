# Measurement tools — control-test these before trusting a number

Extracted from the 2026-09-09 session, where SEVEN measurement bugs shared one root:
measuring a proxy for the property instead of the property, and arming the instrument
without testing it once. Each script here was wrong at least once before it was right.

    kills.sh       <ctx> <impl>            kill count for one wrong implementation
    capcount.sh    <worktree> <ctx> <impl> same, against an arbitrary worktree
    redcount.sh    <worktree> <ctx>        count of registered <ctx>-wrong-* drives
    drivecount.sh  <worktree> <ctx>        same, simpler form
    ohwatch.sh     [conv-dir ...]          status of every live OpenHands run

## The rule these encode

**Run against a KNOWN CONTROL before trusting output.** On `main`:

    loanschedule-wrong-days-in-year-365   must report 45
    loanschedule-wrong-half-even          must report 5
    parties-wrong-iota-ordinals           must report 12
    charges-wrong-rounding-half-even      must report 1
    loanproduct drive count               must report 4

If a control is wrong, the instrument is wrong — not the tree.

## THE SILENT ZERO — repaired 2026-09-09, and why it was the worst one

Every one of these tools used to print a bare `0` on **every** failure path, and
`capcount`/`redcount` additionally `exit 0`'d. Measured that day: run from the repo
root instead of `nexus/`, **all four controls below reported 0** — 45, 5, 12 and 1
all came back as 0, with nothing on stdout or in the exit status to say so.

That is worse than a lost measurement. A `0` from a tool whose job is counting kills
reads as **"this drive is INERT"**, and an inert drive is a finding this programme
acts on — promote a vector that sees it, or delete it with the argument. So the silent
zero did not merely fail to measure; it **manufactured a false finding of exactly the
kind these tools are pointed at**, and the brief rule "a drive that kills ZERO is a
finding to resolve" would have been applied to a drive that was never run.

**The rule now enforced:** a measurement that did not happen must not look like a
measurement that came back zero. On any failure these print **nothing** to stdout, the
reason to stderr, and **exit 2** — so `$(...)` yields empty and the caller breaks
loudly at the point of use. Shared prelude: `_measure.sh`.

Driven red, all five paths, before this was believed: nonexistent worktree, unknown
context, misspelt impl name, `redcount` bad worktree, `drivecount` bad worktree — each
exits 2 with no number. The contrast on the same input: old `'0'` exit 0, new exit 2.

**`kills.sh` no longer depends on cwd** — the worktree defaults to the repo the script
lives in, and is overridable as a third argument.

### The second silent zero, closed at the same time

A **misspelt implementation name** was not rejected: the binary fell through to the
CORRECT implementation, which kills nothing, and the typo read as an inert drive.
`m_require_registered` now checks the name against the binary's own
`-list-implementations` first. Note the listing's shape — `<name>   [-impl] <prose>`
with the prose **wrapping onto continuation lines** — so the name is the **first
field**. Matching the whole line finds nothing (this was wrong once, here, and the
control caught it); matching a substring would accept a name merely *mentioned* in
another drive's prose, and they do cite each other by name.

## `ohwatch.sh` — detect the STALL SIGNATURE, never CPU

A stalled agent is **not an idle process**. Run K sat at **14% CPU doing nothing for
twelve minutes**, so any liveness check built on load average would have called it
healthy the whole time. The signature is the agent **polling a dead terminal**: an
EMPTY terminal command, an observation carrying `exit_code -1`, then ANOTHER empty
command.

`ohwatch.sh` reads the event stream (`~/.openhands/conversations/<id>/events`) and
reports, per run, the event count, seconds since the last event, the last action, and
`STALLED` when the signature is present in the recent tail. It requires the
**conjunction** — repeated empty commands AND a `-1` exit — because either alone is
normal: an agent legitimately sends one empty command to drain a long-running terminal,
and `-1` appears on a genuine timeout.

**Control-tested on the case it was built for.** Run K's own conversation
(`b515218ef37c4175afed35872b126de2`, worktree `oh-gerege-redk`) is flagged `STALLED`
with `empty=2 exit-1=2`, while two concurrently healthy runs on the same machine are
not flagged. An instrument that only ever reports "fine" has not been tested.

When it fires: **kill the run, verify its tree against the bar, and commit its finished
work on its behalf.** A stalled agent has usually done most of the work already.

## The three traps baked into these scripts

1. `-root` IS NOT UNIVERSAL. Most `cmd/conformance` binaries REQUIRE it; loanschedule's
   REJECTS it, and the two error texts differ ("‑root is required" vs "not defined:
   -root"). Handle both or a context silently reads 0.
2. `grep -c` PRINTS 0 AND EXITS 1. Never `grep -c … || echo 0` — it yields "0\n0" and
   every later `$(( ))` dies with "bad math expression".
3. NO `||` FALLBACK AROUND THE MEASUREMENT. A FAIL verdict IS exit 1, so a fallback
   fires on every real kill and concatenates two runs' output.

Also, from the same session: zsh does NOT word-split unquoted variables, so
`for w in $ws` passes the whole list as one argument. Use `while IFS= read -r`.
And macOS has no `timeout(1)` — a liveness check built on it reports "hung" when the
binary is merely absent.
