#!/bin/zsh
# T349 -- what does the guard COST? Three separate numbers, all measured, none estimated.
#
#  (1) bare hook process cost: python3 startup + stdin parse + log write, no network.
#  (2) the network call the guard needs: `git ls-remote origin refs/heads/main`
#      against the REAL origin (git@github.com:buya-v/gerege-nbfi.git), 10 samples.
#  (3) the same against an unroutable host, to bound the worst case.
set -u
CAP=${T349_CAP:?capture dir}
REALREPO=${T349_REALREPO:-/Users/buv/gerege-nbfi}
HOOK=$CAP/probe/pretooluse-probe.py
export T349_LOG="${TMPDIR:-/tmp}/t349-cost.log"
export T349_MODE=log
rm -f $T349_LOG

PAY='{"session_id":"cost","hook_event_name":"PreToolUse","tool_name":"Agent","tool_input":{"description":"x"},"cwd":"/tmp"}'

print -r -- "(1) bare hook process, no network -- 20 samples, ms"
/usr/bin/python3 - "$HOOK" <<'PY'
import json,subprocess,sys,time,os
hook=sys.argv[1]
pay=b'{"session_id":"cost","hook_event_name":"PreToolUse","tool_name":"Agent","tool_input":{"description":"x"},"cwd":"/tmp"}'
env=dict(os.environ); env["T349_MODE"]="log"
xs=[]
for i in range(20):
    t=time.time()
    subprocess.run(["/usr/bin/python3",hook],input=pay,capture_output=True,env=env)
    xs.append((time.time()-t)*1000)
xs.sort()
print("    min=%.1f  median=%.1f  p90=%.1f  max=%.1f" % (xs[0],xs[len(xs)//2],xs[int(len(xs)*0.9)],xs[-1]))
PY

print -r -- ""
print -r -- "(2) git ls-remote against the REAL origin of $REALREPO -- 10 samples, ms"
git -C "$REALREPO" remote get-url origin
/usr/bin/python3 - "$REALREPO" <<'PY'
import subprocess,sys,time
repo=sys.argv[1]
xs=[]
for i in range(10):
    t=time.time()
    p=subprocess.run(["git","-C",repo,"ls-remote","origin","refs/heads/main"],capture_output=True,text=True)
    dt=(time.time()-t)*1000
    xs.append(dt)
    if i==0: print("    first sample rc=%d out=%r" % (p.returncode,p.stdout.strip()[:60]))
xs.sort()
print("    min=%.0f  median=%.0f  p90=%.0f  max=%.0f" % (xs[0],xs[len(xs)//2],xs[int(len(xs)*0.9)],xs[-1]))
PY

print -r -- ""
print -r -- "(3) git ls-remote against an UNROUTABLE host (TEST-NET-1 192.0.2.1) -- 1 sample, no client timeout"
/usr/bin/python3 - <<'PY'
import subprocess,time,tempfile,os
d=tempfile.mkdtemp()
subprocess.run(["git","init","-q",d])
subprocess.run(["git","-C",d,"remote","add","origin","ssh://git@192.0.2.1:22/x.git"])
t=time.time()
try:
    p=subprocess.run(["git","-C",d,"ls-remote","origin","refs/heads/main"],capture_output=True,text=True,timeout=90)
    rc,err=p.returncode,p.stderr.strip()[:120]
except subprocess.TimeoutExpired:
    rc,err=-9,"still hanging at 90s"
print("    elapsed=%.1fs rc=%s err=%s" % (time.time()-t,rc,err))
PY
