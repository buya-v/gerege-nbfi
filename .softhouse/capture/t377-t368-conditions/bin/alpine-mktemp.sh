#!/bin/bash
# T377 — CLOSE T368 §13 / T365 follow-up 4: does `/usr/bin/mktemp` exist on busybox?
#
# T368 could not finish this run (the image did not pull in time) and correctly reported NO
# result rather than guessing. Docker is up on this host (29.6.2), so the closure was
# available and this takes it.
#
# EVIDENCE, NOT A CONTROL. Nothing invokes this from CI, and it must not be read as one — it
# needs a container runtime that the fire does not require. It is a MEASUREMENT script whose
# transcript is `out/05-alpine-mktemp.txt`. The control that this measurement justified is
# `$FIRE_MKTEMP` in `fire-program.sh`, which is on the path that executes.
#
# `bash`, never `sh`: this is a bash script and the repo's wrong-interpreter discipline says
# say so. The SUBJECT it mounts is `#!/bin/zsh` and is run with `/bin/zsh` inside the container.
set -uo pipefail

SUBJECT_DIR="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../bin" && pwd)}"
IMAGE="${IMAGE:-alpine:3}"

echo "subject dir : $SUBJECT_DIR"
echo "subject sha : $(shasum -a 256 "$SUBJECT_DIR/fire-program.sh" | cut -d' ' -f1)"
echo "image       : $IMAGE"
echo "docker      : $(docker --version 2>&1)"
echo "host        : $(uname -srm)"
echo ""

echo "=== 1. bare busybox image: where does mktemp live, and what else is missing? ==="
docker run --rm "$IMAGE" sh -c '
  for b in /usr/bin/mktemp /bin/mktemp /usr/bin/stat /bin/stat /usr/bin/shasum \
           /usr/bin/python3 /usr/bin/find /bin/cp /bin/chmod /bin/rm /bin/zsh \
           /usr/bin/git /usr/bin/cut /usr/bin/curl; do
    if [ -x "$b" ]; then echo "PRESENT $b"; else echo "ABSENT  $b"; fi
  done
  echo "--- mktemp identity ---"
  ls -l /bin/mktemp 2>&1 || true
'
echo ""

echo "=== 2. PROVISIONED host (apk add zsh python3): the wrapper can now START. ==="
echo "    This is the case that matters: a bare image cannot run a #!/bin/zsh script at all,"
echo "    so 'the fire refuses on every Linux host' is only a real claim once zsh is present."
docker run --rm "$IMAGE" sh -c '
  apk add --no-cache zsh python3 >/dev/null 2>&1
  for b in /usr/bin/mktemp /bin/mktemp /usr/bin/python3 /bin/zsh /usr/bin/zsh; do
    if [ -x "$b" ]; then echo "PRESENT $b"; else echo "ABSENT  $b"; fi
  done
'
echo ""

# The container shell is busybox `sh`, so no `PIPESTATUS` and no arrays: the rc is captured
# by redirecting to a file, never through a pipe. (The first run of this probe printed
# `sh: syntax error: bad substitution` for exactly that reason; the transcript of the whole
# self-test was still readable, but the rc was not, so the fix is here rather than glossed.)
RUN_IN_ALPINE='
  apk add --no-cache zsh python3 >/dev/null 2>&1
  /bin/zsh /w/fire-program.sh --self-test-lock-readers > /tmp/st.out 2>&1
  rc=$?
  tail -6 /tmp/st.out
  echo "SELFTEST rc=$rc"
'

echo "=== 3. THE SHIPPED SELF-TEST, run in that container, against the live subject ==="
echo "    Mounted read-only. rc 0 with a full ROWS= tally means \$FIRE_MKTEMP resolved to"
echo "    /bin/mktemp and the whole 45-row corpus ran on busybox."
docker run --rm -v "$SUBJECT_DIR:/w:ro" "$IMAGE" sh -c "$RUN_IN_ALPINE" > /tmp/t377-alp3.txt 2>&1
cat /tmp/t377-alp3.txt
echo ""

echo "=== 4. WHAT THE HARD-CODED PATH DID, reconstructed on the SAME container ==="
echo "    A copy of the subject with \$FIRE_MKTEMP forced back to the literal /usr/bin/mktemp."
echo "    If step 3 is green and this is rc 2, the fix is the only difference between them."
TMPD="$(mktemp -d "${TMPDIR:-/tmp}/t377-alpine.XXXXXX")" || exit 2
trap '[[ -n "${TMPD:-}" && "${TMPD:-}" != "/" ]] && rm -rf "$TMPD"' EXIT
sed 's|^FIRE_MKTEMP="${FIRE_MKTEMP:-/usr/bin/mktemp}"$|FIRE_MKTEMP="/usr/bin/mktemp"   # T377 probe: pre-fix spelling forced back|' \
    "$SUBJECT_DIR/fire-program.sh" > "$TMPD/fire-program.sh"
if ! grep -q 'T377 probe: pre-fix spelling forced back' "$TMPD/fire-program.sh"; then
  echo "VOID: could not force the pre-fix spelling; step 4 proves nothing."
  echo "VERDICT: VOID"
  exit 1
fi
docker run --rm -v "$TMPD:/w:ro" "$IMAGE" sh -c "$RUN_IN_ALPINE" > /tmp/t377-alp4.txt 2>&1
cat /tmp/t377-alp4.txt
echo ""

echo "=== VERDICT ==="
ok=1
grep -q '^ROWS=45 FAIL_OPEN=0 FAIL_SHUT=0 SKIPPED=0$' /tmp/t377-alp3.txt || { echo "step 3: NO GREEN 45-ROW TALLY"; ok=0; }
grep -q '^SELFTEST rc=0$'                             /tmp/t377-alp3.txt || { echo "step 3: rc is not 0";          ok=0; }
grep -q 'could not create a scratch directory'        /tmp/t377-alp4.txt || { echo "step 4: no C2 refusal";        ok=0; }
grep -q '^SELFTEST rc=2$'                             /tmp/t377-alp4.txt || { echo "step 4: rc is not 2";          ok=0; }
if [ "$ok" = 1 ]; then
  echo "PASS — with \$FIRE_MKTEMP the 45-row self-test runs GREEN on busybox; with the"
  echo "hard-coded /usr/bin/mktemp the identical file REFUSES (rc 2) and the fire cannot start."
  echo "The resolver is the only difference between the two runs."
  exit 0
fi
echo "FAIL — the contrast this probe claims was not observed."
exit 1
