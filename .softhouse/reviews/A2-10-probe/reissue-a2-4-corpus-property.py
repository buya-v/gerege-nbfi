#!/usr/bin/env python3
"""A2-10 (f): does A2-4's corpus property still hold?

A2-4: "All 27 non-attempt1 POST refusals ... byte-identical = 24, differs = 3".
Re-issue the same set against the LIVE oracle, using the BRANCH's fixed cap.sh, into a
SANDBOX out/ so not one committed byte is touched, and compare.

Replaying a refusal mutates no committed row (A2-4's own stated reason for choosing
this set). GETs and successful POSTs are deliberately NOT re-issued.
"""
import os, shutil, subprocess, sys, tempfile

SRC = "/tmp/a210/.softhouse/capture/tierA-a2"
sand = tempfile.mkdtemp(prefix="reissue.")
os.makedirs(sand + "/out")
shutil.copytree(SRC + "/req", sand + "/req")
for f in ("cap.sh", "env.sh"):
    shutil.copy(SRC + "/" + f, sand + "/" + f)
os.chmod(sand + "/cap.sh", 0o755)

# --- select the set: non-attempt1, POST, recorded status 4xx
recipes = []
for n in sorted(os.listdir(SRC + "/out")):
    if not n.endswith(".http") or n.startswith("attempt1-"):
        continue
    name = n[:-5]
    meta = open(SRC + "/out/" + n).read()
    line1 = meta.splitlines()[0]
    method, path = line1.split(" ", 1)
    bodyfile = None
    for ln in meta.splitlines():
        if ln.startswith("body-file: "):
            bodyfile = ln.split(" ", 1)[1]
    st = open(SRC + "/out/" + name + ".status").read().strip()
    if method == "POST" and st.startswith("4"):
        recipes.append((name, method, path, bodyfile, st))

print("selected %d non-attempt1 POST recipes with a recorded 4xx" % len(recipes))
same, diff, err = [], [], []
for name, method, path, bodyfile, st in recipes:
    args = ["/bin/sh", sand + "/cap.sh", name, method, path] + ([bodyfile] if bodyfile else [])
    p = subprocess.run(args, capture_output=True)
    if p.returncode != 0:
        err.append((name, p.returncode, p.stderr.decode().strip()[:120]))
        continue
    new_body = open(sand + "/out/" + name + ".json", "rb").read()
    old_body = open(SRC + "/out/" + name + ".json", "rb").read()
    new_st = open(sand + "/out/" + name + ".status").read().strip()
    if new_body == old_body and new_st == st:
        same.append(name)
    else:
        diff.append((name, st, new_st, old_body[:150], new_body[:150]))

print()
print("byte-identical = %d   differs = %d   transport-error = %d" % (len(same), len(diff), len(err)))
print()
for name, ost, nst, ob, nb in diff:
    print("DIFFERS %s  status %s -> %s" % (name, ost, nst))
    print("   was: %r" % ob)
    print("   now: %r" % nb)
for e in err:
    print("TRANSPORT ERROR", e)

# prove nothing committed was touched
p = subprocess.run([sys.executable, SRC + "/manifest.py", "verify"], capture_output=True, cwd=SRC)
print()
print("committed capture dir manifest verify after the re-issue -> exit", p.returncode)
print((p.stdout + p.stderr).decode().strip())
print("sandbox was:", sand)
shutil.rmtree(sand, ignore_errors=True)
