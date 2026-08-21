#!/usr/bin/env bash
# T191 — run the FULL harness in THIS worktree (P-56: a guard's scope defect is invisible
# in every tree except the one it will run in), and grade the oracle-down condition in the
# order the file itself mandates: PRESENCE of the probe line FIRST, then its value.
#
# Four exit-2 paths run BEFORE the probe line is ever printed, one of them a failed HARD
# guard. So `exit 2` alone does NOT mean "oracle down"; `exit 2` AND a probe line actually
# PRINTED AND reading `down` does.
set -u -o pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
OUT="${1:-$HERE/harness-run.txt}"

# shellcheck disable=SC1091
. "$REPO/.softhouse/bin/go-env.sh" >/dev/null 2>&1 || true

bash "$REPO/.softhouse/conformance.sh" > "$OUT" 2>&1
rc=$?

# PRESENCE first. `grep -c` and not `grep -q`, for the reason this whole task exists.
probe_lines="$(LC_ALL=C /usr/bin/grep -ac 'probe *= *' "$OUT")" || true
[ -n "$probe_lines" ] || probe_lines=0

echo "HARNESS EXIT      : $rc"
echo "PROBE LINE PRESENT: $([ "$probe_lines" -gt 0 ] && echo YES || echo NO) ($probe_lines line(s))"
if [ "$probe_lines" -gt 0 ]; then
  echo "PROBE LINE VALUE  :"
  LC_ALL=C /usr/bin/grep -a 'probe *= *' "$OUT" | sed 's/^/    /'
fi
echo "VERDICT LINE      :"
LC_ALL=C /usr/bin/grep -a 'VERDICT' "$OUT" | sed 's/^/    /' || echo "    (none)"
echo
if [ "$rc" = 2 ] && [ "$probe_lines" -eq 0 ]; then
  echo "READING: exit 2 with NO probe line — this is NOT the oracle-down condition."
  echo "READING: the harness died before reaching the probe (a HARD guard, or a toolchain fault)."
elif [ "$rc" = 2 ]; then
  echo "READING: exit 2 WITH a probe line — read the value above before calling it oracle-down."
fi
exit "$rc"
