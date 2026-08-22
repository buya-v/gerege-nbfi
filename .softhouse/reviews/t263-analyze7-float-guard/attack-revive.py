#!/usr/bin/env python3
"""T263 -- is the FROZEN-T114 death condition REVIVABLE?

T164's strongest claim about the register is:

    "FROZEN-T114 ... valid ONLY WHILE the file's sha256 still equals what MANIFEST.sha256
     pins for it. EDIT THE FILE AND THE EXEMPTION DIES WITH IT."

That is only true if MANIFEST.sha256 is itself immutable. It is not: `manifest.py write`
regenerates it, and T164's own task ran it. So the question a reviewer has to answer is
not "does the exemption die" (it does -- T263 arm D5 proved that) but "does it STAY
dead". This script answers it by doing the whole cycle in a scratch copy.

ARM R1  edit a FROZEN file so the exemption dies, then run `manifest.py write`,
        then re-grade. If the guard goes green again, the death condition is a
        speed bump, not a lock.

ARM R2  add a BRAND-NEW file with an unguarded money-shaped json.load, run
        `manifest.py write` so it becomes manifest-pinned, add a FROZEN-T114 record
        naming any existing evidence file, re-grade. If green, a new exemption can be
        minted for any file by anyone who can run two commands.

ARM R3  control -- after R2, does `manifest.py verify` still pass? If yes, no other
        instrument in the rig notices either.
"""
import os
import shutil
import subprocess
import sys
import tempfile

SRC = os.environ["T263_RIG"]
GUARD = "guard-parse-float-ast.py"
REG = "PARSE-FLOAT-EXEMPT.txt"


def fresh():
    d = tempfile.mkdtemp(prefix="t263-revive-")
    r = os.path.join(d, "rig")
    shutil.copytree(SRC, r)
    return r


def run(root, script, *args):
    p = subprocess.run([sys.executable, os.path.join(root, script)] + list(args),
                       capture_output=True, text=True, cwd=root)
    return p.returncode, p.stdout, p.stderr


def grade(root):
    rc, o, e = run(root, GUARD, "--root", root)
    if rc not in (0, 1, 2):
        sys.stderr.write("ABORT: guard exit %d (P-80)\n%s\n" % (rc, e[-1500:]))
        raise SystemExit(3)
    return rc, o, e


def say(label, rc, extra=""):
    print("    %-58s exit=%d  %s" % (label, rc, extra))


print("=" * 92)
print("T263 -- IS THE `FROZEN-T114` DEATH CONDITION REVIVABLE?")
print("=" * 92)

# ------------------------------------------------------------------ ARM R1
print("\nARM R1 -- edit a frozen file, then re-run `manifest.py write`")
r = fresh()
rc, _, _ = grade(r); say("1. pristine rig", rc, "(expect 0)")
p = os.path.join(r, "resolve7.py")
open(p, "a").write("\n# T263: an edit to a T114-frozen file.\n")
rc1, o1, _ = grade(r)
say("2. after editing the frozen file", rc1, "(expect 2 -- the exemption died)")
died = rc1 == 2
mrc, mo, me = run(r, "manifest.py", "write")
say("3. `manifest.py write`", mrc, mo.strip().split("\n")[-1] if mo.strip() else me.strip()[:60])
rc2, o2, e2 = grade(r)
say("4. re-grade after manifest write", rc2,
    "(0 here = the exemption CAME BACK TO LIFE over an edited file)")
revived = rc2 == 0
print("    R1 RESULT: exemption died=%s, revived by `manifest.py write`=%s" % (died, revived))
if revived:
    print("    -> `resolve7.py` now carries a T263 edit AND is still exempt. The guard says:")
    for l in o2.split("\n"):
        if "resolve7.py:24" in l:
            print("       %s" % l.strip())

# ------------------------------------------------------------------ ARM R2
print("\nARM R2 -- mint a NEW exemption for a NEW money-shaped loader")
r = fresh()
new = os.path.join(r, "t263_newmoney.py")
open(new, "w").write(
    "#!/usr/bin/env python3\n"
    '"""A brand-new analysis script that reads oracle amounts."""\n'
    "import json\n"
    "def amounts(p):\n"
    "    return [i['amount'] for i in json.load(open(p))['pageItems']]\n")
rc0, _, _ = grade(r)
say("1. new unguarded loader, no register record", rc0, "(expect 1 -- default-deny)")
L = open(os.path.join(r, REG)).read().split("\n")
L.append("t263_newmoney.py | 5 | FROZEN-T114 | return [i['amount'] for i in "
         "json.load(open(p))['pageItems']] | produced:RED-GREEN-A2-7-guards.txt | "
         "T263: this file produced nothing; the evidence named belongs to another file.")
open(os.path.join(r, REG), "w").write("\n".join(L))
rc1, _, _ = grade(r)
say("2. + a FROZEN-T114 record, before manifest write", rc1,
    "(expect 2 -- MANIFEST does not pin it yet)")
mrc, mo, me = run(r, "manifest.py", "write")
say("3. `manifest.py write`", mrc, mo.strip().split("\n")[-1] if mo.strip() else me.strip()[:60])
rc2, o2, e2 = grade(r)
say("4. re-grade", rc2, "(0 here = a NEW exemption was minted with two commands)")
minted = rc2 == 0
if minted:
    for l in o2.split("\n"):
        if "t263_newmoney" in l:
            print("       %s" % l.strip())
print("    R2 RESULT: new exemption minted for a file that produced no evidence = %s" % minted)

# ------------------------------------------------------------------ ARM R3
print("\nARM R3 -- does any OTHER rig instrument notice the R2 state?")
vrc, vo, ve = run(r, "manifest.py", "verify")
say("`manifest.py verify` after R2", vrc, (vo or ve).strip().split("\n")[-1][:70])
print("    R3 RESULT: manifest.py verify %s"
      % ("also passes -- nothing in the rig notices" if vrc == 0 else "catches it"))

print("\n" + "=" * 92)
print("Both R1 and R2 require a COMMITTED change to MANIFEST.sha256 and (R2) to the")
print("register, so a human reviewing the diff can see them. Neither is a silent widening")
print("at rest. What they show is that the mechanism's strength is CODE REVIEW OF THE")
print("MANIFEST DIFF, not the cryptographic self-invalidation the register advertises.")
