#!/usr/bin/env python3
"""A2-10 independent D-3 poison for manifest.py, written without reading A2-5's prover.

Method for every attack: build a sandbox shaped like the real capture, `write` the
manifest with the tool under test, perform the attack, `verify` with the same tool.
A guard I cannot drive RED is reported as a defect.
"""
import os, shutil, subprocess, sys, tempfile

TOOL = sys.argv[1]
LABEL = sys.argv[2]
rows = []

REAL_FILES = ["CAPTURE-PLAN.md", "DEFECTS-FOUND-BY-REVIEW.md", "cap.sh", "env.sh",
              "run-020-accounts.sh", "mkreq.py", "show.py"]


def sandbox(flagfile=True):
    d = tempfile.mkdtemp(prefix="d3.")
    for sub in ("out", "req", "sql"):
        os.makedirs(os.path.join(d, sub))
    shutil.copy(TOOL, os.path.join(d, "manifest.py"))
    for n in REAL_FILES:
        open(os.path.join(d, n), "w").write("# %s\ncontent of %s\n" % (n, n))
    open(os.path.join(d, "out", "A2-020-real.json"), "w").write('{"resourceId":1}')
    open(os.path.join(d, "out", "A2-020-real.status"), "w").write("200\n")
    open(os.path.join(d, "out", "attempt1-A2-001.json"), "w").write('{"attempt1":true}')
    open(os.path.join(d, "req", "gl-020.json"), "w").write('{"glCode":"10001"}')
    open(os.path.join(d, "sql", "q1.sql"), "w").write("select 1;\n")
    if flagfile:
        open(os.path.join(d, "FLAGGED-NOT-REPRODUCIBLE.txt"), "w").write(
            "# D-1: recipes provably false, NOT citable\nout/attempt1-A2-001.json\n")
    return d


def run(d, cmd):
    p = subprocess.run([sys.executable, os.path.join(d, "manifest.py"), cmd],
                       capture_output=True, cwd=d)
    return p.returncode, (p.stdout + p.stderr).decode()


def attack(name, mutate, expect_red=True, flagfile=True):
    d = sandbox(flagfile=flagfile)
    rc_w, out_w = run(d, "write")
    mutate(d)
    rc, out = run(d, "verify")
    red = rc != 0
    ok = red == expect_red
    rows.append((name, rc, ok, out.strip().splitlines()[:2]))
    print("  %-9s %-52s verify exit=%s  %s" % (
        "RED" if red else "green", name, rc,
        "" if ok else ("<-- EXPECTED %s" % ("RED" if expect_red else "GREEN"))))
    if not ok:
        print("        tool said: %s" % out.strip().replace("\n", " | ")[:300])
    shutil.rmtree(d, ignore_errors=True)
    return ok


print("=== %s :: %s ===" % (LABEL, TOOL))

# ---- control: an untampered sandbox must go GREEN, else every RED below is vacuous
attack("CONTROL untampered sandbox (must be GREEN)", lambda d: None, expect_red=False)

# ---- (b) D-3(i): zero files inspected must be an ERROR
def empty_manifest(d):
    open(os.path.join(d, "MANIFEST.sha256"), "w").write("")
attack("(b) empty MANIFEST.sha256 - INSPECTED NOTHING", empty_manifest)

def strip_to_one(d):
    p = os.path.join(d, "MANIFEST.sha256")
    lines = open(p).readlines()
    open(p, "w").writelines(lines[:1])
attack("(b) manifest stripped to a single line", strip_to_one)

def empty_everything(d):
    open(os.path.join(d, "MANIFEST.sha256"), "w").write("")
    for root, dn, fn in os.walk(d):
        for n in fn:
            if n not in ("manifest.py", "MANIFEST.sha256"):
                os.remove(os.path.join(root, n))
attack("(b) empty manifest AND empty capture dir", empty_everything)

# ---- (c) D-3(ii): fabricated observation in out/<subdir>/
def fabricate_subdir(d):
    os.makedirs(os.path.join(d, "out", "sub"))
    open(os.path.join(d, "out", "sub", "A2-999-FABRICATED.json"), "w").write(
        '{"FABRICATED":"never observed from any oracle"}')
attack("(c) fabricated out/sub/A2-999-FABRICATED.json", fabricate_subdir)

def fabricate_deep(d):
    os.makedirs(os.path.join(d, "out", "a", "b", "c"))
    open(os.path.join(d, "out", "a", "b", "c", "A2-998.json"), "w").write('{"FABRICATED":1}')
attack("(c) fabricated out/a/b/c/A2-998.json (3 deep)", fabricate_deep)

def fabricate_toplevel(d):
    open(os.path.join(d, "out", "A2-997-FABRICATED.json"), "w").write('{"FABRICATED":1}')
attack("(c) fabricated out/A2-997 (top level, pre-fix control)", fabricate_toplevel)

# ---- (d) D-3(iii): the analysis doc, the rig, and manifest.py ITSELF
def poison_plan(d):
    with open(os.path.join(d, "CAPTURE-PLAN.md"), "a") as f:
        f.write("\nMNT rounds HALF_EVEN and money may be stored as a float.\n")
attack("(d) false sentence appended to CAPTURE-PLAN.md", poison_plan)

def poison_rig(d):
    with open(os.path.join(d, "cap.sh"), "a") as f:
        f.write('\nB=https://evil.example/api/v1\n')
attack("(d) cap.sh repointed at another endpoint", poison_rig)

def poison_env(d):
    with open(os.path.join(d, "env.sh"), "a") as f:
        f.write("\nT='Fineract-Platform-TenantId: default'\n")
attack("(d) env.sh switched to the WRONG TENANT", poison_env)

def poison_runscript(d):
    with open(os.path.join(d, "run-020-accounts.sh"), "a") as f:
        f.write("\n# recipe silently changed\n")
attack("(d) run-020-accounts.sh recipe altered", poison_runscript)

def poison_self(d):
    with open(os.path.join(d, "manifest.py"), "a") as f:
        f.write("\n# manifest.py edits ITSELF\n")
attack("(d) manifest.py appends to ITSELF", poison_self)

def poison_self_neuter(d):
    """The nastiest self-edit: neuter verify() so it always returns 0."""
    p = os.path.join(d, "manifest.py")
    src = open(p).read().replace("    sys.exit(verify())", "    sys.exit(0)")
    open(p, "w").write(src)
attack("(d) manifest.py NEUTERS its own verify() -> sys.exit(0)", poison_self_neuter)

def poison_defects(d):
    with open(os.path.join(d, "DEFECTS-FOUND-BY-REVIEW.md"), "a") as f:
        f.write("\nAll defects resolved.\n")
attack("(d) DEFECTS-FOUND-BY-REVIEW.md rewritten", poison_defects)

# ---- evidence deletion / flag integrity
def delete_evidence(d):
    os.remove(os.path.join(d, "out", "A2-020-real.json"))
attack("evidence file deleted from out/", delete_evidence)

def delete_flagged(d):
    os.remove(os.path.join(d, "out", "attempt1-A2-001.json"))
attack("FLAGGED attempt1-* evidence deleted", delete_flagged)

def delete_flagfile(d):
    os.remove(os.path.join(d, "FLAGGED-NOT-REPRODUCIBLE.txt"))
attack("FLAGGED-NOT-REPRODUCIBLE.txt deleted", delete_flagfile)

def uncover_flagged(d):
    p = os.path.join(d, "MANIFEST.sha256")
    lines = [l for l in open(p) if "attempt1" not in l]
    open(p, "w").writelines(lines)
attack("flagged file's manifest line stripped", uncover_flagged)

def mutate_evidence(d):
    open(os.path.join(d, "out", "A2-020-real.json"), "w").write('{"resourceId":999}')
attack("evidence body mutated in place", mutate_evidence)

def malformed(d):
    p = os.path.join(d, "MANIFEST.sha256")
    lines = open(p).readlines()
    lines[0] = "not-a-manifest-line\n"
    open(p, "w").writelines(lines)
attack("malformed manifest line", malformed)

# ---- MY OWN extra attacks, beyond what A2-5 claimed -------------------------------
def symlink_fabrication(d):
    """Drop a SYMLINK observation into out/. entries() skips symlinks."""
    fake = os.path.join(d, "FABRICATED-SOURCE.json")
    open(fake, "w").write('{"FABRICATED":"via symlink, never observed"}')
    os.symlink(fake, os.path.join(d, "out", "A2-996-FABRICATED.json"))
attack("EXTRA: fabricated observation dropped as a SYMLINK in out/", symlink_fabrication)

def symlink_subdir(d):
    """A whole fabricated directory symlinked into out/."""
    src = os.path.join(d, "fabdir")
    os.makedirs(src)
    open(os.path.join(src, "A2-995-FABRICATED.json"), "w").write('{"FABRICATED":1}')
    os.symlink(src, os.path.join(d, "out", "sub"))
attack("EXTRA: fabricated DIRECTORY symlinked as out/sub", symlink_subdir)

def new_toplevel_dir(d):
    """A fabricated observation in a NEW top-level directory (not out/req/sql)."""
    os.makedirs(os.path.join(d, "out2"))
    open(os.path.join(d, "out2", "A2-994-FABRICATED.json"), "w").write('{"FABRICATED":1}')
attack("EXTRA: fabricated observation in a NEW top-level dir out2/", new_toplevel_dir)

def dup_line(d):
    """Two manifest lines for the same path, the second one a lie."""
    p = os.path.join(d, "MANIFEST.sha256")
    lines = open(p).readlines()
    victim = [l for l in lines if l.strip().endswith("out/A2-020-real.json")][0]
    open(p, "w").writelines(lines + ["0" * 64 + "  out/A2-020-real.json\n"])
attack("EXTRA: duplicate manifest line, second one a false hash", dup_line)

def gut_flagfile(d):
    """Comment out every flagged path, leaving the flag file present but toothless."""
    p = os.path.join(d, "FLAGGED-NOT-REPRODUCIBLE.txt")
    open(p, "w").write("# nothing flagged any more\n")
attack("EXTRA: flag file gutted to zero flagged paths", gut_flagfile)

print()
bad = [r for r in rows if not r[2]]
print("attacks=%d  as-expected=%d  NOT-as-expected=%d" % (len(rows), len(rows) - len(bad), len(bad)))
for name, rc, ok, head in bad:
    print("  NOT AS EXPECTED:", name, "exit", rc)
sys.exit(1 if bad else 0)
