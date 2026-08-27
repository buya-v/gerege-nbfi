#!/bin/bash
# A2-34 INDEPENDENT re-derivation of every promoted ledger vector cell.
# Written by the REVIEWER. Does not reuse A2-15's verify-provenance-a2-15.py.
#
# Engine discipline (P-72): every sweep below is `LC_ALL=C /usr/bin/grep -c -aF`
# — /usr/bin/grep is BSD grep, -F is FIXED STRING so no regex metacharacter and
# no \b is involved at all, -a forces binary-safe text mode, LC_ALL=C pins the
# collation. A calibration positive AND a calibration negative are run first so
# every zero below is known to be a real zero and not a silent engine refusal.
set -u
R=/Users/buv/gerege-nbfi/.claude/worktrees/agent-ac008956278f2d6ea
OUT="$R/.softhouse/capture/tierA-a2/out"
G="LC_ALL=C /usr/bin/grep"

echo "######## ENGINE IDENTIFICATION"
echo "-- which grep (interactive name may be a function; scripts get this one):"
command -v grep
/usr/bin/grep --version 2>&1 | head -2
echo "-- does /usr/bin/grep -P exist?"
echo abc | LC_ALL=C /usr/bin/grep -P 'a\wc' ; echo "   /usr/bin/grep -P exit=$?"
echo "-- does /usr/bin/grep honour \\b ?"
echo "hello world" | LC_ALL=C /usr/bin/grep -c '\bworld\b' ; echo "   exit=$?"
echo "-- git grep -E with \\b (T232/T234 claim: reads b literally, returns zero):"
cd "$R"; git grep -c -E '\bledger\b' -- .softhouse/vectors/ledger/LDG-01-manual-je-3leg-minor-units.json ; echo "   git grep -E exit=$?"
git grep -c -F 'ledger' -- .softhouse/vectors/ledger/LDG-01-manual-je-3leg-minor-units.json ; echo "   git grep -F exit=$?"

echo
echo "######## CALIBRATION (P-72): instrument must show non-zero recall AND a true zero"
echo -n "CAL+  '\"amount\"' in A2-347 : "; LC_ALL=C /usr/bin/grep -c -aF '"amount"' "$OUT/A2-347-je-manual-readback.json"
echo -n "CAL-  'ZZZ_NOT_PRESENT_ZZZ' in A2-347 : "; LC_ALL=C /usr/bin/grep -c -aF 'ZZZ_NOT_PRESENT_ZZZ' "$OUT/A2-347-je-manual-readback.json"

echo
echo "######## ARTEFACT EXISTENCE / SIZE / SHA256 (vs the sha the vector CITES)"
python3 - "$R" <<'PY'
import hashlib, json, os, sys, glob
R = sys.argv[1]
vd = os.path.join(R, ".softhouse/vectors/ledger")
for f in sorted(glob.glob(os.path.join(vd, "*.json"))):
    v = json.load(open(f))
    p = v["provenance"]
    for label, refk, shak in (("RESP", "capture_ref", "capture_sha256"),
                              ("REQ ", "request_capture_ref", "request_capture_sha256")):
        ref = p.get(refk)
        if not ref:
            print(f"{v['case_id']:48s} {label} <ABSENT FROM VECTOR>")
            continue
        ap = os.path.join(R, ref)
        if not os.path.exists(ap):
            print(f"{v['case_id']:48s} {label} MISSING FILE {ref}")
            continue
        b = open(ap, "rb").read()
        d = hashlib.sha256(b).hexdigest()
        cited = p.get(shak, "")
        print(f"{v['case_id']:48s} {label} {len(b):7d}B sha={d[:16]} cited={cited[:16]} {'MATCH' if d==cited else '*** SHA MISMATCH ***'} {'NONEMPTY' if b.strip() else '*** EMPTY ***'}")
PY

echo
echo "######## THREE-PART CAPTURE CITATION (T233): capture_case_id occurs in the artefact bytes; rerun_invariant non-empty"
python3 - "$R" <<'PY'
import json, os, sys, glob
R = sys.argv[1]
vd = os.path.join(R, ".softhouse/vectors/ledger")
for f in sorted(glob.glob(os.path.join(vd, "*.json"))):
    v = json.load(open(f)); p = v["provenance"]
    for label, refk, idk in (("RESP", "capture_ref", "capture_case_id"),
                             ("REQ ", "request_capture_ref", "request_capture_case_id")):
        ap = os.path.join(R, p[refk]); cid = p[idk]
        b = open(ap, "rb").read()
        # the id may live in the artefact bytes OR in its .http/.status sidecar or the filename
        inbytes = cid.encode() in b
        infname = cid in os.path.basename(ap)
        side = ""
        for ext in (".http", ".status"):
            sp = os.path.splitext(ap)[0] + ext
            if os.path.exists(sp) and cid.encode() in open(sp, "rb").read():
                side += ext + " "
        print(f"{v['case_id']:48s} {label} case_id={cid:38s} in_bytes={inbytes} in_filename={infname} sidecar={side or '-'}")
    ri = p.get("rerun_invariant", "")
    print(f"{v['case_id']:48s} rerun_invariant len={len(ri)} {'NON-EMPTY' if ri.strip() else '*** EMPTY ***'}")
PY

echo
echo "######## PER-CELL BYTE RE-DERIVATION — every promoted amount_major_text, swept with grep -aF"
python3 - "$R" <<'PY'
import json, os, sys, glob, subprocess
R = sys.argv[1]
vd = os.path.join(R, ".softhouse/vectors/ledger")
bad = 0; total = 0
for f in sorted(glob.glob(os.path.join(vd, "*.json"))):
    v = json.load(open(f)); p = v["provenance"]
    resp = os.path.join(R, p["capture_ref"]); req = os.path.join(R, p["request_capture_ref"])
    print(f"--- {v['case_id']}")
    print(f"    resp artefact: {p['capture_ref']}")
    print(f"    req  artefact: {p['request_capture_ref']}")
    def sweep(path, needle):
        r = subprocess.run(["/usr/bin/grep", "-c", "-aF", needle, path],
                           capture_output=True, text=True, env={"LC_ALL": "C", "PATH": "/usr/bin:/bin"})
        return int(r.stdout.strip() or 0), r.returncode
    for i, leg in enumerate(v["expect"].get("legs", [])):
        total += 1
        mt = leg["amount_major_text"]; mn = leg["amount_minor"]
        # exact-string arithmetic: major text -> minor integer, no float
        ip, _, fp = mt.partition(".")
        fp = (fp + "00")[:2]
        derived = str(int(ip) * 100 + int(fp) * (1 if ip.lstrip("-") else 1)) if not mt.startswith("-") else None
        derived = str(int(ip + fp.ljust(2, "0")))  # concatenation IS the minor-unit integer at 2dp
        okmath = (derived.lstrip("0") or "0") == (mn.lstrip("0") or "0")
        c_resp, rc1 = sweep(resp, f'"amount":{mt}')
        c_resp_alt, _ = sweep(resp, mt)
        c_req, _ = sweep(req, mt)
        c_req_short, _ = sweep(req, mt.rstrip("0").rstrip("."))
        flag = "OK " if (c_resp_alt > 0 and okmath) else "***"
        if flag == "***": bad += 1
        print(f"    {flag} leg[{i}] gl={leg['gl_account_id']:>3} code={leg['gl_account_code']:>6} {leg['entry_side']:>6} "
              f"major={mt:>16} minor={mn:>10} derived={derived:>10} math={'OK' if okmath else 'FAIL'} "
              f"| grep -aF '\"amount\":{mt}' in RESP = {c_resp} | grep -aF '{mt}' in RESP = {c_resp_alt} "
              f"| in REQ (scale6)={c_req} (short '{mt.rstrip('0').rstrip('.')}')={c_req_short}")
    for k in ("total_debits_minor", "total_credits_minor"):
        val = v["expect"].get(k, "")
        if val and val != "0":
            total += 1
            legs = v["expect"]["legs"]
            side = "DEBIT" if "debit" in k else "CREDIT"
            s = sum(int(l["amount_minor"]) for l in legs if l["entry_side"] == side)
            ok = str(s) == val
            if not ok: bad += 1
            print(f"    {'OK ' if ok else '***'} {k} = {val}  recomputed from promoted legs = {s}")
    ref = v["expect"].get("refusal", {})
    if ref.get("http_status"):
        for k in ("http_status", "code", "message"):
            total += 1
            needle = str(ref[k])
            c, _ = sweep(resp, needle)
            # status may live in the .status sidecar
            sp = os.path.splitext(resp)[0] + ".status"
            cs = 0
            if os.path.exists(sp):
                cs, _ = sweep(sp, needle)
            ok = c > 0 or cs > 0
            if not ok: bad += 1
            print(f"    {'OK ' if ok else '***'} refusal.{k} = {needle[:70]!r}  grep -aF in RESP={c} in .status sidecar={cs}")
print(f"\n    PROMOTED CELLS SWEPT: {total}   NOT BYTE-PRESENT / ARITHMETIC FAIL: {bad}")
PY
