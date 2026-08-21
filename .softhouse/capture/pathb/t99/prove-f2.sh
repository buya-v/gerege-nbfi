#!/bin/sh
# T99 F-2 — A PATH-POISONED `shasum` DEFEATS THE DIGEST PIN, AND LEAVES NO DIFF TRACE.
#
# T80 replaced T76's substring pin with a digest comparison, which is the right shape.  It then
# computed the digest with a BARE WORD:
#     creqsha=$(shasum -a 256 "$CANARY_REQ" | cut -d' ' -f1)          # preconditions.sh:195
# A `shasum` earlier on $PATH that prints the pinned constant makes both operands the attacker's,
# and this is WORSE than the tautology it replaced: the recipe looks hardened, the transcript says
# "PASS  canary request pinned by DIGEST COMPARISON", and no file in the repository changes.
#
# Both sides are run.  The live legs send only POST …?command=calculateLoanSchedule (a pure
# calculation) and read-only docker/psql queries; nothing is written to the oracle.  T99_LIVE=0
# skips them and says so.
#
# Legs:
#   2a  the attack itself, live, pre-fix vs fixed — a mutated canary certified as the pinned tie.
#   2b  the fixed instrument under the SAME poisoned PATH with the REAL canary: still passes, so
#       the hardening is not just "refuse everything".
#   2c  known-answer test: a tool that constant-returns the pin never gets to answer.
#   2d  cross-check: a CLEVER liar that passes the KAT and lies on the target is caught by
#       disagreement between two independent implementations.
#   2e  no diff trace: the attack leaves the repository byte-identical.
. "$(dirname "$0")/lib.sh"

LIVE=${T99_LIVE:-1}
SH=${T99_SH:-sh}
PIN=2a6621beb48f753c5a078b0b6ca775c317d36f815f08be3c6ce6e8ab93352154

echo "=== T99 F-2 — the digest pin must not be answerable by \$PATH"
echo "recipe interpreter under test: $SH"
# Snapshot the repository state BEFORE anything below runs.  Leg 2e measures the DELTA, not the
# absolute list: when this proof is driven by run-all.sh the runner's own in-flight transcript
# files are present in `git status`, and reporting those as "changes the attack made" would be a
# false positive of exactly the kind this task exists to remove.
git -C "$REPO" status --porcelain > "${TMPDIR:-/tmp}/t99-f2-status-before.$$"
t99_export
t99_pin "$P/t36/preconditions.sh" "$PIN_PREFIX_PRECOND" preconditions.sh
echo

# ---------------------------------------------------------------- the attacker's tools
cat > "$EXPORT/poison/shasum" <<EOF
#!/bin/sh
# A PATH-poisoned shasum: answers the PINNED digest for whatever it is handed, in the exact output
# shape the real tool uses, so \`… | cut -d' ' -f1\` yields the pin for ANY file.
echo "$PIN  \${*##* }"
EOF
cat > "$EXPORT/poison/liar-const" <<EOF
#!/bin/sh
# A liar that constant-returns the pin, including for the known-answer vectors.
echo "$PIN  \${*##* }"
EOF
cat > "$EXPORT/poison/liar-clever" <<EOF
#!/bin/sh
# A liar that DELEGATES the known-answer vectors to the real tool (so it passes any self-test that
# only checks published vectors) and lies about everything else.  This is the attack a KAT alone
# does not stop, and the reason two independent implementations must agree.
f=\$3
sz=\$(/usr/bin/stat -f %z "\$f" 2>/dev/null || /usr/bin/stat -c %s "\$f" 2>/dev/null || echo 999)
if [ "\$sz" -le 3 ]; then exec /usr/bin/shasum -a 256 "\$f"; fi
echo "$PIN  \$f"
EOF
chmod +x "$EXPORT/poison/shasum" "$EXPORT/poison/liar-const" "$EXPORT/poison/liar-clever"

sed 's/"principal": 1162502.5,/"principal": 1162502.55,/' \
  "$F/t22-audit/req/calc-pmode2-gerege.json" > "$EXPORT/mutated-canary.json"
sha256_file "$EXPORT/mutated-canary.json" || t99_die "cannot digest the mutated canary"
MUT=$SHA256_RESULT
echo "the mutated canary: one character, 1162502.5 -> 1162502.55 (T77's exploit request)"
echo "  true sha256   $MUT"
echo "  pinned sha256 $PIN"
echo "  what the poisoned shasum says for it: $(PATH=$EXPORT/poison:$PATH shasum -a 256 "$EXPORT/mutated-canary.json" | cut -d' ' -f1)"
echo

prefix_admitted=0
fixed_refused=0

# ------------------------------------------------------------------------ 2a. the attack, live
health=$(curl -sk --max-time 10 https://localhost:8443/fineract-provider/actuator/health 2>/dev/null)
case "$LIVE:$health" in
  1:*'"status":"UP"'*)
    for side in prefix fixed; do
      if [ "$side" = prefix ]; then TREE=$P; else TREE=$F; fi
      echo "--- 2a.$side — PATH=<poison>:\$PATH  CANARY_REQ=<mutated>  $SH t36/preconditions.sh gerege"
      ( PATH=$EXPORT/poison:$PATH; export PATH
        CANARY_REQ=$EXPORT/mutated-canary.json "$SH" "$TREE/t36/preconditions.sh" gerege ) \
          > "$EXPORT/f2-$side.txt" 2>&1
      st=$?
      echo "EXIT=$st"
      echo "  PASS lines: $(LC_ALL=C grep -ac '^  PASS' "$EXPORT/f2-$side.txt")   FAIL lines: $(LC_ALL=C grep -ac '^  FAIL' "$EXPORT/f2-$side.txt")"
      LC_ALL=C grep -a 'DIGEST COMPARISON\|DIGEST MISMATCH\|instrument\|effective rounding' "$EXPORT/f2-$side.txt" \
        | cut -c1-250 | sed 's/^/    /'
      LC_ALL=C grep -a 'ALL PRECONDITIONS HOLD\|PRECONDITIONS BREACHED' "$EXPORT/f2-$side.txt" | sed 's/^/    /'
      if [ "$side" = prefix ]; then
        if [ "$st" = 0 ] && LC_ALL=C grep -qa 'PASS  canary request pinned by DIGEST COMPARISON' "$EXPORT/f2-$side.txt" \
           && LC_ALL=C grep -qa 'PASS  effective rounding mode canary' "$EXPORT/f2-$side.txt"; then
          prefix_admitted=1
          echo "  VERDICT: the pin passed on a file whose true sha256 is $MUT, the canary was SENT,"
          echo "           and the run reported ALL PRECONDITIONS HOLD.  The strongest assertion in"
          echo "           the recipe was graded against a request the pin exists to refuse."
        else
          echo "  VERDICT: the attack did not reproduce on the pre-fix bytes."
        fi
      else
        if [ "$st" != 0 ] && LC_ALL=C grep -qa 'DIGEST MISMATCH' "$EXPORT/f2-$side.txt" \
           && ! LC_ALL=C grep -qa 'PASS  effective rounding mode canary' "$EXPORT/f2-$side.txt"; then
          fixed_refused=1
          echo "  VERDICT: digest mismatch, canary NOT sent, run breached.  The poisoned \$PATH was"
          echo "           never consulted: the instrument resolves its tools absolutely."
        else
          echo "  VERDICT: the fixed bytes did not refuse the attack."
        fi
      fi
      echo
    done

    # --------------------------------------------- 2b. same poison, the REAL canary: must pass
    echo "--- 2b.fixed — same poisoned \$PATH, the REAL pinned canary: hardening must not just refuse"
    ( PATH=$EXPORT/poison:$PATH; export PATH
      CANARY_REQ=$F/t22-audit/req/calc-pmode2-gerege.json "$SH" "$F/t36/preconditions.sh" gerege ) \
        > "$EXPORT/f2-control.txt" 2>&1
    echo "EXIT=$?"
    LC_ALL=C grep -a 'DIGEST COMPARISON\|effective rounding mode canary\|ALL PRECONDITIONS HOLD' \
      "$EXPORT/f2-control.txt" | cut -c1-250 | sed 's/^/    /'
    echo
    ;;
  *)
    echo "--- 2a/2b SKIPPED: T99_LIVE=$LIVE, oracle health answered: ${health:-<no answer>}"
    echo "    A skipped leg is never reported as a pass; the hermetic legs below still run."
    echo
    ;;
esac

# ------------------------------------------------------ 2c. known-answer test excludes a liar
echo "--- 2c — a tool that constant-returns the pin never gets to answer (known-answer test)"
(
  . "$F/t36/sha256.sh"
  _sha256_path() {
    case "$1" in
      shasum) echo "$EXPORT/poison/liar-const"; return 0 ;;
      sha256sum) echo /sbin/sha256sum; return 0 ;;
      openssl) echo /usr/bin/openssl; return 0 ;;
      python3) echo /usr/bin/python3; return 0 ;;
    esac
    return 1
  }
  sha256_init
  echo "  tools that survived the KAT: $SHA256_TOOLS"
  case "$SHA256_TOOLS" in
    *liar-const*) echo "  RESULT: the liar SURVIVED — the known-answer test does not work" ;;
    *)            echo "  RESULT: the liar was excluded before it could answer anything" ;;
  esac
  if sha256_file "$EXPORT/mutated-canary.json"; then
    echo "  digest of the mutated canary from the survivors: $SHA256_RESULT (used: $SHA256_USED)"
    [ "$SHA256_RESULT" = "$MUT" ] && echo "  and it is the TRUE digest, not the pin."
  fi
)
echo

# ------------------------------------- 2d. cross-check catches a liar that passes the KAT
echo "--- 2d — a liar that PASSES the known-answer test is caught by cross-implementation"
echo "         disagreement (this is why one hardened tool would not have been enough)"
(
  . "$F/t36/sha256.sh"
  _sha256_path() {
    case "$1" in
      shasum) echo "$EXPORT/poison/liar-clever"; return 0 ;;
      sha256sum) echo /sbin/sha256sum; return 0 ;;
      openssl) echo /usr/bin/openssl; return 0 ;;
      python3) echo /usr/bin/python3; return 0 ;;
    esac
    return 1
  }
  sha256_init
  echo "  tools that survived the KAT: $SHA256_TOOLS"
  case "$SHA256_TOOLS" in
    *liar-clever*) echo "  the clever liar PASSED the known-answer test, as designed" ;;
    *)             echo "  the clever liar failed the KAT (unexpected for this leg)" ;;
  esac
  if sha256_file "$EXPORT/mutated-canary.json"; then
    echo "  RESULT: it answered $SHA256_RESULT and was BELIEVED — cross-checking did not fire"
  else
    echo "  RESULT: REFUSED, no digest returned —"
    echo "    $SHA256_ERROR" | cut -c1-250
  fi
)
echo

# ------------------------------------------------------------------- 2e. the no-diff-trace part
echo "--- 2e — the attack leaves NO DIFF TRACE, which is what makes it worse than the tautology"
git -C "$REPO" status --porcelain > "${TMPDIR:-/tmp}/t99-f2-status-after.$$"
echo "  repository paths that CHANGED STATE while the attack above ran:"
diff "${TMPDIR:-/tmp}/t99-f2-status-before.$$" "${TMPDIR:-/tmp}/t99-f2-status-after.$$" \
  | LC_ALL=C grep -a '^[<>]' | LC_ALL=C grep -av 't99/out/' | sed 's/^/    /'
n=$(diff "${TMPDIR:-/tmp}/t99-f2-status-before.$$" "${TMPDIR:-/tmp}/t99-f2-status-after.$$" \
      | LC_ALL=C grep -a '^[<>]' | LC_ALL=C grep -avc 't99/out/')
rm -f "${TMPDIR:-/tmp}/t99-f2-status-before.$$" "${TMPDIR:-/tmp}/t99-f2-status-after.$$"
echo "  count: $n   (t99/out/ excluded: those are this proof's OWN transcripts being written)"
echo "  (the poisoned tool lives on \$PATH; nothing a reviewer diffs would ever show it)"

t99_verdict "$prefix_admitted" "$fixed_refused" "F-2 (PATH-poisoned digest instrument)"
