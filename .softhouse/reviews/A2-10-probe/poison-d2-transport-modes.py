#!/usr/bin/env python3
"""A2-10 independent D-2 poison, round 2: failure modes the shell/option matrix misses.

  A. PARTIAL TRANSFER  - server sends headers + part of the body then closes.
                         curl exits 18 (or 56) AFTER having written bytes.
  B. CURL ABSENT       - PATH stripped: command substitution returns 127.
  C. CALLER LAUNDERING - cap.sh invoked in a pipeline / subshell / command
                         substitution, i.e. the ways `|| exit 1` can be defeated.
"""
import os, re, shutil, socket, subprocess, sys, tempfile, threading

STALE_TS = "2000-01-01T00:00:00Z"
STALE_BODY = b'{"stale":"BODY FROM AN EARLIER FIRE - MUST NOT BE RE-DATED"}'
CAP = sys.argv[1]
LABEL = sys.argv[2]
results = []


def sandbox(base_url):
    d = tempfile.mkdtemp(prefix="d2b.")
    os.makedirs(d + "/out"); os.makedirs(d + "/req")
    shutil.copy(CAP, d + "/cap.sh"); os.chmod(d + "/cap.sh", 0o755)
    with open(d + "/env.sh", "w") as f:
        f.write("B=%s\n" % base_url)
        f.write("A='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='\n")
        f.write("T='Fineract-Platform-TenantId: gerege'\n")
        f.write("CT='Content-Type: application/json'\nexport B A T CT\n")
    open(d + "/out/POISON.json", "wb").write(STALE_BODY)
    open(d + "/out/POISON.status", "w").write("200\n")
    open(d + "/out/POISON.http", "w").write(
        "POST /glaccounts\nFineract-Platform-TenantId: gerege\n"
        "Authorization: Basic <mifos:password>\ncaptured-at-utc: %s\n" % STALE_TS)
    open(d + "/req/b.json", "w").write('{"x":1}')
    return d


def judge(desc, d, rc):
    bad = []
    if rc == 0:
        bad.append("exit0")
    http = d + "/out/POISON.http"
    if os.path.exists(http):
        m = re.search(r"^captured-at-utc: (.*)$", open(http).read(), re.M)
        ts = m.group(1) if m else "<none>"
        if ts != STALE_TS:
            bad.append("FRESH-TIMESTAMP(%s)" % ts)
    else:
        bad.append("HTTP-RECORD-DELETED")
    body = open(d + "/out/POISON.json", "rb").read() if os.path.exists(d + "/out/POISON.json") else b"<absent>"
    if body != STALE_BODY:
        bad.append("BODY-MUTATED(%r)" % body[:60])
    st = open(d + "/out/POISON.status").read().strip() if os.path.exists(d + "/out/POISON.status") else "<absent>"
    if st != "200":
        bad.append("STATUS-MUTATED(%s)" % st)
    ok = not bad
    results.append(ok)
    print("  %-9s %-46s exit=%-3s %s" % ("CAUGHT" if ok else "*LAUNDERED*", desc, rc, " ".join(bad)))
    shutil.rmtree(d, ignore_errors=True)


# ---------------------------------------------------------------- A. partial transfer
class Partial(threading.Thread):
    daemon = True

    def __init__(self):
        super().__init__()
        self.s = socket.socket()
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind(("127.0.0.1", 0)); self.s.listen(16)
        self.port = self.s.getsockname()[1]

    def run(self):
        while True:
            try:
                c, _ = self.s.accept()
            except OSError:
                return
            try:
                c.recv(65536)
                c.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 4096\r\n\r\n"
                          b'{"TRUNCATED-RESPONSE-NEVER-COMPLETED":true}')
                c.close()          # close mid-body -> curl exit 18
            except OSError:
                pass


srv = Partial(); srv.start()
print("=== %s :: %s ===" % (LABEL, CAP))
print("A. PARTIAL TRANSFER (server closes mid-body, curl exits 18) on 127.0.0.1:%d" % srv.port)
for branch, args in (("body", ["POISON", "POST", "/glaccounts", "req/b.json"]),
                     ("nobody", ["POISON", "POST", "/glaccounts"])):
    d = sandbox("http://127.0.0.1:%d" % srv.port)
    p = subprocess.run(["/bin/sh", d + "/cap.sh"] + args, capture_output=True)
    judge("partial-transfer %s" % branch, d, p.returncode)

# ---------------------------------------------------------------- B. curl absent
print("B. CURL ABSENT (PATH stripped -> 127 from the command substitution)")
for branch, args in (("body", ["POISON", "POST", "/glaccounts", "req/b.json"]),
                     ("nobody", ["POISON", "POST", "/glaccounts"])):
    d = sandbox("https://127.0.0.1:1/api/v1")
    env = dict(os.environ, PATH="/nonexistent")
    p = subprocess.run(["/bin/sh", d + "/cap.sh"] + args, capture_output=True, env=env)
    judge("curl-absent %s" % branch, d, p.returncode)

# ---------------------------------------------------------------- C. caller laundering
print("C. CALLER SHAPES (how a `|| exit 1` guard gets defeated), endpoint closed")
CALLERS = {
    "plain            || exit 1": 'sh "$D/cap.sh" POISON POST /glaccounts req/b.json || exit 1\ncat "$D/out/POISON.json"\n',
    "pipeline to tee  || exit 1": 'sh "$D/cap.sh" POISON POST /glaccounts req/b.json | tee "$D/log" || exit 1\ncat "$D/out/POISON.json"\n',
    "cmd-substitution || exit 1": 'X=$(sh "$D/cap.sh" POISON POST /glaccounts req/b.json) || exit 1\ncat "$D/out/POISON.json"\n',
    "subshell         || exit 1": '( sh "$D/cap.sh" POISON POST /glaccounts req/b.json || exit 1 )\ncat "$D/out/POISON.json"\n',
    "no guard at all           ": 'sh "$D/cap.sh" POISON POST /glaccounts req/b.json\ncat "$D/out/POISON.json"\n',
}
for desc, body in CALLERS.items():
    d = sandbox("https://127.0.0.1:1/api/v1")
    open(d + "/run.sh", "w").write('#!/bin/sh\nD=%s\n%s' % (d, body))
    p = subprocess.run(["/bin/sh", d + "/run.sh"], capture_output=True)
    launders = STALE_BODY in p.stdout
    ok = (p.returncode != 0) and not launders
    results.append(ok)
    print("  %-9s %-46s exit=%-3s %s" % ("CAUGHT" if ok else "*LAUNDERED*", desc, p.returncode,
                                         "STALE BODY ON STDOUT" if launders else ""))
    shutil.rmtree(d, ignore_errors=True)

print("PASS=%d FAIL=%d" % (sum(results), len(results) - sum(results)))
sys.exit(0 if all(results) else 1)
