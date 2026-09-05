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
#     VETO 2       REPEAT PAYLOAD. The added surface payload, normalised (case
#                  folded, whitespace collapsed, digit/hex runs → `#`), is one
#                  this producer has ALREADY used to promote inside the lookback
#                  window. `// heartbeat 1` and `// heartbeat 2` normalise to the
#                  same payload; the second one does not promote. This is what
#                  makes a per-fire heartbeat stop clearing after its first beat,
#                  without naming a path or a wording.
#     VETO 3       THIN PAYLOAD. A promotion carrying fewer than
#                  NOFS_MIN_SUBST_LINES (default 8) substantive added surface
#                  lines does not clear a fire. This is a MATERIALITY floor, not
#                  a shape: it names no path and no wording, only a size, so it
#                  is not a blocklist of paddings already seen. The number is
#                  MEASURED, not chosen by taste — over the whole recorded
#                  history the THINNEST promotion that ever cleared a fire
#                  carries 12 substantive added surface lines (local producer,
#                  88 fires, 36 of them cleared) and 27 (cloud, 4 fires, 4
#                  cleared), and the longest run of cleared-but-thin fires is
#                  ZERO at every floor up to 8. A floor of 8 therefore costs
#                  nothing measured, keeps a 1.5x margin under the observed
#                  minimum, and is what stops a heartbeat whose content is NOVEL
#                  on every beat (T550 attacks G and H) — the shape VETO 2 alone
#                  cannot see, because nothing repeats.
#                  Raising it tightens; lowering it loosens. Re-measure with
#                  .softhouse/capture/t493-zero-turn-escalation/t550-materiality-floor.txt
#                  before changing it.
#
#   WHAT THIS CLOSES AND WHAT IT DOES NOT — read this before trusting it.
#   Git history is entirely under the producer's control, so NO test over git
#   metadata can make a promotion unforgeable, and this one does not claim to.
#   What changed is the COST of the forgery and the DEFAULT when the guard is
#   unsure. T541's attack — one valueless line per fire to any path outside the
#   bookkeeping set — no longer promotes at all: docs/*.md is not on the surface.
#   A heartbeat aimed INSIDE the surface promotes once and is vetoed thereafter.
#   STILL OPEN, and stated rather than hidden: a producer that writes NOVEL,
#   SUBSTANTIVE content into nexus/ or .softhouse/capture/ every fire, forever,
#   still reads GREEN. At that point the attack costs what the work costs, which
#   is where the boundary belongs; the composing guard for that case is
#   .softhouse/bin/check-branch-published.py plus the independent reviewer, not
#   this one. See --explain to audit any single verdict, including its vetoes.
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
#   2  REFUSE  — cannot answer (shallow history, bad ref, no such producer).
#                REFUSE IS NOT GREEN. A caller that treats 2 as pass reintroduces
#                exactly the defect this guard exists for.
#
# USAGE
#   .softhouse/guards/no-op-fire-streak.sh [--producer local|cloud|any]
#        [--ref REF] [--silence-hours H] [--earned-silence-hours H] [--streak N]
#        [--lookback-days D] [--min-subst-lines N] [--now ISO8601] [--explain SHA]
#        [--json] [--quiet]

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

usage() { sed -n '2,130p' "$0" | sed 's/^# \{0,1\}//'; }

while [ $# -gt 0 ]; do
  case "$1" in
    --producer)       PRODUCER="$2"; shift 2 ;;
    --ref)            REF="$2"; shift 2 ;;
    --silence-hours)  SILENCE_HOURS="$2"; shift 2 ;;
    --earned-silence-hours) EARNED_SILENCE_HOURS="$2"; shift 2 ;;
    --streak)         STREAK="$2"; shift 2 ;;
    --lookback-days)  LOOKBACK_DAYS="$2"; shift 2 ;;
    --min-subst-lines) MIN_SUBST_LINES="$2"; shift 2 ;;
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
RAW="$(mktemp)"; PAY="$(mktemp)"; trap 'rm -f "$RAW" "$PAY"' EXIT
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
OLDEST_ISO="$(git log "$REF" --format='%cI' | tail -1)"

NOFS_RAW="$RAW" NOFS_PAY="$PAY" \
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

def substantive(lines):
    return [l for l in lines if not NULL_LINE.match(l)]

def payload_digest(lines):
    """Normalised digest of the added surface payload: case folded, whitespace
    collapsed, digit and hex runs replaced by '#'. `// heartbeat 1` and
    `// heartbeat 2` collapse to the same digest, so the second beat of a
    heartbeat does not promote. Content is never matched against a word list —
    only against what this same producer has already used to promote."""
    norm = '\n'.join(DIGIT_RUN.sub('#', WS_RUN.sub(' ', l.strip().lower()))
                     for l in lines)
    return hashlib.sha256(norm.encode('utf-8', 'replace')).hexdigest()[:16]

for c in commits:
    c['dt']      = datetime.datetime.fromisoformat(c['ts'])
    c['off']     = c['ts'][-6:]
    # AXIS 2's old, deliberately-monotone rule (see header). It can only add RED.
    c['carry']   = [f for f in c['files'] if not book_re.search(f)]
    c['carrying'] = bool(c['carry'])
    # THE PROMOTION. Subject text is never consulted. Default is BOOKKEEPING;
    # REAL must be EARNED by a surface anchor surviving both vetoes.
    c['anchor']  = [f for f in c['files'] if surf_re.search(f)]
    c['offsurf'] = [f for f in c['carry'] if not surf_re.search(f)]
    c['subst']   = substantive(payload.get(c['sha'], []))
    c['digest']  = payload_digest(c['subst']) if c['subst'] else None
    c['earned']  = False
    if not c['anchor']:
        c['why'] = 'NO ANCHOR — no changed path is on the migration surface'
    elif not c['subst']:
        c['why'] = 'VETO 1 NULL PAYLOAD — the surface paths gained no readable line'
    elif len(c['subst']) < min_subst:
        c['why'] = (f"VETO 3 THIN PAYLOAD — {len(c['subst'])} substantive added surface "
                    f"line(s), floor is {min_subst}")
    else:
        c['why'] = None          # decided in the window pass, which needs order

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

# --- VETO 2, applied in time order, per producer -----------------------------
# A digest promotes ONCE per producer per lookback window. The window is measured
# from `now` so that a replay grades the same way a live run would.
window_start = now - datetime.timedelta(days=lookback)
seen = {}                       # (offset, digest) -> first promoting sha
for c in commits:               # oldest -> newest
    if c['why'] is not None:
        continue
    key = (c['off'], c['digest'])
    first = seen.get(key)
    if first is None:
        seen[key] = c['sha']
        c['earned'] = True
    elif c['dt'] < window_start:
        # Outside the graded window the repeat rule is not applied: a digest that
        # first appeared months ago must not silently veto today's work. The
        # window is what the vetoes answer for, and it says so.
        c['earned'] = True
    else:
        c['why'] = (f'VETO 2 REPEAT PAYLOAD — normalised payload {c["digest"]} already '
                    f'promoted at {first[:8]} for this producer inside the window')

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
        print(f"reason    ANCHOR on the migration surface + payload {c['digest']} "
              f"({len(c['subst'])} substantive added line(s), floor {min_subst}), "
              f"all three vetoes survived")
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
        'in_window_veto3_thin_payload': veto3, 'min_substantive_lines': min_subst,
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
        f"{veto3} thin-payload (<{min_subst} substantive lines) "
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
