#!/bin/zsh
# T361 — `[0-9]` in a zsh pattern: code-point range, or locale collation?
#
# It matters because the four year digits go straight into `10#${s[1,4]}` in an ARITHMETIC
# context. If a locale made `[0-9]` match a non-ASCII digit, an unvalidated character would
# reach `(( ))`. The wrapper runs under launchd, whose locale is whatever the login shell
# hands it — not a value the file pins — so this has to be measured across locales, not
# assumed from the one this terminal happens to have.
#
# FAIL DIRECTION of a locale-dependent match: at `lock_released_at` it is OPEN (a string
# that is not an instant would be read as a release); at `lock_started_age` it is either.
emulate -L zsh
set -uo pipefail
SRC="${1:?usage: t361-locale-sweep.zsh <fire-program.sh>}"
W="$(mktemp -d "${TMPDIR:-/tmp}/t361-loc.XXXXXX")" || exit 3
trap 'rm -rf "$W"' EXIT
sed -n '/^_iso8601_epoch() {/,/^}/p' "$SRC" > "$W/iso.zsh"
grep -q '^_iso8601_epoch() {' "$W/iso.zsh" || { print -u2 "ABORT: extraction failed"; exit 3; }

cat > "$W/probe.zsh" <<'PROBE'
emulate -L zsh
set -uo pipefail
source "$1"
v="$(_iso8601_epoch '2026-08-28T14:00:05Z')"; rv=$?
a="$(_iso8601_epoch $'٢٠٢٦-08-28T14:00:05Z')"; ra=$?
f="$(_iso8601_epoch $'２０２６-08-28T14:00:05Z')"; rf=$?
l="$(_iso8601_epoch '2026-02-29T00:00:00Z')"; rl=$?
t="$(_iso8601_epoch '2026-08-28T14:00:05z')"; rt=$?
printf 'valid=%s/rc%d  arabic=rc%d  fullwidth=rc%d  feb29nonleap=rc%d  lowercase_z=rc%d\n' "$v" $rv $ra $rf $rl $rt
PROBE

print -r -- "T361 locale sweep — want on EVERY row:"
print -r -- "  valid=1787925605/rc0  arabic=rc1  fullwidth=rc1  feb29nonleap=rc1  lowercase_z=rc1"
print -r -- ""
typeset -i bad=0 n=0
for L in C POSIX en_US.UTF-8 en_US.ISO8859-1 tr_TR.UTF-8 ar_SA.UTF-8 mn_MN.UTF-8 de_DE.UTF-8 ja_JP.UTF-8 zh_CN.UTF-8; do
  local out
  out="$(LC_ALL="$L" LANG="$L" zsh "$W/probe.zsh" "$W/iso.zsh" 2>&1)"
  n+=1
  local mark=ok
  [[ "$out" == 'valid=1787925605/rc0  arabic=rc1  fullwidth=rc1  feb29nonleap=rc1  lowercase_z=rc1' ]] \
    || { mark='*** WRONG'; bad+=1; }
  printf '%-10s %-18s %s\n' "$mark" "$L" "$out"
done
print -r -- ""
print -r -- "LOCALES=$n WRONG=$bad"
(( bad == 0 )) || exit 1
