#!/usr/bin/env python3
"""T61 separating-shape sweep.

For a named mutation that SURVIVES the promoted corpus, this locates a request
shape on which the mutant and the true port disagree in a PAYABLE amount. That
shape is then the request to put to the reference oracle (Fineract).

It never builds a mutation inside the committed tree. The port is copied to
/tmp/t61sweep/nexus (T58's precedent), the mutation is applied there, and the
scratch tree is thrown away.

    python3 .softhouse/handoff/T61-sweep/run-sweep.py M1 --n 6,12 --p-from ...

Money is int64 minor units end to end; there is no floating point here.
"""
import os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, ".softhouse", "handoff"))

import importlib.util
spec = importlib.util.spec_from_file_location("t61mut", os.path.join(ROOT, ".softhouse/handoff/T61-mutations.py"))
t61mut = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t61mut)

SCRATCH = os.environ.get("T61_SCRATCH", "/tmp/t61sweep")
TC = "/Users/buv/gerege-nbfi/.softhouse/toolchain"


def env():
    e = dict(os.environ)
    e.update(GOROOT=TC + "/go", GOPATH=TC + "/gopath", GOCACHE=TC + "/gocache",
             GOMODCACHE=TC + "/gomodcache", PATH=TC + "/go/bin:" + e.get("PATH", ""))
    return e


def make_scratch():
    if os.path.isdir(SCRATCH):
        shutil.rmtree(SCRATCH)
    os.makedirs(SCRATCH)
    shutil.copytree(os.path.join(ROOT, "nexus"), os.path.join(SCRATCH, "nexus"))
    d = os.path.join(SCRATCH, "nexus", "cmd", "t61sweep")
    os.makedirs(d, exist_ok=True)
    shutil.copy(os.path.join(HERE, "sweep_main.go"), os.path.join(d, "main.go"))


def build(tag):
    out = os.path.join(SCRATCH, "bin-" + tag)
    p = subprocess.run(["go", "build", "-o", out, "./cmd/t61sweep"],
                       cwd=os.path.join(SCRATCH, "nexus"), env=env(),
                       capture_output=True, text=True)
    if p.returncode != 0:
        raise SystemExit("build %s failed:\n%s" % (tag, p.stderr))
    return out


def run(binpath, args):
    p = subprocess.run([binpath] + args, capture_output=True, text=True)
    if p.returncode != 0:
        raise SystemExit("run failed: %s" % p.stderr[:2000])
    return p.stdout


def patch_scratch(mid):
    _, name, patches, _ = t61mut.BY_ID[mid]
    for path, old, new in patches:
        rel = os.path.relpath(path, os.path.join(ROOT, "nexus"))
        target = os.path.join(SCRATCH, "nexus", rel)
        src = open(target).read()
        if src.count(old) != 1:
            raise SystemExit("ANCHOR MISS for %s in %s (%d)" % (mid, rel, src.count(old)))
        open(target, "w").write(src.replace(old, new))
    return name


def cells(line):
    key, digest = line.split("\t", 1)
    return key, digest.strip()


def main():
    mids = [a for a in sys.argv[1:] if re.fullmatch(r"M\d+", a)]
    passthru = [a for a in sys.argv[1:] if a not in mids]
    if not mids:
        raise SystemExit("usage: run-sweep.py M1 [M2 ...] [--n 6,12 --rates 27/125 --p-from N --p-to N --p-step N --dates D --disb-offset-days K]")

    make_scratch()
    base_bin = build("base")
    base = run(base_bin, passthru)
    base_map = dict(cells(l) for l in base.splitlines() if l.strip())
    print("sweep grid: %d shapes" % len(base_map))

    for mid in mids:
        make_scratch()
        name = patch_scratch(mid)
        mut_bin = build(mid)
        mut = run(mut_bin, passthru)
        mut_map = dict(cells(l) for l in mut.splitlines() if l.strip())
        diffs = []
        for k, v in base_map.items():
            mv = mut_map.get(k)
            if mv != v:
                margin = 0
                bad = []
                for i, (a, b) in enumerate(zip(v.split(), (mv or "").split())):
                    if a != b:
                        pa = [int(x) for x in a.split(":")]
                        pb = [int(x) for x in b.split(":")]
                        for j in range(3):
                            if pa[j] != pb[j]:
                                margin = max(margin, abs(pa[j] - pb[j]))
                                bad.append((i, ["principal", "interest", "outstanding"][j], pa[j], pb[j]))
                diffs.append((k, margin, bad))
        diffs.sort(key=lambda t: -t[1])
        print("\n%-4s %-50s separating shapes: %d of %d" % (mid, name, len(diffs), len(base_map)))
        for k, margin, bad in diffs[:8]:
            print("     %s   max margin %d minor" % (k, margin))
            for i, col, a, b in bad[:6]:
                print("        row %-2d %-12s observed-by-true %-14d mutant %d" % (i, col, a, b))
    shutil.rmtree(SCRATCH, ignore_errors=True)


if __name__ == "__main__":
    main()
