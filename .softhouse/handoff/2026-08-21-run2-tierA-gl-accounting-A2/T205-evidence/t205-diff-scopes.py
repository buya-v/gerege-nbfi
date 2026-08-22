import json, sys
def load(p):
    d = {}
    for r in json.load(open(p)):
        for s in r.get("sites", []):
            d[(r["path"], s["line"], s["verb"])] = s
    return d
a = load(sys.argv[1]); b = load(sys.argv[2])
common = set(a) & set(b)
print("keys only in one run (line numbers moved -- the classifier's own file):", sorted(set(a) ^ set(b)))
a = {k: a[k] for k in common}; b = {k: b[k] for k in common}
moved = [(k, a[k], b[k]) for k in a
         if (a[k]["scope"], a[k]["verdict"]) != (b[k]["scope"], b[k]["verdict"])]
print("sites inspected (both runs, identical key set): %d" % len(a))
print("sites whose (scope,verdict) MOVED: %d" % len(moved))
for k, x, y in sorted(moved):
    print("  %s:%d %s" % (k[0], k[1], k[2]))
    print("      %s/%s -> %s/%s   tags=%s  chain=%s"
          % (x["scope"], x["verdict"], y["scope"], y["verdict"],
             ",".join(y["target_tags"]), y.get("scope_via_chain")))
    print("      target: %s" % y["target"])
print()
for lbl, d in (("BEFORE", a), ("AFTER", b)):
    u = [k for k in d if d[k]["scope"] == "UNKNOWN" and d[k]["verdict"] == "UNGUARDED"]
    t = [k for k in d if d[k]["scope"] == "TRUSTED" and d[k]["verdict"] == "UNGUARDED"]
    sc = [k for k in d if d[k]["scope"] == "SCRATCH"]
    ch = [k for k in d if d[k].get("scope_via_chain")]
    print("%-6s UNKNOWN+UNGUARDED=%d  TRUSTED+UNGUARDED=%d  SCRATCH(any)=%d  scope_via_chain=%d"
          % (lbl, len(u), len(t), len(sc), len(ch)))
