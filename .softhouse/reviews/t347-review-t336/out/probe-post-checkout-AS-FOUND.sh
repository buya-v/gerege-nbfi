#!/bin/sh
# T347 REVIEW PROBE -- temporary, always exit 0. Installed by the T347 reviewer to
# re-measure T336's headline negative. If you find this file, it is a leftover; delete it.
TS=$(date '+%Y-%m-%dT%H:%M:%S')
LINE="$TS pid=$$ pwd=$(pwd) GIT_DIR=${GIT_DIR:-unset} old=$1 new=$2 isbranch=$3"
echo "$LINE" >> /tmp/t347-postcheckout.log 2>/dev/null
echo "$LINE" >> /Users/buv/gerege-nbfi/.git/t347-postcheckout-commondir.log 2>/dev/null
echo "$LINE" > "$(pwd)/.t347-postcheckout-marker" 2>/dev/null
exit 0
