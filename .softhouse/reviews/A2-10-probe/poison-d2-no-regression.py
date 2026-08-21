#!/usr/bin/env python3
"""A2-10 D-2 round 3: (1) clean-slate failure writes nothing; (2) the SUCCESS path is
not regressed - a fix that breaks capture is as bad as the defect.

Compares pre-fix and post-fix cap.sh against a real local HTTP server for:
  - 200 with a JSON body           (the normal observation)
  - 400 refusal with a body        (in slice A2 a refusal IS the observation: exit 0)
  - empty body / large body        (byte fidelity)
"""
import os, re, shutil, socket, subprocess, sys, tempfile, threading, http.server

PRE, POST = sys.argv[1], sys.argv[2]


class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def _go(self):
        p = self.path
        if p.endswith("/refuse"):
            code, payload = 400, b'{"developerMessage":"validation.msg.glaccount.glCode.duplicate"}'
        elif p.endswith("/empty"):
            code, payload = 204, b""
        elif p.endswith("/large"):
            code, payload = 200, (b'{"pad":"' + b"A" * 100000 + b'"}')
        else:
            code, payload = 200, b'{"resourceId":42,"officeId":1}'
        n = int(self.headers.get("Content-Length") or 0)
        if n:
            self.rfile.read(n)
        self.send_response(code)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    do_GET = do_POST = do_PUT = do_DELETE = _go


srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = "http://127.0.0.1:%d" % srv.server_address[1]


def run(cap, args, seed=False, base=BASE):
    d = tempfile.mkdtemp(prefix="d2c.")
    os.makedirs(d + "/out"); os.makedirs(d + "/req")
    shutil.copy(cap, d + "/cap.sh"); os.chmod(d + "/cap.sh", 0o755)
    open(d + "/env.sh", "w").write(
        "B=%s\nA='Authorization: Basic x'\nT='Fineract-Platform-TenantId: gerege'\n"
        "CT='Content-Type: application/json'\nexport B A T CT\n" % base)
    open(d + "/req/b.json", "w").write('{"glCode":"10001"}')
    p = subprocess.run(["/bin/sh", d + "/cap.sh"] + args, capture_output=True)
    out = {}
    for ext in ("json", "http", "status"):
        f = "%s/out/%s.%s" % (d, args[0], ext)
        out[ext] = open(f, "rb").read() if os.path.exists(f) else None
    listing = sorted(os.listdir(d + "/out"))
    shutil.rmtree(d, ignore_errors=True)
    return p.returncode, out, listing, p.stderr.decode()


fails = []

print("1. CLEAN SLATE + unreachable endpoint: out/ must be left EMPTY")
for label, cap in (("pre-fix ", PRE), ("post-fix", POST)):
    rc, out, listing, err = run(cap, ["N", "POST", "/glaccounts", "req/b.json"],
                                base="https://127.0.0.1:1/api/v1")
    ok = rc != 0 and listing == []
    if not ok and cap == POST:
        fails.append("clean-slate leaves %r" % listing)
    print("   %s exit=%-3s out/=%s  %s" % (label, rc, listing, "OK" if ok else "<-- writes on failure"))

print("2. SUCCESS PATH not regressed (200 with body)")
rcs = {}
for label, cap in (("pre-fix ", PRE), ("post-fix", POST)):
    rc, out, listing, err = run(cap, ["N", "POST", "/glaccounts", "req/b.json"])
    rcs[label] = (rc, out, listing)
    print("   %s exit=%-3s status=%r body=%r" % (label, rc, out["status"], out["json"]))
    print("            .http = %r" % (out["http"],))
a, b = rcs["pre-fix "], rcs["post-fix"]
if a[1]["json"] != b[1]["json"] or a[1]["status"] != b[1]["status"]:
    fails.append("success-path body/status differ pre vs post")
ha = re.sub(rb"captured-at-utc: .*", b"TS", a[1]["http"] or b"")
hb = re.sub(rb"captured-at-utc: .*", b"TS", b[1]["http"] or b"")
if ha != hb:
    fails.append("success-path .http record differs pre vs post: %r vs %r" % (ha, hb))
else:
    print("   .http records identical modulo the timestamp: OK")
if a[2] != b[2]:
    fails.append("success-path out/ listing differs: %r vs %r" % (a[2], b[2]))

print("3. REFUSAL is still an OBSERVATION (400 must exit 0 and be recorded)")
for label, cap in (("pre-fix ", PRE), ("post-fix", POST)):
    rc, out, listing, err = run(cap, ["N", "POST", "/glaccounts/refuse", "req/b.json"])
    ok = rc == 0 and out["status"] == b"400\n" and b"duplicate" in (out["json"] or b"")
    if not ok and cap == POST:
        fails.append("400 refusal not recorded as an observation (rc=%s status=%r)" % (rc, out["status"]))
    print("   %s exit=%-3s status=%r body=%r %s" % (label, rc, out["status"], out["json"], "OK" if ok else "<-- BAD"))

print("4. EMPTY 204 body and 100KB body (byte fidelity, no-body branch)")
for path, expect_len in (("/glaccounts/empty", 0), ("/glaccounts/large", 100011)):
    for label, cap in (("pre-fix ", PRE), ("post-fix", POST)):
        rc, out, listing, err = run(cap, ["N", "GET", path])
        got = len(out["json"]) if out["json"] is not None else -1
        ok = rc == 0 and got == expect_len
        if not ok and cap == POST:
            fails.append("%s: post-fix len=%s expected=%s rc=%s" % (path, got, expect_len, rc))
        print("   %s %-20s exit=%-3s bodylen=%-7s %s" % (label, path, rc, got, "OK" if ok else "<-- BAD"))

print()
if fails:
    print("REGRESSIONS/DEFECTS IN POST-FIX:")
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("No regression found in the post-fix success path.")
