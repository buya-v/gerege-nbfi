#!/usr/bin/env bash
# T261 -- two small, separable checks on the successor library.
#
# (1) CALLERS.  T250 files "nothing is wired to oracle_send.sh" as backlog B-5.
#     Counted here from T250's OWN COMMITTED TREE (git ls-tree of d2b5772), not
#     from my worktree index -- in my worktree the files are untracked, and
#     counting there would have returned a meaningless 0.  That first attempt is
#     recorded rather than deleted.
# (2) TRAP CLOBBER.  oracle_send.sh's header argues that a sourced library must
#     not mutate the caller's shell, and therefore sets no shell options.  It
#     nonetheless installs `trap ... EXIT HUP INT TERM QUIT` and then runs
#     `trap - EXIT`.  Driven red here WITH A CONTROL ARM: the identical caller
#     that does NOT source the library must show its cleanup running, or the
#     experiment proves nothing and this script says so.
set -uo pipefail
ROOT=$(cd "$(dirname "$0")/../../../.." && pwd)
LIB="$ROOT/.softhouse/capture/lib"
# All scratch goes in a mktemp dir: a LITERAL absolute path that does not exist at
# lint time is a C1 "dead absolute path", and this file also has reassuring arms.
# Using mktemp keeps this instrument off the fail-open frontier by construction.
SCRATCH=$(mktemp -d "${TMPDIR:-/tmp}/t261trap.XXXXXX")
trap 'rm -rf "$SCRATCH"' EXIT

echo "=== (1) who calls oracle_send / wire_attestation, in T250's committed tree? ==="
# Extract T250's committed tree into scratch, then WALK it -- one git call rather
# than one per file.  A non-zero git exit ABORTS (exit 5), and a walk that reaches
# implausibly few files ABORTS too: an empty population is an ERROR, never a zero.
mkdir -p "$SCRATCH/tree"
if ! git -C "$ROOT" archive --format=tar --output="$SCRATCH/t250.tar" \
        d2b5772e893cac8f1635640adebb2b38de6626c9; then
  echo "ABORT: git archive of d2b5772 failed; nothing may be counted." >&2
  exit 5
fi
tar -xf "$SCRATCH/t250.tar" -C "$SCRATCH/tree" || { echo "ABORT: tar failed" >&2; exit 5; }
python3 - "$SCRATCH/tree" <<'PY'
import os, re, sys
root = sys.argv[1]
pat = re.compile(r"oracle_send|wire_attestation")
own = ("capture/lib/oracle_send.sh", "capture/lib/wire_attestation.py",
       "t250-tenant-attestation", "handoff/T250-tenant-attestation.md")
hits, n_files = {}, 0
for dp, dn, fn in os.walk(root):
    dn[:] = [d for d in dn if d not in (".git", "node_modules")]
    for f in fn:
        p = os.path.join(dp, f)
        n_files += 1
        try:
            t = open(p, "rb").read().decode("utf-8", "replace")
        except Exception:
            continue
        c = len(pat.findall(t))
        if c:
            hits[os.path.relpath(p, root)] = c
if n_files < 1000:
    sys.stderr.write("ABORT: only %d files walked; the tree did not extract.\n" % n_files)
    sys.exit(5)
outside = {k: v for k, v in hits.items() if not any(o in k for o in own)}
print("  files walked in tree d2b5772                                  : %d" % n_files)
print("  files mentioning oracle_send/wire_attestation                 : %d" % len(hits))
for k, v in sorted(hits.items()):
    tag = "T250's own" if any(o in k for o in own) else "*** EXTERNAL ***"
    print("      %-72s x%-3d %s" % (k, v, tag))
print("")
print("  mentions OUTSIDE the library itself and T250's own artefacts  : %d" % len(outside))
for k in sorted(outside):
    print("      %s" % k)
PY

echo ""
echo "=== (2) does sourcing oracle_send.sh destroy the caller's EXIT trap? ==="

make_caller() {   # make_caller PATH SOURCE_OR_NOT
  cat > "$1" <<CALLER
#!/usr/bin/env bash
set -uo pipefail
LIB="\$1"
cleanup() { echo "CALLER-CLEANUP-RAN"; }
trap cleanup EXIT
$2
mkdir -p "$SCRATCH/out"
OS_BASE=https://127.0.0.1:1 OS_OUTDIR="$SCRATCH/out" OS_HEADERS='X: y' OS_LIB_DIR="\$LIB" \\
    oracle_send probe GET /x >/dev/null 2>&1 || true
echo "BODY-FINISHED"
CALLER
}

# CONTROL: identical caller, library NOT sourced (so oracle_send is undefined and
# the call is a no-op).  Its cleanup MUST run, or the harness itself is broken.
make_caller "$SCRATCH/ctrl.sh" ''
ctrl=$(bash "$SCRATCH/ctrl.sh" "$LIB" 2>&1)
echo "  CONTROL (library NOT sourced):"
printf '%s\n' "$ctrl" | sed 's/^/      /'
if ! printf '%s' "$ctrl" | python3 -c "import sys;sys.exit(0 if 'CALLER-CLEANUP-RAN' in sys.stdin.read() else 1)"; then
  echo "  ABORT: the control arm's own EXIT trap did not fire; this host cannot"
  echo "  discriminate, so nothing may be concluded about the library. (exit 4)"
  rm -rf "$SCRATCH"
  exit 4
fi
echo "  control OK -- an unsourced caller's EXIT trap DOES fire here."
echo ""

# TREATMENT: identical caller that sources the library.
make_caller "$SCRATCH/treat.sh" '. "$LIB/oracle_send.sh"'
treat=$(bash "$SCRATCH/treat.sh" "$LIB" 2>&1)
echo "  TREATMENT (library sourced, one oracle_send call):"
printf '%s\n' "$treat" | sed 's/^/      /'
if printf '%s' "$treat" | python3 -c "import sys;sys.exit(0 if 'CALLER-CLEANUP-RAN' in sys.stdin.read() else 1)"; then
  echo "  VERDICT: the caller's EXIT trap SURVIVED the library."
else
  echo "  VERDICT: the caller's EXIT trap was DESTROYED by the sourced library --"
  echo "  the two arms differ by exactly the \`. oracle_send.sh\` line."
fi
rm -rf "$SCRATCH"
