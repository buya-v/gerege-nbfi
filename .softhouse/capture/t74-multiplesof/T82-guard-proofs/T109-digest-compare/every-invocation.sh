#!/bin/bash
# T109 step 6 — ATTACK THE COMPARISON. Could the observation "it refuses" be produced by the check
# never running? Only if some invocation form skips it. So: feed the WRONG-BUT-VALID pin (main's
# tip, T103's case 5i) and run the rig every way it is actually invoked. Every form must exit 2
# with ZERO stdout bytes and ZERO proof-row artefacts. Then the CORRECT pin, same forms, must be
# 25/25 — so the refusal is not a rig that simply cannot run.
set -u
ROOT="${1:?repo root}"
RIG="$ROOT/.softhouse/capture/t74-multiplesof/T82-guard-proofs"
PIN="$RIG/FORK-POINT-SHA"
BAK="/tmp/t109-pin-backup2"
cp "$PIN" "$BAK"

MAINTIP="$(git -C "$ROOT" rev-parse main)"

probe() { # $1 = description, rest = command run via a subshell string
  desc="$1"; shift
  out="$( ("$@") 2>/tmp/t109-inv.err )"; got=$?
  rows="$(ls "$RIG/scratch" 2>/dev/null | grep -c '^att-\|^cf-')"
  tail="$(printf '%s' "$out" | tail -n 2 | tr '\n' ' ')"
  printf '  %-58s exit=%s stdout_bytes=%s proof_rows=%s %s\n' \
    "$desc" "$got" "$(printf '%s' "$out" | wc -c | tr -d ' ')" "$rows" "$tail"
}

echo "################ LEG A — WRONG-BUT-VALID PIN (main's tip $MAINTIP) ################"
{ echo "commit $MAINTIP"; grep '^sha256 ' "$BAK"; } > "$PIN"
probe "bash <abs path>, cwd=repo root"        bash -c "cd '$ROOT' && bash '$RIG/prove-guards-go-red.sh'"
probe "bash <rel path>, cwd=repo root"        bash -c "cd '$ROOT' && bash ./.softhouse/capture/t74-multiplesof/T82-guard-proofs/prove-guards-go-red.sh"
probe "bash <bare name>, cwd=rig dir"         bash -c "cd '$RIG' && bash prove-guards-go-red.sh"
probe "bash ./<name>, cwd=rig dir"            bash -c "cd '$RIG' && bash ./prove-guards-go-red.sh"
probe "bash <abs path>, cwd=/tmp"             bash -c "cd /tmp && bash '$RIG/prove-guards-go-red.sh'"
probe "bash <abs path>, cwd=\$HOME"           bash -c "cd \"\$HOME\" && bash '$RIG/prove-guards-go-red.sh'"
probe "direct exec (shebang), cwd=rig dir"    bash -c "cd '$RIG' && chmod +x prove-guards-go-red.sh 2>/dev/null; ./prove-guards-go-red.sh"
probe "sh <abs path> (undocumented form)"     bash -c "cd '$ROOT' && sh '$RIG/prove-guards-go-red.sh'"
probe "zsh <abs path> (undocumented form)"    bash -c "cd '$ROOT' && zsh '$RIG/prove-guards-go-red.sh'"
probe "piped: bash < script (no \$0 path)"     bash -c "cd '$RIG' && bash < prove-guards-go-red.sh"
echo "  --- the stderr of the last form, to show what a \$0-less invocation does ---"
sed -e 's/^/  2| /' /tmp/t109-inv.err | head -8

echo
echo "################ LEG B — CORRECT PIN, SAME FORMS ################"
cp "$BAK" "$PIN"
probe "bash <abs path>, cwd=repo root"        bash -c "cd '$ROOT' && bash '$RIG/prove-guards-go-red.sh'"
probe "bash <bare name>, cwd=rig dir"         bash -c "cd '$RIG' && bash prove-guards-go-red.sh"
probe "bash <abs path>, cwd=/tmp"             bash -c "cd /tmp && bash '$RIG/prove-guards-go-red.sh'"

cp "$BAK" "$PIN"
echo
echo "pin restored byte-identical:"; diff "$BAK" "$PIN" && echo "  yes"
