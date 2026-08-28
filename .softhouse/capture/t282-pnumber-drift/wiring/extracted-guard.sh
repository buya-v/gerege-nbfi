#!/usr/bin/env bash
warn(){ echo "$@" >&2; }
say(){ echo "$@"; }
REPO_ROOT=.
# ---------------------------------------------------------------------------
# T282 — P-NUMBER CITATION DRIFT.  The predicate is the SENTENCE, never the id:
# a guard asking only "is P-n defined?" returns PASS on every recorded instance
# of this defect, because every drifted citation names an id that EXISTS.
# Demonstrated at .softhouse/capture/t282-pnumber-drift/red/20-existence-only-on-RED.txt.
# ---------------------------------------------------------------------------
guard_pnumber_citations() {
  local chk="$REPO_ROOT/.softhouse/capture/t282-pnumber-drift/bin/check-pnumber-citations.py"
  if [ ! -f "$chk" ]; then
    warn "conformance: THE P-NUMBER CITATION CHECKER IS ABSENT: $chk"
    warn "conformance: it is wired into this guard, so its absence is a REFUSAL and never a pass."
    return 1
  fi
  local out rc
  out="$(mktemp "${TMPDIR:-/tmp}/conformance-pnumber.XXXXXXXXXX")" || return 1

  # SELFTEST FIRST. A checker whose predicate has stopped discriminating would
  # report a clean tree in exactly the same words as a clean tree (P-22: a
  # control that cannot fail is worse than none, because it is believed).
  if ! ( cd "$REPO_ROOT" && python3 "$chk" --selftest ) >"$out" 2>&1; then
    warn "conformance: the P-number citation checker FAILED ITS OWN SELFTEST. Its verdict on this"
    warn "conformance: tree is worthless until that is fixed."
    LC_ALL=C sed -n '1,20p' "$out" >&2
    rm -f "$out"; return 1
  fi

  ( cd "$REPO_ROOT" && python3 "$chk" ) >"$out" 2>&1
  rc=$?

  # PRESENCE BEFORE VALUE (P-84): a verdict line that was never PRINTED is a
  # crash, and it must never be read as a clean run.
  if ! LC_ALL=C grep -aqE '^PNUMBER-CITATIONS: VERDICT ' "$out"; then
    warn "conformance: the P-number citation checker printed NO VERDICT line (exit $rc). It did not"
    warn "conformance: run, or did not finish. Silence here reads exactly like a clean register."
    LC_ALL=C sed -n '1,20p' "$out" >&2
    rm -f "$out"; return 1
  fi
  if [ "$rc" -ne 0 ] && [ "$rc" -ne 1 ]; then
    warn "conformance: the P-number citation checker exited $rc, which is neither clean (0) nor"
    warn "conformance: violations (1). 3 is its own refusal-to-run; anything else is a crash."
    LC_ALL=C sed -n '1,20p' "$out" >&2
    rm -f "$out"; return 1
  fi

  LC_ALL=C grep -aE '^PNUMBER-CITATIONS: (register|sites|skipped|declared|  )' "$out" \
    | while IFS= read -r l; do say "$l"; done
  if [ "$rc" -ne 0 ]; then
    warn "conformance: A CITED P-NUMBER CARRIES A RULE SENTENCE THAT patterns.md DEFINES UNDER A"
    warn "conformance: DIFFERENT NUMBER, in a DIRECTIVE file — a file that instructs future workers."
    LC_ALL=C grep -aE '^PNUMBER-CITATIONS: (FATAL|VERDICT)' "$out" >&2
    rm -f "$out"; return 1
  fi
  say "conformance:   P-number citations: VERDICT PASS (evidence-zone drift is REPORTED, never"
  say "conformance:   fatal, and is corrected FORWARD in the patterns.md errata — never in place)."
  rm -f "$out"
  return 0
}
guard_pnumber_citations; echo "GUARD RETURNED $?"
