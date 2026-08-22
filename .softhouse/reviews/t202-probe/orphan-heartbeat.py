import os, signal, subprocess, sys, time
# Decisive orphan test, immune to ps/pgid filtering and ambient reaping:
# the driver stand-in APPENDS A HEARTBEAT every 0.2s.  If the file keeps
# growing after the wrapper has exited, the "driver" outlived the wrapper --
# i.e. an orchestrator is still running with the lock already released.
mode = sys.argv[1]          # plain | group
hb = f"/tmp/t202/heartbeat-{mode}.txt"
if os.path.exists(hb): os.remove(hb)
if mode == "plain":
    handler = 'on_sig() { print -r -- HANDLER; exit 143 }'
else:
    handler = 'on_sig() { print -r -- HANDLER; trap "" INT TERM HUP QUIT; kill -TERM 0 2>/dev/null; exit 143 }'
SCRIPT = f'''
set -uo pipefail
{handler}
trap "on_sig" TERM
print -r -- READY
/bin/zsh -c 'for i in {{1..100}}; do print -r -- "beat $i" >> {hb}; /bin/sleep 0.2; done'
print -r -- END
'''
out = f"/tmp/t202/orphan-{mode}.txt"
with open(out, "wb") as fh:
    p = subprocess.Popen(["/bin/zsh", "-c", SCRIPT], stdout=fh,
                         stderr=subprocess.STDOUT, start_new_session=True)
    time.sleep(1.0)
    os.kill(p.pid, signal.SIGTERM)
    rc = p.wait()
n1 = sum(1 for _ in open(hb)) if os.path.exists(hb) else 0
time.sleep(3.0)
n2 = sum(1 for _ in open(hb)) if os.path.exists(hb) else 0
print(f"mode={mode}  wrapper rc={rc}  wrapper transcript={open(out).read().strip()!r}")
print(f"  heartbeats at wrapper-exit: {n1}   3s later: {n2}")
print("  VERDICT:", "DRIVER OUTLIVED THE WRAPPER (still beating)" if n2 > n1
      else "driver died with the wrapper")
