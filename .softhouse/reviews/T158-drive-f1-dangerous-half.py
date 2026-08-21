#!/usr/bin/env python3
# T158 — F-1, the DANGEROUS half: interrupt AFTER the pre-fix attest.py has already
# mutated the committed evidence set, i.e. after :49 and before :65/:67.
import os, signal, subprocess, sys, time
clone = "/tmp/t158-clone"
E = os.path.join(clone, ".softhouse/capture/pathb/t36/out/emiloop")
STAMP = os.path.join(E, "CAPTURED-FROM-TENANT")
p = subprocess.Popen(["bash", ".softhouse/capture/pathb/t80/prove-f1.sh"], cwd=clone,
                     start_new_session=True, stdout=subprocess.PIPE,
                     stderr=subprocess.STDOUT, text=True)
caught = False
t0 = time.time()
while time.time() - t0 < 120 and p.poll() is None:
    if os.path.exists(STAMP):
        os.killpg(os.getpgid(p.pid), signal.SIGKILL)
        caught = True
        break
    time.sleep(0.002)
out = p.communicate()[0]
print("caught the post-attest window:", caught, " script exit:", p.returncode)
st = subprocess.run(["git", "-C", clone, "status", "--porcelain"],
                    capture_output=True, text=True).stdout.strip()
print("--- git status after the interruption ---")
print(st if st else "(clean)")
print("--- committed-evidence paths left MODIFIED under t36/out/emiloop ---")
print("\n".join(l for l in st.splitlines() if "emiloop" in l) or "(none)")
