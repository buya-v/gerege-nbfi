#!/usr/bin/env bash
# T191. Measure, ON THIS MACHINE, the largest producer output for which an
# EARLY-EXITING consumer does NOT kill the producer.
#
# Method: the producer writes N bytes whose FIRST line matches the pattern; the
# consumer is `grep -q`, which exits 0 on the first match. If the whole N bytes
# fit in the kernel pipe buffer, the producer's write(2) returns before the
# consumer exits, the producer exits 0, and under `set -o pipefail` the pipeline
# is 0. If N exceeds the buffer, the producer blocks in write(2), the consumer
# exits, and the producer dies of SIGPIPE -- so the PIPELINE is non-zero even
# though grep MATCHED. That inversion is the defect.
#
# Do NOT inherit a number from another handoff: this is host- and
# producer-dependent. Run it.
set -u -o pipefail

PRODUCER="${1:-perl}"

probe_perl() { # $1 = total bytes
  perl -e '
    my $n = shift;
    my $s = "MATCHME 1.5\n";
    $s .= ("x" x ($n - length($s) - 1)) . "\n" if $n > length($s);
    print $s;
  ' "$1" | LC_ALL=C /usr/bin/grep -aEq 'MATCHME [0-9]\.[0-9]'
}

probe_printf() { # $1 = total bytes -- the bash BUILTIN printf, as at conformance.sh:1290
  local n="$1" pad
  pad="$(perl -e 'print "x" x (shift() - 12)' "$n")"
  printf '%s' "MATCHME 1.5
$pad" | LC_ALL=C /usr/bin/grep -aEq 'MATCHME [0-9]\.[0-9]'
}

probe() {
  case "$PRODUCER" in
    perl)   probe_perl "$1" ;;
    printf) probe_printf "$1" ;;
    *) echo "unknown producer $PRODUCER" >&2; exit 64 ;;
  esac
}

lo=1024
hi=$((8 * 1024 * 1024))

if probe "$lo"; then echo "endpoint lo=$lo   pipeline EXIT 0   (producer survived; guard sees the match)"
else                 echo "endpoint lo=$lo   pipeline NON-ZERO (producer killed; guard INVERTS)"; fi
if probe "$hi"; then echo "endpoint hi=$hi   pipeline EXIT 0   (producer survived; guard sees the match)"
else                 echo "endpoint hi=$hi   pipeline NON-ZERO (producer killed; guard INVERTS)"; fi

while [ $((hi - lo)) -gt 1 ]; do
  mid=$(((lo + hi) / 2))
  if probe "$mid"; then lo=$mid; else hi=$mid; fi
done

echo "producer=$PRODUCER  consumer=/usr/bin/grep -aEq"
echo "LARGEST CLEAN     (pipeline exit 0, guard fires correctly): $lo bytes"
echo "SMALLEST INVERTING (pipeline non-zero, guard goes SILENT):  $hi bytes"
