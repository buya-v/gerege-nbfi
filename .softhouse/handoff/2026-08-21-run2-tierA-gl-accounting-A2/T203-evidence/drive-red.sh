#!/usr/bin/env bash
# T203 - stage the COMMITTED pre-fix bytes of all six promoters at their real
# depth inside the repo (T57 and T8 derive ROOT from their own __file__, so a
# /tmp copy cannot run), drive the RED proof, then remove the staged copies.
# The staged files are transient and are never committed.
set -uo pipefail
ROOT=/Users/buv/gerege-nbfi/.claude/worktrees/agent-a4762772d2f0d5192
EV="$ROOT/.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T203-evidence"
H="$ROOT/.softhouse/handoff"

cleanup() { rm -f "$H"/T203-PREFIX-*.py; }
trap cleanup EXIT

git -C "$ROOT" show HEAD:.softhouse/handoff/T74-promote-vectors.py     > "$H/T203-PREFIX-T74.py"
git -C "$ROOT" show HEAD:.softhouse/handoff/T61-promote-vectors.py     > "$H/T203-PREFIX-T61.py"
git -C "$ROOT" show HEAD:.softhouse/capture/t64-zeroprincipal/src/T64-promote-vectors.py > "$H/T203-PREFIX-T64.py"
git -C "$ROOT" show HEAD:.softhouse/handoff/T58-promote-vectors.py     > "$H/T203-PREFIX-T58.py"
git -C "$ROOT" show HEAD:.softhouse/handoff/T57-promote-emi-vectors.py > "$H/T203-PREFIX-T57.py"
git -C "$ROOT" show HEAD:.softhouse/handoff/T8-promote-vectors.py      > "$H/T203-PREFIX-T8.py"

echo "STAGED pre-fix bytes (sha256 of each, from the committed blob):"
shasum -a 256 "$H"/T203-PREFIX-*.py

# T64's pre-fix bytes live at a different depth but resolve everything from the
# cwd, so running the staged copy from .softhouse/handoff is faithful.
python3 "$EV/t203-redgreen.py" "$ROOT" red
rc=$?
echo "RED_DRIVER_EXIT=$rc"
exit $rc
