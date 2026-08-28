#!/usr/bin/env python3
"""T357 — ADJUDICATE run-all.sh section 1. Makes an unread RED into a guard that can fail.

THE PROBLEM THIS FIXES, stated as the measurement that found it.
`check-shape.py` has been RED with three named failures since the day it was committed
(they are in TRANSCRIPT-A2-11.txt as generated 2026-08-21T08:11:39Z, they were still
there when T270 re-ran it, still there when T339 re-ran it, and still there when T357
re-ran it). Nobody read them. A verdict nobody reads is not a verdict, and a RED that is
permanently RED is indistinguishable from a RED that just broke -- which is the same
class of trap T270 removed from section 8: a line that always prints the same thing and
therefore carries no information.

WHY check-shape.py IS NOT EDITED. Its three failures are CORRECT and they are the
executable form of a settled finding. run-all.sh states the reading rule -- "sections 1
and 2 assert A2-7'S CLAIMS, so a non-zero exit there is a FINDING AGAINST A2-7, not a
broken script" -- and A2-7's claim here was refuted and struck from the record:

  * A2-11 finding F-1 (.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/
    A2-11.md:429-449) -- A2-7 printed a fenced JSON block attributed to capture
    A2-211-read-product-nine-mandatory.json whose last three lines were FABRICATED.
  * The driver's correction, in place, at A2-7.md:211-221.
  * A2-8, which was consuming the false rule, shipped the correction: A2-8.md:101-120.
  * Recorded as patterns.md P-46 -- "A FABRICATED CAPTURE EXCERPT SURVIVED INTO MERGED
    EVIDENCE, AND ONLY THE PAIRED REVIEWER CAUGHT IT", whose rule 3 is the substance
    here: "Absent != null != empty. In a contract-boundary port these are three
    different wire shapes, and the difference is omitempty/pointer-vs-value in Go."

So the repair is not to make section 1 green. It is to make its RED READABLE and
FALSIFIABLE: this file pins the three adjudicated failures and goes RED if a FOURTH
appears (a new, unadjudicated defect) or if any of the three DISAPPEARS (someone
"fixed" the checker into agreeing with the fabricated claim, which would re-admit
the very error P-46 exists to prevent).

P-22 -- "a guard you have not seen fail is not a guard": every arm below is exercised
against a deliberately broken input in the NEGATIVE CONTROLS section, and this file
exits non-zero if a control fails to trip.
P-25 -- no floating point. Nothing here parses a number; the only numeric values are
counts produced by len().
"""
import ast
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOFTHOUSE = HERE.parents[1]
CHECK = HERE / "check-shape.py"

fails = []


def check(label, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + label + (("\n          " + detail) if detail else ""))
    if not cond:
        fails.append(label)


# --------------------------------------------------------------------------------------
# The three adjudicated failures, pinned by their exact label text as check-shape.py
# prints them (two leading spaces are part of the label, from check-shape.py:77).
# --------------------------------------------------------------------------------------
ADJUDICATED = {
    "  paymentChannelToFundSourceMappings present and null",
    "  feeToIncomeAccountMappings present and null",
    "  penaltyToIncomeAccountMappings present and null",
}


def parse_verdict(stdout, rc):
    """Pure function: transcript text + exit code -> (failure set, declared count).

    Factored out so the NEGATIVE CONTROLS below can feed it fabricated transcripts and
    watch the adjudication trip. A verdict reader that is only ever fed the real, passing
    input is exactly the non-falsifiable check this review keeps finding.
    """
    m = re.search(r"^FAILURES: (\d+)$", stdout, re.M)
    declared = int(m.group(1)) if m else None
    named = set()
    if m:
        for line in stdout[m.end():].splitlines():
            if line.startswith("  - "):
                named.add(line[4:])
    return named, declared, rc


# --------------------------------------------------------------------------------------
print("=== 1. section 1 is OFFLINE — proved from check-shape.py's AST, not from its prose ===")
print("    run-all.sh advertised this section as '[ORACLE] live re-observation'. It is")
print("    neither. It replays committed bytes under obs/. Proving that is what makes the")
print("    corrected label a measurement instead of a second unchecked adjective.")

NETWORK_TOKENS = {
    "urllib", "http", "httplib", "requests", "socket", "ssl", "ftplib", "telnetlib",
    "urllib2", "httpx", "aiohttp", "curl", "subprocess", "os.system", "popen",
}


def network_evidence(src, name):
    """Return every token in SRC that would let it reach the network. Empty == offline."""
    tree = ast.parse(src, filename=name)
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.split(".")[0] in NETWORK_TOKENS:
                    hits.append("import %s" % a.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".")[0] in NETWORK_TOKENS:
                hits.append("from %s import ..." % node.module)
        elif isinstance(node, ast.Attribute):
            if node.attr in ("urlopen", "system", "popen", "Popen", "run", "check_output"):
                hits.append("call .%s(" % node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            low = node.value.lower()
            if low.startswith("http://") or low.startswith("https://"):
                hits.append("URL literal %r" % node.value)
    return sorted(set(hits))


check_src = CHECK.read_text()
hits = network_evidence(check_src, "check-shape.py")
check("check-shape.py contains NO route to the network (AST-walked: imports, attribute "
      "calls, URL literals)", hits == [], "hits=%s" % hits)

imports = sorted({n.names[0].name.split(".")[0] for n in ast.walk(ast.parse(check_src))
                  if isinstance(n, ast.Import)}
                 | {n.module.split(".")[0] for n in ast.walk(ast.parse(check_src))
                    if isinstance(n, ast.ImportFrom) and n.module})
check("check-shape.py's whole import set is {json, sys, decimal, pathlib}",
      imports == ["decimal", "json", "pathlib", "sys"], str(imports))

print()
print("=== 2. and it is DETERMINISTIC — run twice, compare bytes ===")
r1 = subprocess.run([sys.executable, str(CHECK)], capture_output=True, text=True)
r2 = subprocess.run([sys.executable, str(CHECK)], capture_output=True, text=True)
check("two consecutive runs of check-shape.py emit byte-identical stdout",
      r1.stdout == r2.stdout, "len=%d vs %d" % (len(r1.stdout), len(r2.stdout)))
check("two consecutive runs of check-shape.py return the same exit code",
      r1.returncode == r2.returncode, "rc=%d vs %d" % (r1.returncode, r2.returncode))

print()
print("=== 3. the verdict: exit 1, and EXACTLY the three adjudicated failures ===")
named, declared, rc = parse_verdict(r1.stdout, r1.returncode)
check("check-shape.py exits 1 (RED)", rc == 1, "rc=%d" % rc)
check("it declares a failure COUNT and names that many", declared == len(named),
      "declared=%s named=%d" % (declared, len(named)))
unexpected = sorted(named - ADJUDICATED)
missing = sorted(ADJUDICATED - named)
check("NO UNADJUDICATED FAILURE — a fourth failure here is a NEW defect and must be "
      "read, not absorbed", unexpected == [], "unexpected=%s" % unexpected)
check("all three adjudicated failures are STILL PRESENT — losing one would mean the "
      "checker was edited into agreeing with the fabricated A2-7 claim (P-46)",
      missing == [], "missing=%s" % missing)

print()
print("  ADJUDICATION of each, and it is the SAME for all three:")
print("    VERDICT   NOT a defect in the observed evidence. NOT a defect in the checker's")
print("              arithmetic. The checker asserts A2-7's REFUTED claim, and the RED is")
print("              the correct, intended verdict — the executable form of P-46 / A2-11 F-1.")
print("    EVIDENCE  T357 re-observed GET /loanproducts/{46,22,28} and /glaccounts/2 from the")
print("              LIVE reference oracle on fire 20260828-140005 and the bytes came back")
print("              BYTE-IDENTICAL to the committed obs/ files (sha256 match, 4 of 4). The")
print("              obs bytes are not stale and not corrupt. See")
print("              .softhouse/capture/t357-a2-11-section1-red/.")
print("    SOURCE    Fineract's read path serialises through GoogleGsonSerializerHelper,")
print("              which never calls serializeNulls() [VERIFIED: fineract-core/src/main/")
print("              java/org/apache/fineract/infrastructure/core/serialization/")
print("              GoogleGsonSerializerHelper.java — the ONLY serializeNulls() in")
print("              fineract-core + fineract-provider is CommandProcessingResultJson")
print("              Serializer.java:38, the COMMAND-RESULT serializer, not the read")
print("              serializer]. Gson omits null fields by default, so on the read path a")
print("              null-valued field is ABSENT — uniformly, for scalar mapping slots AND")
print("              for collection-valued mapping fields alike. A2-7's 'the collection-")
print("              valued mapping fields behave the opposite way: they are present with")
print("              the value null' is refuted at the source, not merely at the wire.")
print("    CONTRAST  Product 22 has a payment-channel override, and there")
print("              paymentChannelToFundSourceMappings IS present, as a LIST. Set -> present.")
print("              Unset -> absent. Never null. That is the rule the Go port must encode")
print("              (`omitempty` / pointer-vs-value), and it is P-46 rule 3.")
print("    MONEY     Checked and NEGATIVE: none of the three is about rounding, precision or")
print("              a float-shaped cell. check-shape.py parses every document with")
print("              parse_float=Decimal (:25, :47) and compares only ids, key sets and")
print("              strings. No money value is asserted anywhere in section 1, so the")
print("              MathContext(19, HALF_UP) admissibility rule is not engaged. This is a")
print("              WIRE-SHAPE finding, graded MATERIAL-TO-THE-PORT and IMMATERIAL-TO-THE-")
print("              CORPUS — see section 4, which measures the corpus half rather than")
print("              asserting it.")

print()
print("=== 4. THE CORPUS QUESTION, MEASURED: does any of the three touch a GRADED vector? ===")
print("    Searched: every file under .softhouse/vectors/ (recursive), and .softhouse/")
print("    conformance.sh. Tokens: the three key names, 'accountingMappings', 'loanproduct',")
print("    and the capture files section 1 replays.")
TOKENS = ["paymentChannelToFundSourceMappings", "feeToIncomeAccountMappings",
          "penaltyToIncomeAccountMappings", "accountingMappings", "loanproduct",
          "A2-211-read-product-nine-mandatory", "a2-11-get-loanproduct"]
vector_files = sorted(p for p in (SOFTHOUSE / "vectors").rglob("*") if p.is_file())
conf = SOFTHOUSE / "conformance.sh"
hit_rows = []
for tok in TOKENS:
    vhits = [p for p in vector_files if tok in p.read_text(errors="replace")]
    chits = tok in conf.read_text(errors="replace")
    hit_rows.append((tok, len(vhits), chits, [str(p.relative_to(ROOT)) for p in vhits]))
    print("      %-38s vectors=%d  conformance.sh=%s" % (tok, len(vhits), chits))
print("    (population searched: %d files under .softhouse/vectors/, plus conformance.sh)"
      % len(vector_files))
check("NO vector in the store, and no line of conformance.sh, mentions ANY of these "
      "tokens — the three failures touch NOTHING in the graded corpus",
      all(v == 0 and not c for _, v, c, _ in hit_rows),
      "; ".join("%s v=%d c=%s %s" % r for r in hit_rows if r[1] or r[2]) or "all zero")

capture_refs = set()
for p in vector_files:
    if p.suffix == ".json":
        capture_refs.update(re.findall(r'"capture_ref"\s*:\s*"([^"]*)"', p.read_text(errors="replace")))
loanproduct_refs = sorted(r for r in capture_refs if "loanproduct" in r or "product-nine" in r)
check("NO vector's provenance.capture_ref points at a loan-product read",
      loanproduct_refs == [],
      "%d distinct capture_ref values inspected; loan-product-shaped: %s"
      % (len(capture_refs), loanproduct_refs))

print()
print("=== 5. NEGATIVE CONTROLS — P-22, each arm above driven RED on purpose ===")
controls = []


def control(label, cond, detail=""):
    controls.append((label, cond, detail))
    print(("  PASS  " if cond else "  FAIL  ") + label + (("\n          " + detail) if detail else ""))
    if not cond:
        fails.append("NEGATIVE CONTROL DID NOT TRIP: " + label)


# control (a): a FOURTH, unadjudicated failure must be caught.
fake4 = r1.stdout + "\nFAILURES: 4\n" + "".join(
    "  - %s\n" % f for f in sorted(ADJUDICATED | {"  something nobody has adjudicated"}))
n4, d4, _ = parse_verdict(fake4, 1)
control("(a) a FOURTH failure is detected as UNADJUDICATED",
        sorted(n4 - ADJUDICATED) == ["  something nobody has adjudicated"],
        "unexpected=%s" % sorted(n4 - ADJUDICATED))

# control (b): losing one of the three must be caught.
fake2 = "FAILURES: 2\n" + "".join("  - %s\n" % f for f in sorted(ADJUDICATED)[:2])
n2, d2, _ = parse_verdict(fake2, 1)
control("(b) an adjudicated failure that VANISHES is detected as missing",
        len(ADJUDICATED - n2) == 1, "missing=%s" % sorted(ADJUDICATED - n2))

# control (c): a green section 1 must be caught.
n0, d0, rc0 = parse_verdict("FAILURES: 0\n", 0)
control("(c) a section 1 that went GREEN is detected (rc==0 and all three missing)",
        rc0 == 0 and ADJUDICATED - n0 == ADJUDICATED, "declared=%s" % d0)

# control (d): a transcript with no FAILURES: line at all must not be read as clean.
nX, dX, _ = parse_verdict("Traceback (most recent call last):\nValueError\n", 1)
control("(d) a transcript with NO 'FAILURES:' line yields declared=None, not 0 — an "
        "aborted run is never read as a clean run", dX is None and nX == set(),
        "declared=%r named=%r" % (dX, nX))

# control (e): the offline prover must trip on a script that CAN reach the network.
NETSRC = (
    "import json\n"
    "import urllib.request\n"
    "d = urllib.request.urlopen('https://localhost:8443/x').read()\n"
    "json.loads(d)\n"
)
control("(e) the offline prover TRIPS on a synthetic script that imports urllib and "
        "opens a URL", network_evidence(NETSRC, "<synthetic>") != [],
        "hits=%s" % network_evidence(NETSRC, "<synthetic>"))

# control (f): and on the subprocess/curl spelling, which has no urllib in it at all.
CURLSRC = "import subprocess\nsubprocess.run(['curl', '-sk', 'https://localhost:8443/x'])\n"
control("(f) the offline prover TRIPS on the subprocess+curl spelling too",
        network_evidence(CURLSRC, "<synthetic>") != [],
        "hits=%s" % network_evidence(CURLSRC, "<synthetic>"))

# control (g): and it does NOT trip on a plausible offline script — a control that always
# says RED is as useless as one that always says GREEN.
OFFSRC = "import json\nfrom pathlib import Path\njson.loads(Path('x').read_bytes().decode())\n"
control("(g) the offline prover does NOT trip on a genuinely offline script (the control "
        "discriminates, it does not just always fire)",
        network_evidence(OFFSRC, "<synthetic>") == [],
        "hits=%s" % network_evidence(OFFSRC, "<synthetic>"))

print()
print("FAILURES: %d" % len(fails))
for f in fails:
    print("  - " + f)
sys.exit(1 if fails else 0)
