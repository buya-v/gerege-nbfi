#!/usr/bin/env python3
"""T261 -- INDEPENDENT re-derivation of T250's tenant split A/B/C/D (50/5/5/0/45).

Independently written.  WIDER than T250's instrument 12 on both axes, so an
undercount on either side would surface:

  SEND  : Fineract-Platform-TenantId | tenantIdentifier= | psql -d fineract_* |
          PGDATABASE=fineract* | --dbname fineract* | tenant_identifier
  ATTEST: echo/printf/print/<obj>.write of a `Fineract-Platform-TenantId:` line
          AND ALSO a bare `Fineract-Platform-TenantId:` line inside a heredoc
          body (T250's instrument 12 matches only echo|printf|print and so is
          blind to heredoc-written sidecars).

Engine: python3 `re` only (P-75).  No grep / rg / git grep.
Population: `git ls-tree -r --name-only <tree>`; non-zero git exit ABORTS (5).
Calibrated on a positive AND a negative per bucket; disagreement ABORTS (4).

usage: t261-tenant-term.py <tree-ish> <root-dir>
"""
import os
import re
import subprocess
import sys

TREE = sys.argv[1]
ROOT = sys.argv[2]

ORACLE = re.compile(r"\bcurl\b|\bpsql\b|localhost:8443")
SENDS = re.compile(
    r"Fineract-Platform-TenantId"
    r"|tenantIdentifier\s*="
    r"|-d\s+fineract_[a-z]"
    r"|--dbname[= ]+fineract"
    r"|PGDATABASE\s*=\s*[\"']?fineract"
    r"|tenant_identifier",
    re.IGNORECASE,
)
EMIT = re.compile(
    r"""(?:echo|printf|print|\.write)\s*\(?\s*["'][^"'\n]*?"""
    r"""Fineract-Platform-TenantId:\s*(?P<val>[^"'\n]*)["']""",
    re.IGNORECASE,
)
HEREDOC_OPEN = re.compile(r"<<-?\s*[\"']?(?P<tag>[A-Za-z_][A-Za-z0-9_]*)[\"']?")
BARE_TENANT = re.compile(r"^Fineract-Platform-TenantId:\s*(?P<val>.*)$",
                         re.M | re.IGNORECASE)


def read(path):
    with open(path, "rb") as fh:
        raw = fh.read()
    if b"\x00" in raw[:8192]:
        return None
    return raw.decode("utf-8", "replace")


def heredoc_spans(text):
    spans = []
    lines = text.split("\n")
    offs, o = [], 0
    for line in lines:
        offs.append(o)
        o += len(line) + 1
    i = 0
    while i < len(lines):
        m = HEREDOC_OPEN.search(lines[i])
        if m:
            tag = m.group("tag")
            j = i + 1
            while j < len(lines) and lines[j].strip() != tag:
                j += 1
            if j < len(lines):
                spans.append((offs[i + 1] if i + 1 < len(offs) else o,
                              offs[j] if j < len(offs) else o))
                i = j
        i += 1
    return spans


def tenant_attestations(text):
    out = []
    for m in EMIT.finditer(text):
        v = m.group("val")
        kind = "DERIVED" if ("$" in v or "%" in v or "{" in v) else "LITERAL"
        out.append((text.count("\n", 0, m.start()) + 1, v, kind, "emitter"))
    for (a, b) in heredoc_spans(text):
        for m in BARE_TENANT.finditer(text[a:b]):
            v = m.group("val")
            kind = "DERIVED" if ("$" in v or "%" in v or "{" in v) else "LITERAL"
            out.append((text.count("\n", 0, a + m.start()) + 1, v, kind, "heredoc"))
    return out


def calibrate():
    cases = [
        ("send+literal", 'curl -H "$T" x\necho "Fineract-Platform-TenantId: gerege"\n',
         True, 1, "LITERAL"),
        ("send+derived", 'curl -H "$T" x\necho "Fineract-Platform-TenantId: $TEN"\n',
         True, 1, "DERIVED"),
        ("send+silent", 'curl -H "Fineract-Platform-TenantId: g" x\n', True, 0, None),
        ("no-send", 'echo "hello: world"\n', False, 0, None),
        ("heredoc-literal",
         'curl -H "$T" x\ncat > f <<EOF\nFineract-Platform-TenantId: gerege\nEOF\n',
         True, 1, "LITERAL"),
    ]
    ok = True
    for name, src, wsend, wn, wkind in cases:
        send = bool(ORACLE.search(src) and SENDS.search(src))
        at = tenant_attestations(src)
        got_kind = at[0][2] if at else None
        good = (send == wsend) and (len(at) == wn) and (got_kind == wkind)
        print("CALIBRATION %-18s send=%-5s n=%d kind=%-8s  %s"
              % (name, send, len(at), got_kind, "OK" if good else "MISMATCH"))
        if not good:
            ok = False
    if not ok:
        sys.stderr.write("CALIBRATION FAILED -- ABORT\n")
        sys.exit(4)
    print("CALIBRATION OK\n")


def main():
    calibrate()
    p = subprocess.run(["git", "ls-tree", "-r", "--name-only", TREE],
                       capture_output=True, text=True)
    if p.returncode != 0:
        sys.stderr.write("ABORT: git ls-tree rc=%d %s\n" % (p.returncode, p.stderr))
        sys.exit(5)
    scripts = [x for x in p.stdout.splitlines()
               if x.endswith(".sh") or x.endswith(".py")]
    senders, attesters, literal, derived, silent = [], [], [], [], []
    binary = 0
    for rel in scripts:
        path = os.path.join(ROOT, rel)
        if not os.path.isfile(path):
            continue
        text = read(path)
        if text is None:
            binary += 1
            continue
        if not ORACLE.search(text):
            continue
        if not SENDS.search(text):
            continue
        senders.append(rel)
        at = tenant_attestations(text)
        if not at:
            silent.append(rel)
            continue
        attesters.append(rel)
        if any(k == "LITERAL" for _, _, k, _ in at):
            literal.append((rel, at))
        else:
            derived.append((rel, at))
    print("SCOPE tree=%s root=%s ; suffix .sh/.py ; must contain curl/psql/oracle host"
          % (TREE, os.path.realpath(ROOT)))
    print("  .sh/.py scanned : %d" % len(scripts))
    print("  binary skipped  : %d" % binary)
    print("")
    print("A. SEND a tenant selector to the oracle          : %d" % len(senders))
    for x in senders:
        print("      %s" % x)
    print("")
    print("B. of those, ATTEST the tenant into a record     : %d" % len(attesters))
    print("C.   ... as a LITERAL                            : %d" % len(literal))
    for rel, at in literal:
        for (l, v, k, how) in at:
            print("      %s:%d  %s  `%s`  [%s]" % (rel, l, k, v, how))
    print("   ... DERIVED from the value in force           : %d" % len(derived))
    for rel, at in derived:
        for (l, v, k, how) in at:
            print("      %s:%d  %s  `%s`  [%s]" % (rel, l, k, v, how))
    print("")
    print("D. SEND but attest NO tenant line anywhere       : %d" % len(silent))
    for x in silent:
        print("      %s" % x)
    print("")
    print("SPLIT  A=%d  B=%d  C(literal)=%d  derived=%d  D(silent)=%d"
          % (len(senders), len(attesters), len(literal), len(derived), len(silent)))
    assert len(attesters) + len(silent) == len(senders), "A != B + D"
    print("CHECK  B + D == A : %d + %d == %d  OK"
          % (len(attesters), len(silent), len(senders)))


main()
