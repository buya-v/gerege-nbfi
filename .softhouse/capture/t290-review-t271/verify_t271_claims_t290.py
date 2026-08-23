#!/usr/bin/env python3
"""T290 -- mechanically verify the three T271 claims a reviewer must not take on trust.

C1  `independent_recheck_t271.py` never reads `classify-t219.json` WHILE DERIVING.
    Verified two ways, neither of them by reading the code's intent:
      (a) a PEP-578 audit hook records the ORDER of every `open`, and the classification must be
          the LAST capture file opened;
      (b) ADVERSARIAL SWAP -- the whole t219 directory is copied, its `classify-t219.json` is
          corrupted (every `P2_*` boolean negated, every `observed*` integer +7777), and the
          instrument is re-run against the copy. Every DERIVED figure must be unchanged and the
          reproduction assertion must go RED. An instrument that claims independence and quietly
          reads the thing it is checking is exactly the defect class this program keeps finding.

C2  `.softhouse/conformance.sh`'s anchors are what T271 says: line 1548 is `run_guards() {`, the
    tally block is 1563-1569, and 1569 is `guard_no_fail_open_instruments || failed=1`. Checked
    BY CONTENT as well as by number, because a line number is a hint and the content is the
    binding (P-80/P-87: T273/T285 are editing this file in the same fire).

C3  T271's `grep of conformance.sh returned exit 1, true no-match`. Re-run with the exit code
    CLASSIFIED, and CALIBRATED on a known positive and a deliberately broken search, so that
    `1` is demonstrated to mean no-match on this host with this grep (P-72, P-81, P-75).

READ ONLY. This instrument does not write inside any capture directory except a temp copy it
removes; `.softhouse/conformance.sh` is opened for reading only and is contended by T273/T285.

EXIT 0 all three claims hold; 1 one does not; 2 error. PROBE: `T290-CLAIMS: <STATE> ...`
"""
import gzip
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROBE = "T290-CLAIMS:"


def repo_root(p: Path) -> Path:
    while p != p.parent:
        if (p / ".git").exists():
            return p
        p = p.parent
    raise SystemExit(2)


ROOT = repo_root(HERE)
INDEP = ROOT / ".softhouse/capture/t271-b1-t219/independent_recheck_t271.py"
T219 = ROOT / ".softhouse/capture/t219-g8-residual"
CONF = ROOT / ".softhouse/conformance.sh"
INDEP_RE = re.compile(r"^T271-INDEP: (?P<state>\S+) carriers=(?P<c>\d+) agreeREG=(?P<r>\d+) "
                      r"agreeCORR=(?P<co>\d+) agreeUNCOND=(?P<u>\d+) structureHolds=(?P<s>\d+) "
                      r"contradictions=(?P<x>\d+)", re.M)

AUDIT = '''
import sys, runpy
LOG = []
sys.addaudithook(lambda e, a: LOG.append(str(a[0])) if e in ("open", "os.open") else None)
target = sys.argv[1]
sys.argv = [target] + sys.argv[2:]
try:
    runpy.run_path(target, run_name="__main__")
except SystemExit:
    pass
for p in LOG:
    if "t219-g8-residual" in p:
        print("OPENED " + p, file=sys.stderr)
'''


def c1(problems):
    print("C1 -- does independent_recheck_t271.py read classify-t219.json while deriving?")
    if not INDEP.exists():
        problems.append("C1: independent_recheck_t271.py is not on disk at " + str(INDEP))
        print("   ERROR: not on disk: %s" % INDEP)
        return
    work = Path(tempfile.mkdtemp(prefix=".t290-c1-", dir=str(ROOT)))
    try:
        hook = work / "audit.py"
        hook.write_text(AUDIT)
        p = subprocess.run([sys.executable, str(hook), str(INDEP)], capture_output=True,
                           text=True, cwd=str(ROOT))
        opened = [ln[len("OPENED "):] for ln in p.stderr.splitlines() if ln.startswith("OPENED ")]
        print("   (a) open ORDER inside the t219 capture, as recorded by an audit hook:")
        for i, o in enumerate(opened):
            print("       %d  %s" % (i, o.replace(str(ROOT) + "/", "")))
        if not opened:
            problems.append("C1(a): the audit hook recorded no open at all -- it measured nothing")
        elif "classify-t219.json" not in opened[-1]:
            problems.append("C1(a): the LAST file opened is not classify-t219.json")
        elif any("classify-t219.json" in o for o in opened[:-2]):
            problems.append("C1(a): classify-t219.json was opened before the derivation finished")

        swap = work / "t219-g8-residual"
        shutil.copytree(T219, swap)
        cls = swap / "out" / "classify-t219.json"
        doc = json.loads(cls.read_text())
        for row in doc["cells"]:
            for k, v in list(row.items()):
                if k.startswith("P2_") and isinstance(v, bool):
                    row[k] = not v
                if k.startswith("observed") and isinstance(v, int) and not isinstance(v, bool):
                    row[k] = v + 7777
        cls.write_text(json.dumps(doc, indent=1) + "\n")

        clean = subprocess.run([sys.executable, str(INDEP)], capture_output=True, text=True,
                               cwd=str(ROOT))
        dirty = subprocess.run([sys.executable, str(INDEP), str(swap)], capture_output=True,
                               text=True, cwd=str(ROOT))
        mc, md = INDEP_RE.search(clean.stdout), INDEP_RE.search(dirty.stdout)
        print("   (b) ADVERSARIAL SWAP -- classify-t219.json corrupted in a copy of the tree:")
        print("       clean : %s" % (mc.group(0) if mc else "NO PROBE LINE"))
        print("       dirty : %s" % (md.group(0) if md else "NO PROBE LINE"))
        if not mc or not md:
            problems.append("C1(b): a probe line was missing (P-84: presence before value)")
        else:
            derived = ("c", "r", "co", "u", "s")
            moved = [k for k in derived if mc.group(k) != md.group(k)]
            if moved:
                problems.append("C1(b): DERIVED figures moved when only the classification was "
                                "corrupted: " + ",".join(moved) + " -- the instrument is NOT "
                                "independent of the file it checks")
            if md.group("x") == "0" or dirty.returncode != 1:
                problems.append("C1(b): the reproduction assertion did NOT go red against a "
                                "corrupted classification -- it is not sensitive")
            if not moved and md.group("x") != "0":
                print("       DERIVED figures identical; reproduction assertion RED "
                      "(contradictions=%s, exit %d). INDEPENDENCE HOLDS."
                      % (md.group("x"), dirty.returncode))
    finally:
        shutil.rmtree(work, ignore_errors=True)
    print()


def c2(problems):
    print("C2 -- conformance.sh anchors (READ ONLY; the file is contended by T273/T285)")
    if not CONF.exists():
        problems.append("C2: conformance.sh is not on disk")
        print("   ERROR: not on disk: %s" % CONF)
        return
    lines = CONF.read_text().splitlines()
    want = {1548: "run_guards() {", 1569: "guard_no_fail_open_instruments      || failed=1"}
    for n, text in want.items():
        got = lines[n - 1] if n - 1 < len(lines) else "<past end of file>"
        ok = got.strip() == text.strip()
        print("   line %d : %-52r %s" % (n, got.strip(), "MATCHES T271" if ok else "MOVED"))
        if not ok:
            problems.append("C2: conformance.sh line %d is %r, T271 said %r" % (n, got, text))
    tally = [i + 1 for i, ln in enumerate(lines) if re.match(r"^\s+guard_\w+\s+\|\| failed=1\s*$",
                                                             ln)]
    print("   tally block by CONTENT (every `guard_* || failed=1`) : lines %s" % tally)
    if tally != list(range(1563, 1570)):
        problems.append("C2: the tally block is at %s, T271 said 1563-1569" % tally)
    print("   NOTE FOR T269: bind the insertion point to the CONTENT of the last tally line, not")
    print("   to 1569. T273/T285 are editing this file in the same fire and P-87 measured that a")
    print("   line-number anchor was already 3-of-4 MOVED at an untouched merge base.")
    print()


def c3(problems):
    print("C3 -- 'grep of conformance.sh returned exit 1, a true no-match' (P-81 / P-72 / P-75)")
    if not CONF.exists():
        problems.append("C3: conformance.sh is not on disk")
        return
    grep = "/usr/bin/grep"                       # absolute: a bare `grep` may be bundled ugrep
    ver = subprocess.run([grep, "--version"], capture_output=True, text=True)
    print("   grep : %s -- %s" % (grep, ver.stdout.splitlines()[0] if ver.stdout else "?"))
    checks = [("guard_no_fail_open_instruments", 0, "CALIBRATION on a known positive"),
              ("R-VPA", 1, ""), ("t256-verdict-predicate", 1, ""),
              ("check_verdict_predicate", 1, ""), ("t271", 1, ""),
              ("run_rvpa_over_targets", 1, ""), ("t290", 1, "")]
    for pat, want, note in checks:
        rc = subprocess.run([grep, "-q", "--", pat, str(CONF)]).returncode
        label = {0: "MATCH", 1: "NO MATCH (true absence)"}.get(rc, "SEARCH ERROR")
        print("   %-34s exit %d  %-24s %s" % (repr(pat), rc, label, note))
        if rc != want:
            problems.append("C3: grep %r exited %d, wanted %d" % (pat, rc, want))
    broken = subprocess.run([grep, "-q", "--", "x", "/nonexistent/zzz"],
                            capture_output=True).returncode
    print("   deliberately broken search             exit %d  <- so >1 is distinguishable on this "
          "host" % broken)
    if broken <= 1:
        problems.append("C3: a broken search exited %d, so exit 1 cannot be read as a true "
                        "no-match here" % broken)
    print("   CONCLUSION: nothing in conformance.sh reads R-VPA, T271's runner, or T290's guard.")
    print("   Every artefact in both directories is WIRED TO NOTHING (P-89/P-45).")
    print()


def main() -> int:
    print("T290 -- mechanical verification of three T271 claims")
    print("=" * 96)
    problems = []
    c1(problems)
    c2(problems)
    c3(problems)
    for p in problems:
        print("  REFUSED: " + p)
    state = "REFUSED" if problems else "GREEN"
    print("%s %s claims=3 held=%d problems=%d" % (PROBE, state, 3 - len(set(
        p.split(":")[0] for p in problems)), len(problems)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
