#!/bin/bash
# T253 D1 — RED/GREEN drive for the `mktemp -t NAME` portability defect.
#
# THE DEFECT. `.softhouse/conformance.sh` called `mktemp -t NAME` at TEN sites. The two
# mktemp implementations this program actually runs on parse that ARGUMENT LIST DIFFERENTLY,
# and the difference is in getopt's optstring, not in behaviour after parsing:
#
#   GNU coreutils 9.4  `mktemp [OPTION]... [TEMPLATE]`   -t takes NO argument (a flag,
#                      [deprecated]); the next word is the TEMPLATE, and "TEMPLATE must
#                      contain at least 3 consecutive 'X's in last component".
#                      [PRIMARY SOURCE: /usr/bin/mktemp --help, captured verbatim in
#                       transcripts/00-primary-sources.txt]
#   BSD / macOS        `mktemp [-d] [-p tmpdir] [-q] [-t prefix] [-u] template ...`
#                      -t takes `prefix` AS ITS OPTION-ARGUMENT, and mktemp then builds its
#                      own template from prefix + TMPDIR.
#                      [PRIMARY SOURCE: FreeBSD mktemp(1), fetched and captured verbatim in
#                       transcripts/00-primary-sources.txt]
#
# So `mktemp -t conformance-failopen` SUCCEEDS on BSD (prefix consumed) and FAILS on GNU
# (template with zero X's). That is exactly why the harness reads PASS on Buyan's Mac and
# died before the probe line on this Linux host.
#
# THE FIX, and why this form and not another. Both man pages document the SAME positional
# form, and the BSD page gives the shape verbatim as its worked example:
#     "The template may be any file name with some number of `Xs' appended to it,
#      for example /tmp/temp.XXXXXXXXXX."                       -- FreeBSD mktemp(1)
#     "mktemp [OPTION]... [TEMPLATE] ... TEMPLATE must contain at least 3 consecutive 'X's"
#                                                               -- GNU coreutils 9.4
# Ten X's satisfies GNU's >=3 minimum and BSD imposes no minimum. `-t` is dropped entirely,
# so no argument is ever ambiguous between the two parsers.
#
# HONESTY ABOUT THE BSD ARM. THERE IS NO BSD HOST HERE and no BSD mktemp binary
# (busybox ABSENT, toybox ABSENT, only GNU coreutils 9.4 -- see leg 0). LEG 3 therefore
# EXECUTES ONLY THE HALF THAT DIFFERS -- the getopt parse -- using optstrings transcribed
# from the two synopses above. It does NOT execute BSD's file creation, and this instrument
# never claims it does. The form was chosen because BOTH man pages specify it, not because
# it was observed to work here.
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="$SRC_DIR/../transcripts"
mkdir -p "$OUT"
GREP=/usr/bin/grep
pass=0; fail=0
ok()   { pass=$((pass+1)); printf 'OK    %s\n' "$*"; }
bad()  { fail=$((fail+1)); printf 'FAIL  %s\n' "$*"; }

echo "=============================================================================="
echo "LEG 0 -- ENGINE DECLARATION (P-72: name the program that produced every reading)"
echo "=============================================================================="
echo "mktemp binary : $(command -v mktemp)"
/usr/bin/mktemp --version 2>&1 | sed -n '1p'
echo "bash          : $BASH_VERSION"
echo "python3       : $(python3 -V 2>&1)"
echo "BSD mktemp    : $( { command -v busybox || command -v toybox; } 2>/dev/null || echo 'ABSENT -- no BSD/BSD-alike mktemp on this host' )"
echo

# ---------------------------------------------------------------------------------------
# LEG 1 -- THE OLD FORM, EXECUTED. Every shape here is a REAL invocation of the REAL binary.
# ---------------------------------------------------------------------------------------
echo "=============================================================================="
echo "LEG 1 -- OLD FORM \`mktemp -t NAME\` DRIVEN RED on real GNU coreutils 9.4"
echo "=============================================================================="
# Shape 1a: the exact literal that killed the run today.
if err="$(mktemp -t conformance-failopen 2>&1)"; then
  bad "1a old-form file: expected FAILURE, got success -> $err"
else
  if printf '%s' "$err" | $GREP -qF "too few X's"; then
    ok "1a old-form file  REFUSED as designed: $err"
  else
    bad "1a old-form file failed for the WRONG reason: $err"
  fi
fi

# Shape 1b: TYPE drive, not a string drive -- the DIRECTORY form (`-d`), which is site 1960
# and a different code path in mktemp, not merely a different name.
if err="$(mktemp -d -t conformance-prove 2>&1)"; then
  bad "1b old-form DIR: expected FAILURE, got success -> $err"; rmdir "$err" 2>/dev/null || true
else
  ok "1b old-form DIR   REFUSED as designed: $err"
fi

# Shape 1c: A SHAPE THE RULE WAS NOT DESIGNED AROUND (P-76). "just add some X's to the -t
# argument" is the obvious cheap patch. It is still wrong: GNU demands THREE consecutive.
if err="$(mktemp -t conformance-XX 2>&1)"; then
  bad "1c old-form, 2 X's: expected FAILURE, got success -> $err"
else
  ok "1c old-form 2 X's REFUSED (>=3 required, so 'sprinkle X's' is not the fix): $err"
fi

# Shape 1d: THE NEAR-MISS THAT WOULD HAVE PASSED HERE AND STAYED BROKEN ON BSD.
# `-t NAME.XXXXXXXXXX` satisfies GNU. On BSD, -t swallows it as a PREFIX and BSD appends its
# own suffix, so the file lands in TMPDIR with a literal 'XXXXXXXXXX' baked into its name.
# It "works" on both and is wrong on one; a green light here would have hidden that.
if out="$(mktemp -t conformance-nearmiss.XXXXXXXXXX 2>&1)"; then
  ok "1d NEAR-MISS -t NAME.XXXXXXXXXX SUCCEEDS on GNU -> $out"
  echo "      ^ this is why leg 3 exists: passing here says NOTHING about the BSD parse."
  rm -f "$out"
else
  bad "1d near-miss unexpectedly failed: $out"
fi
echo

# ---------------------------------------------------------------------------------------
# LEG 2 -- THE NEW FORM, EXECUTED, over the ENVIRONMENT TYPES that decide the directory.
# TMPDIR is the input whose *type* (unset / set / empty / trailing slash / nonexistent)
# changes the answer, and macOS always sets it WITH A TRAILING SLASH.
# ---------------------------------------------------------------------------------------
echo "=============================================================================="
echo "LEG 2 -- NEW FORM \"\$dir/NAME.XXXXXXXXXX\" DRIVEN GREEN across TMPDIR TYPES"
echo "=============================================================================="
newform() {  # $1 = the already-resolved directory
  mktemp "${1%/}/conformance-t253.XXXXXXXXXX"
}
resolve() {  # exactly the expression the fix uses
  local d="${TMPDIR:-/tmp}"; d="${d%/}"; [ -n "$d" ] || d=/
  printf '%s' "$d"
}

drive_tmpdir() { # $1 label, $2 = "unset" or the value
  local label="$1" val="$2" d f
  if [ "$val" = "unset" ]; then unset TMPDIR; else export TMPDIR="$val"; fi
  d="$(resolve)"
  if f="$(newform "$d" 2>&1)"; then
    case "$f" in
      *//*) bad "2 $label -> DOUBLE SLASH in $f" ;;
      *XXX*) bad "2 $label -> X's NOT substituted: $f" ;;
      *) ok "2 $label  dir=[$d]  ->  $f"; rm -f "$f" ;;
    esac
  else
    bad "2 $label -> $f"
  fi
}
drive_tmpdir "TMPDIR unset            " unset
drive_tmpdir "TMPDIR=/tmp             " /tmp
drive_tmpdir "TMPDIR=/tmp/  (macOS!)  " /tmp/
drive_tmpdir "TMPDIR='' (empty)       " ""
unset TMPDIR

# TYPE drive: the DIRECTORY form must survive the same treatment.
d="$(resolve)"
if f="$(mktemp -d "${d%/}/conformance-t253d.XXXXXXXXXX" 2>&1)"; then
  if [ -d "$f" ]; then ok "2 DIR form (-d) created a DIRECTORY -> $f"; rmdir "$f"
  else bad "2 DIR form did not produce a directory: $f"; fi
else
  bad "2 DIR form -> $f"
fi

# NEGATIVE CONTROL (P-72): the probe must be able to go red. A nonexistent directory MUST
# fail. Without this, "every new-form drive passed" would be unfalsifiable.
if f="$(mktemp "/nonexistent-t253-$$/conformance.XXXXXXXXXX" 2>&1)"; then
  bad "2 NEGATIVE CONTROL: nonexistent dir SUCCEEDED -> $f"
else
  ok "2 NEGATIVE CONTROL nonexistent dir correctly REFUSED: $f"
fi
echo

# ---------------------------------------------------------------------------------------
# LEG 3 -- THE BSD ARM, executed only where it CAN be: the getopt parse.
# ---------------------------------------------------------------------------------------
echo "=============================================================================="
echo "LEG 3 -- OPTION-PARSE DISCRIMINATION, both optstrings, EXECUTED"
echo "         (this executes the PARSE only -- BSD file creation is NOT executed here)"
echo "=============================================================================="
python3 - <<'PY'
import getopt
# Optstrings transcribed from the two synopses captured in 00-primary-sources.txt.
#   GNU  : -t is a FLAG                      -> "dqut"   (t has NO colon)
#   BSD  : -t takes `prefix` as its argument -> "dp:qt:u" (t HAS a colon)
CASES = [
    ("OLD  mktemp -t conformance-failopen",       ["-t", "conformance-failopen"]),
    ("NEW  mktemp /tmp/conformance.XXXXXXXXXX",   ["/tmp/conformance-failopen.XXXXXXXXXX"]),
    ("NEW  mktemp -d /tmp/conformance.XXXXXXXXXX",["-d", "/tmp/conformance-prove.XXXXXXXXXX"]),
]
def parse(optstring, argv):
    opts, rest = getopt.getopt(argv, optstring)
    return dict(opts), rest

rows = []
for label, argv in CASES:
    g = parse("dqut",   argv)
    b = parse("dp:qt:u", argv)
    rows.append((label, g, b))

print("  %-46s %-34s %s" % ("argv", "GNU parse (t = flag)", "BSD parse (t: = takes arg)"))
for label, g, b in rows:
    print("  %-46s %-34s %s" % (label, "opts=%s tmpl=%s" % (g[0], g[1]), "opts=%s tmpl=%s" % (b[0], b[1])))
print()

ok = True
# The OLD form must be parsed DIFFERENTLY by the two -- that IS the defect.
label, g, b = rows[0]
if g[1] == ["conformance-failopen"] and b[1] == []:
    print("OK    3a OLD form: GNU sees TEMPLATE ['conformance-failopen'] (0 X's -> refused);")
    print("      3a          BSD sees NO template and prefix='conformance-failopen' (accepted).")
    print("      3a          THE TWO PARSERS DISAGREE. That is the whole defect, executed.")
else:
    ok = False; print("FAIL  3a old form did not discriminate: GNU=%s BSD=%s" % (g, b))

# The NEW form must be parsed IDENTICALLY by the two -- that is what makes it portable.
for idx, name in ((1, "3b NEW file form"), (2, "3c NEW dir form")):
    label, g, b = rows[idx]
    if g == b:
        print("OK    %s: BOTH parsers agree -- opts=%s template=%s" % (name, g[0], g[1]))
    else:
        ok = False; print("FAIL  %s parsers disagree: GNU=%s BSD=%s" % (name, g, b))

# NEGATIVE CONTROL for leg 3: a form that SHOULD still discriminate, proving the comparison
# is not vacuously equal. `-t` with a following template is ambiguous no matter what.
g = parse("dqut",    ["-t", "foo.XXXXXXXXXX"])
b = parse("dp:qt:u", ["-t", "foo.XXXXXXXXXX"])
if g != b:
    print("OK    3d NEGATIVE CONTROL: `-t foo.XXXXXXXXXX` STILL disagrees (GNU tmpl=%s, BSD tmpl=%s)"
          % (g[1], b[1]))
    print("      3d           -- so leg 3's equality test is discriminating, not vacuous,")
    print("      3d           and the 'just add X's after -t' patch is REFUSED here too.")
else:
    ok = False; print("FAIL  3d negative control did not discriminate")
raise SystemExit(0 if ok else 1)
PY
rc=$?
if [ "$rc" -eq 0 ]; then pass=$((pass+4)); else fail=$((fail+1)); fi
echo
echo "=============================================================================="
printf 'T253 D1 DRIVE: %d OK, %d FAIL\n' "$pass" "$fail"
echo "=============================================================================="
[ "$fail" -eq 0 ]
