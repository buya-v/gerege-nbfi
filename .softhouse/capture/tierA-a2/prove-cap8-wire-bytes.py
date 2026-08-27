#!/usr/bin/env python3
"""T163 — drive the "nothing records what was SENT" defect RED, and prove cap8.sh closes it.

  python3 prove-cap8-wire-bytes.py

THE DEFECT, AND WHY IT IS THE DURABLE HALF OF T163
---------------------------------------------------
A2-11 found resolve7.py reshaping money literals in the body POSTed to the reference
oracle.  Fixing that one script does not stop the next one.  What let it survive
undetected is that THE CORPUS HAS NO RECORD OF THE BYTES THAT WENT OVER THE WIRE:
cap.sh's `.http` writes `body-file: req/foo.json`, a POINTER.  A reviewer can diff what
came BACK; nobody can diff what was SENT.

And the pointer is not even accurate.  `curl -d @FILE` STRIPS carriage returns and
newlines out of a file body, so cap.sh's wire bytes are provably NOT the file's bytes.
That is measured below against a real HTTP server, not quoted from the man page.

HOW THIS IS MEASURED WITHOUT TOUCHING THE REFERENCE ORACLE
-----------------------------------------------------------
A local HTTP server on 127.0.0.1 records the EXACT request body bytes it receives.  Both
scripts are run against it from a sandbox with their own env.sh.  Nothing here contacts
the reference oracle, and nothing under the committed out/ is written.

A POSITIVE CONTROL IS INCLUDED (P-36).  Before any conclusion is drawn, the apparatus is
shown to be capable of observing a difference at all: a body with an interior newline is
sent and the server's record is shown to differ between the two flags.  If the positive
control were flat, every other row here would be a null control and would mean nothing.

GUARD SHAPE (P-35): assertions are POSITIVE and counted; the run fails unless cap.sh goes
RED and cap8.sh goes GREEN on the same battery.
"""
import hashlib
import http.server
import os
import shutil
import subprocess
import sys
import tempfile
import threading

RIG = os.path.dirname(os.path.abspath(__file__))
FAILS = []
RECEIVED = {}


def check(label, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + label + (("\n          " + detail) if detail else ""))
    if not cond:
        FAILS.append(label)
    return bool(cond)


class Recorder(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        RECEIVED[self.path] = self.rfile.read(n)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"observed":true}')

    do_PUT = do_POST

    def do_GET(self):
        RECEIVED[self.path] = b""
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"observed":true}')

    def log_message(self, *a):
        pass


srv = http.server.HTTPServer(("127.0.0.1", 0), Recorder)
PORT = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()

d = tempfile.mkdtemp(prefix="t163-wire-")
os.makedirs(os.path.join(d, "out"))
os.makedirs(os.path.join(d, "req"))
for s in ("cap.sh", "cap8.sh"):
    shutil.copy(os.path.join(RIG, s), d)
with open(os.path.join(d, "env.sh"), "w") as fh:
    fh.write("B=http://127.0.0.1:%d\n"
             "A='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='\n"
             "T='Fineract-Platform-TenantId: gerege'\n"
             "CT='Content-Type: application/json'\n"
             "export B A T CT\n" % PORT)


def send(script, name, body_bytes):
    rel = "req/%s.json" % name
    with open(os.path.join(d, rel), "wb") as fh:
        fh.write(body_bytes)
    path = "/%s" % name
    r = subprocess.run(["sh", os.path.join(d, script), name, "POST", path, rel],
                       capture_output=True, text=True, cwd=d)
    return r, RECEIVED.get(path)


print("=" * 78)
print("T163 — what actually goes over the wire, measured against a recording HTTP server")
print("=" * 78)
print("  recording server: http://127.0.0.1:%d   sandbox: %s" % (PORT, d))
print()

# ------------------------------------------------------------------ positive control
print("POSITIVE CONTROL (P-36) — can this apparatus observe a wire difference at all?")
multiline = b'{\n  "principal": 1200000.00,\n  "note": "two lines"\n}\n'
r_old, got_old = send("cap.sh", "CTRL-old", multiline)
r_new, got_new = send("cap8.sh", "CTRL-new", multiline)
print("  file bytes            : %r" % multiline)
print("  cap.sh  put on wire   : %r" % got_old)
print("  cap8.sh put on wire   : %r" % got_new)
check("the apparatus DISCRIMINATES — the two flags put different bytes on the wire, so a "
      "flat result below would be a real result and not a broken rig",
      got_old is not None and got_new is not None and got_old != got_new,
      "cap.sh sent %d byte(s), cap8.sh sent %d byte(s)"
      % (len(got_old or b""), len(got_new or b"")))
print()

# ------------------------------------------------------------------ RED: cap.sh
print("RED — cap.sh, UNCHANGED by T163")
check("RED: cap.sh's wire bytes are NOT the body file's bytes  (`curl -d @FILE` strips "
      "carriage returns and newlines — measured here, not quoted)",
      got_old != multiline,
      "file sha256 %s != wire sha256 %s"
      % (hashlib.sha256(multiline).hexdigest(), hashlib.sha256(got_old or b"").hexdigest()))
old_http = open(os.path.join(d, "out", "CTRL-old.http")).read()
print("  cap.sh's request record, in full:")
for line in old_http.rstrip("\n").split("\n"):
    print("      " + line)
check("RED: cap.sh writes NO artefact of the wire bytes — out/NAME.req does not exist",
      not os.path.exists(os.path.join(d, "out", "CTRL-old.req")),
      "out/ after cap.sh: %s"
      % sorted(f for f in os.listdir(os.path.join(d, "out")) if f.startswith("CTRL-old")))
check("RED: cap.sh's record carries only a POINTER (`body-file:`) and no digest, so a "
      "later rewrite of req/ is undetectable from the capture",
      "body-file:" in old_http and "body-sha256:" not in old_http,
      "body-file present=%s, body-sha256 present=%s"
      % ("body-file:" in old_http, "body-sha256:" in old_http))
print()

# ------------------------------------------------------------------ GREEN: cap8.sh
print("GREEN — cap8.sh")
new_http = open(os.path.join(d, "out", "CTRL-new.http")).read()
print("  cap8.sh's request record, in full:")
for line in new_http.rstrip("\n").split("\n"):
    print("      " + line)
req_path = os.path.join(d, "out", "CTRL-new.req")
check("cap8.sh writes out/NAME.req", os.path.exists(req_path))
artefact = open(req_path, "rb").read() if os.path.exists(req_path) else None
check("GREEN: out/NAME.req IS BYTE-FOR-BYTE WHAT THE SERVER RECEIVED — the artefact is "
      "the wire, not a pointer at a file that may drift",
      artefact is not None and artefact == got_new,
      "artefact sha256 %s ; received sha256 %s"
      % (hashlib.sha256(artefact or b"").hexdigest(), hashlib.sha256(got_new or b"").hexdigest()))
check("GREEN: and the wire equals the BODY FILE too — `--data-binary` sends the file "
      "verbatim, so all three (file, artefact, wire) are one set of bytes",
      got_new == multiline,
      "file sha256 %s ; wire sha256 %s"
      % (hashlib.sha256(multiline).hexdigest(), hashlib.sha256(got_new or b"").hexdigest()))
sha_file = os.path.join(d, "out", "CTRL-new.req.sha256")
check("cap8.sh writes out/NAME.req.sha256 and it matches the artefact",
      os.path.exists(sha_file)
      and open(sha_file).read().split()[0] == hashlib.sha256(artefact or b"").hexdigest(),
      open(sha_file).read().strip() if os.path.exists(sha_file) else "absent")
check("cap8.sh's .http record carries the digest and the byte count, so the three "
      "artefacts cross-check each other",
      ("body-sha256: " + hashlib.sha256(artefact or b"").hexdigest()) in new_http
      and ("body-bytes: %d" % len(artefact or b"")) in new_http,
      "expected body-sha256 %s and body-bytes %d"
      % (hashlib.sha256(artefact or b"").hexdigest(), len(artefact or b"")))
print()

# --------------------------------------------- the money case, end to end through resolve8
print("END TO END — resolve8.py -> cap8.sh, on a money literal that really occurs in the "
      "corpus")
tmpl = os.path.join(d, "req", "tmpl.json")
obs = os.path.join(d, "req", "obs.json")
resolved = os.path.join(d, "req", "resolved.json")
with open(tmpl, "w") as fh:
    fh.write('{\n  "productId": "__PRODUCT_ID__",\n  "principal": 1200000.00,\n'
             '  "fee": 1200000.000000\n}\n')
with open(obs, "w") as fh:
    fh.write('{"resourceId": 46}\n')
rr = subprocess.run([sys.executable, os.path.join(RIG, "resolve8.py"), tmpl, obs,
                     "resourceId", resolved], capture_output=True, text=True, cwd=d)
check("resolve8.py resolved the template", rr.returncode == 0, rr.stderr.strip())
r3, got3 = send("cap8.sh", "E2E", open(resolved, "rb").read())
print("  bytes on the wire: %r" % got3)
check("END TO END: `1200000.00` and `1200000.000000` reach the wire EXACTLY as written, "
      "and the wire is committed as out/E2E.req",
      got3 is not None and b'"principal": 1200000.00,' in got3
      and b'"fee": 1200000.000000' in got3
      and open(os.path.join(d, "out", "E2E.req"), "rb").read() == got3,
      "wire sha256 %s" % hashlib.sha256(got3 or b"").hexdigest())

# --------------------------------------------- A2-5's D-2 fixes survived the copy
print()
print("A2-5's D-2 TRANSPORT FIXES, RE-PROVEN AGAINST cap8.sh RATHER THAN ASSUMED")
with open(os.path.join(d, "env-dead.sh"), "w") as fh:
    fh.write("B=http://127.0.0.1:1\nA='X: 1'\nT='Y: 1'\nCT='Z: 1'\nexport B A T CT\n")
dead = os.path.join(d, "dead")
os.makedirs(os.path.join(dead, "out"))
os.makedirs(os.path.join(dead, "req"))
shutil.copy(os.path.join(RIG, "cap8.sh"), dead)
shutil.copy(os.path.join(d, "env-dead.sh"), os.path.join(dead, "env.sh"))
with open(os.path.join(dead, "req", "b.json"), "w") as fh:
    fh.write('{"principal": 1200000.00}\n')
for stale in ("D.json", "D.status", "D.http", "D.req", "D.req.sha256"):
    with open(os.path.join(dead, "out", stale), "w") as fh:
        fh.write("STALE FROM AN EARLIER FIRE\n")
before = {f: open(os.path.join(dead, "out", f), "rb").read() for f in os.listdir(os.path.join(dead, "out"))}
rd = subprocess.run(["sh", os.path.join(dead, "cap8.sh"), "D", "POST", "/x", "req/b.json"],
                    capture_output=True, text=True, cwd=dead)
after = {f: open(os.path.join(dead, "out", f), "rb").read() for f in os.listdir(os.path.join(dead, "out"))}
check("a TRANSPORT FAILURE exits non-zero", rd.returncode != 0, "rc=%d" % rd.returncode)
check("a TRANSPORT FAILURE writes NOTHING under out/ — including the new .req and "
      ".req.sha256, so a failed fire cannot leave a fresh-looking wire artefact",
      before == after,
      "%d file(s) before, %d after, %d changed"
      % (len(before), len(after), sum(1 for k in after if before.get(k) != after[k])))
check("the handler NAMES every pre-existing artefact it left intact, .req included",
      all(("out/D." + ext) in rd.stderr for ext in ("json", "status", "http", "req")),
      rd.stderr.strip().replace("\n", " | ")[:300])

# --------------------------------------------- refusal on a missing body file
rm = subprocess.run(["sh", os.path.join(d, "cap8.sh"), "MISS", "POST", "/m", "req/nope.json"],
                    capture_output=True, text=True, cwd=d)
check("cap8.sh REFUSES a missing body file rather than sending an empty body — a wire "
      "artefact of a body that did not exist would be the worst possible artefact",
      rm.returncode != 0 and not os.path.exists(os.path.join(d, "out", "MISS.json")),
      "rc=%d, stderr=%s" % (rm.returncode, rm.stderr.strip()))

srv.shutdown()
shutil.rmtree(d)
print()
print("FAILURES: %d" % len(FAILS))
for f in FAILS:
    print("  - " + f)
sys.exit(1 if FAILS else 0)
