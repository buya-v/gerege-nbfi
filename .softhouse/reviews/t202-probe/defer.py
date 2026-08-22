import os, signal, subprocess, time
# Does zsh run a signal trap IMMEDIATELY, or defer it until the current
# FOREGROUND child exits?  The fire's foreground child is `claude`, which runs
# for HOURS -- so the answer decides what a signal can and cannot achieve.
for child_secs in (0.2, 6):
    SCRIPT = f'''
set -uo pipefail
on_sig() {{ print -r -- "HANDLER at $(date +%s.%N)"; exit 143 }}
trap "on_sig" TERM
print -r -- "READY at $(date +%s.%N)"
/bin/sleep {child_secs}
print -r -- "CHILD DONE at $(date +%s.%N)"
/bin/sleep 30
'''
    out = f"/tmp/t202/defer-{child_secs}.txt"
    with open(out, "wb") as fh:
        p = subprocess.Popen(["/bin/zsh", "-c", SCRIPT], stdout=fh,
                             stderr=subprocess.STDOUT, start_new_session=True)
        time.sleep(0.6)
        t_sig = time.time()
        os.kill(p.pid, signal.SIGTERM)
        rc = p.wait()
        t_end = time.time()
    body = open(out).read()
    handler_t = [l for l in body.splitlines() if l.startswith("HANDLER")]
    print(f"foreground child = sleep {child_secs}s;  signal sent 0.6s in")
    print(f"  wrapper rc={rc}  wall time from signal to wrapper exit = {t_end - t_sig:.2f}s")
    print(f"  {body.strip()}".replace("\n", "\n  "))
    print()
