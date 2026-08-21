#!/usr/bin/env python3
# T158 independent re-derivation of the bash semantics T156 claims:
#   "bash defers a trapped signal until the current FOREGROUND child finishes"
# and that `wait <pid>` yields the child's status.
import os, signal, subprocess, sys, time

def run(script, sig=signal.SIGINT, delay=1.0, timeout=20, wait_child=True):
    t0 = time.time()
    p = subprocess.Popen(["bash", script], start_new_session=True,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    time.sleep(delay)
    os.kill(p.pid, sig)           # to the SCRIPT ONLY, never the process group
    try:
        out = p.communicate(timeout=timeout)[0]
        rc = p.returncode
    except subprocess.TimeoutExpired:
        os.killpg(os.getpgid(p.pid), signal.SIGKILL)
        out = p.communicate()[0]; rc = "TIMEOUT"
    return rc, round(time.time() - t0, 2), out

for name in ("fg.sh", "bg.sh"):
    rc, el, out = run("/tmp/t158-bash/" + name)
    print("=== %s : SIGINT to the script pid only, 1.0 s in" % name)
    print("    exit=%s  elapsed=%ss" % (rc, el))
    for l in out.splitlines():
        print("    | " + l)
    print()

# control: no signal at all -- does `wait` really yield the child's status?
print("=== `wait` status fidelity control (no signal)")
for name in ("fg.sh", "bg.sh"):
    p = subprocess.Popen(["bash", "-c",
        'trap "exit 130" INT; ' +
        ('python3 -c "import sys;sys.exit(3)"; rc=$?' if name == "fg.sh"
         else 'python3 -c "import sys;sys.exit(3)" & P=$!; wait "$P"; rc=$?') +
        '; echo "rc=$rc"'],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    print("    %-7s %s" % (name, p.communicate()[0].strip()))
