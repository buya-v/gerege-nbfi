#!/usr/bin/env python3
"""T202 -- signal-disposition driver that spawns the subject the way launchd
does: exec'd directly, in its OWN session, with DEFAULT signal dispositions
(restore_signals=True is subprocess's default; start_new_session=True does
setsid).  This avoids the POSIX background-job rule that made my first zsh
driver set SIGINT/SIGQUIT to SIG_IGN in the child and report, wrongly, that
zsh ignores them.

usage: tc-spawn.py <subject.zsh> <REPO> <SIGNAL> <label>
"""
import os, signal, subprocess, sys, time

subject, repo, signame, label = sys.argv[1:5]
out = f"/tmp/t202/spawn-{label}-{signame}.txt"
sig = getattr(signal, "SIG" + signame)
lock = os.path.join(repo, ".softhouse", "LOCK")

with open(out, "wb") as fh:
    p = subprocess.Popen(["/bin/zsh", subject, repo], stdout=fh,
                         stderr=subprocess.STDOUT, start_new_session=True)
    # wait for READY
    for _ in range(200):
        try:
            if b"READY" in open(out, "rb").read():
                break
        except FileNotFoundError:
            pass
        time.sleep(0.05)
    time.sleep(0.5)
    print(f"--- sending SIG{signame} to pid {p.pid} (own session, default dispositions) ---")
    os.kill(p.pid, sig)
    t0 = time.time()
    while p.poll() is None and time.time() - t0 < 20:
        time.sleep(0.1)
    if p.poll() is None:
        print("!!! subject STILL ALIVE 20s after the signal — killing it")
        os.kill(p.pid, signal.SIGKILL)
    rc = p.wait()

body = open(out, encoding="utf-8", errors="replace").read()
lines = body.splitlines()
seen_release = False
ticks_after = 0
for l in lines:
    if "lock released" in l or "lock already released" in l:
        seen_release = True
    elif seen_release and l.startswith("TICK"):
        ticks_after += 1
print(f"subject rc                = {rc}"
      + ("  (128+%d, killed by signal %d)" % (rc - 128, rc - 128) if rc > 128 else ""))
print(f"LOCK after                = {'PRESENT-STRANDED' if os.path.exists(lock) else 'absent'}")
print(f"release_lock ran          = {'YES' if seen_release else 'NO'}")
print(f"TICKS AFTER RELEASE       = {ticks_after}   <-- work done while holding NO lock")
print(f"reached BODY COMPLETED    = {'YES' if 'BODY COMPLETED NORMALLY' in body else 'no'}")
print(f"transcript                = {out}")
