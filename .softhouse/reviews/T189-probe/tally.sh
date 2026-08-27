#!/bin/bash
# T189 — tally the matrix by arm, counting cells by outcome class, so the counts in
# the adjudication are computed rather than hand-counted.
set -u
P="$(cd "$(dirname "$0")" && pwd)"
/usr/bin/awk '
/^####/ { arm=$0; sub(/^#+ */,"",arm); sub(/ *#+$/,"",arm); next }
/^IMPL=/ { cell=$0; next }
/^  exit=/ {
  split($0,a,"[= ]+"); rc=a[3]; nb=a[5]; nl=a[7]
  cls = (rc==1 && nb==0) ? "BLIND(exit1,0 bytes)" : ((nl==1 && nb>30 && cell ~ /nul|blob/) ? "THIRD-MODE(Binary file...matches)" : "OK")
  key = arm "\t" cls
  n[key]++
  next
}
END { for (k in n) printf "%-4d  %s\n", n[k], k }
' "$P/matrix-out.txt" | sort -t'	' -k1
