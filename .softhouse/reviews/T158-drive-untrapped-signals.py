#!/usr/bin/env python3
# T158 — the interruption classes T156 did NOT drive: SIGQUIT and SIGPIPE.
# bash runs an EXIT trap on `exit`, on normal end, and on a signal it TRAPS.  For an
# untrapped fatal signal it dies without running the EXIT handler.  T156 traps INT, TERM
# and HUP only.  So: does an untrapped-but-catchable fatal signal strand the store, and
# does the start-up recovery catch it on the next run?
import os, shutil, signal, subprocess, sys, tempfile, time

REPO = "/tmp/t158-clone"
VEC_REL = ".softhouse/vectors/loanschedule/T149-PATHB-TIE-1M162502pt50-12x21pt6pct.json"
T149 = ".softhouse/capture/pathb/t149"
SCRIPT = T149 + "/prove-redgreen.sh"

STUB = '''#!/usr/bin/env python3
import os, signal, sys, time
os.kill(os.getppid(), getattr(signal, os.environ["T158_SIG"]))
time.sleep(30)
'''
CONF = "#!/bin/bash\nexit 0\n"


def build():
    sb = tempfile.mkdtemp(prefix="t158-sq.")
    os.makedirs(os.path.join(sb, T149))
    os.makedirs(os.path.join(sb, ".softhouse", "handoff"))
    shutil.copytree(os.path.join(REPO, ".softhouse", "vectors"),
                    os.path.join(sb, ".softhouse", "vectors"))
    shutil.copyfile(os.path.join(REPO, SCRIPT), os.path.join(sb, SCRIPT))
    open(os.path.join(sb, ".softhouse", "handoff", "T61-mutations.py"), "w").write(STUB)
    open(os.path.join(sb, ".softhouse", "conformance.sh"), "w").write(CONF)
    return sb


for signame in ("SIGQUIT", "SIGPIPE", "SIGUSR1", "SIGALRM"):
    sb = build()
    env = dict(os.environ, T158_SIG=signame)
    p = subprocess.Popen(["bash", os.path.join(sb, SCRIPT)], cwd=sb, env=env,
                         start_new_session=True, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True)
    try:
        out = p.communicate(timeout=20)[0]
        rc = p.returncode
    except subprocess.TimeoutExpired:
        os.killpg(os.getpgid(p.pid), 9); out, rc = p.communicate()[0], "TIMEOUT"
    vec = os.path.exists(os.path.join(sb, VEC_REL))
    park = os.path.exists(os.path.join(sb, T149, ".parked-vector.json"))
    print("%-8s script exit=%-8s vector-in-store=%-5s park-left=%-5s restored-msg=%s"
          % (signame, rc, vec, park, "store restored" in out))
    if not vec:
        # the next run's start-up recovery is the only thing that can save this
        p2 = subprocess.Popen(["bash", os.path.join(sb, SCRIPT)], cwd=sb,
                              env=dict(os.environ, T158_SIG="SIGTERM"),
                              start_new_session=True, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, text=True)
        try:
            out2 = p2.communicate(timeout=20)[0]
        except subprocess.TimeoutExpired:
            os.killpg(os.getpgid(p2.pid), 9); out2 = p2.communicate()[0]
        print("         -> next run: RECOVERED=%s   vector back=%s"
              % ("RECOVERED:" in out2, os.path.exists(os.path.join(sb, VEC_REL))))
    shutil.rmtree(sb, ignore_errors=True)
