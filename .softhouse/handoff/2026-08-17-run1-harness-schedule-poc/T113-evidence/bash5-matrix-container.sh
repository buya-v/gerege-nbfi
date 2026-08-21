#!/bin/bash
# T113 — the whole interpreter + hostile-environment matrix on a REAL bash 5.x,
# both healthy and genuinely psub-dead, against the PRE-FIX and POST-FIX bytes.
#
#   bash .softhouse/handoff/2026-08-17-run1-harness-schedule-poc/T113-evidence/bash5-matrix-container.sh
#
# The host this program runs on has only bash 3.2.57, so every claim in
# conformance.sh's guard comment that names a bash 5.x has to be measured
# somewhere else. This is that somewhere: a throwaway `eclipse-temurin:21-jdk`
# container (bash 5.3.9), `--network none`, repo mounted READ-ONLY, unrelated to
# the Fineract reference-oracle stack. It contacts no reference oracle, starts,
# stops, rebuilds and re-seeds nothing in that stack.
#
# The pre-fix baseline is pinned to an IMMUTABLE COMMIT SHA (P-24). f2813c8 is the
# tip of softhouse/T97-guard-positive-probe — the bytes T106 reviewed, i.e. the
# guard WITH T97's positive probe and WITHOUT T113's one-line F1 fix. Pinning the
# branch NAME would let the baseline follow the fix the moment someone rebases it.
set -u

PREFIX_COMMIT=f2813c8d51199ef676eb2924ca180041d00242db
PREFIX_SHA256=c69e30ff6617debbd2e013cefd903479dcab0f8c9b0c4e3ea273e88b1907951a

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
IMAGE=eclipse-temurin:21-jdk
PREFIX="$REPO_ROOT/.softhouse/.T113-b5-prefix.sh"
INNER="$REPO_ROOT/.softhouse/.T113-b5-inner.sh"
trap 'rm -f "$PREFIX" "$INNER"' EXIT

if ! git -C "$REPO_ROOT" show "$PREFIX_COMMIT:.softhouse/conformance.sh" > "$PREFIX" 2>/dev/null; then
  echo "T113: cannot read $PREFIX_COMMIT:.softhouse/conformance.sh — refusing to report anything." >&2
  exit 1
fi
got="$(shasum -a 256 "$PREFIX" | cut -d' ' -f1)"
if [ "$got" != "$PREFIX_SHA256" ]; then
  echo "T113: pinned pre-fix bytes hash $got, expected $PREFIX_SHA256 — INERT, exit 1." >&2
  exit 1
fi
if grep -q '^      _conformance_psub_line=$' "$PREFIX"; then
  echo "T113: the pinned baseline ALREADY contains the F1 fix — not a pre-fix baseline. INERT, exit 1." >&2
  exit 1
fi
if ! grep -q '^      _conformance_psub_line=$' "$REPO_ROOT/.softhouse/conformance.sh"; then
  echo "T113: the F1 assignment is NOT in the current harness — this would compare two" >&2
  echo "T113: unfixed files and print a false green. INERT, exit 1." >&2
  exit 1
fi

cat > "$INNER" <<'INNER_EOF'
#!/bin/bash
cd /repo || exit 9
PRE=.softhouse/.T113-b5-prefix.sh
POST=.softhouse/conformance.sh
echo "container bash : $(bash --version | head -1)"
echo "container /bin/sh -> $(readlink -f /bin/sh)"
echo

cap() { local v; v="$(bash -c 'IFS= read -r v < <(printf "%s\n" CAP) 2>/dev/null; printf %s "${v:-}"' 2>/dev/null)"; [ "$v" = CAP ] && echo yes || echo no; }
code() { "$@" >/dev/null 2>&1; echo $?; }

section() { echo; echo "=== $1 ==="; }

matrix() {
  local tag="$1"
  echo "psub capability of plain bash here: $(cap)"
  for h in "$PRE" "$POST"; do
    case "$h" in *prefix*) n="PRE-FIX ";; *) n="POST-FIX";; esac
    printf '%s %-46s clean=%s  forged=%s\n' "$n" "$tag" \
      "$(code bash "$h" --help)" \
      "$(code env _conformance_psub_line=conformance-psub-live bash "$h" --help)"
  done
}

section "A. healthy bash 5.3.9 — plain"
matrix "plain bash"

section "B. healthy bash 5.3.9 — --posix"
for h in "$PRE" "$POST"; do
  case "$h" in *prefix*) n="PRE-FIX ";; *) n="POST-FIX";; esac
  printf '%s --posix                                        clean=%s  forged=%s\n' "$n" \
    "$(code bash --posix "$h" --help)" \
    "$(code env _conformance_psub_line=conformance-psub-live bash --posix "$h" --help)"
done

section "C. healthy bash 5.3.9 — argv[0]=sh, and argv[0]=sh --posix"
for h in "$PRE" "$POST"; do
  case "$h" in *prefix*) n="PRE-FIX ";; *) n="POST-FIX";; esac
  a="$( (exec -a sh bash "$h" --help) >/dev/null 2>&1; echo $?)"
  b="$( (exec -a sh bash --posix "$h" --help) >/dev/null 2>&1; echo $?)"
  printf '%s argv0=sh=%s   argv0=sh --posix=%s\n' "$n" "$a" "$b"
done

section "D. bash -r, --posix -r"
for h in "$PRE" "$POST"; do
  case "$h" in *prefix*) n="PRE-FIX ";; *) n="POST-FIX";; esac
  printf '%s -r=%s   --posix -r=%s\n' "$n" "$(code bash -r "$h")" "$(code bash --posix -r "$h")"
done

section "E. non-bash interpreters present in this image"
for s in /bin/dash /bin/sh /usr/bin/dash /bin/zsh /bin/ksh /bin/mksh /bin/busybox; do
  [ -x "$s" ] || continue
  case "$s" in
    */busybox) printf '  %-16s exit=%s\n' "busybox sh" "$(code "$s" sh "$POST")" ;;
    *)         printf '  %-16s exit=%s\n' "$s" "$(code "$s" "$POST")" ;;
  esac
done

section "F. /dev/fd REMOVED — a genuinely psub-dead bash 5.3.9"
rm -f /dev/fd
echo "psub capability now: $(cap)   (must be 'no')"
matrix "psub-dead"
echo
echo "  the same shape under --posix and argv[0]=sh (all must refuse):"
for h in "$PRE" "$POST"; do
  case "$h" in *prefix*) n="PRE-FIX ";; *) n="POST-FIX";; esac
  printf '  %s --posix=%s  argv0=sh=%s  argv0=sh --posix=%s\n' "$n" \
    "$(code bash --posix "$h" --help)" \
    "$( (exec -a sh bash "$h" --help) >/dev/null 2>&1; echo $?)" \
    "$( (exec -a sh bash --posix "$h" --help) >/dev/null 2>&1; echo $?)"
done

section "G. exported-function hijacks on the PSUB-DEAD bash (conformance.sh's own claims)"
hij() { # hij <label> <name> <body> <harness>
  local label="$1" name="$2" body="$3" h="$4" c
  c=$(bash -c "
    $name() { $body }
    export -f '$name' 2>/dev/null || { echo 99; exit; }
    bash \"\$1\" --help >/dev/null 2>&1; echo \$?
  " _ "$h" 2>/dev/null | tail -1)
  printf '  %-42s %s -> exit=%s\n' "$label" "$( [ "$h" = "$PRE" ] && echo PRE-FIX || echo POST-FIX )" "$c"
}
for h in "$PRE" "$POST"; do
  hij "control: no hijack"                          true    ':;'                          "$h"
  hij "[() { return 1; }"                           '['     'return 1;'                   "$h"
  hij "[() { return 0; }"                           '['     'return 0;'                   "$h"
  hij "builtin() { return 1; }"                     builtin 'return 1;'                   "$h"
  hij "builtin() { echo conformance-psub-live; }"   builtin 'echo conformance-psub-live;' "$h"
  hij "eval() { return 1; }"                        eval    'return 1;'                   "$h"
  hij "eval() { echo conformance-psub-live; }"      eval    'echo conformance-psub-live;' "$h"
done

section "H. the refusal text under [() { return 0; } on a HEALTHY-ish shell claim"
echo "(this row is measured on the host too; here it is on 5.3.9)"
bash -c '[() { return 0; }; export -f "["; bash "$1" --help 2>&1 | head -4' _ "$POST"
INNER_EOF

docker run --rm --network none -v "$REPO_ROOT":/repo:ro "$IMAGE" bash /repo/.softhouse/.T113-b5-inner.sh
