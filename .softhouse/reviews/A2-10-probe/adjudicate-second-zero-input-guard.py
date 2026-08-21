#!/usr/bin/env python3
"""A2-10 adjudication of A2-5 self-report #2: it labelled the SECOND zero-input refusal
   REFUSING: found 0 files under out/, req/, sql/ or this directory - INSPECTED NOTHING
as "could not be driven red ... belt-and-braces". Is it inert, or is it broken?

A2-5's stated reason: manifest.py now covers itself, so entries() always yields at least
one file. But entries() skips SYMLINKS (`not os.path.islink(p)`) - so invoke the tool
THROUGH a symlink in a directory holding nothing else and `have` is empty.
"""
import os, subprocess, sys, tempfile

TOOL = sys.argv[1]
LABEL = sys.argv[2]

d = tempfile.mkdtemp(prefix="d3c.")
os.symlink(os.path.abspath(TOOL), os.path.join(d, "manifest.py"))
# a NON-empty manifest, so the FIRST zero-input refusal ("lists 0 files") cannot fire
open(os.path.join(d, "MANIFEST.sha256"), "w").write("%s  out/A2-020.json\n" % ("a" * 64))

p = subprocess.run([sys.executable, os.path.join(d, "manifest.py"), "verify"],
                   capture_output=True, cwd=d)
out = (p.stdout + p.stderr).decode()
print("=== %s ===" % LABEL)
print("dir contents:", sorted(os.listdir(d)))
print("exit:", p.returncode)
print(out.strip())
hit = "found 0 files under" in out
print("SECOND zero-input refusal FIRED:", hit)
sys.exit(0 if hit else 1)
