#!/usr/bin/env bash
# .softhouse/guards/no-op-fire-streak.sh
#
# T493 — NOTHING ESCALATES A ZERO-TURN FIRE.
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
# THE TWO FAILURE MODES, BOTH MEASURED IN THIS REPO'S REAL HISTORY
#   AXIS 1 — NO-OP STREAK.  Fires DO run: they take the lock, reconcile the
#     wrapper state, release the lock, and advance nothing. 2026-08-24/25/26 and
#     2026-08-30/31 are this shape (18 bookkeeping commits per day, 0 real).
#   AXIS 2 — SILENCE.  Fires do not run AT ALL: no lock is taken, so there are no
#     fires to classify and a streak detector alone sees nothing and reports
#     all-clear. The outage live as this guard was written (local producer silent
#     from 2026-09-03T11:09:38Z) is this shape.
#   A guard that implements only axis 1 goes GREEN on the live outage. Both axes
#   are checked; RED if EITHER trips.
#
# HOW A COMMIT IS CLASSIFIED — BY FILE FOOTPRINT, NEVER BY SUBJECT TEXT
#   B-11 and P-104 are this program's record of the opposite mistake:
#   guard_no_float_in_vectors matched a WORD LIST and was defeated by rewording;
#   T528 defeated T527's anchor rule with a one-word reword. So this guard never
#   reads a commit subject to decide bookkeeping-vs-real. A commit is BOOKKEEPING
#   iff every path it changes is scheduler self-churn (the wrapper recording its
#   own existence); it is REAL iff it changes anything else. Rewording a subject
#   cannot move a commit across that line in either direction, because the
#   subject is not an input. See --explain to audit any single verdict.
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
#   0  GREEN   — the producer is advancing; neither axis tripped.
#   1  RED     — a no-op streak and/or a silence breach. Escalate.
#   2  REFUSE  — cannot answer (shallow history, bad ref, no such producer).
#                REFUSE IS NOT GREEN. A caller that treats 2 as pass reintroduces
#                exactly the defect this guard exists for.
#
# USAGE
#   .softhouse/guards/no-op-fire-streak.sh [--producer local|cloud|any]
#        [--ref REF] [--silence-hours H] [--streak N] [--lookback-days D]
#        [--now ISO8601] [--explain SHA] [--json] [--quiet]

set -euo pipefail

PROG="$(basename "$0")"

# ---------------------------------------------------------------------------
# Defaults. Every one is overridable so the guard can be driven RED and GREEN
# against recorded history without editing it.
# ---------------------------------------------------------------------------
REF="${NOFS_REF:-origin/main}"
PRODUCER="${NOFS_PRODUCER:-local}"
SILENCE_HOURS="${NOFS_SILENCE_HOURS:-18}"
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
# state, or releasing the lock. This is a PURPOSE-based definition realised as a
# path set, and it is printed in every report so a reviewer can audit it.
BOOKKEEPING_RE="${NOFS_BOOKKEEPING_RE:-^\.softhouse/(LOCK|RESUME\.md)$|^\.softhouse/(state|logs|runs)/}"

usage() { sed -n '2,60p' "$0" | sed 's/^# \{0,1\}//'; }

while [ $# -gt 0 ]; do
  case "$1" in
    --producer)       PRODUCER="$2"; shift 2 ;;
    --ref)            REF="$2"; shift 2 ;;
    --silence-hours)  SILENCE_HOURS="$2"; shift 2 ;;
    --streak)         STREAK="$2"; shift 2 ;;
    --lookback-days)  LOOKBACK_DAYS="$2"; shift 2 ;;
    --now)            NOW="$2"; shift 2 ;;
    --explain)        EXPLAIN="$2"; shift 2 ;;
    --json)           JSON=1; shift ;;
    --quiet)          QUIET=1; shift ;;
    --no-fetch)       NO_FETCH=1; shift ;;
    -h|--help)        usage; exit 0 ;;
    *) echo "$PROG: unknown argument: $1" >&2; exit 2 ;;
  esac
done

say() { [ "$QUIET" = 1 ] || printf '%s\n' "$*"; }
refuse() {
  # REFUSE is deliberately loud and deliberately NOT exit 0.
  printf 'no-op-fire-streak: REFUSE — %s\n' "$*" >&2
  printf 'no-op-fire-streak: REFUSE IS NOT GREEN. No verdict was reached.\n' >&2
  exit 2
}

case "$PRODUCER" in
  local) WANT_OFFSET="$LOCAL_OFFSET" ;;
  cloud) WANT_OFFSET="$CLOUD_OFFSET" ;;
  any)   WANT_OFFSET="" ;;
  *) refuse "unknown producer '$PRODUCER' (expected local|cloud|any)" ;;
esac

command -v git  >/dev/null 2>&1 || refuse "git not on PATH"
command -v python3 >/dev/null 2>&1 || refuse "python3 not on PATH"
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
# STEP 1 — one pass over the history, then all analysis in python3.
#
# --no-merges: a merge commit reports no paths under --name-only, which would
# make every merge look like bookkeeping. The content a merge brings in is
# already present as the branch commits git log linearises alongside it, so
# excluding merges loses no real work and invents no fake bookkeeping.
# ---------------------------------------------------------------------------
# --numstat (not --name-only) because AXIS 1 needs the DIFF DIRECTION on
# .softhouse/LOCK to tell a lock TAKE (inserts the lock body) from a lock RELEASE
# (deletes it) without reading the words "take" or "release" from the subject.
RAW="$(mktemp)"; trap 'rm -f "$RAW"' EXIT
git log "$REF" --no-merges --numstat --format='@@%H|%cI' > "$RAW" 2>/dev/null \
  || refuse "could not read history of '$REF'"
[ -s "$RAW" ] || refuse "history of '$REF' is empty"

# NOTE: `git log --reverse | head -1` raises SIGPIPE under `set -o pipefail` and
# would abort the guard with exit 141 — which a caller could easily mistake for a
# verdict. Take the last line of the forward log instead; no pipe is closed early.
OLDEST_ISO="$(git log "$REF" --format='%cI' | tail -1)"

NOFS_RAW="$RAW" \
NOFS_A_REF="$REF" NOFS_A_PRODUCER="$PRODUCER" NOFS_A_OFFSET="$WANT_OFFSET" \
NOFS_A_SILENCE="$SILENCE_HOURS" NOFS_A_STREAK="$STREAK" \
NOFS_A_LOOKBACK="$LOOKBACK_DAYS" NOFS_A_NOW="$NOW" NOFS_A_EXPLAIN="$EXPLAIN" \
NOFS_A_JSON="$JSON" NOFS_A_QUIET="$QUIET" NOFS_A_BOOKRE="$BOOKKEEPING_RE" \
NOFS_A_OLDEST="$OLDEST_ISO" NOFS_A_UNSHALLOW="$UNSHALLOW_NOTE" \
python3 <<'PY'
import os, re, sys, json, datetime

raw       = os.environ['NOFS_RAW']
ref       = os.environ['NOFS_A_REF']
producer  = os.environ['NOFS_A_PRODUCER']
offset    = os.environ['NOFS_A_OFFSET']
silence_h = float(os.environ['NOFS_A_SILENCE'])
streak_n  = int(os.environ['NOFS_A_STREAK'])
lookback  = float(os.environ['NOFS_A_LOOKBACK'])
now_s     = os.environ['NOFS_A_NOW'].strip()
explain   = os.environ['NOFS_A_EXPLAIN'].strip()
as_json   = os.environ['NOFS_A_JSON'] == '1'
quiet     = os.environ['NOFS_A_QUIET'] == '1'
book_re   = re.compile(os.environ['NOFS_A_BOOKRE'])
oldest_s  = os.environ['NOFS_A_OLDEST'].strip()
unshallow = os.environ['NOFS_A_UNSHALLOW']

UTC = datetime.timezone.utc
def out(*a):
    if not quiet: print(*a)

# --- parse ------------------------------------------------------------------
commits = []
cur = None
with open(raw) as fh:
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

for c in commits:
    c['dt']    = datetime.datetime.fromisoformat(c['ts'])
    c['off']   = c['ts'][-6:]
    # THE CLASSIFIER. Subject text is never consulted; only the changed paths.
    c['carry'] = [f for f in c['files'] if not book_re.search(f)]
    c['real']  = bool(c['carry'])

def mine(c):
    return (offset == '' or c['off'] == offset)

now = datetime.datetime.fromisoformat(now_s) if now_s else datetime.datetime.now(UTC)
if now.tzinfo is None: now = now.replace(tzinfo=UTC)

# --now is an AS-OF replay, not just a clock relabel. Without this filter the
# guard reads commits that had not happened yet at the replayed instant, which
# silently inverts every historical verdict: replaying 2026-08-27 would grade
# fires from 2026-09-02 and report a NEGATIVE silence. Driving a detector RED
# against recorded history is worthless if the replay can see the future.
future = [c for c in commits if c['dt'] > now]
commits = [c for c in commits if c['dt'] <= now]
if not commits:
    print(f"no-op-fire-streak: REFUSE — no commits at or before --now {now.astimezone(UTC):%Y-%m-%dT%H:%M:%SZ} "
          f"in {ref} (history begins {oldest_s})", file=sys.stderr)
    sys.exit(2)

# --- --explain: audit one verdict ------------------------------------------
if explain:
    hit = [c for c in commits if c['sha'].startswith(explain)]
    if not hit:
        print(f"no-op-fire-streak: REFUSE — no commit matching '{explain}' in {ref} "
              f"(looked in the full --no-merges history of {ref}, {len(commits)} commits, "
              f"oldest {oldest_s}); note merges are excluded by design", file=sys.stderr)
        sys.exit(2)
    c = hit[0]
    print(f"commit    {c['sha']}")
    print(f"committed {c['dt'].astimezone(UTC):%Y-%m-%dT%H:%M:%SZ}  offset {c['off']}  "
          f"producer={'local' if c['off']=='+08:00' else 'cloud' if c['off']=='+00:00' else 'other'}")
    print(f"verdict   {'REAL' if c['real'] else 'BOOKKEEPING'}   (decided from {len(c['files'])} changed path(s); subject text NOT consulted)")
    for f in c['files']:
        print(f"    {'carries' if not book_re.search(f) else 'self-churn'}  {f}")
    sys.exit(0)

# --- window / coverage refusal ---------------------------------------------
window_start = now - datetime.timedelta(days=lookback)
oldest = datetime.datetime.fromisoformat(oldest_s) if oldest_s else None
# If the history does not reach back to the start of the lookback window, the
# window is answering for less than it claims. That is the shallow-clone failure
# in its general form, so it gets the same refusal — UNLESS the repository
# genuinely begins inside the window (a young repo), which we can tell because
# the oldest commit is a root commit we actually hold.
truncated = oldest is not None and oldest > window_start
root_held = True   # oldest commit is present in this clone by construction

pool   = [c for c in commits if mine(c)]
inwin  = [c for c in pool if c['dt'] >= window_start]
reals  = [c for c in pool if c['real']]

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
# discipline as the bookkeeping classifier.
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

# --- AXIS 2 — silence -------------------------------------------------------
last_real = reals[-1] if reals else None
silence = (now - last_real['dt']).total_seconds() / 3600.0 if last_real else None
axis2_red = (last_real is None) or (silence > silence_h)

red = axis1_red or axis2_red

# --- report -----------------------------------------------------------------
book_in_win = len([c for c in inwin if not c['real']])
real_in_win = len([c for c in inwin if c['real']])

if as_json:
    print(json.dumps({
        'ref': ref, 'producer': producer, 'offset': offset or 'any',
        'now': now.astimezone(UTC).isoformat(),
        'history_oldest': oldest_s, 'unshallow': unshallow,
        'lookback_days': lookback, 'window_truncated': truncated,
        'commits_total': len(commits), 'commits_producer': len(pool),
        'in_window_real': real_in_win, 'in_window_bookkeeping': book_in_win,
        'fires_graded': len(graded), 'noop_streak': streak, 'streak_threshold': streak_n,
        'axis1_noop_streak_red': axis1_red,
        'last_real_commit': last_real['sha'] if last_real else None,
        'last_real_at': last_real['dt'].astimezone(UTC).isoformat() if last_real else None,
        'silence_hours': round(silence, 2) if silence is not None else None,
        'silence_threshold_hours': silence_h,
        'axis2_silence_red': axis2_red,
        'verdict': 'RED' if red else 'GREEN',
    }, indent=2))
else:
    out(f"no-op-fire-streak — ref={ref} producer={producer} (committer offset {offset or 'any'})")
    out(f"  history      : {len(commits)} non-merge commits, oldest {oldest_s}; {unshallow}")
    out(f"  bookkeeping  : paths matching {book_re.pattern}")
    out(f"  now          : {now.astimezone(UTC):%Y-%m-%dT%H:%M:%SZ}"
        + ("  [--now override]" if now_s else ""))
    out(f"  window       : last {lookback:g} day(s), from {window_start.astimezone(UTC):%Y-%m-%dT%H:%M:%SZ}"
        + ("   *** TRUNCATED: history begins inside the window ***" if truncated else ""))
    out(f"  in window    : {real_in_win} real, {book_in_win} bookkeeping, {len(graded)} fire(s) graded")
    out("")
    out(f"  AXIS 1 no-op streak : {streak} consecutive no-op fire(s) (threshold {streak_n}) -> "
        + ("RED" if axis1_red else "ok"))
    for (c, end) in streak_detail[:12]:
        out(f"      no-op fire  {c['sha'][:8]}  {c['dt'].astimezone(UTC):%Y-%m-%dT%H:%MZ} .. {end.astimezone(UTC):%H:%MZ}")
    if len(streak_detail) > 12:
        out(f"      ... and {len(streak_detail)-12} more")
    if last_real:
        out(f"  AXIS 2 silence      : {silence:.1f}h since last REAL commit {last_real['sha'][:8]} "
            f"at {last_real['dt'].astimezone(UTC):%Y-%m-%dT%H:%MZ} (threshold {silence_h:g}h) -> "
            + ("RED" if axis2_red else "ok"))
    else:
        out(f"  AXIS 2 silence      : producer has NO real commit in all of history -> RED")
    out("")
    out(f"  VERDICT: {'RED — this producer is not advancing the migration' if red else 'GREEN — producer is advancing'}")
    if red:
        out("")
        out("  ESCALATE. This is the third-occurrence defect T493 was filed for: the two")
        out("  earlier outages (2026-08-24/26 and 2026-08-30/31) were both reconstructed by")
        out("  hand, after the fact, because nothing read the finding the fire already made.")

sys.exit(1 if red else 0)
PY
