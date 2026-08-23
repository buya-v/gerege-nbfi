#!/usr/bin/env bash
# T256 — DRIVE the prescribed activation line. Do not assert that it is portable; run it.
#
# WHAT IS UNDER TEST. Not `go-env.sh` (T253b fixed that, T272 is grafting the strict arm onto
# it, and this drive deliberately does not touch it). What is under test is the ACTIVATION LINE
# that `.softhouse/reference-oracle.md` PRESCRIBES — the sentence that told sixty archived
# instruments to paste `/Users/buv/...` into themselves.
#
# THE LINE IS EXTRACTED FROM THE DOCUMENT AND EXECUTED. It is not copied into this file. If a
# future edit puts a host path back between the T256-ACTIVATION-LINE markers, this drive runs
# THAT and goes red off-host, quoting the offending line. The convention therefore does not ask
# anyone to remember it; it is executed by the thing that grades it.
#
#   P-45 — "A test-only guard is not a guard": a guard nobody has watched fail enforces nothing.
#   `--vacuity` below installs the PRE-T253b hardcoded go-env.sh into the same scratch checkout
#   and shows the assertions turn RED. Watch it fail before believing it when it passes.
#   P-70 — "Latent / not promoted / can never resolve / no guard exists" were four ways this
#   program stated a search result as a world fact: every absence below is decided by testing a
#   real file with `-x`/`-d`, never inferred from an exit status.
#   P-40 — "an enumerator must count what it skipped and say so": the drive count, the pass
#   count and the skip count are all printed, and a skip is a FAILURE here, not a shrug.
#
# ALL WORK HAPPENS IN A SCRATCH DIR. The shared `.softhouse/toolchain/` in the main checkout is
# NEVER moved, renamed or removed — other workers of this fire are compiling against it. "The
# toolchain is absent" is simulated by building a checkout that never had one, which is also a
# truer model of the cloud fire than hiding this host's copy would be.
#
# Usage:  bash 30-portability-red-drive.sh                  # the drive
#         bash 30-portability-red-drive.sh --vacuity        # the pre-T253b hardcode, ON this
#                                                           # host: the path RESOLVES, and the
#                                                           # assertions catch it anyway
#         bash 30-portability-red-drive.sh --vacuity-absent # the same hardcode with the path
#                                                           # NOT EXISTING — what a machine
#                                                           # that is not Buyan's Mac sees
# Exit:   0 every assertion held (or, in a vacuity mode, the assertions correctly went red).
#         1 an assertion failed / a vacuity mode failed to go red. 2 the drive could not run.

set -u -o pipefail

MODE="${1:-drive}"

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
DOC="$REPO/.softhouse/reference-oracle.md"
GO_ENV="$REPO/.softhouse/bin/go-env.sh"
GUARDS="$REPO/.softhouse/guards"

for f in "$DOC" "$GO_ENV" "$GUARDS/check-ledger-invariants.sh"; do
  if [ ! -f "$f" ]; then
    printf 'REFUSING: expected %s and it is not there — the drive is mis-anchored, and a\n' "$f" >&2
    printf 'REFUSING: mis-anchored drive that "passes" is worse than one that does not run.\n' >&2
    exit 2
  fi
done

FAILURES=0
ASSERTS=0
hr()  { printf '%s\n' "------------------------------------------------------------------------"; }
ok()  { ASSERTS=$((ASSERTS+1)); printf '  ASSERT OK   : %s\n' "$1"; }
bad() { ASSERTS=$((ASSERTS+1)); FAILURES=$((FAILURES+1)); printf '  ASSERT FAIL : %s\n' "$1"; }
has() { case "$1" in *"$2"*) return 0 ;; *) return 1 ;; esac; }

SCRATCH="$(mktemp -d "${TMPDIR:-/tmp}/t256.XXXXXXXXXX")"
trap 'rm -rf "$SCRATCH"' EXIT HUP INT TERM QUIT

# =========================================================================================
# STEP 0 — extract the prescribed activation line FROM THE DOCUMENT.
# =========================================================================================
hr
echo "STEP 0 — extract the activation line prescribed by reference-oracle.md"
ACT="$(awk '
  /T256-ACTIVATION-LINE:BEGIN/ { inblk=1; next }
  /T256-ACTIVATION-LINE:END/   { inblk=0 }
  inblk && /^```/              { fence=!fence; next }
  inblk && fence               { print }
' "$DOC")"
ACT_N="$(printf '%s\n' "$ACT" | grep -c . || true)"

echo "  markers  : T256-ACTIVATION-LINE:BEGIN … :END in $DOC"
echo "  extracted: [$ACT]"
echo "  lines    : $ACT_N"

if [ -z "$ACT" ]; then
  echo "REFUSING: no activation line between the markers. The document no longer prescribes" >&2
  echo "REFUSING: anything runnable, which is a defect this drive must not paper over." >&2
  exit 2
fi
[ "$ACT_N" -eq 1 ] && ok "the prescription is exactly ONE line (a line you must assemble is a line you will get wrong)" \
                   || bad "the prescription is $ACT_N lines, not 1"

# The whole point, stated as an assertion rather than a hope.
if has "$ACT" "/Users/"; then
  bad "the prescribed line names a host home directory: $ACT"
else
  ok "the prescribed line names no /Users/... home directory"
fi
if has "$ACT" "/home/"; then
  bad "the prescribed line names a host home directory: $ACT"
else
  ok "the prescribed line names no /home/... home directory"
fi

# =========================================================================================
# STEP 1 — GREEN, on this host: the prescribed line, run from three different directories.
# =========================================================================================
hr
echo "STEP 1 — GREEN: run the PRESCRIBED line verbatim from three working directories"
for d in "$REPO" "$REPO/nexus" "$REPO/.softhouse/guards"; do
  [ -d "$d" ] || { bad "cwd candidate does not exist: $d (measured with -d, not assumed)"; continue; }
  out="$(cd "$d" && eval "$ACT" >/dev/null 2>"$SCRATCH/e1" ; printf 'src=%s|go=%s|root=%s' \
        "${GEREGE_GO_SOURCE:-UNSET}" "$(command -v go || echo NONE)" "${GOROOT:-UNSET}")"
  rel="${d#"$REPO"}"; rel="${rel:-/}"
  echo "  cwd $rel"
  echo "    -> $out"
  if has "$out" "src=pinned"; then
    ok "cwd $rel : resolved the PINNED toolchain (GEREGE_GO_SOURCE=pinned)"
  else
    bad "cwd $rel : did not resolve the pinned toolchain — $out"
  fi
  if has "$out" "go=NONE"; then
    bad "cwd $rel : no go on PATH after activation"
  else
    ok "cwd $rel : a go binary is on PATH after activation"
  fi
done

# =========================================================================================
# STEP 2 — build the OFF-HOST checkout. A git repo with go-env.sh and the guard, and NO
#          toolchain — which is what the cloud fire actually has.
# =========================================================================================
hr
echo "STEP 2 — build a scratch checkout that has NO toolchain (the cloud fire's real shape)"
OFF="$SCRATCH/offhost"
mkdir -p "$OFF/.softhouse/bin" "$OFF/nexus"
git init -q "$OFF"
case "$MODE" in
  --vacuity|--vacuity-absent)
    # P-45: install the PRE-T253b hardcoded body and watch these same assertions go red.
    # The body is reproduced verbatim from .softhouse/capture/t253-portability/instruments/
    # 30-d2-red-drive.sh, which preserved it as a SPECIMEN. It is the defect, deliberately.
    if [ "$MODE" = "--vacuity" ]; then
      HARD_PREFIX="/Users/buv/gerege-nbfi"
      echo "  VACUITY MODE: the PRE-T253b HARDCODED go-env.sh, with the path AS WRITTEN."
      echo "  On THIS host that path exists, so the hardcode 'works' — the scratch checkout"
      echo "  silently borrows a FOREIGN checkout's toolchain. Nothing crashes. That is why a"
      echo "  human eyeballing it on a Mac never sees the defect, and why it must be ASSERTED."
    else
      HARD_PREFIX="$SCRATCH/not-buyans-mac"
      echo "  VACUITY-ABSENT MODE: the same hardcode with the path NOT EXISTING — i.e. every"
      echo "  host that is not Buyan's Mac, including the cloud fire. This is the D2 symptom."
    fi
    cat > "$OFF/.softhouse/bin/go-env.sh" <<OLDBODY
GEREGE_TOOLCHAIN=$HARD_PREFIX/.softhouse/toolchain
export GOROOT="\$GEREGE_TOOLCHAIN/go"
export GOPATH="\$GEREGE_TOOLCHAIN/gopath"
export GOCACHE="\$GEREGE_TOOLCHAIN/gocache"
export GOMODCACHE="\$GEREGE_TOOLCHAIN/gomodcache"
export PATH="\$GOROOT/bin:\$PATH"
OLDBODY
    echo "  Everything below should now FAIL. If it passes, the assertions are vacuous."
    ;;
  *)
    cp "$GO_ENV" "$OFF/.softhouse/bin/go-env.sh"
    ;;
esac
cp -R "$GUARDS" "$OFF/.softhouse/guards"
cp -R "$REPO/nexus/." "$OFF/nexus/"
if [ -d "$OFF/.softhouse/toolchain" ]; then
  bad "scratch checkout unexpectedly HAS a toolchain — the negative case is not negative"
else
  ok "scratch checkout has NO .softhouse/toolchain (decided by -d on the real directory)"
fi
echo "  scratch  : \$SCRATCH/offhost   (real path withheld — it is a mktemp, and printing it"
echo "             into a committed transcript would make the transcript un-reproducible)"

# A `go` that exists on PATH but is NOT at the pinned location: a one-line shim onto this
# host's real compiler. This is the cloud fire's likely condition (a distro/CI go on PATH).
SHIM="$SCRATCH/shim"
mkdir -p "$SHIM"
( cd "$REPO" && eval "$ACT" >/dev/null 2>&1 ; command -v go ) > "$SCRATCH/realgo" 2>/dev/null
REAL_GO="$(cat "$SCRATCH/realgo" 2>/dev/null || true)"
if [ -n "$REAL_GO" ] && [ -x "$REAL_GO" ]; then
  printf '#!/bin/sh\nexec "%s" "$@"\n' "$REAL_GO" > "$SHIM/go"
  chmod +x "$SHIM/go"
  ok "built a PATH-only \`go\` shim (a compiler that exists but is not the pinned one)"
else
  bad "could not locate a real go to shim — STEP 3 cannot run and is NOT being skipped quietly"
fi

# run_off CWD EXTRA_PATH EXTRA_ENV -> writes $SCRATCH/out and $SCRATCH/err, echoes a summary
run_off() {
  local extra_path="$1" pre="$2"
  ( cd "$OFF" \
    && export PATH="${extra_path}/usr/bin:/bin:/usr/sbin:/sbin" \
    && eval "$pre" \
    && eval "$ACT" >"$SCRATCH/out" 2>"$SCRATCH/err"
    printf 'src=%s|goroot=%s|go=%s\n' "${GEREGE_GO_SOURCE:-UNSET}" "${GOROOT:-UNSET}" "$(command -v go || echo NONE)" )
}

# =========================================================================================
# STEP 3 — RED ARM A: toolchain absent, a `go` IS on PATH. Announced fallback, and it RUNS.
# =========================================================================================
hr
echo "STEP 3 — RED ARM A: no pinned toolchain, a \`go\` on PATH"
sum="$(run_off "$SHIM:" "true")"
echo "  summary  : $sum"
echo "  --- stderr as a reader would see it ---"
sed 's/^/  | /' "$SCRATCH/err"
echo "  --- stdout ---"
if [ -s "$SCRATCH/out" ]; then sed 's/^/  | /' "$SCRATCH/out"; else echo "  | (empty)"; fi

has "$sum" "src=fallback-path" \
  && ok "GEREGE_GO_SOURCE=fallback-path — the substitution is RECORDED, not silent" \
  || bad "GEREGE_GO_SOURCE is not fallback-path: $sum"
has "$sum" "goroot=UNSET" \
  && ok "no GOROOT exported (a GOROOT pointing nowhere is the D2 symptom itself)" \
  || bad "a GOROOT was exported off-host: $sum"
has "$sum" "go=NONE" \
  && bad "no go on PATH after activation — the fallback did not take effect" \
  || ok "a usable go is on PATH after activation"
grep -q "NOT the pinned toolchain\|NOT THE PINNED TOOLCHAIN" "$SCRATCH/err" \
  && ok "stderr says in words that this is NOT the pinned toolchain" \
  || bad "stderr never says the toolchain is unpinned — that is the silence this fix exists to end"
grep -q "searched" "$SCRATCH/err" \
  && ok "stderr NAMES THE PATHS SEARCHED — 'not found' is reported as a statement about the search" \
  || bad "stderr asserts an absence without printing the search that produced it"

# Does it actually COMPILE off-host, or merely announce that it might?
echo "  --- proving the fallback compiles something real ---"
bout="$( cd "$OFF" \
         && export PATH="$SHIM:/usr/bin:/bin:/usr/sbin:/sbin" \
         && eval "$ACT" >/dev/null 2>&1 \
         && cd "$OFF/nexus" && go build ./... 2>&1 )"
brc=$?
echo "  go build ./... in the scratch nexus -> rc=$brc"
[ -n "$bout" ] && sed 's/^/  | /' <<<"$bout"
[ "$brc" -eq 0 ] \
  && ok "the fallback toolchain COMPILES the module off-host — resolution is real, not announced" \
  || bad "the fallback did not compile off-host (rc=$brc)"

# =========================================================================================
# STEP 4 — RED ARM B: toolchain absent AND no `go` anywhere. Must fail LOUDLY and LEGIBLY.
# =========================================================================================
hr
echo "STEP 4 — RED ARM B: no pinned toolchain and NO go on PATH at all"
sum="$(run_off "" "true")"
echo "  summary  : $sum"
echo "  --- stderr ---"
sed 's/^/  | /' "$SCRATCH/err"

has "$sum" "src=absent" \
  && ok "GEREGE_GO_SOURCE=absent — the state is named, not left to be guessed" \
  || bad "GEREGE_GO_SOURCE is not absent: $sum"
has "$sum" "goroot=UNSET" \
  && ok "nothing was exported" \
  || bad "something was exported with no compiler behind it: $sum"
[ -s "$SCRATCH/err" ] \
  && ok "the failure is LOUD (stderr is non-empty), not a silent no-op" \
  || bad "SILENT FAILURE — nothing on stderr. This is the exact defect the fix targets"

echo "  --- and now the REAL consumer, in the same condition ---"
gout="$( cd "$OFF" && export PATH="/usr/bin:/bin:/usr/sbin:/sbin" \
         && bash "$OFF/.softhouse/guards/check-ledger-invariants.sh" 2>&1 )"
grc=$?
echo "  check-ledger-invariants.sh -> rc=$grc"
sed 's/^/  | /' <<<"$gout" | head -20
[ "$grc" -eq 2 ] \
  && ok "the real guard EXITS 2 (unusable), which is a refusal and never a pass" \
  || bad "the real guard exited $grc off-host — expected 2"
has "$gout" "NOT a pass" \
  && ok "the guard says 'NOT a pass' in words a transcript reader cannot misread" \
  || bad "the guard's refusal is not legible in its own output"

# =========================================================================================
# STEP 5 — a STALE INHERITED GOROOT must be dropped, and the drop announced.
# =========================================================================================
hr
echo "STEP 5 — a stale inherited GOROOT (points at a directory that is not there)"
sum="$(run_off "$SHIM:" "export GOROOT=$SCRATCH/no-such-goroot")"
echo "  summary  : $sum"
echo "  --- stderr ---"
sed 's/^/  | /' "$SCRATCH/err"
has "$sum" "goroot=UNSET" \
  && ok "the stale GOROOT was DROPPED rather than passed along to break the fallback" \
  || bad "a stale GOROOT survived activation: $sum"
grep -q "dropping inherited GOROOT" "$SCRATCH/err" \
  && ok "the drop is ANNOUNCED on stderr" \
  || bad "the stale GOROOT was handled silently"

# =========================================================================================
# STEP 6 — the prescribed line run OUTSIDE any git checkout. It must fail LOUDLY.
#          This is the one place the self-locating form can misbehave, so it is driven, not
#          argued about.
# =========================================================================================
hr
echo "STEP 6 — the prescribed line run from a directory that is not inside any git checkout"
NOGIT="$SCRATCH/nogit"
mkdir -p "$NOGIT"
( cd "$NOGIT" && eval "$ACT" ) >"$SCRATCH/out" 2>"$SCRATCH/err"
nrc=$?
echo "  rc=$nrc"
echo "  --- stderr ---"
if [ -s "$SCRATCH/err" ]; then sed 's/^/  | /' "$SCRATCH/err"; else echo "  | (empty)"; fi
[ "$nrc" -ne 0 ] \
  && ok "non-zero rc outside a checkout — the caller can tell activation did not happen" \
  || bad "rc=0 outside any checkout: activation SILENTLY did nothing, the worst outcome"
[ -s "$SCRATCH/err" ] \
  && ok "and it said so on stderr" \
  || bad "and it said nothing at all"

# =========================================================================================
hr
echo "asserts: $ASSERTS   failures: $FAILURES   skipped-without-a-failure: 0"
echo "(a condition this drive could not exercise is recorded as an ASSERT FAIL above, never"
echo " dropped — P-40: an enumerator must count what it skipped and say so.)"
case "$MODE" in
  --vacuity|--vacuity-absent)
    hr
    if [ "$FAILURES" -gt 0 ]; then
      echo "VACUITY RESULT ($MODE): the assertions went RED against the pre-T253b hardcoded"
      echo "go-env.sh. They discriminate. A guard nobody has watched fail enforces nothing"
      echo "(P-45) — this one has now been watched failing, transcript committed beside it."
      exit 0
    fi
    echo "VACUITY RESULT ($MODE): THE ASSERTIONS PASSED AGAINST A KNOWN-BAD go-env.sh."
    echo "They are VACUOUS and prove nothing about the version that ships."
    exit 1
    ;;
esac
[ "$FAILURES" -eq 0 ] && { echo "DRIVE: GREEN"; exit 0; }
echo "DRIVE: RED — $FAILURES assertion(s) failed"
exit 1
