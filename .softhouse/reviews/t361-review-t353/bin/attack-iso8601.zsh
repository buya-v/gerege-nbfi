#!/bin/zsh
# T361 — independent adversarial drive of T353's `_iso8601_epoch`.
#
# The function is EXTRACTED FROM THE SHIPPED FILE BY sed, never retyped (P-46), and the
# drive ABORTS if the extraction does not produce a callable function — an empty extraction
# that "passes" is the P-22 shape.
#
# Every expectation below is derived independently of T353's own parity rig:
#   * epoch values are computed by `calendar.timegm` in python3 (proleptic Gregorian,
#     no timezone, no leap seconds) — NOT by `date`, and NOT by T353's `_epoch_iso8601`.
#   * REFUSE means the function must print nothing and return non-zero.
#
# FAIL DIRECTION of a wrong answer here:
#   * a REFUSE where an instant was expected -> `lock_released_at` returns empty and
#     `lock_started_age` returns empty -> arms 1/3/5 cannot fire -> SHUT (liveness).
#   * an ACCEPT where REFUSE was expected -> `lock_released_at` PRINTS the value -> arm 1
#     fires -> a live lock reads FREE -> OPEN (P-85 safety).
#   * a WRONG NUMBER on `started_at` moves arm 3's ceiling: too small = SHUT, too large
#     (or a bogus large age) = OPEN.
emulate -L zsh
set -uo pipefail

SRC="${1:?usage: attack-iso8601.zsh <path to fire-program.sh>}"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/t361-iso.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT

sed -n '/^_iso8601_epoch() {/,/^}/p' "$SRC" >  "$WORK/iso.zsh"
sed -n '/^_epoch_iso8601() {/,/^}/p' "$SRC" >> "$WORK/iso.zsh"
grep -q '^_iso8601_epoch() {' "$WORK/iso.zsh" || { print -u2 "ABORT: extraction of _iso8601_epoch failed"; exit 3; }
grep -q '^_epoch_iso8601() {' "$WORK/iso.zsh" || { print -u2 "ABORT: extraction of _epoch_iso8601 failed"; exit 3; }
source "$WORK/iso.zsh"
whence -w _iso8601_epoch | grep -q function || { print -u2 "ABORT: not a function after source"; exit 3; }

print -r -- "T361 attack on _iso8601_epoch"
print -r -- "source        : $SRC"
print -r -- "sha256(source): $(shasum -a 256 "$SRC" 2>/dev/null | awk '{print $1}')"
print -r -- "zsh           : $ZSH_VERSION   uname: $(uname -sm)"
print -r -- "locale        : LC_ALL=${LC_ALL:-<unset>} LANG=${LANG:-<unset>}"
print -r -- ""

typeset -i N=0 BAD=0
row() {  # $1 expect (integer | REFUSE)  $2 label  $3 input
  local want="$1" label="$2" in="$3" got rc res mark
  got="$(_iso8601_epoch "$in" 2>&1)"; rc=$?
  if (( rc != 0 )); then res=REFUSE; else res="$got"; fi
  N+=1; mark="ok"
  [[ "$res" == "$want" ]] || { mark="*** WRONG"; BAD+=1; }
  printf '%-10s %-38s rc=%d got=%-18s want=%s\n' "$mark" "$label" $rc "$res" "$want"
}

# tg <iso> -> epoch by python calendar.timegm, the INDEPENDENT oracle
tg() { /usr/bin/python3 -c '
import sys,calendar,datetime
s=sys.argv[1]
d=datetime.datetime.strptime(s,"%Y-%m-%dT%H:%M:%SZ")
print(calendar.timegm(d.timetuple()))' "$1"; }

print -r -- "=== A. WELL-FORMED. want = calendar.timegm (independent of BSD date and of T353's rig)"
for iso in \
  1970-01-01T00:00:00Z 1969-12-31T23:59:59Z 2026-08-28T14:00:05Z \
  1900-02-28T00:00:00Z 1900-03-01T00:00:00Z \
  2000-02-29T12:34:56Z 2000-03-01T00:00:00Z \
  2100-02-28T23:59:59Z 2100-03-01T00:00:00Z \
  2004-02-29T00:00:00Z 2400-02-29T00:00:00Z \
  2038-01-19T03:14:07Z 2038-01-19T03:14:08Z \
  1901-12-13T20:45:52Z 9999-12-31T23:59:59Z \
  0001-01-01T00:00:00Z 1582-10-15T00:00:00Z 1752-09-03T00:00:00Z
do
  row "$(tg "$iso")" "$iso" "$iso"
done
# year 0000 — python's strptime/datetime cannot represent it, so the expectation is
# derived by hand from the proleptic-Gregorian days-from-civil identity:
#   0000-01-01 is 719528 days BEFORE 1970-01-01  => -719528*86400
row "$(( -719528 * 86400 ))" "0000-01-01T00:00:00Z (year zero)" "0000-01-01T00:00:00Z"

print -r -- ""
print -r -- "=== B. CALENDAR IMPOSSIBILITIES. want REFUSE. An ACCEPT here is OPEN on released_at."
row REFUSE "1900-02-29 (century non-leap)"      "1900-02-29T00:00:00Z"
row REFUSE "2100-02-29 (century non-leap)"      "2100-02-29T00:00:00Z"
row REFUSE "2026-02-29 (plain non-leap)"        "2026-02-29T00:00:00Z"
row REFUSE "2026-02-30"                         "2026-02-30T00:00:00Z"
row REFUSE "2026-04-31 (30-day month)"          "2026-04-31T00:00:00Z"
row REFUSE "2026-06-31"                         "2026-06-31T00:00:00Z"
row REFUSE "2026-09-31"                         "2026-09-31T00:00:00Z"
row REFUSE "2026-11-31"                         "2026-11-31T00:00:00Z"
row REFUSE "day 00"                             "2026-08-00T00:00:00Z"
row REFUSE "day 32"                             "2026-08-32T00:00:00Z"
row REFUSE "month 00"                           "2026-00-15T00:00:00Z"
row REFUSE "month 13"                           "2026-13-15T00:00:00Z"
row REFUSE "month 99"                           "2026-99-15T00:00:00Z"
row REFUSE "hour 24"                            "2026-08-28T24:00:00Z"
row REFUSE "hour 99"                            "2026-08-28T99:00:00Z"
row REFUSE "minute 60"                          "2026-08-28T14:60:00Z"
row REFUSE "second 61"                          "2026-08-28T14:00:61Z"
row REFUSE "second 99"                          "2026-08-28T14:00:99Z"

print -r -- ""
print -r -- "=== C. THE LEAP SECOND — T353 DELIBERATELY ACCEPTS :60 AND MAPS IT TO THE NEXT SECOND."
print -r -- "    Recorded as an acceptance, not scored as a disagreement. want = the mapped value."
row "$(( $(tg 2016-12-31T23:59:59Z) + 1 ))" "2016-12-31T23:59:60Z (real leap second)" "2016-12-31T23:59:60Z"
row "$(( $(tg 2026-08-28T14:00:00Z) + 60 ))" "14:00:60Z (NOT a leap second, still taken)" "2026-08-28T14:00:60Z"

print -r -- ""
print -r -- "=== D. SHAPE. want REFUSE everywhere. An ACCEPT is OPEN; these are the strings a"
print -r -- "    writer emits to mean NOT RELEASED, or that another producer emits legitimately."
row REFUSE "lowercase z"                        "2026-08-28T14:00:05z"
row REFUSE "+00:00 instead of Z"                "2026-08-28T14:00:05+00:00"
row REFUSE "+08:00 (Asia/Ulaanbaatar)"          "2026-08-28T14:00:05+08:00"
row REFUSE "-00:00"                             "2026-08-28T14:00:05-00:00"
row REFUSE "no zone designator at all"          "2026-08-28T14:00:05"
row REFUSE "space instead of T"                 "2026-08-28 14:00:05Z"
row REFUSE "lowercase t"                        "2026-08-28t14:00:05Z"
row REFUSE "fractional seconds"                 "2026-08-28T14:00:05.123Z"
row REFUSE "basic format, no separators"        "20260828T140005Z"
row REFUSE "5-digit year"                       "12026-08-28T14:00:05Z"
row REFUSE "3-digit year"                       "226-08-28T14:00:05Z"
row REFUSE "negative year"                      "-026-08-28T14:00:05Z"
row REFUSE "leading + on year"                  "+2026-08-28T14:00:05Z"
row REFUSE "leading space"                      " 2026-08-28T14:00:05Z"
row REFUSE "trailing space"                     "2026-08-28T14:00:05Z "
row REFUSE "trailing newline"                   "2026-08-28T14:00:05Z
"
row REFUSE "leading newline"                    "
2026-08-28T14:00:05Z"
row REFUSE "trailing tab"                       $'2026-08-28T14:00:05Z\t'
row REFUSE "trailing CR"                        $'2026-08-28T14:00:05Z\r'
row REFUSE "trailing NUL"                       $'2026-08-28T14:00:05Z\x00'
row REFUSE "NUL in the middle"                  $'2026-08-28\x00T14:00:05Z'
row REFUSE "empty string"                       ""
row REFUSE "the string None"                    "None"
row REFUSE "the string null"                    "null"
row REFUSE "the string pending"                 "pending"
row REFUSE "a bare space"                       " "
row REFUSE "just Z"                             "Z"
row REFUSE "date only"                          "2026-08-28"
row REFUSE "unix epoch as a decimal string"     "1787875200"

print -r -- ""
print -r -- "=== E. EVALUATION / INJECTION. An ACCEPT or a non-empty stdout here is a CODE-EXECUTION"
print -r -- "    class defect: the extracted fields land in zsh arithmetic (\`local -i\`, \`(( ))\`)."
_T361_CANARY=0
row REFUSE "arith injection via subscript"      '2026-08-28T14:00:0${_T361_CANARY::=99}Z'
row REFUSE "command substitution in the value"  '2026-08-28T14:00:0$(touch '"$WORK"'/PWNED)Z'
row REFUSE "backtick"                           '2026-08-28T14:00:0`touch '"$WORK"'/PWNED2`Z'
row REFUSE "glob metachars"                     '????-??-??T??:??:??Z'
row REFUSE "bracket class in the input"         '[0-9][0-9][0-9][0-9]-01-01T00:00:00Z'
row REFUSE "zsh <n-m> numeric glob"             '<1-9>0-08-28T14:00:05Z'
row REFUSE "arithmetic expression as the year"  '1+1 -08-28T14:00:05Z'
row REFUSE "hex-looking year"                   '0x10-08-28T14:00:05Z'
[[ -e "$WORK/PWNED" || -e "$WORK/PWNED2" ]] && { print -r -- "*** WRONG  COMMAND EXECUTION OBSERVED"; BAD+=1; }
N+=1
[[ -e "$WORK/PWNED" || -e "$WORK/PWNED2" ]] || printf '%-10s %-38s\n' ok "no side-effect file created"
(( _T361_CANARY == 0 )) || { print -r -- "*** WRONG  arithmetic assignment canary fired: $_T361_CANARY"; BAD+=1; }
N+=1
(( _T361_CANARY == 0 )) && printf '%-10s %-38s\n' ok "arith canary unfired (_T361_CANARY=0)"

print -r -- ""
print -r -- "=== E2. OCTAL — 08 and 09 are the classic shell date bug. want the CORRECT epoch."
for iso in 2026-08-08T08:08:08Z 2026-09-09T09:09:09Z 2026-08-09T00:00:09Z 2009-09-09T00:00:00Z
do row "$(tg "$iso")" "$iso (leading-zero fields)" "$iso"; done

print -r -- ""
print -r -- "=== F. NON-ASCII DIGITS. zsh [0-9] is a CODE-POINT range; a match here would put a"
print -r -- "    non-ASCII digit into \`10#\` arithmetic. want REFUSE."
row REFUSE "Arabic-Indic digits (U+0660..)"     $'٢٠٢٦-08-28T14:00:05Z'
row REFUSE "fullwidth digits (U+FF10..)"        $'２０２６-08-28T14:00:05Z'
row REFUSE "Devanagari digits"                  $'२०२६-08-28T14:00:05Z'
row REFUSE "superscript two in the year"        $'20²6-08-28T14:00:05Z'

print -r -- ""
print -r -- "=== G. SIZE / OVERFLOW."
BIG="$(/usr/bin/python3 -c 'import sys; sys.stdout.write("9"*10485760)')"
row REFUSE "10 MB of digits"                    "$BIG"
row REFUSE "10 MB after a valid instant"        "2026-08-28T14:00:05Z$BIG"
unset BIG
row REFUSE "9223372036854775807 as the input"   "9223372036854775807"
# the largest and smallest the SHAPE can express
row "$(tg 9999-12-31T23:59:59Z)" "9999-12-31T23:59:59Z (shape max)"  "9999-12-31T23:59:59Z"
row "$(( -719528 * 86400 ))"     "0000-01-01T00:00:00Z (shape min)"  "0000-01-01T00:00:00Z"
print -r -- "    note: the 4-digit-year glob BOUNDS the output to [$(( -719528 * 86400 )), $(tg 9999-12-31T23:59:59Z)]"
print -r -- "    i.e. |value| < 2.6e11, ~7 orders of magnitude inside int64. Overflow is UNREACHABLE."

print -r -- ""
print -r -- "=== H. ROUND-TRIP _epoch_iso8601 -> _iso8601_epoch, 4000 pseudo-random instants + edges"
typeset -i rt=0 rtbad=0
for e in 0 1 59 60 86399 86400 951782400 1709164800 2147483647 2147483648 4102444800 253402300799 \
         $(/usr/bin/python3 -c 'import random; random.seed(20260828); print(" ".join(str(random.randrange(0,253402300800)) for _ in range(4000)))')
do
  iso=""; back=""
  iso="$(_epoch_iso8601 $e)" || { print -r -- "*** WRONG  _epoch_iso8601 refused $e"; rtbad+=1; continue; }
  back="$(_iso8601_epoch "$iso")" || { print -r -- "*** WRONG  _iso8601_epoch refused its own output $iso (from $e)"; rtbad+=1; continue; }
  rt+=1
  [[ "$back" == "$e" ]] || { print -r -- "*** WRONG  round-trip $e -> $iso -> $back"; rtbad+=1; }
done
printf '%-10s round-trip pairs=%d mismatches=%d\n' "$( (( rtbad == 0 )) && print ok || print '*** WRONG')" $rt $rtbad
N+=1; (( rtbad == 0 )) || BAD+=1

print -r -- ""
print -r -- "=== I. CROSS-CHECK _epoch_iso8601 AGAINST python (it builds the self-test's fixtures;"
print -r -- "    a wrong '100 h ago' stamp makes group C prove nothing)."
typeset -i fb=0 fn=0
for e in 0 1 86399 86400 951782400 1709164800 2147483647 4102444800 253402300799 \
         $(/usr/bin/python3 -c 'import random; random.seed(7); print(" ".join(str(random.randrange(0,253402300800)) for _ in range(500)))')
do
  mine=""; theirs=""
  mine="$(_epoch_iso8601 $e)"
  theirs="$(/usr/bin/python3 -c '
import sys,datetime
print(datetime.datetime.fromtimestamp(int(sys.argv[1]),datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))' $e)"
  fn+=1
  [[ "$mine" == "$theirs" ]] || { print -r -- "*** WRONG  e=$e mine=$mine python=$theirs"; fb+=1; }
done
printf '%-10s formatted=%d disagreements=%d\n' "$( (( fb == 0 )) && print ok || print '*** WRONG')" $fn $fb
N+=1; (( fb == 0 )) || BAD+=1

print -r -- ""
print -r -- "CHECKS=$N WRONG=$BAD"
(( BAD == 0 )) || exit 1
exit 0
