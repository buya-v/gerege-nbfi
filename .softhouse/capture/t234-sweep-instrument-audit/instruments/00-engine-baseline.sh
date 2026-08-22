#!/usr/bin/env bash
# T234 — establish WHICH ENGINE each spelling of "grep" actually resolves to,
# separately for (a) the agent's interactive shell and (b) a plain script.
# Run from the repo root.  Engine + flags are stated for every measurement.
set -u
echo "### host"
uname -a
echo
echo "### git"
git --version
echo
echo "### /usr/bin/grep  (what a #!/usr/bin/env bash script gets when PATH is normal)"
/usr/bin/grep --version 2>&1 | head -2
echo
echo "### command -v grep, in THIS script's environment"
command -v grep
echo
echo "### is 'grep' a shell FUNCTION exported into scripts?"
if declare -F grep >/dev/null 2>&1; then echo "YES - grep is a function in this script env"; else echo "NO - grep is not a function in this script env"; fi
env | grep -c '^BASH_FUNC_grep' 2>/dev/null || echo "BASH_FUNC_grep not exported"
echo
echo "### env -i /bin/bash: the most stripped-down script environment"
env -i /bin/bash -c 'command -v grep; /usr/bin/grep --version 2>&1|head -1'
echo
echo "### ugrep present on disk?"
command -v ugrep 2>/dev/null || echo "no standalone ugrep binary on PATH"
echo
echo "### THE CORE MEASUREMENT: does each engine honour \\b ?"
printf 'balance column\n' > /tmp/t234_probe.txt
printf 'the balance column here\n' >> /tmp/t234_probe.txt
printf 'unbalance column here\n'   >> /tmp/t234_probe.txt
echo "-- corpus /tmp/t234_probe.txt --"; cat -A /tmp/t234_probe.txt | sed 's/\$$//'
echo
for eng in "/usr/bin/grep -E" "/usr/bin/grep -P" "git grep -E" "git grep -P"; do
  for pat in 'balance column' '\balance column'; do
    if [[ "$eng" == git* ]]; then
      n=$($eng -c "$pat" -- . 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}')
      printf '%-16s  pat=%-18s  git-tracked-hit-lines=%s\n' "$eng" "$pat" "$n"
    else
      n=$($eng -c "$pat" /tmp/t234_probe.txt 2>/dev/null || echo 0)
      printf '%-16s  pat=%-18s  probefile-hits=%s\n' "$eng" "$pat" "$n"
    fi
  done
done
echo
echo "### /usr/bin/grep -P supported?"
/usr/bin/grep -P 'x' /dev/null; echo "  exit=$? (2 => -P unsupported by BSD grep)"
