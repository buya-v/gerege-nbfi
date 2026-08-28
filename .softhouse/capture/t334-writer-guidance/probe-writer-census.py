#!/usr/bin/env python3
"""T334 - writer census, re-measured from scratch (do not trust T301's table; reproduce it).

QUESTION: which writers can reach a file that another process ALREADY HAS OPEN?
That is the shape that lets an in-place rewrite splice into a RUNNING zsh script,
because zsh does not slurp a script - it returns to the fd for more input.

TWO instruments per writer, not one:
  (1) INODE - stat the target before and after. st_ino changed => the writer built a
      new file and renamed over the name, so a held fd still points at the old bytes
      (ISOLATED).
  (2) FD    - this process holds an open read fd on the ORIGINAL file across the write,
      then lseek(fd,0) + read. If the held fd sees the new bytes, the writer wrote
      THROUGH the original inode (IN PLACE) and could reach a running script.
  Instrument (2) IS the hazard; (1) is the cheap proxy. A leg where they disagree is
  reported as DISAGREE rather than quietly scored.

REFUSAL: every leg asserts the bytes at the PATH actually changed and contain the
mutation marker. A writer that silently no-ops scores NOOP and is never counted as
evidence (T309's first draft passed vacuously; T301 harness defect #3).

Runs unchanged on macOS and Linux - the same file is used for the BSD leg and the
GNU/Linux (container) leg, so the two hosts are compared with one instrument.
"""
import os, shutil, subprocess, tempfile, platform

SEED = b"".join(b"ORIGINAL row %04d ................................\n" % i for i in range(1, 9))
MUT_MARK = b"MUTATED"


def legs():
    """name -> (setup(dir)->env|None, sh command run with cwd=dir against ./target)"""
    L = []

    def plain(name, cmd):
        L.append((name, None, cmd))

    plain("cat > file",               "cat > target <<'E'\nMUTATED body\nE")
    plain("printf > file (truncate)", "printf 'MUTATED body\\n' > target")
    plain(">> append",                "printf 'MUTATED tail\\n' >> target")
    plain("tee file",                 "printf 'MUTATED body\\n' | tee target > /dev/null")
    plain("tee -a file",              "printf 'MUTATED tail\\n' | tee -a target > /dev/null")
    plain("dd conv=notrunc",          "printf 'MUTATED!\\n' | dd of=target conv=notrunc 2>/dev/null")
    plain("cp src dst",               "printf 'MUTATED body\\n' > src; cp src target")
    plain("cp -p src dst",            "printf 'MUTATED body\\n' > src; cp -p src target")
    plain("cat src > dst",            "printf 'MUTATED body\\n' > src; cat src > target")
    plain("mv src dst",               "printf 'MUTATED body\\n' > src; mv src target")
    plain("install -m 755",           "printf 'MUTATED body\\n' > src; install -m 755 src target")
    plain("python open(w)",           "python3 -c \"open('target','w').write('MUTATED body\\n')\"")
    plain("python open(r+)",          "python3 -c \"f=open('target','r+');f.seek(0);f.write('MUTATED');f.close()\"")
    plain("python write+os.replace",  "python3 -c \"open('t.tmp','w').write('MUTATED body\\n');import os;os.replace('t.tmp','target')\"")
    plain("sed -i (in-place flag)",   "sed -i%s 's/ORIGINAL/MUTATED/g' target"
                                      % (" ''" if platform.system() == "Darwin" else ""))
    plain("sed -i.bak",               "sed -i.bak 's/ORIGINAL/MUTATED/g' target")
    plain("sed > tmp; cat tmp > f",   "sed 's/ORIGINAL/MUTATED/g' target > t.tmp && cat t.tmp > target")
    plain("perl -i -pe",              "perl -i -pe 's/ORIGINAL/MUTATED/g' target")
    plain("ex -s",                    "printf '%s\\n' ',s/ORIGINAL/MUTATED/g' 'wq' | ex -s target")
    plain("ed -s",                    "printf '%s\\n' ',s/ORIGINAL/MUTATED/' 'w' 'q' | ed -s target")
    plain("awk > tmp; mv tmp f",      "awk '{gsub(/ORIGINAL/,\"MUTATED\")}1' target > t.tmp && mv t.tmp target")
    plain("patch",                    "sed 's/ORIGINAL/MUTATED/g' target > new.txt; "
                                      "diff -u target new.txt > p.diff || true; patch target < p.diff >/dev/null")
    plain("noclobber-defeating >|",   "printf 'MUTATED body\\n' >| target")

    # ---- git write paths: a repo whose branch `other` carries the mutated bytes
    def gitsetup(d):
        e = dict(os.environ, GIT_AUTHOR_NAME="p", GIT_AUTHOR_EMAIL="p@x",
                 GIT_COMMITTER_NAME="p", GIT_COMMITTER_EMAIL="p@x",
                 GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_SYSTEM="/dev/null")
        subprocess.run(
            ["/bin/sh", "-c",
             "git init -q -b main . && git add target && git commit -qm base && "
             "git checkout -q -b other && sed 's/ORIGINAL/MUTATED/g' target > t && mv t target && "
             "git commit -qam mutated && git checkout -q main"],
            cwd=d, env=e, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return e

    G = "git "
    L.append(("git merge --ff-only",       gitsetup, G + "merge -q --ff-only other"))
    L.append(("git checkout other -- <p>", gitsetup, G + "checkout other -- target"))
    L.append(("git restore -s other <p>",  gitsetup, G + "restore -s other target"))
    L.append(("git reset --hard other",    gitsetup, G + "reset -q --hard other"))
    L.append(("git apply <patch>",         gitsetup, G + "diff HEAD other -- target > p.diff && " + G + "apply p.diff"))
    L.append(("git checkout-index -f -a",  gitsetup, G + "read-tree other && " + G + "checkout-index -f -a"))
    L.append(("git stash pop",             gitsetup,
              "sed 's/ORIGINAL/MUTATED/g' target > t && mv t target && " + G + "stash -q && " + G + "stash pop -q"))
    L.append(("git pull --ff-only",        gitsetup, G + "pull -q --ff-only . other"))
    return L


def main():
    root = tempfile.mkdtemp(prefix="t334-writers.")
    print("HOST      : %s %s (%s)" % (platform.system(), platform.release(), platform.machine()))
    print("uname -a  : %s" % subprocess.run(["uname", "-a"], stdout=subprocess.PIPE).stdout.decode().strip())
    for tool in ("sh", "sed", "cp", "install", "patch", "git", "perl", "ex", "ed", "tee", "dd"):
        p = shutil.which(tool)
        v = ""
        if p and tool == "sed":
            r = subprocess.run([p, "--version"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            v = r.stdout.decode().splitlines()[0] if r.returncode == 0 else "(rejects --version => BSD sed)"
        elif p and tool == "git":
            v = subprocess.run([p, "--version"], stdout=subprocess.PIPE).stdout.decode().strip()
        print("  %-8s %-20s %s" % (tool, p or "MISSING", v))
    print("SELECTOR  : os.stat(path).st_ino before/after  AND  held read fd -> os.lseek(fd,0)+os.read")
    print("WORKDIR   : %s" % root)
    print()
    hdr = "%-30s %-12s %-12s %-8s %-11s %s" % (
        "WRITER", "INODE_BEFORE", "INODE_AFTER", "CHANGED", "FD_SEES_NEW", "VERDICT")
    print(hdr)
    print("-" * len(hdr))
    rows = []
    for name, setup, cmd in legs():
        d = tempfile.mkdtemp(prefix="leg.", dir=root)
        tgt = os.path.join(d, "target")
        with open(tgt, "wb") as f:
            f.write(SEED)
        env = setup(d) if setup else None
        before_ino = os.stat(tgt).st_ino
        fd = os.open(tgt, os.O_RDONLY)                       # the held fd: the hazard's own shape
        r = subprocess.run(["/bin/sh", "-c", cmd], cwd=d, env=env or os.environ,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        try:
            after_ino = os.stat(tgt).st_ino
            after_bytes = open(tgt, "rb").read()
        except FileNotFoundError:
            after_ino, after_bytes = -1, b""
        os.lseek(fd, 0, 0)
        fd_bytes = os.read(fd, 1 << 16)
        os.close(fd)
        changed = (after_bytes != SEED) and (MUT_MARK in after_bytes)
        fd_sees = (MUT_MARK in fd_bytes)
        # rc!=0 is UNSCORABLE even when the bytes changed: a multi-step leg can mutate the
        # file in its SETUP and then have the writer under test fail, which scores the setup
        # (found the hard way -- the `git stash pop` leg scored ISOLATED on a host with no
        # git, because its `sed >t && mv t target` prologue had already renamed).
        if r.returncode != 0:
            verdict = "ERROR rc=%d %s" % (r.returncode, r.stdout.decode()[:50].replace("\n", " "))
        elif not changed:
            verdict = "NOOP (leg proves nothing)"
        elif fd_sees and before_ino == after_ino:
            verdict = "IN PLACE  <-- CAN REACH A RUNNING SCRIPT"
        elif (not fd_sees) and before_ino != after_ino:
            verdict = "ISOLATED (rename)"
        else:
            verdict = "DISAGREE same_inode=%s fd_sees=%s" % (before_ino == after_ino, fd_sees)
        rows.append((name, verdict))
        print("%-30s %-12d %-12d %-8s %-11s %s" % (
            name, before_ino, after_ino, "yes" if changed else "NO",
            "YES" if fd_sees else "no", verdict))
    print()
    print("IN PLACE (dangerous): " + ", ".join(n for n, v in rows if v.startswith("IN PLACE")))
    print("ISOLATED (safe)     : " + ", ".join(n for n, v in rows if v.startswith("ISOLATED")))
    bad = [(n, v) for n, v in rows if not (v.startswith("IN PLACE") or v.startswith("ISOLATED"))]
    print("UNSCORED            : " + (", ".join("%s [%s]" % (n, v) for n, v in bad) if bad else "(none)"))
    print("legs=%d in_place=%d isolated=%d unscored=%d" % (
        len(rows), sum(v.startswith("IN PLACE") for _, v in rows),
        sum(v.startswith("ISOLATED") for _, v in rows), len(bad)))
    print("DONE")


main()
