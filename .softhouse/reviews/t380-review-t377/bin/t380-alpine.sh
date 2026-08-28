#!/bin/bash
# T380 — INDEPENDENT re-run of T377's busybox closure. Two measurements, and a CONTROL that
# is the point: the SAME file with the resolver forced back to the literal `/usr/bin/mktemp`
# must REFUSE, so the resolver is demonstrably the only difference.
set -uo pipefail
SUBJ="${SUBJ:-/tmp/t380-subject/.softhouse/bin/fire-program.sh}"
W="${W:-/tmp/t380-alpine}"
rm -rf "$W"; mkdir -p "$W"
cp "$SUBJ" "$W/fire-program.sh"
# The control: undo the resolver, restoring `main`'s hard-coded spelling.
sed 's|^FIRE_MKTEMP="\${FIRE_MKTEMP:-/usr/bin/mktemp}"$|FIRE_MKTEMP="/usr/bin/mktemp"|; s|^  if \[\[ -x "\$_c" \]\]; then FIRE_MKTEMP="\$_c"; break; fi$|  :|' \
  "$W/fire-program.sh" > "$W/fire-program-forced.sh"
# belt and braces: force the value unconditionally at the end of the resolver block
python3 - "$W/fire-program-forced.sh" <<'PY'
import sys
p=sys.argv[1]; s=open(p,encoding="utf-8").read()
a='FIRE_MKTEMP="${FIRE_MKTEMP:-/usr/bin/mktemp}"'
assert s.count(a)==1, s.count(a)
open(p,"w",encoding="utf-8").write(s.replace(a,'FIRE_MKTEMP=/usr/bin/mktemp   # T380 CONTROL: main\'s hard-coded spelling',1))
PY
echo "=== step 1: busybox userland — where is mktemp?"
docker run --rm alpine:3 ls -l /usr/bin/mktemp /bin/mktemp 2>&1

echo
echo "=== step 2: PROVISIONED alpine (apk add zsh python3), SHIPPED file (resolver ON)"
docker run --rm -v "$W:/w:ro" alpine:3 sh -c \
  'apk add --no-cache --quiet zsh python3 >/dev/null 2>&1 || { echo "APK FAILED (no network?)"; exit 90; }
   ls -l /bin/zsh /usr/bin/python3 2>&1 | sed "s/^/  /"
   /bin/zsh /w/fire-program.sh --self-test-lock-readers 2>&1 | tail -3
   echo "SELFTEST rc=${PIPESTATUS[0]}"' 2>&1

echo
echo "=== step 3: CONTROL — same file, resolver forced back to the literal /usr/bin/mktemp"
docker run --rm -v "$W:/w:ro" alpine:3 sh -c \
  'apk add --no-cache --quiet zsh python3 >/dev/null 2>&1 || { echo "APK FAILED (no network?)"; exit 90; }
   /bin/zsh /w/fire-program-forced.sh --self-test-lock-readers 2>&1 | tail -3
   echo "SELFTEST rc=${PIPESTATUS[0]}"' 2>&1
