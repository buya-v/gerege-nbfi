#!/bin/sh
# T138 — V-F, pinned precisely.  T115 states the hazard as "a read-only $O would
# leave the previous run's files and grade STALE bytes".  A shell redirect to an
# EXISTING file does not need directory write permission, so the condition has to
# be stated more exactly than that.  Three sub-cases, measured.
set -u
W=${1:?workdir}
PRE=$W/pre/.softhouse/capture/t91/shell-invariance.sh
POST=$W/post/.softhouse/capture/t91/shell-invariance.sh

mk() {  # mk <dir>  — one pair that genuinely DIFFERS
  rm -rf "$1"; mkdir -p "$1/z-sh" "$1/z-bash"
  printf 'AAA\nEXIT=0\n' > "$1/z-sh/A1.txt"
  printf 'BBB DIFFERENT\nEXIT=1\n' > "$1/z-bash/A1.txt"
}

echo "=== CASE 0  control: writable \$O, no stale scratch"
mk "$W/vf0"; sh "$PRE" "$W/vf0" z; echo "PRE_EXIT=$?"; echo

echo "=== CASE 1  \$O dir mode 555, NO pre-existing scratch"
mk "$W/vf1"; chmod 555 "$W/vf1"
sh "$PRE" "$W/vf1" z 2>&1; echo "PRE_EXIT=$?"; chmod 755 "$W/vf1"
echo "   -> the redirect cannot CREATE the file; diff has no input; fail-closed (false DIFFERS)."; echo

echo "=== CASE 2  \$O dir mode 555, stale scratch present and WRITABLE (mode 644)"
mk "$W/vf2"; printf 'STALE\n' > "$W/vf2/.inv-a"; printf 'STALE\n' > "$W/vf2/.inv-b"
chmod 644 "$W/vf2/.inv-a" "$W/vf2/.inv-b"; chmod 555 "$W/vf2"
sh "$PRE" "$W/vf2" z 2>&1; echo "PRE_EXIT=$?"; chmod 755 "$W/vf2"
echo "   -> redirect to an EXISTING writable file succeeds; the difference IS caught."; echo

echo "=== CASE 3  \$O dir mode 555 AND stale scratch mode 444 (a read-only checkout / RO mount)"
mk "$W/vf3"; printf 'STALE\n' > "$W/vf3/.inv-a"; printf 'STALE\n' > "$W/vf3/.inv-b"
chmod 444 "$W/vf3/.inv-a" "$W/vf3/.inv-b"; chmod 555 "$W/vf3"
sh "$PRE" "$W/vf3" z 2>&1; echo "PRE_EXIT=$?"
echo "   <- THIS is the vacuous pass: it graded the STALE bytes and reported agreement."
chmod 755 "$W/vf3"; chmod 644 "$W/vf3/.inv-a" "$W/vf3/.inv-b"; echo

echo "=== CASE 3', same directory, POST-fix script"
chmod 444 "$W/vf3/.inv-a" "$W/vf3/.inv-b"; chmod 555 "$W/vf3"
sh "$POST" "$W/vf3" z 2>&1; echo "POST_EXIT=$?"
chmod 755 "$W/vf3"; chmod 644 "$W/vf3/.inv-a" "$W/vf3/.inv-b"; echo

echo "=== CASE 4  the same shape without any directory permissions at all:"
echo "    scratch files left read-only by an earlier interrupted run, \$O writable"
mk "$W/vf4"; printf 'STALE\n' > "$W/vf4/.inv-a"; printf 'STALE\n' > "$W/vf4/.inv-b"
chmod 444 "$W/vf4/.inv-a" "$W/vf4/.inv-b"
sh "$PRE" "$W/vf4" z 2>&1; echo "PRE_EXIT=$?"
chmod 644 "$W/vf4/.inv-a" "$W/vf4/.inv-b"
echo "   -> a read-only \$O is NOT required; read-only SCRATCH FILES are enough."
