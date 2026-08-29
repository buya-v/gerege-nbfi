#!/usr/bin/env bash
# T469 slow-HOST wrapper.  The code under test is NEVER edited; only the host is slowed.
# Also LOGS every argv so probe counts are measured on the HOST side, independently of
# whatever note the module under test chooses to print.
if [ -n "${T469_GITLOG:-}" ]; then
  printf '%s\n' "$*" >> "$T469_GITLOG"
fi
if [ -n "${T469_SLEEP:-}" ] && [ "${T469_SLEEP}" != "0" ]; then
  /bin/sleep "$T469_SLEEP"
fi
exec "${T469_REALGIT:?real git}" "$@"
