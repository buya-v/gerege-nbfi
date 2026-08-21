#!/bin/sh
# T99 F-1 — THE OUTPUT-PATH GUARD COMPARED BASENAMES, SO THE HAZARD SURVIVED ONE DIRECTORY DOWN.
#
# T80 closed a mis-filing hazard at the top level: a `gerege` capture must not land in a directory
# named for `default`.  The guard it wrote tests the LEAF:
#     Obase=$(basename "$O"); case "$Obase" in "$TENANT" | *-"$TENANT" ) : ;; * ) die ... ;; esac
# `out/recapture-default/sub-gerege` has leaf `sub-gerege`, which matches `*-gerege`, so a real
# gerege capture lands INSIDE the default tenant's capture directory and the run exits 0.
#
# Both sides are run: the attack against main's bytes and against this branch's.
#   1a hermetic (docker/curl stubbed) — the guard's decision and its side effects.
#   1b LIVE against the reference oracle — the whole thing: exit 0, four captures filed under
#      `recapture-default/`.  It sends only POST …?command=calculateLoanSchedule (a pure
#      calculation) and read-only docker/psql queries, into a /tmp export: no committed evidence
#      and no oracle row is touched.  T99_LIVE=0 skips it.
#   1c the same basename-only shape in attest.py, found by sweeping rather than by the brief.
#   1d the happy path, because hardening that breaks it is not hardening.
. "$(dirname "$0")/lib.sh"

LIVE=${T99_LIVE:-1}
ATTACK=t36/out/recapture-default/sub-gerege

echo "=== T99 F-1 — a capture must not be filed one directory down inside another tenant's"
t99_export
t99_stubs
t99_pin "$P/t36/recapture.sh" "$PIN_PREFIX_RECAPTURE" recapture.sh
t99_pin "$P/t36/attest.py"    "$PIN_PREFIX_ATTEST"    attest.py
echo
echo "THE ATTACK:  TENANT=gerege RECAPTURE_OUT=<tree>/$ATTACK  sh t36/recapture.sh"
echo "             the leaf 'sub-gerege' matches *-gerege; the directory it sits IN is"
echo "             'recapture-default', which is another tenant's capture directory."
echo

prefix_admitted=0
fixed_refused=0

# ------------------------------------------------------------------ 1a. hermetic, both sides
for side in prefix fixed; do
  if [ "$side" = prefix ]; then TREE=$P; else TREE=$F; fi
  rm -rf "$TREE/$ATTACK"
  echo "--- 1a.$side — hermetic run (docker/curl stubbed, the shared oracle is untouched)"
  ( PATH=$EXPORT/stub:$PATH; export PATH
    TENANT=gerege RECAPTURE_OUT=$TREE/$ATTACK sh "$TREE/t36/recapture.sh" ) \
      > "$EXPORT/f1-$side.txt" 2>&1
  echo "EXIT=$?"
  if LC_ALL=C grep -qa 'ABORT: output directory' "$EXPORT/f1-$side.txt"; then
    echo "  guard verdict: REFUSED before anything ran —"
    LC_ALL=C grep -a 'ABORT: output directory' "$EXPORT/f1-$side.txt" | cut -c1-260 | sed 's/^/    /'
    if [ "$side" = fixed ]; then fixed_refused=1; fi
  else
    echo "  guard verdict: ADMITTED — the run proceeded past the output-path check into:"
    head -1 "$EXPORT/f1-$side.txt" | sed 's/^/    /'
  fi
  echo "  what now exists at $ATTACK:"
  if [ -d "$TREE/$ATTACK" ]; then
    find "$TREE/$ATTACK" -type f | sed "s|$TREE/||" | sort | sed 's/^/    /'
    if [ -f "$TREE/$ATTACK/CAPTURED-FROM-TENANT" ]; then
      echo "    ^ a '$(cat "$TREE/$ATTACK/CAPTURED-FROM-TENANT")' provenance stamp, written INSIDE recapture-default/"
    fi
  else
    echo "    (the directory was never created)"
  fi
  # T99b: `prefix_admitted` used to be set by the ABSENCE of the ABORT string, which is an
  # observation a run that never happened produces just as readily as a run the guard let past —
  # the very defect shape this task exists to remove.  It now requires the POSITIVE ARTEFACT: a
  # directory that was actually created one level inside `recapture-default/` and a provenance
  # stamp inside it reading `gerege`.  Nothing but a bypassed guard writes that.
  if [ "$side" = prefix ]; then
    stamp_txt=''
    [ -f "$TREE/$ATTACK/CAPTURED-FROM-TENANT" ] && stamp_txt=$(head -1 "$TREE/$ATTACK/CAPTURED-FROM-TENANT" | tr -d '\r')
    if ! LC_ALL=C grep -qa 'ABORT: output directory' "$EXPORT/f1-$side.txt" \
       && [ -d "$TREE/$ATTACK" ] && [ "$stamp_txt" = gerege ]; then
      prefix_admitted=1
    else
      echo "  (the pre-fix leg produced no misfiled artefact: directory present=$( [ -d "$TREE/$ATTACK" ] && echo yes || echo no ), stamp='$stamp_txt' — this proof is NOT demonstrating the defect)"
    fi
  fi
  echo
done

# ------------------------------------------------------------------ 1b. live, both sides
health=$(curl -sk --max-time 10 https://localhost:8443/fineract-provider/actuator/health 2>/dev/null)
case "$LIVE:$health" in
  1:*'"status":"UP"'*)
    echo "--- 1b.prefix — the SAME attack against the LIVE reference oracle, pre-fix bytes"
    rm -rf "$P/$ATTACK"
    TENANT=gerege RECAPTURE_OUT=$P/$ATTACK sh "$P/t36/recapture.sh" > "$EXPORT/f1-live-prefix.txt" 2>&1
    live_exit=$?
    echo "EXIT=$live_exit"
    echo "  preconditions: $(LC_ALL=C grep -ac '^  PASS' "$EXPORT/f1-live-prefix.txt") PASS, $(LC_ALL=C grep -ac '^  FAIL' "$EXPORT/f1-live-prefix.txt") FAIL"
    LC_ALL=C grep -a '^B-0' "$EXPORT/f1-live-prefix.txt" | sed "s|$P/||" | sed 's/^/  /'
    echo "  now inside the default tenant's capture directory:"
    find "$P/t36/out/recapture-default" -type f | sed "s|$P/||" | sort | sed 's/^/    /'
    if [ "$live_exit" = 0 ] && [ -f "$P/$ATTACK/B-01-baseline-raw.json" ]; then
      echo "  VERDICT: EXIT 0, four real oracle captures and a 'gerege' stamp, filed one directory"
      echo "           down inside 'recapture-default'.  Nothing downstream can tell."
    else
      echo "  VERDICT: the live run did not complete (exit $live_exit) — the hermetic 1a result stands alone."
    fi
    echo
    echo "--- 1b.fixed — the same live invocation against this branch's bytes"
    rm -rf "$F/$ATTACK"
    TENANT=gerege RECAPTURE_OUT=$F/$ATTACK sh "$F/t36/recapture.sh" > "$EXPORT/f1-live-fixed.txt" 2>&1
    echo "EXIT=$?"
    head -1 "$EXPORT/f1-live-fixed.txt" | cut -c1-260 | sed 's/^/  /'
    echo "  captures written: $(find "$F/$ATTACK" -type f 2>/dev/null | wc -l | tr -d ' ')"
    ;;
  *)
    echo "--- 1b SKIPPED: T99_LIVE=$LIVE, oracle health answered: ${health:-<no answer>}"
    echo "    Reported as skipped.  A skipped live leg is never reported as a pass."
    ;;
esac
echo

# --------------------------------------------------- 1c. the same defect in attest.py (P-12 sweep)
echo "--- 1c — the same basename-only shape at attest.py:51, found by sweeping for the SHAPE"
for side in prefix fixed; do
  if [ "$side" = prefix ]; then TREE=$P; else TREE=$F; fi
  out=$(ATTEST_OUT=$TREE/$ATTACK python3 "$TREE/t36/attest.py" gerege 2>&1 | head -1)
  case "$out" in
    ABORT:*) echo "  $side:   REFUSED — $(echo "$out" | cut -c1-200)…" ;;
    *)       echo "  $side:   ADMITTED — first line: $(echo "$out" | cut -c1-200)" ;;
  esac
done
echo

# ----------------------------------------------------------------- 1d. the happy path still works
echo "--- 1d — hardening that breaks the happy path is not hardening (fixed bytes, guard only)"
for want in "t36/out/recapture-gerege:the default derivation" \
            "t80/out/attest-gerege:an explicit t80-style directory" \
            "t22-probe/out/x-gerege:another task directory"; do
  d=${want%%:*}; label=${want#*:}
  ( PATH=$EXPORT/stub:$PATH; export PATH
    TENANT=gerege RECAPTURE_OUT=$F/$d sh "$F/t36/recapture.sh" ) > "$EXPORT/f1-happy.txt" 2>&1
  if LC_ALL=C grep -qa 'ABORT: output directory' "$EXPORT/f1-happy.txt"; then
    echo "  REFUSED (UNEXPECTED)  $d — $label"
    fixed_refused=0
  else
    echo "  accepted              $d — $label"
  fi
done

t99_verdict "$prefix_admitted" "$fixed_refused" "F-1 (basename-only output-path guard)"
