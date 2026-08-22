#!/usr/bin/env python3
"""T250 instrument 11 -- SELECTOR CHECK for instrument 10.

P-76 addendum: check your selector before you trust your conditions.  Instrument
10 narrowed twice, and each narrowing could hide population:

  NARROWING A: suffix `.sh` or `.py`.
      -> could miss an attestation writer with another suffix (Makefile, .zsh,
         .bash, extensionless executable, .md-embedded recipe).
  NARROWING B: the file must itself contain `curl` or `psql`.
      -> could miss a caller/driver that writes the sidecar while a helper does
         the transport.
  NARROWING C: `shadowing_var` requires the variable value to EQUAL the emitted
      value.  A REDACTED literal (`Authorization: Basic <mifos:password>` while
      `$A` holds the real base64) is equally unfalsifiable but does NOT match.

Each narrowing is measured here so the skip is COUNTED (P-40), not assumed empty.
Engine: python3 `re` only (P-75).  git failure ABORTS (exit 5).
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

BINARY_HINT = re.compile(rb"\x00")
# a script that WRITES a sidecar named *.http
HTTP_SIDECAR = re.compile(r"""\.http\b""")
# a call out to one of the known transport helpers
HELPER_CALL = re.compile(r"""\bcap(?:8|9|10)?\.sh\b|\bcapture\.sh\b|\blib\.sh\b""")


def read(path):
    with open(path, "rb") as fh:
        raw = fh.read()
    if BINARY_HINT.search(raw[:8192]):
        return None
    return raw.decode("utf-8", "replace")


def main():
    proc = subprocess.run(["git", "-C", ROOT, "ls-files"], capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write("ABORT: git ls-files rc=%d\n" % proc.returncode)
        sys.exit(5)
    tracked = proc.stdout.splitlines()

    scripts = set(p for p in tracked if p.endswith(".sh") or p.endswith(".py"))
    binary = 0
    missing = 0

    attest_any = []          # writes >=1 literal `Key: value`, ANY suffix
    attest_nonscript = []    # ... and is NOT .sh/.py
    attest_no_oracle = []    # ... is .sh/.py, writes attestation, no curl/psql in file
    helper_writers = []      # ... no curl/psql but calls a known transport helper
    http_writers = []        # mentions a `.http` sidecar path, any suffix
    redaction_class = []     # key-shadowed but value differs (redacted literal)

    for rel in tracked:
        path = os.path.join(ROOT, rel)
        if not os.path.isfile(path):
            missing += 1
            continue
        text = read(path)
        if text is None:
            binary += 1
            continue
        if HTTP_SIDECAR.search(text):
            http_writers.append(rel)
        hits = _pop.attest_lines(text)
        if not hits:
            continue
        attest_any.append(rel)
        if rel not in scripts:
            attest_nonscript.append(rel)
            continue
        if not _pop.ORACLE_RE.search(text):
            attest_no_oracle.append(rel)
            if HELPER_CALL.search(text):
                helper_writers.append(rel)
            continue
        # NARROWING C: same key, different value -> redacted / drifted literal.
        scope = _pop.in_scope_vars(path, text)
        for line_no, key, val, _raw in hits:
            if _pop.shadowing_var(scope, key, val):
                continue
            for name, vals in sorted(scope.items()):
                for v in vals:
                    if v.strip().startswith(key + ": ") and v.strip() != "%s: %s" % (key, val):
                        redaction_class.append((rel, line_no, key, val, name, v.strip()))
                        break
                else:
                    continue
                break

    print("SCOPE: every path in `git ls-files` of %s" % ROOT)
    print("tracked files                                  : %d" % len(tracked))
    print("  binary, SKIPPED                              : %d" % binary)
    print("  tracked but absent from disk, SKIPPED        : %d" % missing)
    print("")
    print("NARROWING A -- suffix filter")
    print("  files (ANY suffix) emitting >=1 literal `Key: value` : %d" % len(attest_any))
    print("  of those NOT .sh/.py (would have been missed)        : %d" % len(attest_nonscript))
    for p in attest_nonscript:
        print("      %s" % p)
    print("")
    print("NARROWING B -- `curl|psql` in-file filter")
    print("  .sh/.py attestation writers with NO curl/psql        : %d" % len(attest_no_oracle))
    print("  of those that call a known transport helper          : %d" % len(helper_writers))
    for p in helper_writers:
        print("      %s" % p)
    print("")
    print("NARROWING C -- exact-value match in shadowing_var")
    print("  REDACTION CLASS: same header key held by an in-scope var,")
    print("  emitted literal differs (unfalsifiable but deliberate) : %d" % len(redaction_class))
    for rel, line_no, key, val, name, v in redaction_class:
        print("      %s:%d  emitted `%s: %s`  while $%s = `%s`" % (rel, line_no, key, val, name, v))
    print("")
    print("CROSS-CHECK -- files naming a `.http` sidecar path      : %d" % len(http_writers))
    for p in http_writers:
        print("      %s" % p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
