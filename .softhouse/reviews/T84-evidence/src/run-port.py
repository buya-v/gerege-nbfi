import json, os, shutil, subprocess, sys
from decimal import Decimal

ROOT = '/Users/buv/gerege-nbfi/.claude/worktrees/agent-a6c2c61c89d384f71'
TC = "/Users/buv/gerege-nbfi/.softhouse/toolchain"
e = dict(os.environ)
e.update(GOROOT=TC + "/go", GOPATH=TC + "/gopath", GOCACHE=TC + "/gocache",
         GOMODCACHE=TC + "/gomodcache", PATH=TC + "/go/bin:" + e.get("PATH", ""))
scratch = "/tmp/t84port"
shutil.rmtree(scratch, ignore_errors=True); os.makedirs(scratch)
shutil.copytree(os.path.join(ROOT, "nexus"), os.path.join(scratch, "nexus"))
d = os.path.join(scratch, "nexus", "cmd", "t84port"); os.makedirs(d)
shutil.copy('/tmp/t84portsrc/main.go', os.path.join(d, "main.go"))
p = subprocess.run(["go", "run", "./cmd/t84port"], cwd=os.path.join(scratch, "nexus"),
                   env=e, capture_output=True, text=True)
if p.returncode != 0:
    sys.exit("port run failed:\n" + p.stderr[:4000])
port = {r["case"]: r for r in json.loads(p.stdout)}
shutil.rmtree(scratch, ignore_errors=True)

def minor(t):
    neg = t.startswith("-"); t = t.lstrip("-")
    w, _, fr = t.partition(".")
    assert len(fr) <= 2 or set(fr[2:]) == {"0"}, t
    fr = (fr + "00")[:2]
    v = int(w or 0) * 100 + int(fr)
    return -v if neg else v

caps = {}
for f in ('/tmp/t84probe/out/capture-t84-raw.json', '/tmp/t84probe2/out/capture-t84b-raw.json'):
    for c in json.load(open(f))["captures"]:
        caps[c["id"]] = c

cal = 0; report = []
for cid, cap in caps.items():
    pr = port.get(cid)
    if pr is None:
        sys.exit("port did not answer " + cid)
    if pr.get("error"):
        report.append((cid, "REFUSED", pr["error"], None)); continue
    per = cap["observed"]["periods"]; rows = pr["rows"]
    if len(rows) != len(per):
        report.append((cid, "ROWCOUNT", len(rows), len(per))); continue
    diffs = []
    for i, pp in enumerate(per):
        for wire, field in (("principal", "principal_minor"), ("interest", "interest_minor"),
                            ("balance", "outstanding_principal_minor")):
            if pp.get(wire) is None: continue
            if minor(pp[wire]) != rows[i][field]:
                diffs.append({"row": i, "field": field, "oracle": minor(pp[wire]), "port": rows[i][field]})
    if cid.startswith("P-CAL-"): cal += len(diffs)
    report.append((cid, "OK", diffs, rows[-1]["outstanding_principal_minor"]))

print("calibration mismatch cells (must be 0):", cal)
print("refused:", [r[0] for r in report if r[1] == "REFUSED"][:10],
      len([r for r in report if r[1] == "REFUSED"]))
diverge = [r for r in report if r[1] == "OK" and r[2]]
print("cases with any cell mismatch: %d of %d" % (len(diverge), len(report)))
by_field = {}
for r in diverge:
    for dd in r[2]: by_field[dd["field"]] = by_field.get(dd["field"], 0) + 1
print("divergent cells by column:", by_field)
multi = [r for r in diverge if len(r[2]) > 1]
print("\ncases with MORE THAN ONE divergent cell: %d" % len(multi))
for r in sorted(multi, key=lambda r: -len(r[2]))[:12]:
    fields = {}
    for dd in r[2]: fields[dd["field"]] = fields.get(dd["field"], 0) + 1
    print("   %-28s %3d divergent cells  %s" % (r[0], len(r[2]), fields))
print("\nport final-row outstanding on the 600%% family (port amortizes?):")
for r in report:
    if r[1] == "OK" and "R600p0" in r[0] and ("-N10" in r[0] or "-N11" in r[0] or "-N12" in r[0]):
        print("   %-28s port last-row outstanding = %s, divergent cells = %d" % (r[0], r[3], len(r[2])))
json.dump([[r[0], r[1], r[2] if r[1] == "OK" else str(r[2]), r[3]] for r in report],
          open('/tmp/t84-port-report.json', 'w'), indent=1)
