#!/bin/bash
# T155 probe (ii) — INDEPENDENT. Inject a floating-point LITERAL and an
# IMAGINARY LITERAL, each carrying ZERO forbidden identifiers, into the
# loanschedule tree and ask the question that matters:
#
#   does `bash .softhouse/conformance.sh` — the command the program actually
#   runs, which NEVER runs `go test` — go non-zero?
#
# A guard reachable only from `go test` is not a guard (P-45). Arms:
#   PRE  = the fork-point tree (187e972), the hole as inherited
#   POST = a SCRATCH MERGE of softhouse/T154-nofloat-guards into CURRENT main
#          (P-24: never the branch tip alone)
#
# The probe sources are T155's own, written before reading T154's fixtures.
set -u
PRE=/tmp/t155/pre
POST=/tmp/t155/post
REL=nexus/internal/apps/loanschedule
OUTD=/tmp/t155/out
mkdir -p "$OUTD"
. /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh

# --- the three probe sources ----------------------------------------------
# Each declares NO forbidden identifier: no float32/float64, no complex64/128,
# no big.Float, no Parse/Format/AppendFloat. Only the LITERAL is the violation.
mk_float() { cat > "$1/$REL/t155_probe.go" <<'GO'
package loanschedule

// t155FloatLiteralProbe carries no forbidden IDENTIFIER at all. Go infers an
// untyped float constant and the arithmetic is IEEE-754 binary floating point.
func t155FloatLiteralProbe(p int64) int64 {
	r := 0.036
	return p + int64(r)
}

var _ = t155FloatLiteralProbe
GO
}
mk_imag() { cat > "$1/$REL/t155_probe.go" <<'GO'
package loanschedule

// t155ImagLiteralProbe is token.IMAG. The identifier "complex128" never appears
// in the source, so an identifier scan sees nothing.
func t155ImagLiteralProbe() interface{} {
	z := 3i
	return z
}

var _ = t155ImagLiteralProbe
GO
}
mk_hexfloat() { cat > "$1/$REL/t155_probe.go" <<'GO'
package loanschedule

// t155HexFloatProbe is a hexadecimal floating-point literal — also token.FLOAT,
// and it contains neither a '.' followed by a digit nor an e/E exponent, so the
// shell guard's byte regex could not see it even if it looked for literals.
func t155HexFloatProbe(p int64) int64 {
	r := 0x1p-2
	return p + int64(r)
}

var _ = t155HexFloatProbe
GO
}
clean() { rm -f "$1/$REL/t155_probe.go"; }

run_arm() { # $1 tree, $2 label
  local tree="$1" label="$2" rc out
  out="$OUTD/ii-$label.txt"
  ( cd "$tree" && bash "$tree/.softhouse/conformance.sh" ) > "$out" 2>&1
  rc=$?
  local probe="NO-PROBE-LINE"
  if LC_ALL=C grep -aq 'probe = ' "$out"; then probe="$(LC_ALL=C grep -a 'probe = ' "$out" | sed 's/.*probe = //')"; fi
  local verdict; verdict="$(LC_ALL=C grep -a '^VERDICT' "$out" | head -1)"
  local cens;   cens="$(LC_ALL=C grep -a 'no-float census' "$out" | head -1 | sed 's/^ *//')"
  printf '  exit=%s  probe=%s\n  %s\n  %s\n' "$rc" "$probe" "${verdict:-<no VERDICT line>}" "${cens:-<no census line>}"
  LC_ALL=C grep -a 'FLOATING POINT ON A MONEY PATH\|floating-point literal\|t155_probe' "$out" | head -4 | sed 's/^/  ! /'
  echo "$rc"
}

FAILS=0
check() { # $1 label $2 want $3 got
  if [ "$2" = "$3" ]; then echo "  => OK (wanted exit $2)"; else echo "  => *** DISAGREES: wanted exit $2, got $3 ***"; FAILS=$((FAILS+1)); fi
}

for kind in float imag hexfloat; do
  echo "======================================================================"
  echo "PROBE: $kind literal, zero forbidden identifiers"
  echo "======================================================================"
  for arm in PRE POST; do
    tree=$PRE; want=0            # PRE: the hole — conformance still says PASS
    [ "$arm" = POST ] && { tree=$POST; want=2; }
    "mk_$kind" "$tree"
    echo "-- $arm ($tree)"
    got="$(run_arm "$tree" "$kind-$arm" | tee /dev/stderr | tail -1)"
    check "$kind-$arm" "$want" "$got"
    clean "$tree"
  done
done

echo
echo "PRE arms wanted exit 0 (the inherited hole); POST arms wanted exit 2."
echo "rows disagreeing with T155's own expectation: $FAILS"
[ "$FAILS" -eq 0 ] || exit 1
