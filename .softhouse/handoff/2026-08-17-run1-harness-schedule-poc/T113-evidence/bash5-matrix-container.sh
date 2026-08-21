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
#
# T130 ARMED THIS SCRIPT (T121's F-T121-2). Its INERT guards were already strong,
# but they protect the SUBJECT and never protected the OBSERVATION: the load-bearing
# expectations lived in prose — `(must be 'no')`, `(all must refuse)` — and the
# script exited 0 whatever the numbers were. Sections A, D and F now assert; the
# survey sections (B, C, E, G, H) still only report, and say so in their headings so
# nobody mistakes a printed number for a checked one. The host requires the
# container's summary line to be PRESENT as well as clean: a container that died
# must not read as a pass.
#
# DRIVEN RED (P-22): delete the `rm -f /dev/fd` line from the generated inner script
# and re-run it in the same image. Section F's precondition and both of its
# clean/forged rows go red — the exact vacuity that would otherwise be invisible on
# any image where removing /dev/fd silently fails.
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

ipass=0; ifail=0
iok()  { ipass=$((ipass + 1)); printf '  ok    %s\n' "$1"; }
ibad() { ifail=$((ifail + 1)); printf '  FAIL  %s\n' "$1"; printf '        %s\n' "${2:-}"; }
eq()   { # eq <label> <got> <want> <why-if-wrong>
  if [ "$2" = "$3" ]; then iok "$1 = $3"; else ibad "$1 = $2, expected $3" "$4"; fi
}

TOKEN="$(sed -n 's/^CONFORMANCE_PSUB_TOKEN="\(.*\)"$/\1/p' "$POST" | head -1)"

section() { echo; echo "=== $1 ==="; }

# matrix <tag> <want-clean|-> <want-forged-PRE|-> <want-forged-POST|->
# A `-` means "report only, do not assert" — used by the survey sections, so that a
# printed number is never mistaken for a checked one.
matrix() {
  local tag="$1" wclean="${2:--}" wpre="${3:--}" wpost="${4:--}"
  echo "psub capability of plain bash here: $(cap)"
  for h in "$PRE" "$POST"; do
    case "$h" in *prefix*) n="PRE-FIX "; wf="$wpre";; *) n="POST-FIX"; wf="$wpost";; esac
    local c f
    c="$(code bash "$h" --help)"
    f="$(code env _conformance_psub_line="$TOKEN" bash "$h" --help)"
    printf '%s %-46s clean=%s  forged=%s\n' "$n" "$tag" "$c" "$f"
    [ "$wclean" = - ] || eq "$n $tag clean" "$c" "$wclean" "the guard's decision on a clean environment moved"
    [ "$wf" = - ]     || eq "$n $tag forged" "$f" "$wf" \
      "$( [ "$wf" = 0 ] && echo 'the PRE-FIX bytes must ADMIT the forge — that is the defect this script exists to reproduce' || echo 'the POST-FIX bytes must REFUSE the forge — forged=0 means the F1 fix has regressed' )"
  done
}

section "A. healthy bash 5.3.9 — plain   [ASSERTED: no false refusal, either side of the fix]"
# A healthy shell must be admitted whether or not the forge variable is set, and
# whether or not the fix is present. This is the control that distinguishes a FIX
# from a blanket refusal.
matrix "plain bash" 0 0 0

section "B. healthy bash 5.3.9 — --posix   [survey: reported, not asserted]"
for h in "$PRE" "$POST"; do
  case "$h" in *prefix*) n="PRE-FIX ";; *) n="POST-FIX";; esac
  printf '%s --posix                                        clean=%s  forged=%s\n' "$n" \
    "$(code bash --posix "$h" --help)" \
    "$(code env _conformance_psub_line=conformance-psub-live bash --posix "$h" --help)"
done

section "C. healthy bash 5.3.9 — argv[0]=sh, and argv[0]=sh --posix   [survey: reported, not asserted]"
for h in "$PRE" "$POST"; do
  case "$h" in *prefix*) n="PRE-FIX ";; *) n="POST-FIX";; esac
  a="$( (exec -a sh bash "$h" --help) >/dev/null 2>&1; echo $?)"
  b="$( (exec -a sh bash --posix "$h" --help) >/dev/null 2>&1; echo $?)"
  printf '%s argv0=sh=%s   argv0=sh --posix=%s\n' "$n" "$a" "$b"
done

section "D. bash -r, --posix -r   [ASSERTED: refused at 3, both sides of the fix]"
for h in "$PRE" "$POST"; do
  case "$h" in *prefix*) n="PRE-FIX ";; *) n="POST-FIX";; esac
  r="$(code bash -r "$h")"; pr="$(code bash --posix -r "$h")"
  printf '%s -r=%s   --posix -r=%s\n' "$n" "$r" "$pr"
  eq "$n bash -r"          "$r"  3 "a restricted shell cannot run this harness and must be refused at 3, not admitted or reported as an outage at 2"
  eq "$n bash --posix -r"  "$pr" 3 "same, in POSIX mode"
done

section "E. non-bash interpreters present in this image   [survey: reported, not asserted — interpreter-matrix.sh asserts these]"
for s in /bin/dash /bin/sh /usr/bin/dash /bin/zsh /bin/ksh /bin/mksh /bin/busybox; do
  [ -x "$s" ] || continue
  case "$s" in
    */busybox) printf '  %-16s exit=%s\n' "busybox sh" "$(code "$s" sh "$POST")" ;;
    *)         printf '  %-16s exit=%s\n' "$s" "$(code "$s" "$POST")" ;;
  esac
done

section "F. /dev/fd REMOVED — a genuinely psub-dead bash 5.3.9   [ASSERTED: the whole point of this script]"
rm -f /dev/fd
nowcap="$(cap)"
echo "psub capability now: $nowcap   (must be 'no')"
# PRECONDITION. Every row below is a claim about a psub-DEAD interpreter. If
# /dev/fd survived, this is a HEALTHY bash, everything is admitted, and printing
# that as "the forge is closed" would be a lie in the shape of a green.
eq "F precondition: psub capability" "$nowcap" no \
   "/dev/fd was not removed, so this is a HEALTHY bash and nothing below is evidence about the forge"
matrix "psub-dead" 3 0 3
echo
echo "  the same shape under --posix and argv[0]=sh (all must refuse):"
for h in "$PRE" "$POST"; do
  case "$h" in *prefix*) n="PRE-FIX ";; *) n="POST-FIX";; esac
  p="$(code bash --posix "$h" --help)"
  a="$( (exec -a sh bash "$h" --help) >/dev/null 2>&1; echo $?)"
  b="$( (exec -a sh bash --posix "$h" --help) >/dev/null 2>&1; echo $?)"
  printf '  %s --posix=%s  argv0=sh=%s  argv0=sh --posix=%s\n' "$n" "$p" "$a" "$b"
  eq "$n psub-dead --posix"          "$p" 3 "a psub-dead shell must be refused at 3"
  eq "$n psub-dead argv0=sh"         "$a" 3 "a psub-dead shell must be refused at 3"
  eq "$n psub-dead argv0=sh --posix" "$b" 3 "a psub-dead shell must be refused at 3"
done

section "G. exported-function hijacks on the PSUB-DEAD bash (conformance.sh's own claims)   [survey: reported, not asserted — these document a HOSTILE ENVIRONMENT, which the guard explicitly does not claim to defend against]"
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

section "H. the refusal text under [() { return 0; } on a HEALTHY-ish shell claim   [survey: reported, not asserted]"
echo "(this row is measured on the host too; here it is on 5.3.9)"
bash -c '[() { return 0; }; export -f "["; bash "$1" --help 2>&1 | head -4' _ "$POST"

echo
echo "======================================================================="
printf 'T113/T130 BASH5 MATRIX: %d passed, %d failed\n' "$ipass" "$ifail"
echo "======================================================================="
INNER_EOF

out="$(docker run --rm --network none -v "$REPO_ROOT":/repo:ro "$IMAGE" bash /repo/.softhouse/.T113-b5-inner.sh 2>&1)"
rc=$?
printf '%s\n' "$out"

# HOST-SIDE CHECK. The container's counters mean nothing if it never reached the
# end, so the ABSENCE of a summary line is an error, not a pass (P-22).
summary="$(printf '%s\n' "$out" | grep -E '^T113/T130 BASH5 MATRIX:' | tail -1)"
if [ -z "$summary" ]; then
  echo "T113: the container printed no summary line (docker rc=$rc) — it did not finish." >&2
  echo "T113: a run with no result is a FAILURE, not a pass. exit 1." >&2
  exit 1
fi
case "$summary" in
  *", 0 failed") echo "T113: container assertions all passed."; exit 0 ;;
  *)             echo "T113: container assertions FAILED — $summary" >&2; exit 1 ;;
esac
