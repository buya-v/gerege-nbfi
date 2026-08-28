#!/usr/bin/env bash
# T272 — WHO ACTUALLY SOURCES go-env.sh, AND WHICH OF THEM RUN UNDER `set -e`.
#
# WHY. The F-8 correction now shipping inside go-env.sh says "all three consumers of this
# file" and names them. T254b said "both consumers". Both counts are about the LIVE harness,
# and both are stated as if they were the whole world. This instrument MEASURES the whole
# world instead, so the comment can say what it actually audited and what it did not
# (P-70: an absence — or a census — is a statement about the SEARCH; say where you looked).
#
# The distinction that matters:
#   LIVE      .softhouse/conformance.sh and .softhouse/guards/*  — run by the bar, every fire.
#   ARCHIVED  .softhouse/capture/**, .softhouse/reviews/**, .softhouse/handoff/**  — evidence
#             from finished tasks. They source this file too. They are NOT run by the bar and
#             a change here cannot redden one, but "three consumers" is false about them.
#
# It reads and reports. It writes nothing anywhere (patterns.md: probes never write).
# Exit: 0 census produced. 2 the census could not run.
set -u -o pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$REPO" || exit 2

SEL='^[[:space:]]*(\.|source)[[:space:]].*go-env\.sh'
echo "T272 — go-env.sh CONSUMER CENSUS"
echo "repo    : (path withheld: host state)"
echo "date    : $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo "selector: grep -rlE '$SEL' --include='*.sh' over the whole tree"
echo "          plus a SECOND selector for the indirect form (a path held in a variable),"
echo "          because the two guards source \$REPO_ROOT/.softhouse/bin/go-env.sh and the"
echo "          literal-path selector CANNOT see them. A one-selector census would have"
echo "          reported the two load-bearing guards as non-consumers."
echo

# --- selector 1: a literal `. .../go-env.sh` line -----------------------------------------
LIT="$(grep -rlE "$SEL" --include='*.sh' . 2>/dev/null | sed 's|^\./||' | sort)"
# --- selector 2: assigns the path to a variable, then sources the variable -----------------
VAR="$(grep -rlE 'go-env\.sh' --include='*.sh' . 2>/dev/null | sed 's|^\./||' | sort)"

rc_lit=$?; : "$rc_lit"
ALL="$(printf '%s\n%s\n' "$LIT" "$VAR" | grep -v '^$' | sort -u)"
[ -n "$ALL" ] || { echo "REFUSING: the selector matched NOTHING, which cannot be true — this file" >&2
                   echo "REFUSING: is sourced by the bar. A zero here is a broken selector, not a world fact." >&2
                   exit 2; }

live=0; arch=0; own=0; sete_live=0; sete_arch=0
echo "=== LIVE consumers (run by the bar) ==="
while IFS= read -r f; do
  case "$f" in
    .softhouse/bin/go-env.sh) own=$((own+1)); continue ;;
    .softhouse/capture/*|.softhouse/reviews/*|.softhouse/handoff/*) continue ;;
  esac
  # A file that only NAMES go-env.sh in prose is not a consumer. Require a sourcing line,
  # literal or via a variable that was assigned the path.
  if grep -qE "$SEL" "$f" 2>/dev/null; then :
  elif grep -qE '^[[:space:]]*(\.|source)[[:space:]]+"?\$' "$f" 2>/dev/null && grep -q 'go-env\.sh' "$f"; then :
  else continue; fi
  live=$((live+1))
  if grep -qE '^[[:space:]]*set[[:space:]]+-[a-z]*e' "$f"; then
    sete_live=$((sete_live+1)); tag='SET -e  <-- would ABORT on a strict refusal'
  else
    tag="$(grep -nE '^[[:space:]]*set[[:space:]]+-' "$f" | head -1 | sed 's/^[[:space:]]*//')"
    [ -n "$tag" ] || tag='(no `set -` line at all)'
  fi
  printf '  %-56s %s\n' "$f" "$tag"
done <<EOF
$ALL
EOF

echo
echo "=== ARCHIVED sourcers (evidence from finished tasks; the bar does not run them) ==="
while IFS= read -r f; do
  case "$f" in
    .softhouse/capture/*|.softhouse/reviews/*|.softhouse/handoff/*) ;;
    *) continue ;;
  esac
  grep -qE "$SEL" "$f" 2>/dev/null || continue
  arch=$((arch+1))
  if grep -qE '^[[:space:]]*set[[:space:]]+-[a-z]*e' "$f"; then
    sete_arch=$((sete_arch+1))
    printf '  %-70s SET -e\n' "$f"
  fi
done <<EOF
$ALL
EOF
echo "  (only the \`set -e\` ones are listed by name; the rest are counted below)"

echo
echo "------------------------------------------------------------------------"
echo "LIVE consumers                 : $live"
echo "  of which run under \`set -e\` : $sete_live"
echo "ARCHIVED sourcers              : $arch"
echo "  of which run under \`set -e\` : $sete_arch"
echo "go-env.sh itself               : $own (excluded)"
echo
echo "READ THIS THE RIGHT WAY. An archived script under \`set -e\` is NOT a live hazard:"
echo "GEREGE_GO_STRICT is set by no fire, so the one non-zero arm is unreachable unless a"
echo "human asks for it, and every one of these scripts predates the switch. It is listed"
echo "because 'all N consumers' is a claim about a SEARCH, and this is the search."
exit 0
