#!/bin/sh
# T135 probe corpus: vacuous-absence shapes NOT written the way T99b's sweep expects.
# Each of these passes on empty input exactly like the three F-5 sites.
hits=$(printf '%s' "" | grep -i -c 'mariadb')          # split flags
[ "$hits" = "0" ] && echo PASS1
n=$(printf '%s' "" | grep --count 'ojdbc')             # long flag
[ "$n" -eq 0 ] && echo PASS2                            # -eq instead of =
BANNED=$(printf '%s' "" | grep -icE 'oracle')          # uppercase var
[ "$BANNED" = "0" ] && echo PASS3
if ! printf '%s' "" | grep -q 'mysql-connector'; then echo PASS4; fi
out=$(printf '%s' "")
[ "x$out" = "x" ] && echo PASS5                         # x-prefix idiom
[ ${#out} -eq 0 ] && echo PASS6                         # length idiom
printf '' > /tmp/t135/missprobe/scan.txt
[ -s /tmp/t135/missprobe/scan.txt ] || echo PASS7       # test -s
awk 'END{if(NR==0) print "PASS8"}' /tmp/t135/missprobe/scan.txt
case "$out" in "") echo PASS9 ;; esac                   # case-on-empty
test -z "$out" && echo PASS10                           # `test -z`, no brackets
