#!/usr/bin/env python3
"""T211 spawner -- launchd-faithful.

Reproduces the launchd invocation shape EXACTLY:

    <key>ProgramArguments</key> = [ /bin/zsh, -lc, <script path> ]

...in its OWN SESSION (setsid) with DEFAULT signal dispositions.

The default-disposition point is NOT optional.  T202 recorded P-55 against its
own first probe: it backgrounded the subject from a NON-job-control zsh, POSIX
makes such a child SIG_IGN INT/QUIT, and the probe therefore "measured" that
zsh ignores SIGINT.  That was an artefact of the harness, not a property of
zsh.  subprocess's restore_signals=True (the default) resets SIGPIPE/SIGXFZ/
SIGXFSZ/SIGINT/SIGQUIT to SIG_DFL in the child after fork, and
start_new_session=True does setsid() -- together, the dispositions launchd
gives the job.

usage: spawn.py <subject.zsh> <SIGNAL|none> <label> [ready-token] [delay] [timeout]
"""
import functools
import os
import signal
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))

subject, signame, label = sys.argv[1:4]
ready_tok = sys.argv[4] if len(sys.argv) > 4 else "READY"
delay = float(sys.argv[5]) if len(sys.argv) > 5 else 0.5
timeout = float(sys.argv[6]) if len(sys.argv) > 6 else 45.0

out = os.path.join(HERE, "out-%s.txt" % label)
if not os.path.isabs(subject):
    subject = os.path.join(HERE, subject)

print = functools.partial(print, flush=True)
print("# spawner  : /bin/zsh -lc %s   (the launchd ProgramArguments shape)" % subject)
print("# session  : start_new_session=True (setsid)")
print("# disposit.: restore_signals=True -- INT/QUIT/PIPE reset to SIG_DFL in the child")
print("#            (this is the P-55 control: without it the probe measures itself)")

with open(out, "wb") as fh:
    p = subprocess.Popen(
        ["/bin/zsh", "-lc", subject],
        stdout=fh, stderr=subprocess.STDOUT,
        start_new_session=True, restore_signals=True,
    )
    t_ready = None
    for _ in range(600):
        try:
            if ready_tok.encode() in open(out, "rb").read():
                t_ready = time.time()
                break
        except FileNotFoundError:
            pass
        time.sleep(0.05)
    if t_ready is None:
        print("!!! subject never printed %r within 30s" % ready_tok)

    if signame != "none":
        time.sleep(delay)
        sig = getattr(signal, "SIG" + signame)
        try:
            sid = os.getsid(p.pid)
        except Exception:
            sid = "?"
        t_sig = time.time()
        print("--- t=0.000  epoch=%.6f  sending SIG%s to pid %d "
              "(sid=%s, own session, default dispositions) ---"
              % (t_sig, signame, p.pid, sid))
        os.kill(p.pid, sig)
    else:
        t_sig = time.time()
        print("--- no signal sent (control run) ---")

    deadline = t_sig + timeout
    while p.poll() is None and time.time() < deadline:
        time.sleep(0.02)
    strand = p.poll() is None
    if strand:
        print("!!! t=%7.3f  subject STILL ALIVE %.0fs after the signal -- "
              "the harness SIGKILLs it now" % (time.time() - t_sig, timeout))
        os.kill(p.pid, signal.SIGKILL)
    rc = p.wait()
    t_end = time.time()

print("EXIT LATENCY (signal -> wrapper exit) = %.3fs%s"
      % (t_end - t_sig, "   <-- DEFERRED/HUNG, harness had to SIGKILL" if strand else ""))
if rc < 0:
    print("subject rc = %d   (python reports -N for death by signal N -> signal %d)" % (rc, -rc))
elif rc > 128:
    print("subject rc = %d   (128+%d)" % (rc, rc - 128))
else:
    print("subject rc = %d" % rc)
print("transcript = %s" % out)
print("--- subject transcript " + "-" * 50)
sys.stdout.write(open(out, encoding="utf-8", errors="replace").read())
print("--- end transcript " + "-" * 53)
