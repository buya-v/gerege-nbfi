#!/usr/bin/env python3
"""T250 instrument 12 -- the TENANT term specifically, and the worse class.

Instruments 10/11 measure the general shape (literal attestation where a
variable was available).  This one asks the question T245 F-2 actually raises:

  A. how many tracked scripts SEND a tenant selector to the reference oracle
     (`Fineract-Platform-TenantId` header, or `tenantIdentifier=` query param,
     or a `psql -d fineract_<tenant>` read-back)?
  B. of those, how many ATTEST the tenant into a sidecar AT ALL?
  C. of those that attest, how many attest it as a LITERAL (F-2 proper)?
  D. of those that send, how many attest NOTHING -- which is strictly worse
     than a literal, because there is no line to be wrong.

Reported as counts AND rosters (P-67: both terms; P-66: scope stated).
SCOPE: `git ls-files` of this worktree, suffix .sh or .py.  Nothing else.
Engine: python3 `re` (P-75).  git failure ABORTS (exit 5).
"""
import os
import re
import subprocess
import sys

ROOT = os.path.realpath(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..", "..", "..")
)
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
_pop = __import__("10-population")

SENDS_TENANT = re.compile(
    r"""Fineract-Platform-TenantId|tenantIdentifier\s*=|-d\s+fineract_[a-z]""",
    re.IGNORECASE,
)
# writes into a sidecar/record file rather than just printing to a terminal
WRITES_RECORD = re.compile(r""">\s*"?\$?\{?(?:HTTP|OUT|REC|ATTEST|SIDECAR)|\.http|open\(""")


def read(path):
    with open(path, "rb") as fh:
        raw = fh.read()
    if b"\x00" in raw[:8192]:
        return None
    return raw.decode("utf-8", "replace")


def tenant_attest_lines(text):
    """Emitted `Fineract-Platform-TenantId: ...` lines, literal or derived."""
    out = []
    for m in re.finditer(
        r"""(?:echo|printf|print)[^\n]*?["']Fineract-Platform-TenantId:\s*([^"'\n]*)["']""",
        text,
    ):
        line_no = text.count("\n", 0, m.start()) + 1
        val = m.group(1)
        out.append((line_no, val, "DERIVED" if "$" in val or "%" in val else "LITERAL"))
    return out


def main():
    proc = subprocess.run(["git", "-C", ROOT, "ls-files"], capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write("ABORT: git ls-files rc=%d\n" % proc.returncode)
        sys.exit(5)
    scripts = [p for p in proc.stdout.splitlines() if p.endswith(".sh") or p.endswith(".py")]

    senders, attesters, literal, derived, silent = [], [], [], [], []
    skipped_binary = 0
    for rel in scripts:
        path = os.path.join(ROOT, rel)
        if not os.path.isfile(path):
            continue
        text = read(path)
        if text is None:
            skipped_binary += 1
            continue
        if not _pop.ORACLE_RE.search(text):
            continue
        if not SENDS_TENANT.search(text):
            continue
        senders.append(rel)
        tl = tenant_attest_lines(text)
        if not tl:
            silent.append(rel)
            continue
        attesters.append(rel)
        if any(k == "LITERAL" for _, _, k in tl):
            literal.append((rel, tl))
        else:
            derived.append((rel, tl))

    print("SCOPE: git ls-files of %s ; suffix .sh/.py ; must invoke curl or psql" % ROOT)
    print("  .sh/.py scanned                              : %d" % len(scripts))
    print("  binary, SKIPPED                              : %d" % skipped_binary)
    print("")
    print("A. scripts that SEND a tenant selector to the oracle      : %d" % len(senders))
    for p in senders:
        print("      %s" % p)
    print("")
    print("B. of those, that ATTEST the tenant into a record at all  : %d" % len(attesters))
    print("C. of those attesters, attesting it as a LITERAL (F-2)    : %d" % len(literal))
    for p, tl in literal:
        for line_no, val, kind in tl:
            print("      %s:%d  %s  `%s`" % (p, line_no, kind, val))
    print("   ... attesting it DERIVED from the value in force       : %d" % len(derived))
    for p, tl in derived:
        for line_no, val, kind in tl:
            print("      %s:%d  %s  `%s`" % (p, line_no, kind, val))
    print("")
    print("D. SEND a tenant but attest NO tenant line anywhere       : %d" % len(silent))
    print("   (strictly worse than a literal: no line to be wrong)")
    for p in silent:
        print("      %s" % p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
