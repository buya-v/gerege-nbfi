#!/usr/bin/env python3
"""T217 -- launchd-faithful spawn of push-subject.zsh with a hard wall-clock
CEILING (own session, default dispositions -- same P-55 control as T211's
spawn.py). If the subject is still alive at the ceiling, that IS the red
result (a hang), and the harness reaps the whole session so a killed fake-git
`sleep` cannot leak into the next case.

usage: spawn-push.py <subject.zsh> <label> <ceiling_secs>
"""
import os
import signal
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
subject, label, ceiling = sys.argv[1], sys.argv[2], float(sys.argv[3])
out = os.path.join(HERE, "out-%s.txt" % label)

print("# spawner  : /bin/zsh -lc %s   (the launchd ProgramArguments shape)" % subject)
print("# session  : start_new_session=True (setsid)")
print("# ceiling  : %.1fs" % ceiling)

t0 = time.time()
with open(out, "wb") as fh:
    p = subprocess.Popen(
        ["/bin/zsh", "-lc", subject],
        stdout=fh, stderr=subprocess.STDOUT,
        start_new_session=True, restore_signals=True,
    )
    while p.poll() is None and time.time() - t0 < ceiling:
        time.sleep(0.02)
    hung = p.poll() is None
    if hung:
        print("!!! t=%7.3f  subject STILL ALIVE %.0fs after start -- HUNG, harness "
              "is reaping the whole session now" % (time.time() - t0, ceiling))
        try:
            os.killpg(os.getsid(p.pid), signal.SIGKILL)
        except Exception as e:
            print("!!! killpg failed: %r -- falling back to killing just the top pid" % e)
            p.kill()
        p.wait()
    else:
        p.wait()
t1 = time.time()

print("WALL TIME (start -> subject exit or forced reap) = %.3fs%s"
      % (t1 - t0, "   <-- HUNG past ceiling" if hung else ""))
print("subject rc = %s" % p.returncode)
print("transcript = %s" % out)
print("--- subject transcript " + "-" * 50)
sys.stdout.write(open(out, encoding="utf-8", errors="replace").read())
print("--- end transcript " + "-" * 53)
