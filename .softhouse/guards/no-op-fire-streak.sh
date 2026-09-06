#!/usr/bin/env bash
# .softhouse/guards/no-op-fire-streak.sh
#
# T493 — NOTHING ESCALATES A ZERO-TURN FIRE.
# T550 — REAL IS NOW EARNED, NOT INHERITED (T541 MAJOR-1).
#
# WHAT THIS IS
#   A cross-fire watchdog. It reads a git ref's commit history and decides,
#   mechanically, whether a named producer (the local Mac launchd fire, or the
#   cloud fire) has stopped advancing the migration.
#
# WHY IT CANNOT LIVE INSIDE THE FIRE IT WATCHES
#   A fire that cannot run is exactly the fire that cannot report that it could
#   not run. `classify_driver_turns()` in .softhouse/bin/fire-program.sh detects
#   a zero-turn fire precisely and writes the finding into the RESUME.md banner —
#   where nothing reads it. That is P-45 ("a guard that only works when someone
#   remembers to run it enforces nothing") applied to the scheduler itself.
#   So this guard is designed to be run by the OTHER fire: the cloud fire watches
#   the local fire's silence, and vice versa. It takes the producer to watch as
#   an argument precisely so it can never be pointed at itself by accident
#   (see --producer and the self-watch warning below).
#
# THE THREE FAILURE MODES, ALL MEASURED IN THIS REPO'S REAL HISTORY
#   AXIS 1 — NO-OP STREAK.  Fires DO run: they take the lock, reconcile the
#     wrapper state, release the lock, and advance nothing. 2026-08-24/25/26 and
#     2026-08-30/31 are this shape (18 bookkeeping commits per day, 0 real).
#   AXIS 2 — SILENCE.  Fires do not run AT ALL: no lock is taken, so there are no
#     fires to classify and a streak detector alone sees nothing and reports
#     all-clear. The outage live as this guard was written (local producer silent
#     from 2026-09-03T11:09:38Z) is this shape.
#   AXIS 3 — PADDED ADVANCE (added by T550).  A producer commits continuously —
#     so AXIS 2's clock never runs — but nothing it commits is migration work.
#     T541 drove this by construction: eight consecutive fires, each appending one
#     valueless line to docs/*.md, read GREEN on both of T493's axes.
#   A guard that implements only axis 1 goes GREEN on the live outage; a guard
#   that implements only axes 1+2 goes GREEN on T541's padding. All three are
#   checked; RED if ANY trips.
#
# HOW A COMMIT IS CLASSIFIED — REAL IS EARNED, NEVER INHERITED
#   B-11 and P-104 are this program's record of one mistake and T541 is the record
#   of the next one:
#     * guard_no_float_in_vectors matched a WORD LIST and was defeated by
#       rewording; T528 defeated T527's anchor rule with a one-word reword. So
#       this guard never reads a commit subject. Rewording cannot move a commit
#       across any line here, because the subject is not an input. VERIFIED by
#       T541's attacks (a), (b) and (c) — all three defeated.
#     * T493 then keyed the classifier on the FILE FOOTPRINT with the default set
#       to REAL: a commit was real unless EVERY path it touched was scheduler
#       self-churn. A blocklist with a permissive default has an infinite escape
#       set — every path nobody thought to list. T541 walked out of it with one
#       appended line per fire in docs/*.md and drove both axes GREEN.
#
#   T550 INVERTS THE DEFAULT, which is the only repair that closed the equivalent
#   class in .softhouse/bin/check-branch-published.py (T527 closed one phrasing,
#   T528 broke it with a second, T536 closed the class by making every extracted
#   sha REFERENCE by default and requiring LANDING to be EARNED by an explicit
#   promotion surviving two vetoes). The same three-part shape is used here:
#
#     DEFAULT      Every commit is BOOKKEEPING. Nothing is real by being seen.
#     ANCHOR       A commit is OFFERED for promotion only if at least one path it
#                  changes lies on the declared MIGRATION SURFACE — the places
#                  where an advance of the Fineract→Go migration is actually
#                  recorded (see NOFS_SURFACE_RE). This is an ALLOWLIST: a path
#                  nobody enumerated does NOT promote. Unknown paths therefore
#                  fail toward RED (escalate), never toward GREEN, and every one
#                  of them is printed as UNCLASSIFIED-PATH so the surface can be
#                  grown deliberately rather than discovered after an outage.
#     VETO 1       NULL PAYLOAD. The lines the commit ADDS to its surface paths
#                  are all blank or bare markers (`//`, `#`, `<!--`, `*/`, `}`).
#                  A change that adds no readable line advanced nothing.
#     VETO 2       REPEAT PAYLOAD, in two halves that answer different questions.
#                  (a) WHOLE PAYLOAD — T550's rule, kept: the added surface
#                  payload, normalised (case folded, whitespace collapsed,
#                  digit/hex runs → `#`), is one this producer has already put on
#                  the surface. `// heartbeat 1` and `// heartbeat 2` normalise
#                  to the same payload, so a beat that varies only in its numbers
#                  does not promote a second time.
#                  (b) PER LINE — added by T553: every substantive added line is
#                  normalised on its own (case folded, whitespace collapsed;
#                  digits DELIBERATELY KEPT, see norm_line) and a line whose form
#                  this producer has already put on the surface is SPENT. What
#                  survives is the NOVEL RESIDUE. If the residue is empty the
#                  commit does not promote.
#     VETO 3       THIN PAYLOAD. A promotion whose NOVEL RESIDUE carries fewer
#                  than NOFS_MIN_SUBST_LINES (default 8) lines does not clear a
#                  fire. This is a MATERIALITY floor, not a shape: it names no
#                  path and no wording, only a size, so it is not a blocklist of
#                  paddings already seen.
#
#   *** THE COMPOSITION RULE — T553, closing T552 MAJOR-1. Read this before
#   changing either veto. EACH VETO IS APPLIED TO THE RESIDUE THE PREVIOUS VETO
#   LEAVES, NEVER TO THE RAW PAYLOAD: VETO 1 leaves the substantive lines, VETO 2
#   leaves the novel ones, and VETO 3's floor is counted over THAT residue.
#   Before T553 the two vetoes were individually sound and did not compose —
#   VETO 2 hashed the WHOLE payload while VETO 3 counted a multiset that admitted
#   verbatim duplicates, so payload VETO 2 would have rejected wholesale still
#   counted toward the floor the moment ONE novel line was mixed in. T552 drove
#   it: seven verbatim-repeated lines plus one novel line held an eight-fire
#   no-op streak GREEN at exit 0, and the identical shape defeated a floor of 40.
#   RAISING THE FLOOR IS NOT THE REPAIR AND NEVER WAS — the padder's cost scales
#   in bytes of boilerplate, which cost nothing, not in novel content. Counting
#   the floor over the novel residue makes boilerplate worth exactly zero. ***
#
#                  THE FLOOR IS MEASURED, not chosen by taste, and it was
#                  RE-MEASURED under the novel-residue rule (T553): over the
#                  whole recorded history the thinnest promotion that ever
#                  cleared a fire carries 12 NOVEL substantive added surface
#                  lines (local, 89 fires, 36 cleared) and 27 (cloud, 5 fires,
#                  5 cleared) — the same two numbers T550 measured over the raw
#                  multiset, i.e. counting novelty instead of lines costs the
#                  real corpus nothing. A floor of 8 keeps a 1.5x margin under
#                  the observed minimum. Raising it tightens; lowering it
#                  loosens; a floor below 1 is REFUSED, because a floor of 0
#                  would promote a payload with no novel line at all.
#                  Re-measure with, in this directory,
#                  t550-materiality-floor.py (raw multiset, T550's method) and
#                  t553-sweep.py (novel residue + hourly false-RED replay)
#                  before changing it.
#
#   WHAT THIS CLOSES AND WHAT IT DOES NOT — read this before trusting it.
#   Git history is entirely under the producer's control, so NO test over git
#   metadata can make a promotion unforgeable, and this one does not claim to.
#   What changed is the COST of the forgery and the DEFAULT when the guard is
#   unsure. T541's attack — one valueless line per fire to any path outside the
#   bookkeeping set — no longer promotes at all: docs/*.md is not on the surface.
#   A heartbeat aimed INSIDE the surface promotes once and is vetoed thereafter.
#   Padding is worth zero: only the novel residue is counted.
#
#   THE RESIDUAL, MEASURED RATHER THAN CHARACTERISED. T550 stated its residual as
#   "the attack costs what the work costs"; T552 measured that claim FALSE at 16
#   bytes per fire, so this one is stated as a number and DRIVEN (transcripts in
#   .softhouse/handoff/T553-t552-conditions.md, rig t553-plant-attacks.sh):
#     * The cheapest promotion this guard admits is exactly NOFS_MIN_SUBST_LINES
#       lines that are new to this producer. Driven as `atk-mine-min`: 8 lines of
#       ONE character each — 8 bytes of content, 16 bytes with newlines, per fire
#       — holds an eight-fire no-op streak GREEN at exit 0.
#     * The RATE needed is lower still. Driven as `atk-mine-j`: the same
#       promotion on 2 of 8 fires is GREEN (AXIS 1 streak 2, AXIS 3 18.0 h). The
#       binding constraint is one promotion per `--streak` fires AND per
#       `--earned-silence-hours`, not one per fire.
#     * What the fix removed is the ability to pay in BOILERPLATE: `atk-mine-k`
#       (7 repeated + 1 novel) and `atk-mine-k40` (39 repeated + 1 novel) are now
#       RED exit 1 at every floor, where before they were GREEN at every floor.
#   So the honest statement of the boundary is: a producer that emits 8 lines of
#   never-before-used text per promotion still reads GREEN, and that is CHEAP —
#   it is not the cost of the work. The composing guard for content that is new
#   but worthless is .softhouse/bin/check-branch-published.py plus the
#   independent reviewer, not this one. See --explain to audit any single
#   verdict, including which lines were novel.
#
#   THE NOVELTY LEDGER SPANS THE WHOLE RECORDED HISTORY, NOT THE LOOKBACK WINDOW
#   (T552 MINOR-3). The window decides which FIRES are graded; it does not expire
#   a line. A line this producer put on the surface a month ago is still spent
#   today. That is the fail-closed direction, and it is what the shipped code
#   always did for repeats — the comment that promised otherwise was the thing
#   that was wrong, and it is gone. Cost of the strict reading, measured: ZERO
#   verdict changes over 482 hourly replays of the whole recorded history for
#   both producers (t553-sweep.py).
#
#   AXIS 2 DELIBERATELY KEEPS T493's OLD, FORGEABLE RULE, and that is safe
#   because AXIS 2 is MONOTONE: it can only ADD red. It answers the weaker
#   question "has this producer committed anything at all beyond its own
#   churn?", and a forged promotion can silence AXIS 2 but cannot silence AXIS 1
#   or AXIS 3, and the verdict is the OR of the three. Keeping it also preserves
#   every silence figure T493 published and T541 re-derived, so the two records
#   still compare line for line.
#
# SHALLOW CLONES — REFUSE, NEVER UNDER-REPORT
#   A cloud clone is SHALLOW. A --since window over a shallow clone silently
#   answers for the shallow part only: a 7-day and a 14-day window return the
#   same answer with no error, and the guard says "all clear" because it cannot
#   see the history. That is worse than no guard. This guard detects shallowness,
#   attempts `git fetch --unshallow`, and if it still cannot see far enough back
#   to cover its own lookback window it EXITS 2 (REFUSE) rather than 0 (GREEN).
#
# EXIT CODES
#   0  GREEN   — the producer is advancing; no axis tripped.
#   1  RED     — a no-op streak, a silence breach, and/or an earned-advance
#                breach. Escalate.
#   2  REFUSE  — cannot answer (shallow history, bad ref, no such producer,
#                unusable option value, no temp file, an analyser crash, or an
#                analyser status that is not itself a verdict).
#                REFUSE IS NOT GREEN. A caller that treats 2 as pass reintroduces
#                exactly the defect this guard exists for.
#
#   FAIL-CLOSED HAS NO HALF (T552 MAJOR-2). Exit 1 means ONE thing — a verdict
#   about the producer — so no failure of the guard itself may leak it. Before
#   T553 the analyser's crash paths all refused with 2 while the SHELL PROLOGUE
#   leaked 1: `--ref` with no value tripped `set -u` ($2: unbound variable) and an
#   unwritable TMPDIR made mktemp fail, and the call site logs exit 1 as
#   "**RED — THAT PRODUCER IS NOT ADVANCING THE MIGRATION**" — a guard failure
#   presenting as a migration outage. Every prologue path now refuses: each
#   option is checked for its value before `$2` is read, both mktemp calls and
#   the oldest-commit read refuse on failure, NOFS_PAYLOAD_CAP is validated
#   before it can silently redefine the classifier inside awk, and any analyser
#   status outside {0,1,2} is converted to REFUSE with the raw status printed.
#   There is NO bypass flag and no env var that turns any of this off (P-45).
#
# USAGE
#   .softhouse/guards/no-op-fire-streak.sh [--producer local|cloud|any]
#        [--ref REF] [--silence-hours H] [--earned-silence-hours H] [--streak N]
#        [--lookback-days D] [--min-subst-lines N] [--now ISO8601] [--explain SHA]
#        [--json] [--quiet] [--no-fetch]
#   Every option that takes a value REFUSES (exit 2) if the value is missing;
#   there is no flag that disables a veto, an axis or the refusal itself.

set -euo pipefail

PROG="$(basename "$0")"

# ---------------------------------------------------------------------------
# Defaults. Every one is overridable so the guard can be driven RED and GREEN
# against recorded history without editing it.
# ---------------------------------------------------------------------------
REF="${NOFS_REF:-origin/main}"
PRODUCER="${NOFS_PRODUCER:-local}"
SILENCE_HOURS="${NOFS_SILENCE_HOURS:-18}"
EARNED_SILENCE_HOURS="${NOFS_EARNED_SILENCE_HOURS:-36}"
STREAK="${NOFS_STREAK:-6}"
LOOKBACK_DAYS="${NOFS_LOOKBACK_DAYS:-14}"
NOW="${NOFS_NOW:-}"
EXPLAIN=""
JSON=0
QUIET=0
NO_FETCH="${NOFS_NO_FETCH:-0}"

# Producer identity is a MACHINE fact (the committer's UTC offset), not a word in
# a subject line. The local Mac fire commits at +08:00 (Asia/Ulaanbaatar, no DST
# — see CLAUDE.md); the cloud fire commits at +00:00. Overridable for a tenant
# whose local host sits in Asia/Hovd (+07).
LOCAL_OFFSET="${NOFS_LOCAL_OFFSET:-+08:00}"
CLOUD_OFFSET="${NOFS_CLOUD_OFFSET:-+00:00}"

# Scheduler self-churn. A commit confined to these paths advanced NOTHING: it is
# the wrapper taking the lock, reconciling its own banner, checkpointing its own
# state, or releasing the lock. Used by AXIS 2 ONLY, which is monotone (it can
# only add RED) — see the header. AXIS 1 and AXIS 3 do not consult it.
BOOKKEEPING_RE="${NOFS_BOOKKEEPING_RE:-^\.softhouse/(LOCK|RESUME\.md)$|^\.softhouse/(state|logs|runs)/}"

# THE MIGRATION SURFACE — the allowlist that anchors a promotion to REAL.
# These are the places where an advance of the Fineract→Go migration is actually
# recorded, and nothing else promotes:
#   nexus/                     the Go module being built — the product itself
#   .softhouse/capture/        captured oracle output and drive transcripts
#   .softhouse/vectors/        golden vectors
#   .softhouse/handoff/        worker deliverables
#   .softhouse/reviews/        independent review deliverables
#   .softhouse/guards/         the enforcement machinery
#   .softhouse/bin/            the pipeline machinery
#   .claude/                   the pipeline's own skills
#   docs/adr/                  ratified DEC-n contract records
# DELIBERATELY ABSENT, and this is the point of an allowlist: .softhouse/LOCK,
# RESUME.md, tasks.json, program.json, patterns.md, gates.md, observations/,
# docs/** other than adr/, and every path nobody has enumerated. An unenumerated
# path does not promote, is reported as UNCLASSIFIED-PATH, and therefore fails
# toward escalation. Growing this set is a deliberate act with a diff.
SURFACE_RE="${NOFS_SURFACE_RE:-^nexus/|^\.softhouse/(capture|vectors|handoff|reviews|guards|bin)/|^\.claude/|^docs/adr/}"

# Per-commit cap on added lines read for the payload vetoes. A commit whose first
# N added surface lines are all null but whose 200th line is substantive is
# judged NULL PAYLOAD and does not promote — conservative in the escalating
# direction, and stated here rather than discovered later.
PAYLOAD_CAP="${NOFS_PAYLOAD_CAP:-200}"

# VETO 3 materiality floor: substantive added surface lines a promotion must
# carry to clear a fire. Measured, not chosen by taste — see the header. The
# thinnest promotion that ever cleared a fire in the recorded history carries 12.
MIN_SUBST_LINES="${NOFS_MIN_SUBST_LINES:-8}"

# Print the whole header block (every line from line 2 up to the last comment
# line before `set -euo pipefail`), not a hard-coded line range that silently
# truncates as the header grows.
usage() { awk 'NR>1 && /^#/ {sub(/^# ?/,""); print; next} NR>1 && !/^#/ {exit}' "$0"; }

# say/refuse are defined BEFORE the option parser because the parser itself must
# be able to REFUSE. T552 MAJOR-2: `--ref` with no value left `$2` unset, `set -u`
# aborted the script with exit 1, and the call site logs exit 1 as
# "**RED — THAT PRODUCER IS NOT ADVANCING THE MIGRATION**". A guard FAILURE
# presenting as a FINDING is the exact defect the analyser's excepthook closed one
# layer up; the shell prologue must not have the other half of it.
say() { [ "$QUIET" = 1 ] || printf '%s\n' "$*"; }
refuse() {
  # REFUSE is deliberately loud and deliberately NOT exit 0, and NOT exit 1.
  printf 'no-op-fire-streak: REFUSE — %s\n' "$*" >&2
  printf 'no-op-fire-streak: REFUSE IS NOT GREEN. No verdict was reached.\n' >&2
  exit 2
}
# Every option below takes a value. `need_val <flag> <argc>` refuses when the
# value is missing, so no `$2` is ever read unset.
need_val() { [ "$2" -ge 2 ] || refuse "$1 requires a value (none was given)"; }

while [ $# -gt 0 ]; do
  case "$1" in
    --producer)       need_val "$1" $#; PRODUCER="$2"; shift 2 ;;
    --ref)            need_val "$1" $#; REF="$2"; shift 2 ;;
    --silence-hours)  need_val "$1" $#; SILENCE_HOURS="$2"; shift 2 ;;
    --earned-silence-hours) need_val "$1" $#; EARNED_SILENCE_HOURS="$2"; shift 2 ;;
    --streak)         need_val "$1" $#; STREAK="$2"; shift 2 ;;
    --lookback-days)  need_val "$1" $#; LOOKBACK_DAYS="$2"; shift 2 ;;
    --min-subst-lines) need_val "$1" $#; MIN_SUBST_LINES="$2"; shift 2 ;;
    --now)            need_val "$1" $#; NOW="$2"; shift 2 ;;
    --explain)        need_val "$1" $#; EXPLAIN="$2"; shift 2 ;;
    --json)           JSON=1; shift ;;
    --quiet)          QUIET=1; shift ;;
    --no-fetch)       NO_FETCH=1; shift ;;
    -h|--help)        usage; exit 0 ;;
    *) refuse "unknown argument: $1" ;;
  esac
done

# T552 MINOR-5: NOFS_PAYLOAD_CAP reaches awk raw, and an empty or non-numeric
# value silently redefines the classifier — `''` makes awk's `n < cap` a string
# comparison that drops EVERY payload line (nothing can ever earn), `'abc'`
# disables the cap. Both fail toward escalation rather than toward GREEN, but a
# value the guard cannot classify must REFUSE, not be guessed at.
case "$PAYLOAD_CAP" in
  ''|*[!0-9]*) refuse "NOFS_PAYLOAD_CAP must be a positive integer; got '$PAYLOAD_CAP'" ;;
esac
[ "$PAYLOAD_CAP" -ge 1 ] || refuse "NOFS_PAYLOAD_CAP must be at least 1; got '$PAYLOAD_CAP'"

case "$PRODUCER" in
  local) WANT_OFFSET="$LOCAL_OFFSET" ;;
  cloud) WANT_OFFSET="$CLOUD_OFFSET" ;;
  any)   WANT_OFFSET="" ;;
  *) refuse "unknown producer '$PRODUCER' (expected local|cloud|any)" ;;
esac

command -v git  >/dev/null 2>&1 || refuse "git not on PATH"
command -v python3 >/dev/null 2>&1 || refuse "python3 not on PATH"
command -v awk >/dev/null 2>&1 || refuse "awk not on PATH"
git rev-parse --git-dir >/dev/null 2>&1 || refuse "not inside a git repository"

# ---------------------------------------------------------------------------
# STEP 0 — SHALLOW REFUSAL, BEFORE ANY MEASUREMENT.
#
# This block is the whole reason the guard can be trusted in a cloud clone. A
# shallow repository answers a --since query for the shallow part ONLY, with no
# error and no warning, so the guard would report "all clear" on an outage it
# simply cannot see.
# ---------------------------------------------------------------------------
shallow_now() {
  # Two independent signals: git's own predicate, and the shallow file itself.
  # Either one is enough to distrust the history.
  if [ "$(git rev-parse --is-shallow-repository 2>/dev/null || echo true)" = "true" ]; then return 0; fi
  local gd; gd="$(git rev-parse --git-common-dir 2>/dev/null || echo .git)"
  [ -s "$gd/shallow" ] && return 0
  return 1
}

UNSHALLOW_NOTE="repository was already complete"
if shallow_now; then
  if [ "$NO_FETCH" = 1 ]; then
    refuse "history is SHALLOW and --no-fetch was given; a --since window over a shallow clone answers for the shallow part only"
  fi
  say "no-op-fire-streak: history is SHALLOW — attempting 'git fetch --unshallow' before measuring"
  if git fetch --unshallow --quiet >/dev/null 2>&1; then
    UNSHALLOW_NOTE="unshallowed by this guard via 'git fetch --unshallow'"
  else
    # A repo that is not shallow-cloneable this way (e.g. a partial clone, or the
    # network is gone) must not be measured.
    git fetch --depth=2147483647 --quiet >/dev/null 2>&1 || true
    UNSHALLOW_NOTE="attempted unshallow"
  fi
  if shallow_now; then
    refuse "history is STILL SHALLOW after 'git fetch --unshallow'; refusing to answer for a window this clone cannot see"
  fi
fi

git rev-parse --verify --quiet "$REF" >/dev/null || refuse "ref '$REF' does not exist in this clone (looked with: git rev-parse --verify $REF)"

# ---------------------------------------------------------------------------
# STEP 1 — two passes over the history, then all analysis in python3.
#
# --no-merges: a merge commit reports no paths under --name-only, which would
# make every merge look like bookkeeping. The content a merge brings in is
# already present as the branch commits git log linearises alongside it, so
# excluding merges loses no real work and invents no fake bookkeeping.
# ---------------------------------------------------------------------------
# PASS 1 — --numstat (not --name-only) because AXIS 1 needs the DIFF DIRECTION on
# .softhouse/LOCK to tell a lock TAKE (inserts the lock body) from a lock RELEASE
# (deletes it) without reading the words "take" or "release" from the subject.
# T552 MAJOR-2: an unwritable or full TMPDIR made `mktemp` fail and `set -e`
# aborted with exit 1 — a migration-outage alarm raised by the guard's own
# inability to run. Both temp files REFUSE instead, and the trap is armed before
# either assignment so a refusal between them still cleans up.
RAW=""; PAY=""
trap 'rm -f -- "$RAW" "$PAY" 2>/dev/null || true' EXIT
RAW="$(mktemp)" || refuse "could not create a temporary file for the history pass (mktemp failed; TMPDIR=${TMPDIR:-/tmp}). This is a GUARD FAILURE, not a finding about the producer."
PAY="$(mktemp)" || refuse "could not create a temporary file for the payload pass (mktemp failed; TMPDIR=${TMPDIR:-/tmp}). This is a GUARD FAILURE, not a finding about the producer."
git log "$REF" --no-merges --numstat --format='@@%H|%cI' > "$RAW" 2>/dev/null \
  || refuse "could not read history of '$REF'"
[ -s "$RAW" ] || refuse "history of '$REF' is empty"

# PASS 2 — the ADDED LINES, for the two payload vetoes. `-U0` drops context lines
# so every '+' line is genuinely an addition. The awk filter keeps the commit
# marker, the file headers and at most PAYLOAD_CAP added lines per commit, which
# takes ~4.3M lines of raw diff down to ~300k. The commit marker is @COMMIT@ and
# NOT `@@`, because `-U0` hunk headers themselves start with `@@`.
# awk consumes the whole stream, so no SIGPIPE can reach git under `pipefail`.
git log "$REF" --no-merges -p -U0 --no-color --format='@COMMIT@%H' 2>/dev/null \
  | awk -v cap="$PAYLOAD_CAP" '
      /^@COMMIT@/    { n = 0; print; next }
      /^\+\+\+ /     { print; next }
      /^\+/          { if (n < cap) { print; n++ } next }
    ' > "$PAY" || refuse "could not read the diff payload of '$REF'"

# NOTE: `git log --reverse | head -1` raises SIGPIPE under `set -o pipefail` and
# would abort the guard with exit 141 — which a caller could easily mistake for a
# verdict. Take the last line of the forward log instead; no pipe is closed early.
OLDEST_ISO="$(git log "$REF" --format='%cI' | tail -1)" \
  || refuse "could not read the oldest commit date of '$REF' (git log failed). GUARD FAILURE, not a finding."
[ -n "$OLDEST_ISO" ] || refuse "the oldest commit date of '$REF' came back empty. GUARD FAILURE, not a finding."

# The analyser's status is the guard's verdict, and ONLY 0/1/2 are verdicts.
# `set -e` would otherwise abort here with whatever the interpreter returned —
# 137 from an OOM kill, 139 from a segfault — and a caller pattern-matching on
# "not 0" would read a dead analyser as a producer finding. Anything outside
# {0,1,2} becomes REFUSE, with the raw status printed so nothing is hidden.
ANALYSER_RC=0
if NOFS_RAW="$RAW" NOFS_PAY="$PAY" \
NOFS_A_REF="$REF" NOFS_A_PRODUCER="$PRODUCER" NOFS_A_OFFSET="$WANT_OFFSET" \
NOFS_A_SILENCE="$SILENCE_HOURS" NOFS_A_EARNED_SILENCE="$EARNED_SILENCE_HOURS" \
NOFS_A_STREAK="$STREAK" \
NOFS_A_LOOKBACK="$LOOKBACK_DAYS" NOFS_A_NOW="$NOW" NOFS_A_EXPLAIN="$EXPLAIN" \
NOFS_A_JSON="$JSON" NOFS_A_QUIET="$QUIET" NOFS_A_BOOKRE="$BOOKKEEPING_RE" \
NOFS_A_SURFRE="$SURFACE_RE" NOFS_A_MINSUBST="$MIN_SUBST_LINES" \
NOFS_A_OLDEST="$OLDEST_ISO" NOFS_A_UNSHALLOW="$UNSHALLOW_NOTE" \
python3 <<'PY'
import os, re, sys, json, datetime, hashlib, collections

# An unhandled exception must REFUSE (exit 2), never leak python's own exit 1 —
# which the caller would read as a RED verdict this guard never reached. A crash
# is "no verdict", and the caller's exit-2 branch already says so out loud.
def _crash(kind, exc, tb):
    import traceback
    print("no-op-fire-streak: REFUSE — the analyser raised %s: %s" % (kind.__name__, exc),
          file=sys.stderr)
    traceback.print_exception(kind, exc, tb, file=sys.stderr)
    print("no-op-fire-streak: REFUSE IS NOT GREEN. No verdict was reached.", file=sys.stderr)
    sys.exit(2)
sys.excepthook = _crash

raw       = os.environ['NOFS_RAW']
pay       = os.environ['NOFS_PAY']
ref       = os.environ['NOFS_A_REF']
producer  = os.environ['NOFS_A_PRODUCER']
offset    = os.environ['NOFS_A_OFFSET']
silence_h = float(os.environ['NOFS_A_SILENCE'])            # HOURS, not money
earned_h  = float(os.environ['NOFS_A_EARNED_SILENCE'])     # HOURS, not money
streak_n  = int(os.environ['NOFS_A_STREAK'])
lookback  = float(os.environ['NOFS_A_LOOKBACK'])           # DAYS, not money
now_s     = os.environ['NOFS_A_NOW'].strip()
explain   = os.environ['NOFS_A_EXPLAIN'].strip()
as_json   = os.environ['NOFS_A_JSON'] == '1'
quiet     = os.environ['NOFS_A_QUIET'] == '1'
book_re   = re.compile(os.environ['NOFS_A_BOOKRE'])
surf_re   = re.compile(os.environ['NOFS_A_SURFRE'])
min_subst = int(os.environ['NOFS_A_MINSUBST'])
oldest_s  = os.environ['NOFS_A_OLDEST'].strip()
unshallow = os.environ['NOFS_A_UNSHALLOW']

UTC = datetime.timezone.utc
def out(*a):
    if not quiet: print(*a)


# --- parse pass 1: footprint ------------------------------------------------
commits = []
cur = None
with open(raw, encoding='utf-8', errors='replace') as fh:
    for line in fh:
        line = line.rstrip('\n')
        if line.startswith('@@'):
            if cur: commits.append(cur)
            sha, ts = line[2:].split('|', 1)
            cur = {'sha': sha, 'ts': ts, 'files': [], 'stat': []}
        elif line.strip() and cur is not None:
            # numstat: "<insertions>\t<deletions>\t<path>"; '-' for binary.
            parts = line.split('\t')
            if len(parts) >= 3:
                ins = 0 if parts[0] == '-' else int(parts[0])
                dele = 0 if parts[1] == '-' else int(parts[1])
                cur['files'].append(parts[2])
                cur['stat'].append((parts[2], ins, dele))
            else:
                cur['files'].append(line)
if cur: commits.append(cur)
commits.reverse()                      # oldest -> newest

# --- parse pass 2: added lines, restricted to the migration surface ----------
# The SAME surface regex decides both the anchor and which added lines are read,
# so there is one source of truth for "on the surface" and it is printable.
payload = collections.defaultdict(list)
sha = None
on_surface = False
with open(pay, encoding='utf-8', errors='replace') as fh:
    for line in fh:
        line = line.rstrip('\n')
        if line.startswith('@COMMIT@'):
            sha = line[8:].strip()
            on_surface = False
        elif line.startswith('+++ '):
            p = line[4:].strip()
            if p.startswith('b/'):
                p = p[2:]
            on_surface = (p != '/dev/null') and bool(surf_re.search(p))
        elif on_surface and sha and line.startswith('+'):
            payload[sha].append(line[1:])

# A "null" added line: blank, or nothing but comment/markup/brace decoration.
NULL_LINE = re.compile(r'^[\s{}()\[\];,.:*=_~`>|+-]*(//+|\#+|--+|<!--|-->|/\*+|\*+/|\*+)?'
                       r'[\s{}()\[\];,.:*=_~`>|+-]*$')
DIGIT_RUN = re.compile(r'[0-9a-f]{4,}|[0-9]+', re.I)
WS_RUN    = re.compile(r'\s+')

if min_subst < 1:
    print("no-op-fire-streak: REFUSE — --min-subst-lines must be at least 1; "
          f"got {min_subst}. A floor of 0 would let a payload with NO novel line "
          "promote, which is the defect T553 closed. REFUSE IS NOT GREEN.",
          file=sys.stderr)
    sys.exit(2)

def substantive(lines):
    return [l for l in lines if not NULL_LINE.match(l)]

# T550's normalisation, used for the WHOLE-PAYLOAD repeat test, is
# `DIGIT_RUN.sub('#', norm_line(l))` — case folded, whitespace collapsed, digit
# and hex runs replaced by '#'. `// heartbeat 1` and `// heartbeat 2` collapse to
# the same form, so a payload that varies only in its numbers is the same
# payload. Content is never matched against a word list — only against what this
# same producer has already put on the surface. It is computed in line_forms().

def norm_line(l):
    """The PER-LINE normalisation: case folded and whitespace collapsed, and
    DELIBERATELY NOT digit-collapsed.

    T553 drove the digit-collapsed version first and it produced a FALSE RED on
    the negative control: twelve rows of a captured numeric table differ only in
    their numbers, so the digit-collapsed form maps all twelve to ONE line and a genuinely
    productive 12-line capture reads as 1 novel line and fails the floor. A
    captured vector table is the most ordinary shape on this migration surface,
    so that normalisation cannot be the novelty test.

    Keeping the digits costs nothing against a padder: the cheapest known padding
    (T552's `atk-mine-i`, eight two-character lines) never needed a digit to
    defeat the floor, so collapsing digits removes no attack while removing real
    work. The whole-payload digit-collapsed test above still catches a payload
    repeated with only its numbers changed."""
    return WS_RUN.sub(' ', l.strip().lower())

def line_key(nl):
    # 8 bytes is ~2e-9 collision probability over the ~300k payload lines this
    # repository carries, and a collision can only make a line look ALREADY SEEN
    # — i.e. it fails toward escalation, never toward GREEN.
    return hashlib.blake2b(nl.encode('utf-8', 'replace'), digest_size=8).digest()

def line_forms(lines):
    """Both normalised forms of every line, in ONE pass: the digit-preserving
    per-line form (novelty) and the digit-collapsed shape (whole payload). The
    shape is derived FROM the per-line form so `.lower()` and the whitespace
    collapse are not paid twice — this is the whole of the cost difference the
    novelty test adds on a 2,600-commit history."""
    keys, shapes = [], []
    for l in lines:
        nl = norm_line(l)
        keys.append(line_key(nl))
        shapes.append(DIGIT_RUN.sub('#', nl))
    return keys, shapes

def digest_of(shapes):
    """Whole-payload digest over T550's digit-collapsed normalisation."""
    return hashlib.sha256('\n'.join(shapes).encode('utf-8', 'replace')).hexdigest()[:16]

for c in commits:
    c['dt']      = datetime.datetime.fromisoformat(c['ts'])
    c['off']     = c['ts'][-6:]
    # AXIS 2's old, deliberately-monotone rule (see header). It can only add RED.
    c['carry']   = [f for f in c['files'] if not book_re.search(f)]
    c['carrying'] = bool(c['carry'])
    # THE PROMOTION. Subject text is never consulted. Default is BOOKKEEPING;
    # REAL must be EARNED by a surface anchor surviving all three vetoes.
    c['anchor']  = [f for f in c['files'] if surf_re.search(f)]
    c['offsurf'] = [f for f in c['carry'] if not surf_re.search(f)]
    c['subst']   = substantive(payload.get(c['sha'], []))
    c['novel']   = []
    c['digest']  = None
    c['earned']  = False
    if not c['anchor']:
        c['why'] = 'NO ANCHOR — no changed path is on the migration surface'
    elif not c['subst']:
        c['why'] = 'VETO 1 NULL PAYLOAD — the surface paths gained no readable line'
    else:
        # VETO 2 and VETO 3 are BOTH decided in the ordered pass below, because
        # novelty is a property of what came BEFORE this commit. Deciding VETO 3
        # here — over the raw multiset, before VETO 2 has removed the repeats —
        # is exactly the composition defect T552 drove (MAJOR-1).
        c['why'] = None

def mine(c):
    return (offset == '' or c['off'] == offset)

now = datetime.datetime.fromisoformat(now_s) if now_s else datetime.datetime.now(UTC)
if now.tzinfo is None: now = now.replace(tzinfo=UTC)

# --now is an AS-OF replay, not just a clock relabel. Without this filter the
# guard reads commits that had not happened yet at the replayed instant, which
# silently inverts every historical verdict: replaying 2026-08-27 would grade
# fires from 2026-09-02 and report a NEGATIVE silence. Driving a detector RED
# against recorded history is worthless if the replay can see the future.
n_all = len(commits)
commits = [c for c in commits if c['dt'] <= now]
n_filtered = n_all - len(commits)
if not commits:
    print(f"no-op-fire-streak: REFUSE — no commits at or before --now {now.astimezone(UTC):%Y-%m-%dT%H:%M:%SZ} "
          f"in {ref} (history begins {oldest_s})", file=sys.stderr)
    sys.exit(2)

# --- VETO 2 then VETO 3, COMPOSED, applied in time order, per producer -------
# THE COMPOSITION RULE (T553, closing T552 MAJOR-1):
#   each veto is applied to the RESIDUE the previous veto leaves, never to the
#   raw payload — VETO 1 leaves the SUBSTANTIVE lines, VETO 2 leaves the NOVEL
#   ones, and VETO 3's materiality floor is counted over that novel residue.
#
# Before T553, VETO 2 hashed the WHOLE payload and VETO 3 counted the WHOLE
# substantive multiset, so a payload VETO 2 would have rejected wholesale still
# counted toward VETO 3's floor as soon as one novel line was mixed in: seven
# verbatim-repeated lines + one novel line cleared a floor of 8 and defeated the
# digest at the same time, and the same shape defeated a floor of 40. Counting
# the floor over the novel residue makes the padding worthless, because padding
# is by construction not novel — and it does it WITHOUT naming a path, a wording
# or a list of shapes already seen (B-11 / P-104).
#
# A line is NOVEL for this producer if its normalised form has not appeared in
# this producer's own substantive surface payload EARLIER in this history, and
# has not already been counted inside this same commit. Novelty is recorded for
# every anchored commit that carried substantive payload, whether or not that
# commit promoted: a line this producer has already put on the surface is spent,
# and re-mixing it later must not buy a second promotion.
window_start = now - datetime.timedelta(days=lookback)
seen_payload = {}               # (offset, payload digest) -> sha that first used it
seen_lines   = {}               # (offset, line_key)       -> sha that first used it
for c in commits:               # oldest -> newest
    if c['why'] is not None:
        continue
    keys, shapes = line_forms(c['subst'])
    c['digest'] = digest_of(shapes)
    novel, here = [], set()
    for l, k in zip(c['subst'], keys):
        if (c['off'], k) in seen_lines or k in here:
            continue            # already spent by this producer, or by this commit
        here.add(k)
        novel.append(l)
    first_payload = seen_payload.get((c['off'], c['digest']))
    # Spend the payload and every line in it, promoted or not: content this
    # producer has already put on the surface must not buy a second promotion by
    # being re-mixed later.
    seen_payload.setdefault((c['off'], c['digest']), c['sha'])
    for k in keys:
        seen_lines.setdefault((c['off'], k), c['sha'])
    c['novel'] = novel
    if first_payload is not None:
        # VETO 2a — T550's rule, kept verbatim in effect: the WHOLE payload,
        # digit-collapsed, is one this producer has already put on the surface.
        c['why'] = (f'VETO 2 REPEAT PAYLOAD — normalised payload {c["digest"]} already '
                    f'used at {first_payload[:8]} by this producer')
    elif not novel:
        # VETO 2b — nothing in it is new, line by line.
        first = seen_lines.get((c['off'], keys[0]), '?' * 8)
        c['why'] = (f'VETO 2 REPEAT LINES — all {len(c["subst"])} substantive added '
                    f'surface line(s) were already on this producer\'s surface '
                    f'(the first of them at {first[:8]}); nothing here is new')
    elif len(novel) < min_subst:
        # VETO 3 — the floor, counted over the residue VETO 2 leaves.
        c['why'] = (f'VETO 3 THIN PAYLOAD — {len(novel)} NOVEL substantive added surface '
                    f'line(s) of {len(c["subst"])} (the other {len(c["subst"]) - len(novel)} '
                    f'were already on this producer\'s surface), floor is {min_subst}')
    else:
        c['earned'] = True

# --- --explain: audit one verdict ------------------------------------------
if explain:
    hit = [c for c in commits if c['sha'].startswith(explain)]
    if not hit:
        # MINOR-4 (T541): this search set is AS-OF --now, and saying "the full
        # history" here tells an operator a commit is absent when it is merely
        # later. Both counts are printed so the difference is visible.
        asof = (f" as of --now {now.astimezone(UTC):%Y-%m-%dT%H:%M:%SZ}" if now_s else "")
        print(f"no-op-fire-streak: REFUSE — no commit matching '{explain}' in {ref}{asof} "
              f"(looked in {len(commits)} of {n_all} --no-merges commits; "
              f"{n_filtered} later commit(s) were excluded by --now; oldest {oldest_s}); "
              f"note merges are excluded by design. 'Not found' here is a statement "
              f"about the search, not about the world.", file=sys.stderr)
        sys.exit(2)
    c = hit[0]
    print(f"commit    {c['sha']}")
    print(f"committed {c['dt'].astimezone(UTC):%Y-%m-%dT%H:%M:%SZ}  offset {c['off']}  "
          f"producer={'local' if c['off']=='+08:00' else 'cloud' if c['off']=='+00:00' else 'other'}")
    print(f"verdict   {'REAL (earned)' if c['earned'] else 'BOOKKEEPING'}   "
          f"(decided from {len(c['files'])} changed path(s) and "
          f"{len(payload.get(c['sha'], []))} added surface line(s); subject text NOT consulted)")
    if not c['earned']:
        print(f"reason    {c['why']}")
    else:
        print(f"reason    ANCHOR on the migration surface + novel payload {c['digest']} "
              f"({len(c['novel'])} NOVEL of {len(c['subst'])} substantive added line(s), "
              f"floor {min_subst}), all three vetoes survived")
    if c['subst']:
        print(f"payload   {len(c['subst'])} substantive added surface line(s), "
              f"{len(c['novel'])} of them novel for this producer "
              f"(VETO 3 counts the NOVEL residue, not the raw multiset)")
    for f in c['files']:
        if surf_re.search(f):
            tag = 'SURFACE   '
        elif book_re.search(f):
            tag = 'self-churn'
        else:
            tag = 'off-surface'
        print(f"    {tag}  {f}")
    print(f"    AXIS 2 carry rule (monotone, can only add RED): "
          f"{'carries' if c['carrying'] else 'self-churn only'}")
    sys.exit(0)

# --- window / coverage ------------------------------------------------------
oldest = datetime.datetime.fromisoformat(oldest_s) if oldest_s else None
# MINOR-5 (T541): the earlier comment here promised a refusal this code cannot
# produce. It does not refuse, and that is CORRECT — a young repository whose
# root is inside the lookback window is not blind, it is young, and genuine
# blindness (a shallow clone) is already refused at STEP 0. `truncated` is a
# REPORT flag only, and the dead `root_held` constant is gone.
truncated = oldest is not None and oldest > window_start

pool   = [c for c in commits if mine(c)]
inwin  = [c for c in pool if c['dt'] >= window_start]
reals  = [c for c in pool if c['earned']]
carrys = [c for c in pool if c['carrying']]

if not pool:
    print(f"no-op-fire-streak: REFUSE — no commits at all from producer '{producer}' "
          f"(offset {offset or 'any'}) in {ref} "
          f"(looked at all {len(commits)} non-merge commits, {oldest_s} .. now). "
          f"'Not found' here is a statement about the search: either the producer never "
          f"committed, or its committer offset differs from {offset!r} — set NOFS_LOCAL_OFFSET.",
          file=sys.stderr)
    sys.exit(2)

# --- AXIS 1 — no-op fire streak --------------------------------------------
# A fire is reconstructed from the lock-take commit. Take vs release is decided
# by DIFF DIRECTION on .softhouse/LOCK (a take inserts the lock body, a release
# deletes it), never by the words "take" or "release" — same anti-reword
# discipline as the classifier.
LOCK_PATH = '.softhouse/LOCK'
def lock_event(c):
    """Return 'take', 'release' or None — decided by diff direction, not words.

    A fire TAKES the lock by writing the lock body into an absent file (pure
    insertion) and RELEASES it by deleting that body (pure deletion). Counting
    both as fires double-counts every fire, which is why this split exists.
    A lock file that is rewritten in place (insertions AND deletions) is treated
    as a take: some other agent re-claimed a lock that was already held.
    """
    if not c['stat'] or any(p != LOCK_PATH for p, _, _ in c['stat']):
        return None
    ins = sum(i for _, i, _ in c['stat'])
    dele = sum(d for _, _, d in c['stat'])
    if ins > 0 and dele == 0: return 'take'
    if dele > 0 and ins == 0: return 'release'
    return 'take' if ins else None

fires = [c for c in pool if lock_event(c) == 'take']
fires.sort(key=lambda c: c['dt'])

# Pair each lock event with the next one; a fire's window runs from its lock
# event to the next lock event (or to now for the newest).
fire_windows = []
for i, c in enumerate(fires):
    end = fires[i+1]['dt'] if i+1 < len(fires) else now
    fire_windows.append((c, end))

# Only fires whose window is inside the lookback window are graded.
graded = [(c, end) for (c, end) in fire_windows if c['dt'] >= window_start]

def real_in(a, b):
    # EARNED work only. This is the line T541 walked through: it used to be any
    # commit outside the bookkeeping blocklist, so one appended line to any
    # unlisted path cleared a fire.
    return [c for c in reals if a <= c['dt'] < b]

streak = 0
streak_detail = []
for (c, end) in reversed(graded):
    r = real_in(c['dt'], end)
    if r:
        break
    streak += 1
    streak_detail.append((c, end))
streak_detail.reverse()

axis1_red = streak >= streak_n

# --- AXIS 2 — silence (monotone; T493's original rule, deliberately kept) ----
last_carry = carrys[-1] if carrys else None
silence = (now - last_carry['dt']).total_seconds() / 3600.0 if last_carry else None
axis2_red = (last_carry is None) or (silence > silence_h)

# --- AXIS 3 — padded advance (T550) -----------------------------------------
# Hours since the last EARNED promotion. This is the axis a padding campaign
# cannot silence, and it is the one that catches a padder that never takes the
# lock (so AXIS 1 has no fires to grade) while committing continuously (so
# AXIS 2's clock never runs).
last_real = reals[-1] if reals else None
earned_silence = (now - last_real['dt']).total_seconds() / 3600.0 if last_real else None
axis3_red = (last_real is None) or (earned_silence > earned_h)

red = axis1_red or axis2_red or axis3_red

# --- report -----------------------------------------------------------------
book_in_win = len([c for c in inwin if not c['earned']])
real_in_win = len([c for c in inwin if c['earned']])
veto1 = len([c for c in inwin if c['anchor'] and not c['subst']])
veto3 = len([c for c in inwin if c['why'] and c['why'].startswith('VETO 3')])
veto2 = len([c for c in inwin if c['why'] and c['why'].startswith('VETO 2')])
offsurf = collections.Counter()
for c in inwin:
    if not c['anchor']:
        for f in c['offsurf']:
            offsurf[f] += 1

if as_json:
    print(json.dumps({
        'ref': ref, 'producer': producer, 'offset': offset or 'any',
        'now': now.astimezone(UTC).isoformat(),
        'history_oldest': oldest_s, 'unshallow': unshallow,
        'lookback_days': lookback, 'window_truncated': truncated,
        'commits_total': len(commits), 'commits_excluded_by_now': n_filtered,
        'commits_producer': len(pool),
        'surface_re': surf_re.pattern, 'bookkeeping_re': book_re.pattern,
        'in_window_earned_real': real_in_win, 'in_window_bookkeeping': book_in_win,
        'in_window_veto1_null_payload': veto1, 'in_window_veto2_repeat_payload': veto2,
        'in_window_veto3_thin_payload': veto3, 'min_novel_substantive_lines': min_subst,
        'veto3_counts': 'novel residue (lines surviving VETO 2), not the raw multiset',
        'last_earned_novel_lines': len(last_real['novel']) if last_real else None,
        'last_earned_substantive_lines': len(last_real['subst']) if last_real else None,
        'in_window_unclassified_paths': len(offsurf),
        'fires_graded': len(graded), 'noop_streak': streak, 'streak_threshold': streak_n,
        'axis1_noop_streak_red': axis1_red,
        'last_carry_commit': last_carry['sha'] if last_carry else None,
        'silence_hours': round(silence, 2) if silence is not None else None,
        'silence_threshold_hours': silence_h,
        'axis2_silence_red': axis2_red,
        'last_earned_commit': last_real['sha'] if last_real else None,
        'last_earned_at': last_real['dt'].astimezone(UTC).isoformat() if last_real else None,
        'last_earned_paths': last_real['anchor'][:8] if last_real else None,
        'earned_silence_hours': round(earned_silence, 2) if earned_silence is not None else None,
        'earned_silence_threshold_hours': earned_h,
        'axis3_padded_advance_red': axis3_red,
        'verdict': 'RED' if red else 'GREEN',
    }, indent=2))
else:
    out(f"no-op-fire-streak — ref={ref} producer={producer} (committer offset {offset or 'any'})")
    out(f"  history      : {len(commits)} non-merge commits at or before --now"
        + (f" ({n_filtered} later commit(s) excluded)" if n_filtered else "")
        + f", oldest {oldest_s}; {unshallow}")
    out(f"  surface      : REAL is EARNED by a path matching {surf_re.pattern}")
    out(f"  self-churn   : AXIS 2 only — paths matching {book_re.pattern}")
    out(f"  now          : {now.astimezone(UTC):%Y-%m-%dT%H:%M:%SZ}"
        + ("  [--now override]" if now_s else ""))
    out(f"  window       : last {lookback:g} day(s), from {window_start.astimezone(UTC):%Y-%m-%dT%H:%M:%SZ}"
        + ("   *** TRUNCATED: history begins inside the window ***" if truncated else ""))
    out(f"  in window    : {real_in_win} earned-real, {book_in_win} bookkeeping, "
        f"{len(graded)} fire(s) graded")
    out(f"  vetoed       : {veto1} null-payload, {veto2} repeat-payload, "
        f"{veto3} thin-payload (<{min_subst} NOVEL substantive lines; the floor is "
        f"counted over the novel residue, never the raw multiset) "
        f"— anchored commits that did NOT promote")
    if offsurf:
        top = ', '.join(f"{p} x{n}" for p, n in offsurf.most_common(5))
        out(f"  UNCLASSIFIED-PATH: {len(offsurf)} path(s) carried work in window but are not on "
            f"the surface, so they never promote: {top}"
            + (" ..." if len(offsurf) > 5 else ""))
    out("")
    out(f"  AXIS 1 no-op streak : {streak} consecutive no-op fire(s) (threshold {streak_n}) -> "
        + ("RED" if axis1_red else "ok"))
    for (c, end) in streak_detail[:12]:
        out(f"      no-op fire  {c['sha'][:8]}  {c['dt'].astimezone(UTC):%Y-%m-%dT%H:%MZ} .. {end.astimezone(UTC):%H:%MZ}")
    if len(streak_detail) > 12:
        out(f"      ... and {len(streak_detail)-12} more")
    if last_carry:
        out(f"  AXIS 2 silence      : {silence:.1f}h since last commit carrying anything "
            f"{last_carry['sha'][:8]} at {last_carry['dt'].astimezone(UTC):%Y-%m-%dT%H:%MZ} "
            f"(threshold {silence_h:g}h) -> " + ("RED" if axis2_red else "ok"))
    else:
        out(f"  AXIS 2 silence      : producer has NO carrying commit in all of history -> RED")
    if last_real:
        out(f"  AXIS 3 padded adv.  : {earned_silence:.1f}h since last EARNED commit "
            f"{last_real['sha'][:8]} at {last_real['dt'].astimezone(UTC):%Y-%m-%dT%H:%MZ} "
            f"(threshold {earned_h:g}h) -> " + ("RED" if axis3_red else "ok"))
        out(f"      earned by   : {', '.join(last_real['anchor'][:4])}"
            + (" ..." if len(last_real['anchor']) > 4 else ""))
    else:
        out(f"  AXIS 3 padded adv.  : producer has NEVER earned a REAL commit -> RED")
    out("")
    out(f"  VERDICT: {'RED — this producer is not advancing the migration' if red else 'GREEN — producer is advancing'}")
    if red:
        out("")
        out("  ESCALATE. This is the third-occurrence defect T493 was filed for: the two")
        out("  earlier outages (2026-08-24/26 and 2026-08-30/31) were both reconstructed by")
        out("  hand, after the fact, because nothing read the finding the fire already made.")

sys.exit(1 if red else 0)
PY
then
  ANALYSER_RC=0
else
  ANALYSER_RC=$?
fi
case "$ANALYSER_RC" in
  0|1|2) exit "$ANALYSER_RC" ;;
  *) refuse "the analyser exited $ANALYSER_RC — neither GREEN (0), RED (1) nor REFUSE (2). No verdict was reached; this is a GUARD FAILURE, not a finding about the producer." ;;
esac
