#!/usr/bin/env python3
"""THE RATCHET: no NEW capture sidecar may be written without a derivation line.

WHY THIS EXISTS, AND WHY IT IS NOT `verify` WIRED INTO THE HARNESS
------------------------------------------------------------------
T269 must wire T250's derived attestation into the automatic path.  Before
writing this I measured what such a wiring would actually grade, because a gate
whose population is empty is decoration and this program has named that class
(P-45) eight times:

    tracked `*.http` sidecars in the repository      285
      DERIVED (carry the `attestation-derivation:` line)     54
        of those SCHEMA 2 (response attested)                 0
      LEGACY (no provenance line at all)                     231
        of which .softhouse/capture/tierA-a2                 226   <- the corpus
                                                                      the vectors
                                                                      actually cite
    [MEASURED on this tree; reproduce with `--report`.]

So: **every sidecar the vector store cites is LEGACY.**  `wire_attestation.py
verify` REFUSES a legacy sidecar (exit 2, "it may be true, but nothing here can
tell you"), and that refusal is correct -- those captures were taken by the
`cap*.sh` chain, which is exactly the rig T250 exists to replace.  Wiring
`verify` over the committed corpus today would therefore produce 226 refusals and
zero verdicts.  It cannot be done, and saying so is not a deferral: re-capturing
the corpus through `oracle_send` is a separate, large, oracle-bound task.

What CAN be gated today, and what this instrument does, is the RATCHET:

    the number of committed sidecars with NO derivation line may never RISE.

That is the property T250's successor was built to deliver -- new captures are
derived -- and it is enforceable now, on the whole tree, without re-capturing
anything.  Every capture taken through `oracle_send` self-checks at birth (a
hard failure that voids the capture), so the pair is: derivation checked at
capture time, population checked at harness time.

BOTH TERMS ARE PRINTED, ALWAYS (P-67).  A count of derived sidecars without the
count of undecided ones is the shape this program keeps re-finding.

DELIBERATELY TAMPERED EVIDENCE IS EXCLUDED, BY NAME, AND COUNTED
-----------------------------------------------------------------
Red-drive evidence trees contain sidecars that were tampered ON PURPOSE -- one of
them (`t250arms/arm-4`) is a legacy-shaped forgery whose whole point is to have
no provenance line.  Counting those as "unattested captures" would be a false
figure, and silently skipping them would be an exemption list, which is the
default-allow shape T274 was filed to remove.  So a directory may declare itself
by containing a file named `ATTEST-TAMPERED-EVIDENCE`, and this instrument:

  * EXCLUDES that directory and everything under it from the counts;
  * PRINTS every excluded directory and how many sidecars it holds;
  * REQUIRES the excluded directory list to equal the PINNED list exactly, so a
    new exclusion cannot be created without a pin change in the same commit --
    the same discipline `FAILOPEN_PIN_FILE_LIST` uses in `conformance.sh`.

FAIL-CLOSED BY CONSTRUCTION
---------------------------
  * `git ls-files` exit != 0                       -> REFUSE (2).  Nonzero is an
    error, never "clean"; this program has been bitten by exit-1-means-no-match.
  * zero sidecars found                            -> REFUSE (2).  "Not found is
    a statement about the search, never about the world."
  * a sidecar that cannot be read                  -> REFUSE (2).
  * pin file missing or unparseable                -> REFUSE (2).
  * legacy count ABOVE the pin                     -> FAIL (1).  A new
    unattested sidecar was committed.
  * legacy count BELOW the pin                     -> FAIL (1).  Good news that
    must move the pin IN THE SAME COMMIT, or the pin starts excusing a weakness
    that is no longer there.
  * excluded directory set != pinned set           -> FAIL (1).

WHAT THIS DOES NOT CLAIM
------------------------
It does not verify a single sidecar.  It counts.  A sidecar carrying the
derivation line is counted as derived even if its assertions are false --
`wire_attestation.py verify` is what decides that, and it runs at capture time
inside `oracle_send`.  Nor does it say the 226 legacy captures are wrong: T245
established their tenant by three independent routes from database contents.  It
says only that they are UNATTESTED BY THIS RIG, which is a statement about the
evidence, not about the world.

MONEY: this instrument reads file paths and first lines.  No monetary value is
parsed and there is no float anywhere in it.
"""
import argparse
import json
import os
import subprocess
import sys

TAG = "attestation-derivation: curl --trace-ascii; request headers AS SENT"
SCHEMA2 = "attestation-schema: 2"
MARKER = "ATTEST-TAMPERED-EVIDENCE"


class Refuse(Exception):
    """No verdict may be issued.  Never a pass."""


def tracked_sidecars(root):
    proc = subprocess.run(["git", "-C", root, "ls-files", "-z", "--", "*.http"],
                          capture_output=True)
    if proc.returncode != 0:
        raise Refuse(
            "`git ls-files` exited %d in %s: %s -- a nonzero exit is an ERROR, and "
            "this refuses rather than treating an empty result as a clean tree"
            % (proc.returncode, root, proc.stderr.decode("utf-8", "replace").strip()))
    paths = [p for p in proc.stdout.decode("utf-8", "replace").split("\0") if p]
    if not paths:
        raise Refuse(
            "`git ls-files -- '*.http'` matched NOTHING under %s. That is a "
            "statement about the search, not about the world: either the root is "
            "wrong or the corpus is gone. No verdict." % root)
    return sorted(paths)


def marker_dirs(root):
    """Directories that declare themselves as deliberately tampered evidence."""
    proc = subprocess.run(["git", "-C", root, "ls-files", "-z", "--", "*" + MARKER],
                          capture_output=True)
    if proc.returncode != 0:
        raise Refuse("`git ls-files` for markers exited %d: %s"
                     % (proc.returncode, proc.stderr.decode("utf-8", "replace").strip()))
    out = []
    for p in proc.stdout.decode("utf-8", "replace").split("\0"):
        if not p:
            continue
        if os.path.basename(p) != MARKER:
            continue
        out.append(os.path.dirname(p))
    return sorted(out)


def under(path, directory):
    return path == directory or path.startswith(directory.rstrip("/") + "/")


def classify(root, paths, excluded_dirs):
    derived, schema2, legacy, excluded = [], [], [], []
    for p in paths:
        if any(under(p, d) for d in excluded_dirs):
            excluded.append(p)
            continue
        full = os.path.join(root, p)
        try:
            with open(full, "rb") as fh:
                text = fh.read().decode("utf-8", "replace")
        except OSError as exc:
            raise Refuse("cannot read sidecar %s: %s -- an unreadable file is not a "
                         "clean one" % (p, exc))
        first = text.split("\n", 1)[0].rstrip("\r")
        if first == TAG:
            derived.append(p)
            if SCHEMA2 in text:
                schema2.append(p)
        else:
            legacy.append(p)
    return derived, schema2, legacy, excluded


def by_prefix(paths, depth):
    counts = {}
    for p in paths:
        key = "/".join(p.split("/")[:depth])
        counts[key] = counts.get(key, 0) + 1
    return sorted(counts.items())


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--root", default="")
    ap.add_argument("--pin", default=os.path.join(here, "attest_population_pin.json"))
    ap.add_argument("--report", action="store_true",
                    help="print the measurement and exit 0 without grading it")
    args = ap.parse_args(argv)

    try:
        root = args.root
        if not root:
            proc = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                                  capture_output=True)
            if proc.returncode != 0:
                raise Refuse("cannot locate the repository root: git rev-parse exited "
                             "%d" % proc.returncode)
            root = proc.stdout.decode().strip()

        paths = tracked_sidecars(root)
        excluded_dirs = marker_dirs(root)
        derived, schema2, legacy, excluded = classify(root, paths, excluded_dirs)

        sys.stdout.write("attest-population: tracked `*.http` sidecars under %s: %d\n"
                         % (root, len(paths)))
        sys.stdout.write("attest-population:   DERIVED (carry the provenance line): %d, "
                         "of which SCHEMA 2 (response attested): %d\n"
                         % (len(derived), len(schema2)))
        sys.stdout.write("attest-population:   LEGACY  (no provenance line at all)  : %d "
                         "-- BOTH TERMS, always\n" % len(legacy))
        for key, n in by_prefix(legacy, 3):
            sys.stdout.write("attest-population:     legacy: %-56s %d\n" % (key, n))
        sys.stdout.write("attest-population:   EXCLUDED as declared tampered evidence: %d "
                         "sidecar(s) in %d directory(ies)\n"
                         % (len(excluded), len(excluded_dirs)))
        for d in excluded_dirs:
            n = sum(1 for p in excluded if under(p, d))
            sys.stdout.write("attest-population:     excluded: %-54s %d\n" % (d, n))
        sys.stdout.write(
            "attest-population:   NOT CLAIMED: this counts sidecars, it does not verify "
            "one. A legacy sidecar is UNATTESTED BY THIS RIG, which is a statement "
            "about the evidence and not about the capture.\n")

        if args.report:
            return 0

        if not os.path.isfile(args.pin):
            raise Refuse("pin file does not exist: %s" % args.pin)
        try:
            with open(args.pin) as fh:
                pin = json.load(fh)
        except ValueError as exc:
            raise Refuse("pin file %s is not parseable: %s" % (args.pin, exc))
        for key in ("legacy_sidecars", "tampered_evidence_dirs"):
            if key not in pin:
                raise Refuse("pin file %s carries no `%s`" % (args.pin, key))

        failures = []
        if len(legacy) > pin["legacy_sidecars"]:
            failures.append(
                "LEGACY sidecars ROSE: %d measured, %d pinned. A capture sidecar was "
                "committed with no derivation line. New captures go through "
                "`oracle_send`, which derives one; nothing else may write a sidecar."
                % (len(legacy), pin["legacy_sidecars"]))
        elif len(legacy) < pin["legacy_sidecars"]:
            failures.append(
                "LEGACY sidecars FELL: %d measured, %d pinned. That is good news, and "
                "the pin must lose the difference IN THE SAME COMMIT -- otherwise the "
                "pin starts excusing a weakness that is no longer there."
                % (len(legacy), pin["legacy_sidecars"]))
        pinned_dirs = sorted(pin["tampered_evidence_dirs"])
        if excluded_dirs != pinned_dirs:
            for d in excluded_dirs:
                if d not in pinned_dirs:
                    failures.append(
                        "UNPINNED tampered-evidence exclusion: %s. A directory cannot "
                        "exclude itself from this count without a pin change in the "
                        "same commit." % d)
            for d in pinned_dirs:
                if d not in excluded_dirs:
                    failures.append(
                        "PINNED exclusion no longer present: %s. The pin must lose the "
                        "row in the same commit." % d)

        if failures:
            sys.stderr.write("attest-population: FAIL\n")
            for f in failures:
                sys.stderr.write("  %s\n" % f)
            sys.stderr.write("  The pin is %s.\n" % args.pin)
            return 1
        sys.stdout.write(
            "attest-population: PASS -- legacy %d == pinned %d; %d declared "
            "tampered-evidence directory(ies), all pinned.\n"
            % (len(legacy), pin["legacy_sidecars"], len(excluded_dirs)))
        return 0
    except Refuse as exc:
        sys.stderr.write("attest-population REFUSING: %s\n" % exc)
        return 2


if __name__ == "__main__":
    sys.exit(main())
