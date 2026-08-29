#!/usr/bin/env bash
# T440: attack the CONSTRUCTION of T424's amended guard, rather than re-measuring its arms.
set -uo pipefail
PATCH="$1"
WORK=$(mktemp -d "${TMPDIR:-/tmp}/t440-attack.XXXXXXXX") || exit 2
trap 'rm -rf "$WORK"' EXIT
fails=0
ok(){ printf '  [OK]   %s\n' "$1"; }
no(){ printf '  [FINDING] %s\n' "$1"; fails=$((fails+1)); }

echo "T440 CONSTRUCTION ATTACK on the amended FU-T386-7 guard"
echo "bash: $BASH_VERSION   host tee: $(command -v tee)"
echo

echo "== A1: does bash really WAIT for every pipeline member, in the forms used here? =="
# A slow writer: it sleeps AFTER its producer has exited, then writes the payload.
cat > "$WORK/slowtee" <<'EOF'
#!/usr/bin/env python3
import sys, time
p = sys.argv[1]
data = sys.stdin.read()
time.sleep(1.0)                # producer is long gone by now
open(p, "w").write(data)       # payload lands only at the very end
EOF
chmod +x "$WORK/slowtee"
: > "$WORK/a1.log"
start=$(date +%s)
printf 'PAYLOAD\n' | "$WORK/slowtee" "$WORK/a1.log"
after=$(cat "$WORK/a1.log")
end=$(date +%s)
printf '  after the pipeline returned: file=[%s]  elapsed=%ss\n' "$after" "$((end-start))"
[ "$after" = "PAYLOAD" ] && ok "bash waited for the RIGHTMOST member; its late write is visible" \
  || no "bash did NOT wait: file was [$after]"

# the same, with the guard's exact form: cmd 2>&1 | tee LOG   (writer as the rightmost member)
: > "$WORK/a1b.log"
bash -c 'echo INNER; echo E >&2' 2>&1 | "$WORK/slowtee" "$WORK/a1b.log"
pipe=( "${PIPESTATUS[@]}" )
printf '  form `cmd 2>&1 | writer LOG` -> file=[%s] PIPESTATUS=(%s)\n' "$(tr '\n' ';' < "$WORK/a1b.log")" "${pipe[*]}"
grep -q INNER "$WORK/a1b.log" && ok "same form: complete after the pipeline returns" || no "incomplete"

# lastpipe: the one shopt that changes who runs the last member
lp=$(bash -c 'shopt -s lastpipe; set +m; echo hi | { read -r v; echo "in-parent:$v"; }; echo "PIPESTATUS=${PIPESTATUS[*]}"' 2>&1)
printf '  shopt -s lastpipe        -> %s\n' "$(printf '%s' "$lp" | tr '\n' ' ')"
echo "  note: lastpipe is OFF by default and is not set anywhere in this drive or patch."

echo
echo "== A2: extract the guard and check the ENV-BYPASS surface =="
grep '^+' "$PATCH" | grep -v '^+++' | sed 's/^+//' > "$WORK/added.txt"
n=$(grep -c -F 'if [ -z "${T381_DRIVE_INNER:-}" ]; then' "$WORK/added.txt")
printf '  T381_DRIVE_INNER gate occurrences: %s\n' "$n"
[ "$n" = 1 ] || { echo "REFUSED: anchor not unique"; exit 3; }
awk 'index($0,"if [ -z \"${T381_DRIVE_INNER:-}\" ]; then")==1 {o=1} o {print} o && $0=="fi" {exit}' \
  "$WORK/added.txt" > "$WORK/guard.sh"

# build a specimen that HAS a failing arm
mkspec(){ { echo '#!/usr/bin/env bash'; echo 'set -uo pipefail'; cat "$WORK/guard.sh"
  echo 'echo "  >>> D-R5 DID NOT REPRODUCE in the RED specimen."'
  echo 'echo "END OF DRIVES."'; echo 'exit 0'; } > "$1"; bash -n "$1" || exit 2; }
mkspec "$WORK/spec.sh"

rc=0; bash "$WORK/spec.sh" >/dev/null 2>&1 || rc=$?
printf '  normal invocation, failing arm                    -> exit %s\n' "$rc"
[ "$rc" = 1 ] && ok "the guard catches the failing arm (exit 1)" || no "expected 1, got $rc"

rc=0; T381_DRIVE_INNER=1 bash "$WORK/spec.sh" >/dev/null 2>&1 || rc=$?
printf '  with T381_DRIVE_INNER=1 EXPORTED, same failing arm -> exit %s\n' "$rc"
if [ "$rc" = 0 ]; then
  no "ENV BYPASS: an exported T381_DRIVE_INNER makes the drive skip its own grader and exit 0"
else
  ok "T381_DRIVE_INNER=1 does not fail open (exit $rc)"
fi
echo "  (compare: T402's guard was gated on T381_DRIVE_LOG being set, so it had the mirror-image"
echo "   surface -- UNSETTING that variable skipped it. Both are internal names.)"

rc=0; out=$(T381_DRIVE_LOG=/nonexistent-dir-zzz/x.log bash "$WORK/spec.sh" 2>&1) || rc=$?
printf '  T381_DRIVE_LOG pointed at an unwritable path      -> exit %s\n' "$rc"
[ "$rc" = 2 ] && ok "refuses (2) rather than passing when its transcript will not open" || no "got $rc: $out"

echo
echo "== A3: is the sentinel check defeatable by the drive's own output? =="
mkspec2(){ { echo '#!/usr/bin/env bash'; echo 'set -uo pipefail'; cat "$WORK/guard.sh"
  echo "$1"; echo 'echo "END OF DRIVES."'; echo 'exit 0'; } > "$WORK/s2.sh"; }
mkspec2 'echo "  >>> D-R5 DID NOT REPRODUCE."; echo "END OF DRIVES."'
rc=0; bash "$WORK/s2.sh" >/dev/null 2>&1 || rc=$?
printf '  drive prints the sentinel TWICE                    -> exit %s\n' "$rc"
[ "$rc" = 2 ] && ok "doubled sentinel refuses (2) -- exactly-once is enforced, not at-least-once" || no "got $rc"
mkspec2 'echo "nothing bad here"'
rc=0; bash "$WORK/s2.sh" >/dev/null 2>&1 || rc=$?
printf '  healthy, sentinel once                            -> exit %s\n' "$rc"
[ "$rc" = 0 ] && ok "healthy passes (0) -- the sentinel check is not vacuous" || no "got $rc"

echo
echo "== A4: GNU tee, if this host has one =="
GT=""
for c in gtee /opt/homebrew/opt/coreutils/libexec/gnubin/tee /usr/local/opt/coreutils/libexec/gnubin/tee; do
  command -v "$c" >/dev/null 2>&1 && { GT=$(command -v "$c"); break; }
done
if [ -z "$GT" ]; then
  echo "  NO GNU coreutils tee on this host. T424's '[UNVERIFIED: any specific tee]' bound STANDS,"
  echo "  and T440 could not narrow it either."
else
  echo "  GNU tee found at $GT -- $("$GT" --version 2>&1 | head -1)"
  mkdir -p "$WORK/gshim"; ln -sf "$GT" "$WORK/gshim/tee"
  mkspec "$WORK/spec.sh"
  hits=0; for i in 1 2 3 4 5 6 7 8; do
    rc=0; PATH="$WORK/gshim:$PATH" bash "$WORK/spec.sh" >/dev/null 2>&1 || rc=$?
    [ "$rc" = 1 ] && hits=$((hits+1)); done
  printf '  NEW guard / failing arm / GNU tee -> %s/8 exit 1\n' "$hits"
  [ "$hits" = 8 ] && ok "the amended guard is correct on GNU tee too" || no "GNU tee: only $hits/8"
fi

echo
echo "== A5: is the guard actually LIVE anywhere, or only shipped as a patch? =="
echo "  (answered outside this drive, against the tree)"
echo
echo "T440-ATTACK-RESULT: findings=$fails"
exit 0
