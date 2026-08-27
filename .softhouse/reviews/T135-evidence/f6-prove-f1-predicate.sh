#!/bin/sh
# T135 — F-6 item 1, driven for REAL rather than simulated.
# A reachable "died for an unrelated reason" on the PRE-FIX bytes: an invalid TENANT makes
# recapture.sh die at its identifier check, which prints "ABORT: TENANT=..." (NOT the string
# "ABORT: output directory") and creates nothing.  That is precisely the state the OLD predicate
# reads as "the guard admitted the attack".
set -u
P=/tmp/t135/f1/main/.softhouse/capture/pathb          # git archive ab2de89 = main's bytes
ATTACK=t36/out/recapture-default/sub-gerege
rm -rf "$P/$ATTACK"
out=$(cd "$P/t36" && TENANT='bad/tenant' RECAPTURE_OUT="$P/$ATTACK" PATH=/tmp/t135/f1/bin:$PATH \
        sh "$P/t36/recapture.sh" 2>&1)
echo "the run's output:"
printf '%s\n' "$out" | sed 's/^/    /'
echo
stamp=''
[ -f "$P/$ATTACK/CAPTURED-FROM-TENANT" ] && stamp=$(head -1 "$P/$ATTACK/CAPTURED-FROM-TENANT")
dir=no; [ -d "$P/$ATTACK" ] && dir=yes
echo "artefacts: attack directory present=$dir  stamp='$stamp'"
echo

# OLD predicate (T99's rescued bytes): set from the ABSENCE of one string.
if printf '%s\n' "$out" | LC_ALL=C grep -qa 'ABORT: output directory'; then old=0; else old=1; fi
# NEW predicate (T99b): absence PLUS the positive artefacts.
if ! printf '%s\n' "$out" | LC_ALL=C grep -qa 'ABORT: output directory' \
   && [ -d "$P/$ATTACK" ] && [ "$stamp" = gerege ]; then new=1; else new=0; fi
echo "OLD prove-f1 predicate  prefix_admitted = $old   <- 1 means 'the guard let the attack through'"
echo "NEW prove-f1 predicate  prefix_admitted = $new"
echo
[ "$old" = 1 ] && [ "$new" = 0 ] && \
  echo "RESULT: the old predicate reports the defect REPRODUCED from a run that wrote nothing;" && \
  echo "        the new one does not.  F-6 item 1 confirmed on real bytes, not simulated."
