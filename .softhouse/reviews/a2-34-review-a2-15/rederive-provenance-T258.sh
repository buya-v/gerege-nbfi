#!/bin/bash
# A2-34 INDEPENDENT re-derivation of every promoted ledger vector cell.
# SUCCESSOR to rederive-provenance.sh, which is FAIL-OPEN and stays where it is.  [T258]
#
# WHY A SUCCESSOR AND NOT AN EDIT — the argument, because the argument is the deliverable
# ---------------------------------------------------------------------------------------
# `rederive-provenance.sh` hard-codes `R=/Users/.../worktrees/agent-ac008956278f2d6ea` at :11.
# That worktree was pruned. Its `cd "$R"` at :24 runs under `set -u` with no `-e` and no `||`,
# so the failed `cd` does not stop it, every later `glob` finds nothing, and it exits 0 printing
# `PROMOTED CELLS SWEPT: 0   NOT BYTE-PRESENT / ARITHMETIC FAIL: 0`. RE-MEASURED BY T258 AT ITS
# OWN COMMIT, by RUNNING it and not by reading it: exit 0, 31 lines of output, root ABSENT
# (transcript: .softhouse/capture/t255-frontier-rot/transcripts/40-original-fail-open.txt).
# It is TIER1B on FAILOPEN_PIN_FILE_LIST for exactly this.
#
# THE ORIGINAL IS DELIBERATELY LEFT UNREPAIRED, and that is not timidity:
#   * REPAIRING IT REMOVES IT FROM THE FAIL-OPEN FRONTIER. conformance.sh states the rule in its
#     own words -- a '-' line means "the pin must lose the row IN THE SAME COMMIT, or the pin
#     starts excusing a weakness that is no longer there". So an in-place repair REQUIRES an edit
#     to FAILOPEN_PIN_FILE_LIST in the same commit.
#   * `.softhouse/conformance.sh` IS HELD EXCLUSIVELY BY T323 THIS BATCH and T258 may not touch
#     it. An in-place repair here would therefore land a tree whose graded bar is EXIT 2 --
#     trading a recorded, pinned, visible weakness for a broken harness.
# So T258 STOPS AND REPORTS, which is what its brief instructs, and the exact one-line pin patch
# is in T258's handoff under `## Follow-ups`. WHOEVER APPLIES IT MUST DELETE OR REPAIR
# `rederive-provenance.sh` AND DROP THE TIER1B ROW IN ONE COMMIT. Until then the original is
# pinned, which is the honest state: recorded, visible, and refusing to grow.
#
# T114/T176 INDEPENDENTLY REQUIRE A SUCCESSOR RATHER THAN AN EDIT: a rig whose output is in the
# record gets a labelled correction or a successor file, never a retro-edit. CHECKED BEFORE
# WRITING, the way T236 checked: `find`/`grep` over every `*MANIFEST*` and `*.sha256` under
# `.softhouse/` names NEITHER `rederive-provenance.sh` NOR anything else in this directory, so no
# byte-pin is being broken either way -- but the successor convention applies regardless.
#
# WHAT IS DIFFERENT HERE, AND IT IS ONLY THE FAIL-CLOSEDNESS
# -----------------------------------------------------------
# The arithmetic and the sweeps are the reviewer's, unchanged in substance. What changed:
#   1. THE ROOT IS DISCOVERED, NEVER TYPED. `git rev-parse --show-toplevel`. No absolute path
#      literal appears in this file, so it cannot acquire a dead root the way the original did.
#   2. `set -euo pipefail`. A failed `cd` is fatal, so nothing downstream can report about a
#      directory that was never entered.
#   3. THE CORPUS IS ASSERTED BEFORE IT IS SWEPT (T238 C3). Zero vectors, or a missing capture
#      directory, is a REFUSAL with exit 2 -- never a zero printed as a result. THE ORIGINAL'S
#      DEFECT WAS NOT THE DEAD PATH; it was that a count of 0 and a count it never took printed
#      the same sentence.
#   4. THE P-72 CALIBRATION IS FATAL. The original ran one and printed an EMPTY count and carried
#      on, which is the calibration having no effect at all. Here a positive that is not found,
#      or a negative that is, exits 2 before any cell is reported.
#   5. THE FINAL COUNT CARRIES ITS OWN DENOMINATOR and the exit code follows the failures.
#
# MONEY (CLAUDE.md, non-negotiable): every amount is handled as INTEGER MINOR UNITS or as the
# EXACT DECIMAL TEXT from the vector. `amount_major_text` -> `amount_minor` is done by string
# surgery and `int()`, never by float, and never by Decimal-to-float. There is no `float(` in
# this file and no arithmetic on anything that has passed through one.
#
# ENGINE (P-33/P-53/P-75): `/usr/bin/grep` by absolute path, BSD grep, `LC_ALL=C`, `-a`, `-F`
# fixed strings only -- no regex metacharacter and no \b/\d anywhere.
#
# EXIT: 0 all promoted cells re-derived and byte-present; 1 at least one cell failed; 2 the rig
# could not reach or trust its corpus. It fails closed in every direction.
set -euo pipefail

R="$(git rev-parse --show-toplevel)"
cd "$R"
OUT="$R/.softhouse/capture/tierA-a2/out"
VD="$R/.softhouse/vectors/ledger"

die() { echo ""; echo "REFUSED -- $*"; echo "No count is reported, because no count was taken."; exit 2; }

echo "######## ROOT AND CORPUS (asserted before anything is swept)"
echo "repo root (discovered, never typed): $R"
echo "commit                             : $(git rev-parse HEAD)"
[ -d "$VD" ]  || die "the ledger vector directory is not there: $VD"
[ -d "$OUT" ] || die "the A2 capture directory is not there: $OUT"
NV=$(find "$VD" -maxdepth 1 -name '*.json' -type f | LC_ALL=C /usr/bin/grep -ac '' || true)
NA=$(find "$OUT" -maxdepth 1 -type f | LC_ALL=C /usr/bin/grep -ac '' || true)
echo "ledger vectors found               : $NV"
echo "capture artefacts found            : $NA"
[ "${NV:-0}" -ge 1 ] || die "ZERO ledger vectors. A rig that inspects nothing passes everything."
[ "${NA:-0}" -ge 1 ] || die "ZERO capture artefacts under $OUT."

echo ""
echo "######## ENGINE IDENTIFICATION"
command -v grep
/usr/bin/grep --version 2>&1 | head -2

echo ""
echo "######## CALIBRATION (P-72) -- FATAL, unlike the original's"
CALFILE="$(find "$VD" -maxdepth 1 -name '*.json' -type f | LC_ALL=C sort | head -1)"
echo "calibration subject: ${CALFILE#$R/}"
CALPOS=$(LC_ALL=C /usr/bin/grep -c -aF '"case_id"' "$CALFILE" || true)
CALNEG=$(LC_ALL=C /usr/bin/grep -c -aF 'ZZZ_NOT_PRESENT_ZZZ' "$CALFILE" || true)
echo "CAL+  '\"case_id\"'          : ${CALPOS:-<EMPTY>}"
echo "CAL-  'ZZZ_NOT_PRESENT_ZZZ' : ${CALNEG:-<EMPTY>}"
case "${CALPOS:-}" in ''|*[!0-9]*) die "the CAL+ count came back EMPTY OR NON-NUMERIC. The original printed exactly this and carried on." ;; esac
case "${CALNEG:-}" in ''|*[!0-9]*) die "the CAL- count came back EMPTY OR NON-NUMERIC." ;; esac
[ "$CALPOS" -ge 1 ] || die "CAL+ found ZERO known-positive hits. Every zero below would be a broken engine, not a measurement."
[ "$CALNEG" -eq 0 ] || die "CAL- found $CALNEG hits for a string that is not there. The engine is not measuring what it is asked."
echo "calibration OK -- a zero below is a real zero."

echo ""
echo "######## ARTEFACT EXISTENCE / SIZE / SHA256 (vs the sha the vector CITES)"
echo "######## THREE-PART CAPTURE CITATION (T233)"
echo "######## PER-CELL BYTE RE-DERIVATION -- integer minor units only, no float"
python3 - "$R" <<'PY'
import hashlib, json, os, sys, glob, subprocess

R = sys.argv[1]
vd = os.path.join(R, ".softhouse/vectors/ledger")
files = sorted(glob.glob(os.path.join(vd, "*.json")))
if not files:
    print("\nREFUSED -- the python arm globbed ZERO vectors after the shell arm counted some.")
    sys.exit(2)

def sweep(path, needle):
    """FIXED-STRING byte sweep. rc 0 = found, 1 = a real absence, anything else = engine error,
    which RAISES rather than being reported as an absence."""
    r = subprocess.run(["/usr/bin/grep", "-c", "-aF", needle, path],
                       capture_output=True, text=True,
                       env={"LC_ALL": "C", "PATH": "/usr/bin:/bin"})
    if r.returncode not in (0, 1):
        raise RuntimeError("grep exit %d on %s" % (r.returncode, path))
    return int(r.stdout.strip() or 0)

def minor_from_major_text(mt):
    """EXACT decimal text -> integer minor units, at 2dp. String surgery and int() only:
    no float, no Decimal-to-float, no rounding of any kind. '-1.5' -> -150, '3' -> 300."""
    neg = mt.startswith("-")
    body = mt[1:] if neg else mt
    ip, _, fp = body.partition(".")
    if len(fp) > 2 and fp[2:].strip("0"):
        raise ValueError("more than 2 significant decimal places in %r; minor-unit conversion "
                         "would lose money" % mt)
    fp = (fp + "00")[:2]
    v = int((ip or "0") + fp)
    return -v if neg else v

bad = 0
total = 0
checked_files = 0

for f in files:
    v = json.load(open(f, encoding="utf-8"))
    p = v["provenance"]
    cid_top = v["case_id"]
    checked_files += 1
    print("\n--- %s" % cid_top)

    # ---- artefact existence / sha256 -------------------------------------
    for label, refk, shak in (("RESP", "capture_ref", "capture_sha256"),
                              ("REQ ", "request_capture_ref", "request_capture_sha256")):
        total += 1
        ref = p.get(refk)
        if not ref:
            bad += 1
            print("    *** %s <ABSENT FROM VECTOR> (%s)" % (label, refk))
            continue
        ap = os.path.join(R, ref)
        if not os.path.exists(ap):
            bad += 1
            print("    *** %s MISSING FILE %s" % (label, ref))
            continue
        b = open(ap, "rb").read()
        d = hashlib.sha256(b).hexdigest()
        cited = p.get(shak, "")
        okd = (d == cited)
        oknz = bool(b.strip())
        if not (okd and oknz):
            bad += 1
        print("    %s %s %7dB sha=%s cited=%s %s %s"
              % ("OK " if (okd and oknz) else "***", label, len(b), d[:16], cited[:16],
                 "MATCH" if okd else "*** SHA MISMATCH ***",
                 "NONEMPTY" if oknz else "*** EMPTY ***"))

    # ---- three-part capture citation (T233) -------------------------------
    for label, refk, idk in (("RESP", "capture_ref", "capture_case_id"),
                             ("REQ ", "request_capture_ref", "request_capture_case_id")):
        total += 1
        ap = os.path.join(R, p[refk])
        cid = p[idk]
        b = open(ap, "rb").read()
        inbytes = cid.encode() in b
        infname = cid in os.path.basename(ap)
        side = ""
        for ext in (".http", ".status"):
            sp = os.path.splitext(ap)[0] + ext
            if os.path.exists(sp) and cid.encode() in open(sp, "rb").read():
                side += ext + " "
        found = inbytes or infname or bool(side)
        if not found:
            bad += 1
        print("    %s %s case_id=%s in_bytes=%s in_filename=%s sidecar=%s"
              % ("OK " if found else "***", label, cid, inbytes, infname, side or "-"))
    total += 1
    ri = p.get("rerun_invariant", "")
    if not ri.strip():
        bad += 1
    print("    %s rerun_invariant len=%d %s"
          % ("OK " if ri.strip() else "***", len(ri), "NON-EMPTY" if ri.strip() else "*** EMPTY ***"))

    # ---- per-cell byte re-derivation --------------------------------------
    resp = os.path.join(R, p["capture_ref"])
    req = os.path.join(R, p["request_capture_ref"])
    for i, leg in enumerate(v["expect"].get("legs", [])):
        total += 1
        mt = leg["amount_major_text"]
        mn = leg["amount_minor"]
        derived = minor_from_major_text(mt)
        okmath = (str(derived) == str(int(mn)))
        c_resp_alt = sweep(resp, mt)
        c_req = sweep(req, mt)
        flag = "OK " if (c_resp_alt > 0 and okmath) else "***"
        if flag == "***":
            bad += 1
        print("    %s leg[%d] gl=%3s code=%6s %6s major=%16s minor=%10s derived=%10d math=%s "
              "| '%s' in RESP=%d in REQ=%d"
              % (flag, i, leg["gl_account_id"], leg["gl_account_code"], leg["entry_side"],
                 mt, mn, derived, "OK" if okmath else "FAIL", mt, c_resp_alt, c_req))

    for k in ("total_debits_minor", "total_credits_minor"):
        val = v["expect"].get(k, "")
        if val and val != "0":
            total += 1
            legs = v["expect"]["legs"]
            side = "DEBIT" if "debit" in k else "CREDIT"
            s = sum(int(l["amount_minor"]) for l in legs if l["entry_side"] == side)
            ok = (str(s) == str(val))
            if not ok:
                bad += 1
            print("    %s %s = %s  recomputed from promoted legs = %d"
                  % ("OK " if ok else "***", k, val, s))

    ref = v["expect"].get("refusal", {})
    if ref.get("http_status"):
        for k in ("http_status", "code", "message"):
            total += 1
            needle = str(ref[k])
            c = sweep(resp, needle)
            sp = os.path.splitext(resp)[0] + ".status"
            cs = sweep(sp, needle) if os.path.exists(sp) else 0
            ok = (c > 0 or cs > 0)
            if not ok:
                bad += 1
            print("    %s refusal.%s = %r  in RESP=%d in .status sidecar=%d"
                  % ("OK " if ok else "***", k, needle[:70], c, cs))

print("\n    VECTOR FILES READ    : %d" % checked_files)
print("    PROMOTED CELLS SWEPT : %d   NOT BYTE-PRESENT / ARITHMETIC FAIL: %d" % (total, bad))
if total == 0:
    print("\nREFUSED -- ZERO cells swept over %d vector file(s). A zero here is not a result." % checked_files)
    sys.exit(2)
sys.exit(1 if bad else 0)
PY
