#!/usr/bin/env python3
"""
T284 -- THE `verify` CALL-SITE REGISTRY.  Default-deny, pinned, enumerable.

WHY THIS EXISTS AND NOT JUST A DOCUMENT
---------------------------------------
T274 moved `wire_attestation.py` to sidecar schema 2.  Three FROZEN instruments
that call `verify` with request-only arguments began REFUSING (exit 2) on every
fresh capture.  The refusal is CORRECT -- a schema 1 caller has no business
issuing a verdict about a schema 2 artefact set -- but T274 could not repair the
callers (T114: they produced committed evidence), and so three instruments were
left correct, loud, and DEAD, with nobody owning them.

`P-45 -- A TEST-ONLY GUARD IS NOT A GUARD.  When hardening a check, verify the
path that actually executes in CI/conformance calls it, not merely that a test
does.`  A per-site decision recorded only in a handoff is the same shape one
layer out: it is a guard that works when someone remembers to read it.  So the
decisions live in a PIN that a program checks, and a new or changed call site
turns this instrument red.

WHAT IT MEASURES
----------------
Every tracked `*.sh` / `*.py` in the repository is read.  A line is an
INVOCATION of `verify` when, after joining backslash continuations and dropping
`#` comment lines, it names the module (`wire_attestation.py`, `$WA`, `${WA}`)
followed by the subcommand `verify`, AND it carries either `--sidecar` (the
required flag, so the flags are readable here) or `$@` (the flags come from the
caller and are NOT readable here).

Each invocation is CLASSIFIED by the response artefacts it presents:

  SCHEMA2_COMPLETE  all three of --resp / --resphdr / --status
  REQUEST_ONLY      none of the three.  Valid ONLY against a schema 1 sidecar;
                    a schema 2 sidecar REFUSES here, which is the T284 defect.
  PARTIAL           some but not all.  ALWAYS a refusal at run time; recorded as
                    its own class so it can never be mistaken for either.
  INDIRECT          the flags reach the module through `$@`.  Not statically
                    readable, therefore NOT ASSUMED COMPATIBLE -- it must be
                    declared in the pin with the site that supplies the flags.

ENGINE (P-33/P-53): the corpus comes from `git ls-files -z`, not from a shell
glob and not from `grep`/`rg`, whose agent-shell aliases have measured recall
holes (P-75).  A nonzero `git ls-files` exit is an ERROR and REFUSES; it is
never read as an empty tree.  Classification is done in Python with `re`; no
`\\b \\d \\s \\w` is ever handed to `git grep -E` because `git grep -E` is not
used at all.

CALIBRATION (P-72): a guard that cannot fail is not a guard.  Two known
positives must be found before any verdict is issued -- `.softhouse/capture/
lib/oracle_send.sh` (a SCHEMA2_COMPLETE site) and `.softhouse/capture/
t250-tenant-attestation/instruments/30-redB-mismatch-detected.sh` (a
REQUEST_ONLY site).  If either is missing, or if either classifies differently
from its known class, this REFUSES rather than reporting a clean tree.

EXIT STATUS
-----------
  0  the measured population equals the pin, every frozen file is byte-identical
     to its pinned digest, and every declared successor exists
  1  DRIFT.  A verdict was reached and it is NO: an undeclared call site, a
     declared one that vanished, a class that changed, a frozen file that moved,
     or a missing successor.
  2  REFUSED.  No verdict may be issued: no pin, an unreadable pin, an empty
     corpus, a failed calibration, an unreadable source file.  NEVER a pass.

MONEY (CLAUDE.md non-negotiable): this module parses no monetary value.  There
is no `float(` and no `json.load(...)` of a capture body anywhere in it; the only
JSON it reads is its own pin, and every number in that pin is a count.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys

MODULE_TOKEN = re.compile(r'(?:wire_attestation\.py|\$\{WA\}|\$WA)["\']?\s+verify(?:\s|$)')
RESP_FLAGS = ("--resp", "--resphdr", "--status")

# Known positives.  If these are not found with these classes, no verdict.
CALIBRATION = {
    ".softhouse/capture/lib/oracle_send.sh": "SCHEMA2_COMPLETE",
    ".softhouse/capture/t250-tenant-attestation/instruments/"
    "30-redB-mismatch-detected.sh": "REQUEST_ONLY",
}


class Refuse(Exception):
    """No verdict may be issued.  Never a pass."""


def tracked_sources(root):
    proc = subprocess.run(
        ["git", "-C", root, "ls-files", "-z", "--", "*.sh", "*.py"],
        capture_output=True)
    if proc.returncode != 0:
        raise Refuse(
            "`git ls-files` exited %d in %s: %s -- a nonzero exit is an ERROR and "
            "this refuses rather than reading an empty result as a clean tree."
            % (proc.returncode, root,
               proc.stderr.decode("utf-8", "replace").strip()))
    paths = [p for p in proc.stdout.decode("utf-8", "replace").split("\0") if p]
    if not paths:
        raise Refuse(
            "`git ls-files -- '*.sh' '*.py'` matched NOTHING under %s. That is a "
            "statement about the SEARCH, not about the world: either the root is "
            "wrong or the corpus is gone. No verdict." % root)
    return sorted(paths)


def logical_lines(text):
    """Join backslash continuations; yield (first_line_number, joined_text)."""
    out = []
    raw = text.split("\n")
    i = 0
    while i < len(raw):
        start = i + 1
        buf = raw[i]
        while buf.endswith("\\") and i + 1 < len(raw):
            buf = buf[:-1] + " " + raw[i + 1]
            i += 1
        out.append((start, buf))
        i += 1
    return out


def classify_invocation(joined):
    present = [f for f in RESP_FLAGS if re.search(re.escape(f) + r"(?:\s|=|$)", joined)]
    if re.search(r'"\$@"|\$@', joined) and "--sidecar" not in joined:
        return "INDIRECT"
    if len(present) == 3:
        return "SCHEMA2_COMPLETE"
    if not present:
        return "REQUEST_ONLY"
    return "PARTIAL"


def invocations_in(root, path):
    full = os.path.join(root, path)
    try:
        with open(full, "rb") as fh:
            text = fh.read().decode("utf-8", "replace")
    except OSError as exc:
        raise Refuse("cannot read tracked source %s: %s -- an unreadable file is "
                     "not a clean one." % (path, exc))
    found = []
    for lineno, joined in logical_lines(text):
        if joined.lstrip().startswith("#"):
            continue
        if not MODULE_TOKEN.search(joined):
            continue
        if "--sidecar" not in joined and not re.search(r'"\$@"|\$@', joined):
            continue
        found.append({"line": lineno, "class": classify_invocation(joined),
                      "text": " ".join(joined.split())[:160]})
    return found


def measure(root):
    sites = {}
    for path in tracked_sources(root):
        hits = invocations_in(root, path)
        if hits:
            sites[path] = hits
    if not sites:
        raise Refuse(
            "ZERO `verify` call sites were found in the whole tracked tree. The "
            "module is called by `oracle_send.sh` at minimum, so a zero here means "
            "the detector broke, not that the callers went away. No verdict.")
    return sites


def calibrate(sites):
    for path, want in sorted(CALIBRATION.items()):
        if path not in sites:
            raise Refuse(
                "CALIBRATION FAILED: the known positive %s carries no detected "
                "`verify` invocation. A detector that cannot find a call site it "
                "is known to contain cannot report that other files have none "
                "(P-72). No verdict." % path)
        classes = sorted({h["class"] for h in sites[path]})
        if want not in classes:
            raise Refuse(
                "CALIBRATION FAILED: %s is known to hold a %s invocation; measured "
                "classes are %s. The classifier moved, so no verdict may be issued "
                "about any other site." % (path, want, ", ".join(classes)))


def sha256_of(root, path):
    full = os.path.join(root, path)
    try:
        with open(full, "rb") as fh:
            return hashlib.sha256(fh.read()).hexdigest()
    except OSError as exc:
        raise Refuse("cannot digest %s: %s" % (path, exc))


def load_pin(pin_path):
    if not os.path.exists(pin_path):
        raise Refuse(
            "the call-site pin %s does not exist. Without it there is nothing to "
            "compare the measurement against, and an unpinned census is a report, "
            "not a guard. No verdict." % pin_path)
    try:
        with open(pin_path, "rb") as fh:
            pin = json.loads(fh.read().decode("utf-8"))
    except (OSError, ValueError) as exc:
        raise Refuse("the call-site pin %s is unreadable or not JSON: %s. No "
                     "verdict." % (pin_path, exc))
    if not isinstance(pin.get("sites"), dict) or not pin["sites"]:
        raise Refuse("the call-site pin %s declares no `sites`. An empty pin would "
                     "make every measured site a violation and every removal "
                     "invisible. No verdict." % pin_path)
    return pin


def grade(root, sites, pin):
    failures = []
    declared = pin["sites"]

    for path in sorted(set(sites) - set(declared)):
        failures.append(
            "UNDECLARED call site: %s carries %d `verify` invocation(s) and is not "
            "in the pin. Every call site must state, in the pin, which schema it is "
            "scoped to and why -- default-deny: an undeclared site is refused, "
            "never assumed compatible.\n      %s"
            % (path, len(sites[path]),
               "\n      ".join("L%d %s  %s" % (h["line"], h["class"], h["text"])
                               for h in sites[path])))

    for path in sorted(set(declared) - set(sites)):
        failures.append(
            "DECLARED call site VANISHED: %s is in the pin and carries no detected "
            "`verify` invocation now. Either it was deleted (remove it from the pin "
            "in the same commit) or the detector stopped seeing it (worse)." % path)

    for path in sorted(set(declared) & set(sites)):
        entry = declared[path]
        want = list(entry.get("invocations", []))
        got = [h["class"] for h in sites[path]]
        if want != got:
            failures.append(
                "CLASS DRIFT at %s: pin declares %s, measured %s."
                % (path, want or "[]", got))
        if entry.get("frozen"):
            want_sha = entry.get("sha256", "")
            got_sha = sha256_of(root, path)
            if want_sha != got_sha:
                failures.append(
                    "FROZEN FILE MOVED: %s is declared FROZEN (it produced committed "
                    "evidence -- T114's standing ruling: anything that produced "
                    "committed evidence is superseded by a scratch copy, NEVER edited "
                    "in place).\n      pinned   %s\n      measured %s"
                    % (path, want_sha or "<none>", got_sha))
        for succ in entry.get("successors", []):
            if not os.path.exists(os.path.join(root, succ)):
                failures.append(
                    "MISSING SUCCESSOR: %s declares its successor as %s, which does "
                    "not exist. A supersession that points at nothing is a retirement "
                    "with the coverage silently dropped." % (path, succ))
        for req in entry.get("required_files", []):
            if not os.path.exists(os.path.join(root, req)):
                failures.append(
                    "MISSING REQUIRED FILE: %s declares %s, which does not exist. That "
                    "file is the notice a reader meets in the directory itself; without "
                    "it the decision survives only in a handoff, which is the shape "
                    "P-45 names -- a guard that works only when someone remembers to "
                    "read it enforces nothing." % (path, req))
    return failures


def report(sites, pin):
    print("T284 CALL-SITE REGISTRY")
    print("  engine: git ls-files -z -- '*.sh' '*.py'  +  python re "
          "(no grep, no rg, no git grep -E)")
    total = sum(len(v) for v in sites.values())
    print("  corpus: %d file(s) carrying %d `verify` invocation(s)"
          % (len(sites), total))
    tally = {}
    for hits in sites.values():
        for h in hits:
            tally[h["class"]] = tally.get(h["class"], 0) + 1
    for k in sorted(tally):
        print("    %-17s %d" % (k, tally[k]))
    print("  pin: %d declared site(s)" % len(pin["sites"]))
    print()
    for path in sorted(sites):
        entry = pin["sites"].get(path, {})
        print("  %s" % path)
        print("      decision: %s" % entry.get("decision", "<UNDECLARED>"))
        for h in sites[path]:
            print("      L%-5d %-17s" % (h["line"], h["class"]))


def main(argv=None):
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--root", default="")
    ap.add_argument("--pin", default=os.path.join(here, "callsite_registry.json"))
    ap.add_argument("--census", action="store_true",
                    help="print the measurement and exit 0 WITHOUT grading it")
    args = ap.parse_args(argv)

    root = args.root
    if not root:
        proc = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                              capture_output=True, cwd=here)
        if proc.returncode != 0:
            print("callsite-registry REFUSING: `git rev-parse --show-toplevel` "
                  "exited %d; the repository root is not known, so the corpus is "
                  "not known. No verdict." % proc.returncode, file=sys.stderr)
            return 2
        root = proc.stdout.decode("utf-8", "replace").strip()

    try:
        sites = measure(root)
        calibrate(sites)
        if args.census:
            report(sites, {"sites": {}})
            print("\ncallsite-registry: CENSUS ONLY -- nothing was graded.")
            return 0
        pin = load_pin(args.pin)
        report(sites, pin)
        failures = grade(root, sites, pin)
    except Refuse as exc:
        print("callsite-registry REFUSING: %s" % exc, file=sys.stderr)
        return 2

    print()
    if failures:
        print("callsite-registry: FAIL -- %d finding(s)" % len(failures))
        for f in failures:
            print("  * %s" % f)
        return 1
    print("callsite-registry: PASS -- %d call site(s), all declared, all classes "
          "as pinned, %d frozen file(s) byte-identical."
          % (len(sites), sum(1 for e in pin["sites"].values() if e.get("frozen"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
