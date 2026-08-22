import os, collections
OUT = "/tmp/t276/t275tree/.softhouse/capture/tierA-a2/out"
names = collections.defaultdict(set)
for f in os.listdir(OUT):
    if not f.startswith("A2-5"):
        continue
    base = f.split(".")[0]
    names[base].add(f[len(base):])
http = [n for n, s in names.items() if ".http" in s]
sql = [n for n, s in names.items() if ".psql" in s]
print("A2-5xx HTTP captures:", len(http), " SQL captures:", len(sql), " total:", len(names))
bad = []
for n in http:
    s = names[n]
    need = {".http", ".json", ".status"}
    if not need <= s:
        bad.append((n, "missing " + str(need - s)))
    if ".req" in s and ".req.sha256" not in s:
        bad.append((n, "req without digest"))
for n in sql:
    s = names[n]
    need = {".psql", ".txt", ".sql", ".sql.sha256"}
    if not need <= s:
        bad.append((n, "missing " + str(need - s)))
print("INCOMPLETE ARTEFACT SETS:", bad if bad else "none")
for n in sorted(http):
    print("  ", n, open(os.path.join(OUT, n + ".status")).read().strip())
for n in sorted(sql):
    rec = open(os.path.join(OUT, n + ".psql")).read()
    ex = [l for l in rec.splitlines() if l.startswith("psql-exit-status")]
    print("  ", n, ex)
