"""T276: A2-504 and A2-507 are committed A2-5xx GET captures that prove-t275-reissue.py
never inspects (they are in neither IDEMPOTENT_HTTP, SUPERSEDED_READ nor MUTATING, and
being HTTP they are not auto-discovered by the .psql sweep). Apply the SUPERSEDED_READ
assertion to them by hand and see whether the omission concealed a failure or was benign.
"""
import hashlib, os, subprocess, shutil, tempfile

C = "/tmp/t276/t275tree/.softhouse/capture/tierA-a2"
OUT = os.path.join(C, "out")
CUR = "A2-521-loanproduct23-after-channel-repoint"


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


scratch = tempfile.mkdtemp(prefix="t276-gap-")
copy = os.path.join(scratch, "tierA-a2")
shutil.copytree(C, copy)
shutil.rmtree(os.path.join(copy, "out"))
os.makedirs(os.path.join(copy, "out"))

cur = sha(os.path.join(OUT, CUR + ".json"))
print("current-state capture", CUR, cur[:16])
for name in ["A2-504-loanproduct23-after-repoint", "A2-507-loanproduct23-after-channel"]:
    subprocess.run(["sh", os.path.join(copy, "cap8.sh"), name, "GET", "/loanproducts/23"],
                   capture_output=True, text=True)
    old = sha(os.path.join(OUT, name + ".json"))
    fresh = sha(os.path.join(copy, "out", name + ".json"))
    verdict = ("SUPERSEDED (differs from snapshot, equals current)"
               if old != fresh and fresh == cur else
               "IDENTICAL to snapshot" if old == fresh else
               "MATCHES NEITHER -- would have FAILED the prover's assertion")
    print(f"  {name:<40} snapshot {old[:16]}  fresh {fresh[:16]}  -> {verdict}")
shutil.rmtree(scratch, ignore_errors=True)
