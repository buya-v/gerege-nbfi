#!/usr/bin/env python3
"""Tamper ONE captured artefact set, exactly as T261 did, and say what it changed.

This is the attacker in the T274 red-drives.  It is deliberately dumb and
explicit: every mode prints the before/after of the thing it touched, so the
transcript shows the attack rather than asserting it happened.

It is used against BOTH arms -- the T250 baseline rig and the T274 fixed rig --
with the SAME mode strings, so the two arms differ in the verifier under test and
in nothing else.

REFUSES (exit 2) if the shape it expects is not there.  A tamper that silently
did nothing would make a fail-open look like a fix, which is the class of defect
this whole task exists to remove.
"""
import os
import sys


def die(msg):
    sys.stderr.write("TAMPER REFUSED: %s\n" % msg)
    raise SystemExit(2)


def read_lines(path):
    if not os.path.isfile(path):
        die("no such file: %s" % path)
    with open(path, "rb") as fh:
        return fh.read().decode("utf-8").split("\n")


def write_lines(path, lines):
    with open(path, "w") as fh:
        fh.write("\n".join(lines))


def mode_del_body_sha(d, name):
    """T261 F-4 / route R1.

    Delete the `body-sha256:` ASSERTION from the sidecar and swap the committed
    request body for DIFFERENT BYTES OF THE SAME LENGTH.  body-bytes still
    matches, Content-Length still matches, the header record is untouched.  The
    committed request body is now a forgery.
    """
    sc = os.path.join(d, name + ".http")
    body = os.path.join(d, name + ".req")
    lines = read_lines(sc)
    kept = [l for l in lines if not l.startswith("body-sha256: ")]
    if len(kept) == len(lines):
        die("no `body-sha256: ` line in %s -- nothing to delete" % sc)
    write_lines(sc, kept)
    with open(body, "rb") as fh:
        original = fh.read()
    # SAME LENGTH, DIFFERENT BYTES, AND STILL VALID JSON.  The length is what
    # makes the attack work (body-bytes and Content-Length keep matching); the
    # JSON validity is required by the harness's OWN wire-float round-trip
    # guard, which treats every `*.req` under .softhouse/capture as a request
    # body and REFUSES (hard, exit 2) on one it cannot parse.  A first version of
    # this instrument forged `XXXX...` and took the BAR to exit 2 -- see the
    # handoff.  `swapcase` touches only ASCII letters, never a structural
    # character, so the forgery is byte-different and still a request body.
    forged = original.swapcase()
    if forged == original:
        die("forged body is identical to the original; the tamper is inert")
    if len(forged) != len(original):
        die("forged body is %d bytes, original %d -- the attack needs the SAME length"
            % (len(forged), len(original)))
    with open(body, "wb") as fh:
        fh.write(forged)
    print("  tamper: deleted `body-sha256:` from the sidecar")
    print("  tamper: replaced %s (%d bytes) with %d DIFFERENT bytes of the SAME length"
          % (os.path.basename(body), len(original), len(forged)))


def mode_swap_headers(d, name):
    """T261 F-5 / route R2a -- reorder two wire header lines in the sidecar."""
    sc = os.path.join(d, name + ".http")
    lines = read_lines(sc)
    a = b = None
    for i, l in enumerate(lines):
        if l.startswith("Fineract-Platform-TenantId: "):
            a = i
        if l.startswith("Content-Type: "):
            b = i
    if a is None or b is None:
        die("expected both a tenant header and a Content-Type header in %s" % sc)
    lines[a], lines[b] = lines[b], lines[a]
    write_lines(sc, lines)
    print("  tamper: swapped sidecar lines %d and %d (%r <-> %r)"
          % (a + 1, b + 1, lines[b], lines[a]))


def mode_drop_dup(d, name, value):
    """T261 F-5 / route R2b -- drop ONE of two IDENTICAL duplicated headers.

    The wire carried the header twice (curl does not de-duplicate; T250's own
    red-drive C measured both values reaching the server).  The sidecar now says
    one went out.
    """
    sc = os.path.join(d, name + ".http")
    lines = read_lines(sc)
    n = lines.count(value)
    if n < 2:
        die("sidecar %s carries %r %d time(s); the duplicate shape needs 2" % (sc, value, n))
    out, dropped = [], False
    for l in lines:
        if l == value and not dropped:
            dropped = True
            continue
        out.append(l)
    write_lines(sc, out)
    print("  tamper: wire and sidecar each carried %r %d times; dropped ONE copy "
          "from the sidecar" % (value, n))


def mode_append_crosscheck(d, name):
    """T261 F-7 / route R3a -- invent an extra assertion under a KNOWN key.

    `known_keys` in the T250 verifier was an EXEMPTION LIST: a line whose key it
    recognised was `continue`d past every check.  So a fictional byte count rides
    in on a recognised key.
    """
    sc = os.path.join(d, name + ".http")
    lines = read_lines(sc)
    while lines and not lines[-1].strip():
        lines.pop()
    lines.append("content-length-crosscheck: MATCH (99999 bytes)")
    lines.append("")
    write_lines(sc, lines)
    print("  tamper: appended `content-length-crosscheck: MATCH (99999 bytes)` "
          "-- a byte count that is fiction, under a key the verifier recognised")


def mode_alter_crosscheck(d, name):
    """Route R3b -- the same exemption, taken by ALTERING the real line instead of
    adding a second one.  R3a smuggles a line in; R3b makes the existing one lie."""
    sc = os.path.join(d, name + ".http")
    lines = read_lines(sc)
    hit = False
    for i, l in enumerate(lines):
        if l.startswith("content-length-crosscheck: "):
            print("  tamper: %r -> `content-length-crosscheck: MATCH (99999 bytes)`" % l)
            lines[i] = "content-length-crosscheck: MATCH (99999 bytes)"
            hit = True
    if not hit:
        die("no `content-length-crosscheck: ` line in %s" % sc)
    write_lines(sc, lines)


def mode_drop_schema(d, name):
    """The DOWNGRADE shape.  Not one of T261's five: it is a route the T274 fix
    could have OPENED, so it is driven here too.  Delete `attestation-schema: 2`
    and see whether the response checks can be escaped."""
    sc = os.path.join(d, name + ".http")
    lines = read_lines(sc)
    kept = [l for l in lines if not l.startswith("attestation-schema:")]
    if len(kept) == len(lines):
        die("no `attestation-schema:` line in %s -- nothing to downgrade" % sc)
    write_lines(sc, kept)
    print("  tamper: deleted the `attestation-schema: 2` line (downgrade to schema 1)")


MODES = {
    "del-body-sha": (mode_del_body_sha, 2),
    "swap-headers": (mode_swap_headers, 2),
    "drop-dup": (mode_drop_dup, 3),
    "append-crosscheck": (mode_append_crosscheck, 2),
    "alter-crosscheck": (mode_alter_crosscheck, 2),
    "drop-schema": (mode_drop_schema, 2),
}


def main(argv):
    if len(argv) < 3 or argv[1] not in MODES:
        sys.stderr.write("usage: tamper.py MODE DIR NAME [ARG]\n  modes: %s\n"
                         % ", ".join(sorted(MODES)))
        return 2
    fn, nargs = MODES[argv[1]]
    if len(argv) - 2 != nargs:
        sys.stderr.write("mode %s takes %d argument(s)\n" % (argv[1], nargs))
        return 2
    fn(*argv[2:])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
