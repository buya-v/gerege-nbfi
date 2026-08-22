#!/usr/bin/env bash
# T245 — INDEPENDENT re-derivation of the five claims the /softhouse-program driver made
# in commit 358c3b9 ("driver: the oracle PIN FILE did not name the database every ledger
# vector came from") against .softhouse/reference-oracle.md.
#
# READ-ONLY. Every statement here is a SELECT, a `git show`, or a file read. It writes
# nothing to the oracle, nothing to the vector store, nothing outside stdout and /tmp.
#
# ENGINE ROSTER (P-72 / P-75). In an agent shell `grep` and `rg` are SHELL FUNCTIONS, not
# the programs their names say: `grep` execs bundled ugrep 7.5.0 with `-G --ignore-files
# --hidden -I` and six `--exclude-dir` flags silently prepended (measured 33% recall on a
# purpose-built fixture, exit 0, nothing said anything was skipped), and `rg` has no binary
# at all (`rg P F` exits 127, but `rg P F | head` exits 0). `git grep -E` both MISSES true
# hits and FABRICATES. This script therefore uses ONLY: /usr/bin/grep, `git grep -F`
# (calibrated below on a known POSITIVE *and* a known NEGATIVE), psql, and python3 `re`
# over whole-file BYTES — the last of which is deliberately NOT line-oriented, because
# every sweep in this program has been and T234 found 743 matches spanning a newline.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
STAMP=$(git rev-parse HEAD)
echo "T245 measurement — STAMPED AT COMMIT: $STAMP"
echo "wall clock (UTC):  $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "type grep     -> $(type grep 2>&1 | head -1)"
echo "/usr/bin/grep -> $(/usr/bin/grep --version | head -1)"
echo

echo "=== ORACLE REACHABILITY ==="
curl -sk --max-time 20 https://localhost:8443/fineract-provider/actuator/health; echo
docker ps --format '{{.Names}}  {{.Image}}  {{.Status}}'
echo

echo "=== CLAIM (2): THREE Fineract databases; fineract_gerege has 281 public tables and is tenant 2 ==="
docker exec fineract-db-1 psql -U root -d postgres -A -F'|' -c "select datname from pg_database order by 1;"
for db in fineract_tenants fineract_default fineract_gerege; do
  printf '%-18s public tables = ' "$db"
  docker exec fineract-db-1 psql -U root -d "$db" -t -A -c "select count(*) from information_schema.tables where table_schema='public';"
done
echo

echo "=== CLAIM (3): tenant registry, and the tenant -> database MAPPING (measured, not inferred) ==="
docker exec fineract-db-1 psql -U root -d fineract_tenants -A -F'|' -c \
 "select t.id, t.identifier, t.name, t.timezone_id, c.schema_name, c.schema_server, c.schema_server_port
    from tenants t join tenant_server_connections c on c.id = t.oltp_id order by t.id;"
echo

echo "=== CLAIM (5) LEG 1: the tenant header in each committed capture .http sidecar ==="
python3 - <<'PY'
import re,os
base='.softhouse/capture/tierA-a2/out'
cases=['A2-343-manual-je-3leg','A2-347-je-manual-readback','A2-337-repayment-split',
       'A2-338-je-after-repayment-coverage','A2-382-repayment-overpay','A2-383-je-after-overpay',
       'A2-344-manual-je-unbalanced','A2-345-manual-je-header','A2-346-manual-je-nomanual',
       'A2-390-db-ledger-state-a2-15']
for c in cases:
    t=open(os.path.join(base,c+'.http'),encoding='utf-8',errors='replace').read().splitlines()
    ten=[l for l in t if re.search(r'tenant|fineract_',l,re.I)]
    print('  %-40s %-52s %s' % (c, t[0][:52], ten or 'NO TENANT LINE'))
PY
echo
echo "  capture env.sh (sourced by cap.sh / cap8.sh / cap9.sh):"
/usr/bin/grep -n 'TenantId' .softhouse/capture/tierA-a2/env.sh
echo "  BUT the .http sidecar line is a HARD-CODED LITERAL, not an echo of \$T:"
/usr/bin/grep -n 'echo "Fineract-Platform-TenantId' .softhouse/capture/tierA-a2/cap.sh .softhouse/capture/tierA-a2/cap8.sh .softhouse/capture/tierA-a2/cap9.sh
echo "  (contrast cap9.sh, which DOES echo the variable for the idempotency key:)"
/usr/bin/grep -n 'echo "Idempotency-Key' .softhouse/capture/tierA-a2/cap9.sh
echo

echo "=== CLAIM (5) LEG 2: THE DECISIVE ONE — the rows themselves, in BOTH tenant databases ==="
echo "-- LDG-01 cites transaction a28f573f34c7 --"
echo "   fineract_gerege:"
docker exec fineract-db-1 psql -U root -d fineract_gerege -A -F'|' -c \
 "select transaction_id, account_id, type_enum, amount, currency_code from acc_gl_journal_entry where transaction_id='a28f573f34c7' order by id;"
echo "   fineract_default:"
docker exec fineract-db-1 psql -U root -d fineract_default -A -F'|' -c \
 "select transaction_id, account_id, type_enum, amount, currency_code from acc_gl_journal_entry where transaction_id='a28f573f34c7' order by id;"
echo "-- LDG-04 cites transaction a28f573ffb9b --"
docker exec fineract-db-1 psql -U root -d fineract_gerege  -A -F'|' -c "select transaction_id, account_id, type_enum, amount from acc_gl_journal_entry where transaction_id='a28f573ffb9b' order by id;"
docker exec fineract-db-1 psql -U root -d fineract_default -A -F'|' -c "select count(*) as rows_in_default from acc_gl_journal_entry where transaction_id='a28f573ffb9b';"
echo "-- LDG-02 / LDG-03 legs --"
docker exec fineract-db-1 psql -U root -d fineract_gerege -A -F'|' -c \
 "select transaction_id, account_id, type_enum, amount, loan_transaction_id from acc_gl_journal_entry where transaction_id in ('L25','L27') order by transaction_id, id;"
docker exec fineract-db-1 psql -U root -d fineract_default -A -F'|' -c \
 "select count(*) as rows_in_default from acc_gl_journal_entry where amount in (270450.580000,22049.420000,889549.420000,90151.760000,20298.820000);"
echo "-- LDG-REFUSE-01/02 name GL 16/18/21 by id, code, name and manual_journal_entries_allowed --"
docker exec fineract-db-1 psql -U root -d fineract_gerege -A -F'|' -c \
 "select id, gl_code, name, account_usage, manual_journal_entries_allowed from acc_gl_account where id in (1,4,6,8,10,16,17,18,21) order by id;"
echo "   the SAME query against fineract_default:"
docker exec fineract-db-1 psql -U root -d fineract_default -A -F'|' -c \
 "select id, gl_code, name, account_usage, manual_journal_entries_allowed from acc_gl_account order by id;"
echo "-- and the whole-database emptiness that settles it --"
for db in fineract_gerege fineract_default; do
  printf '   %-18s ' "$db"
  docker exec fineract-db-1 psql -U root -d "$db" -t -A -c \
   "select 'journal_entries='||(select count(*) from acc_gl_journal_entry)||' gl_accounts='||(select count(*) from acc_gl_account)||' loans='||(select count(*) from m_loan)||' loan_products='||(select count(*) from m_product_loan);"
done
echo

echo "=== CLAIM (5) LEG 3: the vectors cite EXACTLY these committed artefacts (sha256) ==="
python3 - <<'PY'
import json,glob,hashlib,os
ok=bad=0
for f in sorted(glob.glob('.softhouse/vectors/ledger/*.json')):
    p=json.load(open(f))['provenance']
    for rk,sk in (('capture_ref','capture_sha256'),('request_capture_ref','request_capture_sha256')):
        if rk not in p: continue
        got=hashlib.sha256(open(p[rk],'rb').read()).hexdigest()
        ok+=got==p[sk]; bad+=got!=p[sk]
        if got!=p[sk]: print('  MISMATCH',os.path.basename(f),rk,got,p[sk])
print('  provenance digest check: MATCH=%d MISMATCH=%d' % (ok,bad))
PY
echo

echo "=== CLAIM (1): the PRE-EDIT pin file. Instrument = python3 re over raw BYTES, whole file, NOT line-oriented ==="
git show 358c3b9^:.softhouse/reference-oracle.md > /tmp/t245-pre.md
python3 - <<'PY'
import re
pre=open('/tmp/t245-pre.md','rb').read(); post=open('.softhouse/reference-oracle.md','rb').read()
print('  CALIBRATION  known POSITIVE b"fineract_default" in PRE  ->', len(re.findall(b'fineract_default',pre)))
print('  CALIBRATION  known NEGATIVE b"zzq_nonexistent"  in PRE  ->', len(re.findall(b'zzq_nonexistent',pre)))
for n in [b'fineract_gerege',b'gerege',b'Gerege',b'Asia/Ulaanbaatar',b'Asia/Kolkata']:
    print('  %-20r PRE=%-4d POST=%d' % (n,len(re.findall(re.escape(n),pre)),len(re.findall(re.escape(n),post))))
print(r'  MULTI-LINE probe rb"fineract[\s\S]{0,40}?gerege" in PRE ->', len(re.findall(rb'fineract[\s\S]{0,40}?gerege',pre)))
print('  every PRE line naming the tenant gerege (case-insensitive):')
for i,l in enumerate(pre.decode().splitlines(),1):
    if 'gerege' in l.lower(): print('   %4d: %s' % (i,l[:150]))
PY
echo

echo "=== CLAIM (4): tracked-file counts. git grep -F, CALIBRATED, cross-checked against an independent python byte scan ==="
echo -n "  CALIB positive  'fineract_gerege' @HEAD .softhouse/  : "; git grep -F -l -a "fineract_gerege" HEAD -- .softhouse/ | wc -l
echo -n "  CALIB negative  'zzq_nonexistent' @HEAD .softhouse/  : "; git grep -F -l -a "zzq_nonexistent" HEAD -- .softhouse/ | wc -l || true
for c in c0be92b 358c3b9 HEAD; do
  g=$(git grep -F -l -a "fineract_gerege"  "$c" -- .softhouse/ | wc -l | tr -d ' ')
  d=$(git grep -F -l -a "fineract_default" "$c" -- .softhouse/ | wc -l | tr -d ' ')
  ga=$(git grep -F -l -a "fineract_gerege"  "$c" | wc -l | tr -d ' ')
  da=$(git grep -F -l -a "fineract_default" "$c" | wc -l | tr -d ' ')
  echo "  $c  under .softhouse/: gerege=$g default=$d   | whole tree: gerege=$ga default=$da"
done
echo

echo "=== THE FINDING THE DRIVER'S EDIT DID NOT REACH: the pin file's OPERATIVE instruction table ==="
/usr/bin/grep -n -A7 '^## Connection facts for vector capture' .softhouse/reference-oracle.md || true
echo -n "  tracked files in the WHOLE repo carrying the string 'tenantIdentifier=default': "
git grep -F -l -a "tenantIdentifier=default" HEAD | wc -l || true
echo

echo "=== SWEEP (task item 5): files naming a tenant DATABASE without naming a tenant IDENTIFIER ==="
python3 - <<'PY'
import subprocess,re
files=[f.decode() for f in subprocess.run(['git','ls-files','-z'],capture_output=True).stdout.split(b'\0') if f]
DB=re.compile(rb'fineract_(default|gerege|tenants)|-d\s+fineract')
STRICT=re.compile(rb'Fineract-Platform-TenantId|tenantIdentifier|ThreadLocalContextUtil\.setTenant|tenant[_ ]identifier|BY_TENANT|\|\s*Tenant\s*\||tenant\s*[:=]\s*`?(gerege|default)|`(gerege|default)`\s+tenant|tenant\s+`?(gerege|default)',re.I)
print('  scope: ALL %d tracked files at HEAD, read as BYTES (binaries included),' % len(files))
print('         matcher = python3 re over the WHOLE FILE -> multi-line, NOT line-oriented.')
print('  CALIB DB     positive .softhouse/reference-oracle.md      ->', bool(DB.search(open('.softhouse/reference-oracle.md','rb').read())))
print('  CALIB DB     negative .softhouse/vectors/PIN.json         ->', bool(DB.search(open('.softhouse/vectors/PIN.json','rb').read())))
print('  CALIB STRICT positive .softhouse/capture/tierA-a2/env.sh  ->', bool(STRICT.search(open('.softhouse/capture/tierA-a2/env.sh','rb').read())))
print('  CALIB STRICT negative .softhouse/vectors/PIN-ledger.json  ->', bool(STRICT.search(open('.softhouse/vectors/PIN-ledger.json','rb').read())))
db=[];bad=[]
for f in files:
    try: b=open(f,'rb').read()
    except Exception: continue
    if DB.search(b):
        db.append(f)
        if not STRICT.search(b): bad.append(f)
print('  names a tenant DATABASE                      : %d' % len(db))
print('  ... and names NO tenant identifier anywhere  : %d' % len(bad))
for f in sorted(bad): print('     ',f)
print('  AND SEPARATELY, the two STORE-LEVEL PINS, which name NEITHER:')
for f in ('.softhouse/vectors/PIN.json','.softhouse/vectors/PIN-ledger.json'):
    b=open(f,'rb').read()
    print('     %-38s names a database=%s  names a tenant=%s' % (f, bool(DB.search(b)), bool(STRICT.search(b))))
PY
echo
echo "T245 measurement COMPLETE — re-stamp at finish: $(git rev-parse HEAD)"
