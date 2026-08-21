#!/bin/bash
# T155's OWN poison corpus. Written before reading any T154 fixture.
#
# The invalid byte must sit OUTSIDE a JSON string literal (the guard's perl
# stage deletes string literals first, so a byte hidden inside one is deleted
# with it and proves nothing) and on the SAME LINE as the float, BEFORE it —
# BSD grep's blindness is per line and starts at the bad byte.
set -eu
P="${1:-/tmp/t155/poison}"
rm -rf "$P"; mkdir -p "$P"

# --- JSON corpus -----------------------------------------------------------
printf '{\n  "note": "x", "rate_pct": 3.6\n}\n'          > "$P/p1.json"  # clean float
printf '{\n  "note": "x", \xe2 "rate_pct": 3.6\n}\n'     > "$P/p2.json"  # 0xE2 BEFORE, same line
printf '{\n  "note": "x", \x00 "rate_pct": 3.6\n}\n'     > "$P/p3.json"  # NUL BEFORE, same line
printf '{\n  "rate_pct": 3.6, \xe2 "z": 1\n}\n'          > "$P/p4.json"  # 0xE2 AFTER
printf '{\n  "amount": "1250000", "term": 12\n}\n'       > "$P/p5.json"  # clean integers
printf '{\n  "x": 1, \xe2 "y": 1e3\n}\n'                 > "$P/p6.json"  # 0xE2 BEFORE an exponent
printf '{\n  "note": "x", \xe2 "rate_pct": 3.6\n}\n'     > "$P/p7.json"  # same as p2, for the e2e plant

# --- Go corpus -------------------------------------------------------------
printf 'package x\n\nfunc A() { var v float64; _ = v }\n'                        > "$P/g1.go"
printf 'package x\n\nfunc A() { s := "\xe2"; var v float64; _ = v; _ = s }\n'    > "$P/g2.go"
printf 'package x\n\nfunc A() { var v int64; _ = v }\n'                          > "$P/g3.go"

echo "poison written to $P"
ls -l "$P"
