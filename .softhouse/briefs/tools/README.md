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

**Two trailing -1s is NOT a kill signal, and treating it as one cried wolf twice on
2026-09-10.** A run at `trailing=2, idle=2s` had just issued a real command — it wedged and
was already recovering, which is what two other runs did that day, one of them going on to
close the fee/penalty finding. The instantaneous condition "cannot run a command right now"
is TRUE for a healthy agent mid-recovery.

The signature that matters is **SUSTAINED**, so a kill needs evidence of TIME or of
REPETITION:

    trailing >= 2                  -> wedged(recovering?)   visible, NOT a kill signal
    trailing >= 4                  -> STALLED-NOW           dead terminal, regardless of idle
    trailing >= 2 and idle >= 180s -> STALLED-NOW           wedged and not recovering

Control-tested on four real conversations, both polarities, including two live runs:
run K (`trailing=2`, idle 24h) fires by time; the run killed on 2026-09-10
(`trailing=6`, 8 events in 5 minutes, all failed probes) fires by repetition; a live
recovering run (`trailing=2, idle=35s`) does NOT fire; a healthy run does not fire.

### The THIRD stall: the agent, not the terminal

`OH-GLVEC-AB` sat at **11.6% CPU for ten minutes** with `trailing-1 = 0`. Its command had
COMPLETED — no process left, its output file had stopped growing — it had not probed
anything, and it simply never emitted another event. The shell was fine; the agent was
blocked on the LLM (the provider had logged `DeepseekException - peer closed connection
without sending complete message body` earlier the same day). **Neither terminal rule
catches this, because there is no `-1` to count**, and CPU says nothing: 11.6% of a core is
indistinguishable from work. It is exactly the shape of run K.

**The signal is SILENCE plus LIVENESS.** A working agent emits events; even a long command
emits one when it finishes. But idle alone is not enough — a conversation directory
outlives its process, so a *finished* run's idle grows without bound and eventually looks
identical to a stalled one.

    no live process whose cwd matches this conversation -> (no live process)
    live, idle >= 600s                                  -> STALLED-NOW(silent)

Liveness is **measured**, from `ps` + `lsof -d cwd`, not inferred from idle time.

**This rule took three attempts, and each wrong version was caught by the control test, not
in production:**

1. idle alone — lit up run K *and* a run that had finished successfully and been **merged
   hours earlier**.
2. a 600s–3600s window — still flagged a merged run that happened to sit inside it.
3. real liveness matching — correct on both polarities: a live run at `idle=1s` is
   unflagged, killed and finished runs read `(no live process)`.

**Attempt 3's first cut had a false NEGATIVE, and it was worth more than the fix.** It
reported a genuinely live run as dead, because the run's commands said
`cd /Users/buv/oh-gerege-glvec` while its process cwd was `/Users/buv/oh-gerege-glvec2` —
**the driver had re-dispatched into a new worktree without updating the path written in the
brief**, so the agent was working in the *previous, killed* run's directory on the *old*
branch. The detector's disagreement with reality exposed a dispatch bug that would
otherwise have produced a commit on an abandoned branch. **When an instrument and the world
disagree, find out which is wrong before fixing either.**

**What kills a terminal, in practice:** an **unterminated quote**. The 2026-09-10 kill was
a `docker exec … psql -tAc "SELECT …` whose closing `"` was missing. The shell sat on stdin
waiting for the rest of the string; it does not error, it hangs, and it takes the run with
it. `C-c` does not rescue it either — the wrapper sends `C-c` as *input text* to a shell
that is asking for more string.

When STALLED-NOW fires: **kill the run, verify its tree against the bar, and commit its
finished work on its behalf.** A stalled agent has usually done most of the work already —
though the 2026-09-10 kill had none, having wedged at event 31.

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

## The oracle's database is `gerege-oracle-db` — NOT `fineract-db-1` (2026-09-11)

Two PostgreSQL 18.3 containers on this host both carry a `fineract_gerege` database.
**Only `gerege-oracle-db` (host port 55432) backs the live reference oracle
(`gerege-oracle-app`, :8443).** `fineract-db-1` (host port 5432) is a stale, older instance:
it answers every query convincingly and wrongly (on 2026-09-11 it held 109 journal entries
with max id 113 while the live oracle's REST returned ids up to 140).

Control before trusting any SQL read: the row count / max id of the table you read must
agree with what the REST API returns for the same tenant. `docker exec gerege-oracle-db
psql -U postgres -d fineract_gerege -At -c '…'` — read-only, and never `fineract_default`.

A committed capture is also not the live tenant: `tierA-a2/` (A2-3xx) came from an earlier
instance — its journal-entry ids name different rows on today's `gerege`.

## review.sh — the merge review as one command (2026-09-11)

    bash .softhouse/briefs/tools/review.sh <worktree> <context> [impl]

Reads the run's COMMITTED diff against main and checks: scope, guards untouched, float on
added lines, every added vector's capture hashes, the four standing controls, every added
drive WITH the store and WITHOUT the added vectors, the corpus (impl fails 0), and coverage
of every changed port function from the graded corpus. Exit 0 PASS / 1 FAIL / 2 a
measurement did not happen. It never merges or pushes — the driver still reads the diff.

Control-tested on OH-REVERSAL-X (`REVIEW_BASE=aa19ef6e^`, worktree at `aa19ef6e`): it
reproduced every figure the driver had measured by hand — 4 drives 1/0, both hashes, 35
drives, 87.5% / 75.0% coverage. Its first run also caught a wrong control name in itself
(`…-rounding-half-even` does not exist; the impl is `loanschedule-wrong-half-even` = 5) and
reported it as UNMEASURED rather than 0.

`ledger` drives are not measured here (no conformance binary): read the CENSUS block.

## mapgen.py — one generated MAP per context (2026-09-11)

    python3 .softhouse/briefs/tools/mapgen.py [--root <worktree>] [<context> …]   # writes .softhouse/maps/<ctx>.md

For each context: seams and capabilities (with `in_graded_domain`), every vector and its
capture, where `Register`/`RegisterWrong` live, every drive with file:line, every port
function with file:line, the captures its vectors cite, every capture directory's OWNER
title, the measuring commands for THAT binary, and the oracle / DB / source locations.
**Generated, never hand-written — regenerate after every merge that touches a context.**

Control-tested before use: each map's drive count against the binary's own
`-list-implementations` — 14/14 binaries agree, and ledger's 17 equals its census. The
control caught two defects first: `loanschedule` registers 17 of its 25 drives through a
table (the generator now takes the list FROM THE BINARY), and the driver's own check loop
reported 0 for thirteen binaries because zsh passed `-root <path>` as ONE argument — the
same word-splitting trap recorded above, this time in the control, not the tool.

## Two instrument defects found 2026-09-11, both by a control disagreeing

1. **mapgen.py counted another context's drives.** The loanschedule binary HOSTS the 17
   ledger drives (`-ledger-impl`), so "every `-wrong-` name" gave loanschedule 25 drives
   where it has 8. The first control compared the map against the binary with the SAME
   `-wrong-` grep, so the two agreed for the wrong reason — **a control that shares the
   instrument's bias is not a control.** The re-run control uses three independent
   readings (binary listing filtered by `<ctx>-wrong-`, redcount.sh's own listing, the
   map) and all 14 binaries agree.
2. **capcount.sh could not measure loanschedule-go.** That binary gates its verdict on
   `-oracle-probe`; a WRONG impl prints `LOAN SCHEDULE N mismatch` before the UNUSABLE
   verdict (so kills.sh worked), the CORRECT impl printed nothing measurable. `m_run` now
   passes the oracle's ACTUAL health (a down oracle still yields exit 2), and `m_extract`
   reads `VERDICT: PASS (exit 0)` with no mismatch line as 0. Controls after: 45 / 5 / 1,
   capcount loanschedule-go 0, savings-go 0.
