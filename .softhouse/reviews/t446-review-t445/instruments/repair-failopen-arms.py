import subprocess, sys, os

ROOT = "/Users/buv/gerege-nbfi/.claude/worktrees/agent-a3c527271d46c1b56/.softhouse/reviews/t446-review-t445/instruments"

OLD_TAIL = '''LC_ALL=C grep -m1 '^VERDICT' "$WORK/$ARM/bar.log" || echo "VERDICT = (none)"
LC_ALL=C grep -m1 'GUARDS-DIR-REGISTRATION: population=' "$WORK/$ARM/bar.log" || echo "(no census line)"'''

NEW_TAIL = '''# COUNT FIRST, THEN READ -- for the VERDICT line and the census line exactly as for the
# probe line. `grep … || echo "(none)"` prints a negative it did not measure and cannot
# tell "the line is absent" from "the log is absent", which is T238's C2 fail-open arm
# and P-84's own mistake one file over. An absent log is an INSTRUMENT failure and exits.
if [ ! -s "$WORK/$ARM/bar.log" ]; then
  echo "INSTRUMENT FAILURE: $WORK/$ARM/bar.log is missing or empty. Nothing was measured."
  exit 3
fi
NV="$(LC_ALL=C grep -c '^VERDICT' "$WORK/$ARM/bar.log")" || NV=0
echo "VERDICT line count = $NV"
if [ "$NV" -ge 1 ]; then LC_ALL=C grep -m1 '^VERDICT' "$WORK/$ARM/bar.log"; fi
NC="$(LC_ALL=C grep -c 'GUARDS-DIR-REGISTRATION: population=' "$WORK/$ARM/bar.log")" || NC=0
echo "census line count  = $NC"
if [ "$NC" -ge 1 ]; then LC_ALL=C grep -m1 'GUARDS-DIR-REGISTRATION: population=' "$WORK/$ARM/bar.log"; fi'''

OLD_HASH = '''echo "    identical to the committed blob? $( cd "$C" && [ "$(git rev-parse "HEAD:$CONFREL")" = "$(git hash-object "$CONFREL")" ] && echo YES || echo '*** NO ***' )"'''

NEW_HASH = '''# The two hashes are read into names and compared in the open, so an EMPTY hash --
# which `[ "$a" = "$b" ] && echo YES || echo NO` would silently report as a difference,
# or as a match if both were empty -- is its own refusal (T238 C2).
CB="$( cd "$C" && git rev-parse "HEAD:$CONFREL" )" || CB=""
WB="$( cd "$C" && git hash-object "$CONFREL" )" || WB=""
if [ -z "$CB" ] || [ -z "$WB" ]; then
  echo "INSTRUMENT FAILURE: one of the two hashes is EMPTY (committed='$CB' materialised='$WB')."
  exit 3
elif [ "$CB" = "$WB" ]; then
  echo "    identical to the committed blob? YES"
else
  echo "    identical to the committed blob? *** NO ***"
fi'''

for name in ("drive-longs.sh", "drive-rwb3.sh", "drive-rwb3-v2.sh", "drive-rwb3-v3.sh"):
    p = os.path.join(ROOT, name)
    s = open(p, encoding="utf-8").read()
    before = subprocess.run(["shasum", "-a", "256", p], capture_output=True, text=True).stdout.split()[0]
    n = 0
    if OLD_TAIL in s:
        s = s.replace(OLD_TAIL, NEW_TAIL); n += 1
    if OLD_HASH in s:
        s = s.replace(OLD_HASH, NEW_HASH); n += 1
    open(p, "w", encoding="utf-8").write(s)
    after = subprocess.run(["shasum", "-a", "256", p], capture_output=True, text=True).stdout.split()[0]
    print(f"{name}: {n} arm(s) repaired  {before} -> {after}")
