#!/bin/bash
# T459 arms. usage: bash arms.sh <baseref> <arm> [arm ...]
set -u
. "$( cd "$( dirname "$0" )" && pwd )/drive.sh"
BASE="$1"; shift
for A in "$@"; do
  arm "$A" "$BASE"
  D="$( stage "$A" "$BASE" )" || exit 3
  case "$A" in
    Z)   : ;;                                    # control, unmutated
    CTL) plant_unreg "$D/src" ;;                 # unregistered checker, nothing absolving it
    LONGS|LONGSTRIP|LONGSTRIP1|LONGNOP)
         plant_unreg "$D/src"
         case "$A" in
           LONGS)      M=ROW ;;
           LONGSTRIP)  M=STRIP ;;
           LONGSTRIP1) M=STRIP1 ;;
           LONGNOP)    M=NOP ;;
         esac
         forge "$D/src" "$D/forged.txt" "$M"
         collide "$D/src" "$D/forged.txt"
         rm -f "$D/src/forged.txt" 2>/dev/null
         ;;
  esac
  reclone "$D"
  runbar "$D/graded" "$D/bar.log"
done
