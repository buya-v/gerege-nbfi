#!/bin/zsh
# =====================================================================================
# T380 — INDEPENDENT attack on T377's two other closures in `.softhouse/bin/fire-program.sh`:
#   (A) F-T368-3, the top-of-file threshold validator and its `EX_CONFIG` 78 discriminator;
#   (B) the `$FIRE_MKTEMP` resolver, whose WHOLE POINT is that it must not reintroduce the
#       `$PATH` hijack that the hard-coded `/usr/bin/mktemp` was bought to prevent.
#
# The knob cases drive the SHIPPED wrapper (no mutation needed — the environment is the
# input). The hijack cases plant a hostile `mktemp` and check it is NEVER consulted.
#
# NO MONEY IS COMPUTED ON THIS PATH. Every number is an exit status or a count of seconds.
# =====================================================================================
emulate -L zsh
set -u

SUBJ="${SUBJ:-/tmp/t380-subject/.softhouse/bin/fire-program.sh}"
SUBJ_BIN="${SUBJ:h}"
SUBJ_REPO="${SUBJ_REPO:-/tmp/t380-subject}"
WORK="${WORK:-/tmp/t380-knobs}"
/bin/rm -rf "$WORK"; /bin/mkdir -p "$WORK/hijack"

typeset -i CHECKS=0 WRONG=0

# knob <id> <VAR> <value> <want_rc> <want_regex> <forbid_regex|->
knob() {
  local id="$1" var="$2" val="$3" want_rc="$4" want_re="$5" forbid_re="$6" out; local -i rc
  out="$(env "$var=$val" FIRE_NO_SNAPSHOT=1 FIRE_SCRIPT_DIR="$SUBJ_BIN" GEREGE_NBFI_REPO="$SUBJ_REPO" \
         /bin/zsh "$SUBJ" --probe 2>&1)"; rc=$?
  print -r -- "$out" > "$WORK/$id.out"
  local v="ok"
  (( rc == want_rc )) || v="*** WRONG rc=$rc want=$want_rc"
  [[ "$v" == ok ]] && { print -r -- "$out" | LC_ALL=C grep -qE "$want_re" || v="*** WRONG missing /$want_re/"; }
  [[ "$v" == ok && "$forbid_re" != "-" ]] && { print -r -- "$out" | LC_ALL=C grep -qE "$forbid_re" && v="*** WRONG forbidden /$forbid_re/"; }
  [[ "$v" == ok ]] || (( WRONG+=1 )); (( CHECKS+=1 ))
  print -r -- "$id  $v  rc=$rc  $var=$val"
}

print -r -- "=== T380 knob + mktemp attack — subject $SUBJ"
print -r -- ""

# --- A. THE KNOB VALIDATOR. `EX_CONFIG` 78 must be reached, and the READER message must be
#        ABSENT — that is the whole discrimination F-T368-3 bought. -----------------------
READER='lock-reader self-test FAILED'
knob k01 LOCK_RELEASE_SKEW_SECS 'abc'                    78 'not a non-negative decimal integer of seconds' "$READER"
knob k02 LOCK_RELEASE_SKEW_SECS '99999999999999999999'   78 'does not fit this shell.s integer type; it wraps to -' "$READER"
knob k03 LOCK_RELEASE_SKEW_SECS '-100000'                78 'not a non-negative decimal integer' "$READER"
knob k04 LOCK_CEILING_SECS      'abc'                    78 'LOCK_CEILING_SECS is not a non-negative' "$READER"
knob k05 LOCK_CEILING_SECS      '0'                      78 'below its structural minimum of 1' "$READER"
knob k06 LOCK_MAX_AGE_SECS      '0'                      78 'below its structural minimum of 1' "$READER"
# ARITHMETIC INJECTION. The refusal QUOTES the payload back, so the token appears as DATA;
# only an ANCHORED `^INJECTED$` means it EXECUTED. (T377's own driver was wrong here first and
# kept the failing transcript; this case is written anchored from the start.)
knob k07 LOCK_RELEASE_SKEW_SECS '0)) || { print INJECTED; }; ((1' 78 'CONFIGURATION ERROR' '^INJECTED$'
knob k08 LOCK_RELEASE_SKEW_SECS '$(print INJECTED)'      78 'CONFIGURATION ERROR' '^INJECTED$'
# LEGITIMATE VALUES MUST STILL START THE FIRE — a bound, not a ban.
knob k09 LOCK_RELEASE_SKEW_SECS '0'                       0 'tally VERIFIED by the wiring' 'CONFIGURATION ERROR'
knob k10 LOCK_CEILING_SECS      '604800'                  0 'tally VERIFIED by the wiring' 'CONFIGURATION ERROR'
# LEADING ZEROS: accepted, and must not be misread as octal or tripped by the round-trip.
knob k11 LOCK_RELEASE_SKEW_SECS '0003600'                 0 'tally VERIFIED by the wiring' 'CONFIGURATION ERROR'
# EXACT int64 BOUNDARY, from BOTH sides. The round-trip must accept max and refuse max+1.
knob k12 LOCK_CEILING_SECS      '9223372036854775807'     0 'tally VERIFIED by the wiring' 'CONFIGURATION ERROR'
knob k13 LOCK_CEILING_SECS      '9223372036854775808'    78 'does not fit this shell.s integer type' "$READER"
# EMPTY and WHITESPACE — `set -u` plus `:-` default means empty takes the DEFAULT, so this
# must be GREEN; a lone space must be REFUSED.
knob k14 LOCK_RELEASE_SKEW_SECS ''                        0 'tally VERIFIED by the wiring' 'CONFIGURATION ERROR'
knob k15 LOCK_RELEASE_SKEW_SECS ' 3600'                  78 'CONFIGURATION ERROR' "$READER"
knob k16 LOCK_RELEASE_SKEW_SECS '+3600'                  78 'CONFIGURATION ERROR' "$READER"
knob k17 LOCK_RELEASE_SKEW_SECS '3600.0'                 78 'CONFIGURATION ERROR' "$READER"
knob k18 LOCK_RELEASE_SKEW_SECS '0x10'                   78 'CONFIGURATION ERROR' "$READER"

print -r -- ""
print -r -- "--- B. \$FIRE_MKTEMP must NEVER be resolvable through \$PATH or the environment ---"

# A hostile `mktemp` that would be found first by any $PATH lookup. It prints a directory it
# controls; if the wrapper ever used it, the marker below would appear.
cat > "$WORK/hijack/mktemp" <<'HIJACK'
#!/bin/sh
d="$(/usr/bin/mktemp -d /tmp/t380-hijacked.XXXXXX)"
printf 'HIJACKED-MKTEMP-WAS-CONSULTED\n' >&2
printf '%s\n' "$d"
HIJACK
/bin/chmod +x "$WORK/hijack/mktemp"

hij() {
  local id="$1"; shift
  local out; local -i rc
  out="$(env "$@" /bin/zsh "$SUBJ" --probe 2>&1)"; rc=$?
  print -r -- "$out" > "$WORK/$id.out"
  local v="ok"
  (( rc == 0 )) || v="*** WRONG rc=$rc want=0"
  [[ "$v" == ok ]] && { print -r -- "$out" | LC_ALL=C grep -q 'HIJACKED-MKTEMP-WAS-CONSULTED' && v="*** WRONG the planted mktemp WAS consulted"; }
  [[ "$v" == ok ]] && { /bin/ls -d /tmp/t380-hijacked.* >/dev/null 2>&1 && v="*** WRONG the planted mktemp left a scratch dir"; }
  [[ "$v" == ok ]] || (( WRONG+=1 )); (( CHECKS+=1 ))
  print -r -- "$id  $v  rc=$rc"
}

# h01 — $PATH entirely replaced by the attacker's directory.
hij h01 PATH="$WORK/hijack:/usr/bin:/bin" FIRE_NO_SNAPSHOT=1 FIRE_SCRIPT_DIR="$SUBJ_BIN" GEREGE_NBFI_REPO="$SUBJ_REPO"
# h02 — the attacker EXPORTS FIRE_MKTEMP itself, hoping the resolver honours an inherited value.
hij h02 FIRE_MKTEMP="$WORK/hijack/mktemp" FIRE_NO_SNAPSHOT=1 FIRE_SCRIPT_DIR="$SUBJ_BIN" GEREGE_NBFI_REPO="$SUBJ_REPO"
# h03 — both at once, AND with the T301 snapshot re-exec LIVE, so the second `mktemp` call
#       site (the snapshot dir) is exercised too.
hij h03 PATH="$WORK/hijack:/usr/bin:/bin" FIRE_MKTEMP="$WORK/hijack/mktemp" FIRE_SNAPSHOT_OF= FIRE_SCRIPT_DIR= FIRE_REPO_SCRIPT= GEREGE_NBFI_REPO="$SUBJ_REPO"

print -r -- ""
print -r -- "CHECKS=$CHECKS WRONG=$WRONG"
(( WRONG == 0 )) && { print -r -- "RESULT: PASS"; exit 0; }
print -r -- "RESULT: FAIL"; exit 1
