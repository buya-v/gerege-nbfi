#!/usr/bin/env bash
# T446 — arm RWB3: does `guard_registration_decisive_lines` actually watch the line
# that decides, or only a line that mentions the same words?
#
# T445 pins SEVEN decisive lines by CONTENT and evaluates TWO of them. Five are
# protected by text-matching alone, and the pin for "the WITNESS naming test reads the
# TRACKED BLOB" sits on the ASSIGNMENT `self_text="$( … git cat-file blob "$self_blob" … )"`,
# not on the `grep` that uses it. So the assignment can stay, the pin stays satisfied,
# and the deciding grep can be pointed back at this host in ONE substitution.
#
# This arm makes exactly that substitution, on the T445 TIP, over T444's own M-1
# fixture, and runs the whole bar.
set -u
WORK="${1:?}"; SRC="${2:?}"; REF="${3:?}"; ARM="${4:-RWB3}"
G=".softhouse/guards"; CONFREL=".softhouse/conformance.sh"
MEMBER="zz-t446-member.sh"

rm -rf "$WORK/$ARM"; mkdir -p "$WORK/$ARM"
S="$WORK/$ARM/seed"; C="$WORK/$ARM/graded"; CWD="$WORK/$ARM/cwd"; mkdir -p "$CWD"
git clone -q "$SRC" "$S" || exit 1
( cd "$S" && git checkout -q "$REF" ) || exit 1

# --- T444's M-1 fixture -------------------------------------------------------------
{ printf '#!/usr/bin/env bash\n'
  printf '# a scratch checker planted by the T446 RWB3 arm\n'
  printf '# GUARDS-DIR-REGISTRATION: REACHED-BY %s/W.txt\n' "$G"
  printf 'exit 0\n'; } > "$S/$G/$MEMBER"
chmod +x "$S/$G/$MEMBER"
{ printf 'a decoy witness. it names nothing.\n'; printf 'end.\n'; } > "$S/$G/W.txt"

# --- the one-line evasion, applied ONLY for the ATTACK arm --------------------------
if [ "$ARM" = "RWB3" ]; then
  python3 - "$S/$CONFREL" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = 'elif ! LC_ALL=C grep -qF -- "$base" <<<"$self_text"; then'
new = 'elif ! LC_ALL=C grep -qF -- "$base" "$REPO_ROOT/$self_norm"; then'
assert s.count(old) == 1, s.count(old)
open(p, 'w', encoding='utf-8').write(s.replace(old, new))
PYEOF
  if ! LC_ALL=C grep -q 'grep -qF -- "\$base" "\$REPO_ROOT/\$self_norm"' "$S/$CONFREL"; then
    echo "SUBSTITUTION DID NOT APPLY"; exit 1
  fi
fi

( cd "$S" && git add -A ) || exit 1
BLOB="$( cd "$S" && printf '%s' "$MEMBER" | git hash-object -w --stdin )" || exit 1
( cd "$S" && git update-index --add --cacheinfo "120000,$BLOB,$G/w.txt" ) || exit 1
( cd "$S" && git -c user.email=t446@local -c user.name=t446 commit -q -m "T446 RWB3 fixture" ) || exit 1
git clone -q "$S" "$C" 2>"$WORK/$ARM/clonewarn" || exit 1

echo "================================ arm $ARM ================================"
echo "the deciding grep, as deployed in the graded tree:"
LC_ALL=C grep -n 'grep -qF -- "\$base" ' "$C/$CONFREL" | sed 's/^/    /'
echo "the pinned needle for it is still present in the executable text? (assignment line)"
LC_ALL=C grep -c 'git cat-file blob "\$self_blob"' "$C/$CONFREL" | sed 's/^/    occurrences = /'
echo "index around the collision:"
( cd "$C" && git ls-files -s -- "$G" | LC_ALL=C grep -i 'w.txt\|zz-t446' | sed 's/^/    /' )
echo "clone warnings:"; sed 's/^/    /' "$WORK/$ARM/clonewarn"
echo "git status --porcelain:"; ( cd "$C" && git status --porcelain | sed 's/^/    /' )
echo "what a FILESYSTEM read of $G/W.txt returns in the graded tree:"
( cd "$C" && cat "$G/W.txt" | sed 's/^/    /' )

RC=0
( cd "$CWD" && bash "$C/$CONFREL" ) > "$WORK/$ARM/bar.log" 2>&1 || RC=$?
N="$(LC_ALL=C grep -c 'probe = ' "$WORK/$ARM/bar.log" || true)"
echo "EXIT = $RC"
echo "probe line count (read BEFORE its value) = $N"
if [ "$N" -ge 1 ]; then echo "probe value = $(LC_ALL=C grep -m1 'probe = ' "$WORK/$ARM/bar.log" | sed 's/.*probe = //')"
else echo "probe value = ABSENT"; fi
# COUNT FIRST, THEN READ -- for the VERDICT line and the census line exactly as for the
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
if [ "$NC" -ge 1 ]; then LC_ALL=C grep -m1 'GUARDS-DIR-REGISTRATION: population=' "$WORK/$ARM/bar.log"; fi
echo "--- what the NEW watch reported ---"
LC_ALL=C grep -n 'registration decisive' "$WORK/$ARM/bar.log" | sed 's/^/    /'
echo "--- registration sentences ---"
LC_ALL=C grep -n 'guards_dir_registration\|guards-dir registration\|REACHED-BY \|verified: it names' "$WORK/$ARM/bar.log" | head -20
