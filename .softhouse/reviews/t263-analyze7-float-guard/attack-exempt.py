#!/usr/bin/env python3
"""T263 -- attack PARSE-FLOAT-EXEMPT.txt, the highest-risk artifact in T164's diff.

T164 claims the register is DEFAULT-DENY, ENUMERABLE, PINNED and SELF-INVALIDATING. Each
of those is a claim about a DEATH CONDITION. This script CAUSES every death condition and
records what the guard actually did, and then tries five WIDENING attacks T164 did not
test -- ways to get a site exempted, or to keep it exempted, that should not work.

Method: a pristine copy of the rig is made for every arm, mutated, and graded. Nothing in
the repository is touched.

    exit 0 = the guard PASSED           exit 1 = FAIL         exit 2 = REFUSE

For a death condition, REFUSE (2) is the pass mark. For a widening attack, exit 0 is the
finding.
"""
import os
import shutil
import subprocess
import sys
import tempfile

SRC = os.environ["T263_RIG"]          # pristine tierA-a2 at T164 tip
GUARD = "guard-parse-float-ast.py"
REG = "PARSE-FLOAT-EXEMPT.txt"
ROWS = []


def fresh():
    d = tempfile.mkdtemp(prefix="t263-exempt-")
    r = os.path.join(d, "rig")
    shutil.copytree(SRC, r)
    return r


def grade(root):
    p = subprocess.run([sys.executable, os.path.join(root, GUARD), "--root", root],
                       capture_output=True, text=True)
    if p.returncode not in (0, 1, 2):
        sys.stderr.write("ABORT: guard exit %d -- outside {0,1,2}, an ERROR (P-80)\n%s\n"
                         % (p.returncode, p.stderr[-2000:]))
        raise SystemExit(3)
    return p.returncode, p.stdout, p.stderr


def reg_lines(root):
    return open(os.path.join(root, REG)).read().split("\n")


def write_reg(root, lines):
    open(os.path.join(root, REG), "w").write("\n".join(lines))


def record(arm, kind, want, rc, out, err, note=""):
    combined = out + err
    ok = (rc == want)
    ROWS.append((arm, kind, want, rc, "ok" if ok else "**MISMATCH**", note))
    print("  %-6s %-52s want=%d got=%d  %s"
          % ("ok" if ok else "MISS", arm, want, rc, note))
    return combined


def find_rec(lines, needle):
    for i, l in enumerate(lines):
        if l.startswith(needle) and "|" in l:
            return i
    raise SystemExit("ABORT: no register record starting %r -- the register changed "
                     "shape and this attack would silently measure nothing (P-66)" % needle)


def main():
    print("=" * 96)
    print("T263 -- DEATH CONDITIONS OF PARSE-FLOAT-EXEMPT.txt, caused not read")
    print("=" * 96)

    # ---- control: the register as committed must be GREEN, else nothing below means anything
    r = fresh()
    rc, out, err = grade(r)
    record("CONTROL: rig as committed", "control", 0, rc, out, err,
           "PASS printed: %s" % ("yes" if "PASS --" in out else "NO"))
    enumerated = out.count("FROZEN-T114")
    print("        register records printed in guard output: %d" % enumerated)
    baseline_out = out

    print()
    print("-- DEATH CONDITIONS (a REFUSE, exit 2, is the pass mark) " + "-" * 38)

    # 1. unknown category
    r = fresh(); L = reg_lines(r); i = find_rec(L, "resolve7.py | 24")
    L[i] = L[i].replace("FROZEN-T114", "FROZEN-T999", 1); write_reg(r, L)
    rc, out, err = grade(r); record("D1 unknown category FROZEN-T999", "death", 2, rc, out, err)

    # 2. stale record -- site does not exist
    r = fresh(); L = reg_lines(r); i = find_rec(L, "resolve7.py | 24")
    L[i] = L[i].replace("resolve7.py | 24", "resolve7.py | 9999", 1); write_reg(r, L)
    rc, out, err = grade(r); record("D2 stale: no such call site (line 9999)", "death", 2, rc, out, err)

    # 3. site now carries parse_float -> record is unnecessary
    r = fresh()
    p = os.path.join(r, "resolve7.py"); s = open(p).read().split("\n")
    assert "json.load(open(tmpl))" in s[23], s[23]
    s[23] = s[23].replace("json.load(open(tmpl))",
                          "json.load(open(tmpl), parse_float=decimal.Decimal)")
    open(p, "w").write("\n".join(s))
    rc, out, err = grade(r); record("D3 target FIXED -> record now unnecessary", "death", 2, rc, out, err)

    # 4. pinned source drift
    r = fresh(); L = reg_lines(r); i = find_rec(L, "resolve7.py | 24")
    L[i] = L[i].replace("body = json.load(open(tmpl))", "body = json.load(open(TMPL))", 1)
    write_reg(r, L)
    rc, out, err = grade(r); record("D4 pinned source text drifted", "death", 2, rc, out, err)

    # 5. FROZEN-T114 dies when the file's sha256 leaves MANIFEST.sha256
    r = fresh()
    p = os.path.join(r, "resolve7.py")
    open(p, "a").write("\n# T263 edit: this file is no longer frozen.\n")
    rc, out, err = grade(r)
    c = record("D5 FROZEN file EDITED (sha256 moves)", "death", 2, rc, out, err)
    print("        guard says: %s"
          % next((l.strip() for l in c.split("\n") if "HAS BEEN EDITED" in l), "(nothing)"))

    # 6. FROZEN-T114 dies when the named committed evidence disappears
    r = fresh(); os.remove(os.path.join(r, "RED-GREEN-A2-7-guards.txt"))
    rc, out, err = grade(r); record("D6 named committed evidence deleted", "death", 2, rc, out, err)

    # 7. FROZEN-T114 cannot be verified without MANIFEST.sha256
    r = fresh(); os.remove(os.path.join(r, "MANIFEST.sha256"))
    rc, out, err = grade(r); record("D7 MANIFEST.sha256 removed", "death", 2, rc, out, err)

    # 8. malformed record (wrong field count)
    r = fresh(); L = reg_lines(r); i = find_rec(L, "resolve7.py | 24")
    L[i] = "resolve7.py | 24 | FROZEN-T114 | body = json.load(open(tmpl))"; write_reg(r, L)
    rc, out, err = grade(r); record("D8 malformed record (4 fields not 6)", "death", 2, rc, out, err)

    # 9. REPRODUCTION-T207 dies when the target gains parse_float.
    #    No T207 record ships in this register, so one is INSTALLED to test the code path
    #    that would run if anyone ever used it. First green, then killed.
    r = fresh()
    open(os.path.join(r, "t263_repro.py"), "w").write(
        "import json\n"
        "def go(p):\n"
        "    return json.load(open(p))\n")
    open(os.path.join(r, "t263_target.py"), "w").write(
        "import json\n"
        "def t(p):\n"
        "    return json.load(open(p))\n")
    L = reg_lines(r)
    L.append("t263_repro.py | 3 | REPRODUCTION-T207 | return json.load(open(p)) | "
             "reproduces:t263_target.py:3 | T263 probe of the T207 code path")
    write_reg(r, L)
    rc, out, err = grade(r)
    record("D9a REPRODUCTION-T207 green while target unfixed", "death", 1, rc, out, err,
           "exit 1 expected: t263_target.py:3 is itself an undeclared violation")
    tgt_declared = "t263_repro.py" in out and "DECLARED REPRODUCTION-T207" in out
    print("        repro site graded DECLARED REPRODUCTION-T207: %s" % tgt_declared)
    # now fix the target -> the exemption must die (REFUSE), not merely stay green
    s = open(os.path.join(r, "t263_target.py")).read().replace(
        "json.load(open(p))", "json.load(open(p), parse_float=__import__('decimal').Decimal)")
    open(os.path.join(r, "t263_target.py"), "w").write(s)
    rc, out, err = grade(r)
    c = record("D9b target FIXED -> T207 exemption must die", "death", 2, rc, out, err)
    print("        guard says: %s"
          % next((l.strip() for l in c.split("\n") if "NOW CARRIES parse_float" in l),
                 "(nothing)"))

    print()
    print("-- WIDENING ATTACKS (exit 0 is the finding) " + "-" * 51)

    # W1. Can an ARBITRARY new violating site be exempted FROZEN-T114 by naming any
    #     existing file as its `produced:` evidence? The guard never checks that the
    #     named evidence was actually produced by the named file.
    r = fresh()
    open(os.path.join(r, "t263_newmoney.py"), "w").write(
        "import json\n"
        "def amounts(p):\n"
        "    return json.load(open(p))['pageItems']\n")
    # a brand-new file is not in MANIFEST.sha256 -> should be denied on that ground
    L = reg_lines(r)
    L.append("t263_newmoney.py | 3 | FROZEN-T114 | return json.load(open(p))['pageItems'] "
             "| produced:RED-GREEN-A2-7-guards.txt | T263: not frozen at all, and the "
             "evidence named was produced by a different file")
    write_reg(r, L)
    rc, out, err = grade(r)
    record("W1 exempt a BRAND-NEW file as FROZEN-T114", "widen", 2, rc, out, err,
           "denied only because MANIFEST does not pin it")

    # W2. Same attack, but on an EXISTING manifest-pinned, unedited rig file that has a
    #     violating load added... no: adding a load edits it, so sha moves. Instead take an
    #     EXISTING unedited pinned file that ALREADY has an undeclared-but-absent site.
    #     Test the real question: does `produced:` have to be true?  Point an EXISTING
    #     valid record at a completely unrelated evidence file.
    r = fresh(); L = reg_lines(r); i = find_rec(L, "resolve7.py | 24")
    L[i] = L[i].replace("produced:req/a2-7-loan-220-resolved.json",
                        "produced:CAPTURE-PLAN.md", 1)
    write_reg(r, L)
    rc, out, err = grade(r)
    record("W2 swap `produced:` for an unrelated existing file", "widen", 0, rc, out, err,
           "guard only checks the path EXISTS, not that the file produced it")

    # W3. `reproduces:` may name an ABSOLUTE path outside the rig entirely.
    r = fresh()
    out_dir = tempfile.mkdtemp(prefix="t263-outside-")
    ext = os.path.join(out_dir, "external.py")
    open(ext, "w").write("import json\ndef t(p):\n    return json.load(open(p))\n")
    open(os.path.join(r, "t263_repro2.py"), "w").write(
        "import json\ndef go(p):\n    return json.load(open(p))\n")
    L = reg_lines(r)
    L.append("t263_repro2.py | 3 | REPRODUCTION-T207 | return json.load(open(p)) | "
             "reproduces:%s:3 | T263: target lives outside the rig and outside the repo" % ext)
    write_reg(r, L)
    rc, out, err = grade(r)
    record("W3 `reproduces:` an ABSOLUTE path outside the repo", "widen", 1, rc, out, err,
           "exit 0 would mean an out-of-tree file can license an in-tree float")
    print("        repro2 graded DECLARED: %s"
          % ("DECLARED REPRODUCTION-T207" in out and "t263_repro2.py" in out))

    # W4. Delete the register entirely -- does the guard fail CLOSED?
    r = fresh(); os.remove(os.path.join(r, REG))
    rc, out, err = grade(r)
    record("W4 register DELETED entirely", "widen", 1, rc, out, err,
           "fail-closed: the 6 declared sites become violations")

    # W5. Truncate the register to empty
    r = fresh(); open(os.path.join(r, REG), "w").write("")
    rc, out, err = grade(r)
    record("W5 register EMPTIED", "widen", 1, rc, out, err, "fail-closed expected")

    # W6. Does the guard check the register's OWN integrity against MANIFEST.sha256?
    #     Add a harmless-looking comment: if the guard verified its own register digest
    #     this would REFUSE.
    r = fresh(); L = reg_lines(r)
    L.insert(0, "# T263: the register itself was edited. Does anything notice?")
    write_reg(r, L)
    rc, out, err = grade(r)
    record("W6 REGISTER ITSELF edited (its manifest digest now stale)", "widen", 2, rc, out, err,
           "the guard does not verify its own register's digest")

    print()
    print("=" * 96)
    misses = [x for x in ROWS if x[4] != "ok"]
    print("ARMS RUN: %d   ARMS WHERE THE GUARD DID NOT DO WHAT T263 EXPECTED: %d"
          % (len(ROWS), len(misses)))
    for a, k, w, g, s, n in misses:
        print("  %-6s %-52s want=%d got=%d  %s" % (k, a, w, g, n))
    print()
    print("Note on the pass mark: for `death` arms exit 2 is correct. For `widen` arms the")
    print("`want` column records what a CORRECT guard should do; a mismatch there is a")
    print("finding against the guard, not against this script.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
