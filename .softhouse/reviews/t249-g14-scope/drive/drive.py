#!/usr/bin/env python3
"""T249 — adversarial re-drive of ready-tasks.py's OPEN CONTRACT GATE scope printer.

Read-only with respect to the repo. Each arm builds a THROWAWAY `.softhouse` tree in
a temp dir and copies `ready-tasks.py` into it, so the script's `root`
(`os.path.dirname(os.path.dirname(os.path.abspath(__file__)))`) resolves to the
FIXTURE and never to the real repo. Nothing under the repo is written except this
directory's transcripts.

Usage:  python3 drive.py <repo-root> <out-dir>
"""
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile

SECTION_START = "OPEN CONTRACT GATES"
SECTION_END = "DEPENDENCY EDGES"


def base_gate(prog, gid):
    for g in prog["gates_pending"]:
        if g["id"] == gid:
            return g
    raise SystemExit("gate %s not found" % gid)


def only_g14(prog):
    """Strip gates_pending down to G-14 alone so each arm is a clean single-gate read."""
    p = copy.deepcopy(prog)
    p["gates_pending"] = [g for g in p["gates_pending"] if g["id"] == "G-14"]
    return p


def arms(prog):
    """Yield (name, what-I-expect-to-see, mutated program dict)."""
    g14 = base_gate(prog, "G-14")

    def mk(blocks_value, present=True, extra=None, gates=None):
        p = only_g14(prog)
        g = p["gates_pending"][0]
        if present:
            g["blocks"] = blocks_value
        else:
            g.pop("blocks", None)
        if extra:
            g.update(extra)
        if gates is not None:
            p["gates_pending"] = gates
        return p

    yield ("A00-baseline-real-tree", "control: real G-14, recorded scope printed",
           copy.deepcopy(prog))
    yield ("A01-blocks-absent", "driver's negative arm: fallback + 'NO SCOPE RECORDED'",
           mk(None, present=False))
    yield ("A02-blocks-empty-string", "should behave as NO SCOPE -> fallback",
           mk(""))
    yield ("A03-blocks-whitespace-only", "should behave as NO SCOPE -> fallback",
           mk("   \t\n   "))
    yield ("A04-blocks-int-zero", "NON-STRING. str(0)='0' -> truthy after strip",
           mk(0))
    yield ("A05-blocks-int-nonzero", "NON-STRING number", mk(12345))
    yield ("A06-blocks-json-null", "JSON null -> str(None)='None'", mk(None))
    yield ("A07-blocks-false", "JSON false -> str(False)='False'", mk(False))
    yield ("A08-blocks-true", "JSON true -> str(True)='True'", mk(True))
    yield ("A09-blocks-empty-list", "[] -> str='[]'", mk([]))
    yield ("A10-blocks-empty-dict", "{} -> str='{}'", mk({}))
    yield ("A11-blocks-list-of-str", "list -> repr-ish stringification",
           mk(["NOTHING. Go under nexus/ is permitted."]))
    yield ("A12-blocks-dict", "dict -> repr-ish stringification",
           mk({"nexus": "permitted", "vectors": "permitted"}))
    yield ("A13-blocks-float", "float — money-adjacent shape, must not appear anywhere",
           mk(0.0))
    yield ("A14-blocks-DENIES-permission",
           "text that does NOT grant permission; header must not make it read permissive",
           mk("EVERYTHING. No task may write Go under nexus/ and no vector of any "
              "shape may be stored for this context until this gate closes."))
    yield ("A15-blocks-newlines-and-bullets",
           "multi-line scope: textwrap.wrap collapses newlines",
           mk("PERMITS:\n  - Go under nexus/\nFORBIDS:\n  - contract-shaped vectors"))
    yield ("A16-blocks-single-long-token",
           "one token longer than width 84",
           mk("N" + "O" * 200 + "THING"))
    yield ("A17-provenance-absent",
           "scope present, NO decided_by / reviewed_by: printed with no provenance at all",
           mk("NOTHING. Everything is permitted.",
              extra={"blocks_decided_by": None, "blocks_reviewed_by": None}))

    # two open CONTRACT gates at once — never existed when the code was written
    two = copy.deepcopy(prog)
    keep = [g for g in two["gates_pending"] if g["id"] == "G-14"]
    other = copy.deepcopy(keep[0])
    other["id"] = "G-15"
    other["state"] = "OPEN — RAISED by a hypothetical later worker"
    other["title"] = "A second open CONTRACT gate that records NO scope"
    other.pop("blocks", None)
    other.pop("blocks_decided_by", None)
    other.pop("blocks_reviewed_by", None)
    two["gates_pending"] = keep + [other]
    yield ("A18-two-open-contract-gates",
           "one with scope, one without — both must print their OWN verdict", two)

    two_perm = copy.deepcopy(two)
    two_perm["gates_pending"][1]["blocks"] = (
        "NOTHING. Writing Go under nexus/ and storing contract-shaped vectors is "
        "permitted for every context.")
    two_perm["gates_pending"][1]["blocks_decided_by"] = "itself"
    yield ("A19-two-gates-second-self-permits",
           "SELF-ISSUED PERMISSION SLIP: unreviewed free text printed as authoritative",
           two_perm)

    # filter-level arms: these test the SELECTOR, which the patch did not touch
    low = only_g14(prog)
    low["gates_pending"][0]["state"] = "open — raised, lower case"
    yield ("A20-state-lowercase-open",
           "SELECTOR: 'OPEN' substring is case-SENSITIVE — gate may vanish", low)

    noclass = only_g14(prog)
    noclass["gates_pending"][0].pop("class", None)
    yield ("A21-class-missing",
           "SELECTOR: G-13 in the real file has NO class key — such a gate vanishes",
           noclass)

    lowclass = only_g14(prog)
    lowclass["gates_pending"][0]["class"] = "contract"
    yield ("A22-class-lowercase",
           "SELECTOR: exact == 'CONTRACT' — lower case vanishes", lowclass)

    reopened = only_g14(prog)
    reopened["gates_pending"][0]["state"] = "CLOSED — the OPEN question is settled"
    yield ("A23-state-CLOSED-containing-OPEN",
           "SELECTOR: substring match — a CLOSED gate whose prose contains OPEN",
           reopened)

    # a gate written under the OTHER, pre-existing `blocks` convention (names what is
    # blocked rather than stating a scope). G-9 is real text from the live file.
    g9 = only_g14(prog)
    g9["gates_pending"][0]["blocks"] = base_gate(prog, "G-9")["blocks"]
    g9["gates_pending"][0].pop("blocks_decided_by", None)
    g9["gates_pending"][0].pop("blocks_reviewed_by", None)
    yield ("A24-legacy-blocks-convention",
           "REAL G-9 text: the field's OLD convention names what is blocked, not a scope",
           g9)

    g12 = only_g14(prog)
    g12["gates_pending"][0]["blocks"] = base_gate(prog, "G-12")["blocks"]
    g12["gates_pending"][0].pop("blocks_decided_by", None)
    g12["gates_pending"][0].pop("blocks_reviewed_by", None)
    yield ("A25-legacy-blocks-now-STALE",
           "REAL G-12 text, which is STALE at HEAD (six ledger vectors exist)", g12)


def run_arm(repo, name, prog, outdir):
    tmp = tempfile.mkdtemp(prefix="t249-")
    try:
        fx = os.path.join(tmp, ".softhouse")
        os.makedirs(os.path.join(fx, "bin"))
        os.makedirs(os.path.join(fx, "runs"))
        shutil.copy(os.path.join(repo, ".softhouse", "bin", "ready-tasks.py"),
                    os.path.join(fx, "bin", "ready-tasks.py"))
        shutil.copy(os.path.join(repo, ".softhouse", "tasks.json"),
                    os.path.join(fx, "tasks.json"))
        with open(os.path.join(fx, "program.json"), "w") as fh:
            json.dump(prog, fh, indent=1, ensure_ascii=False)
        proc = subprocess.run(
            [sys.executable, os.path.join(fx, "bin", "ready-tasks.py")],
            capture_output=True, text=True)
        out = proc.stdout + proc.stderr
        keep, lines = False, []
        for line in out.splitlines():
            if SECTION_START in line:
                keep = True
            elif SECTION_END in line:
                keep = False
            if keep:
                lines.append(line)
        return proc.returncode, "\n".join(lines)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    repo, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(repo, ".softhouse", "program.json")) as fh:
        prog = json.load(fh)
    sha = subprocess.run(["git", "-C", repo, "rev-parse", "HEAD"],
                         capture_output=True, text=True).stdout.strip()
    report = ["T249 adversarial re-drive of ready-tasks.py gate-scope printer",
              "MEASURED at commit %s" % sha,
              "python %s" % sys.version.split()[0], ""]
    for name, expectation, prog_mut in arms(prog):
        rc, section = run_arm(repo, name, prog_mut, outdir)
        report.append("=" * 78)
        report.append("ARM %s   (exit %d)" % (name, rc))
        report.append("what this probes: %s" % expectation)
        report.append("-" * 78)
        report.append(section if section.strip() else "(NO OPEN CONTRACT GATES SECTION EMITTED)")
        report.append("")
    with open(os.path.join(outdir, "TRANSCRIPT.txt"), "w") as fh:
        fh.write("\n".join(report) + "\n")
    print("\n".join(report))


if __name__ == "__main__":
    main()
