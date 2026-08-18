#!/usr/bin/env python3
"""T36 — machine-readable ATTESTATION SIDECAR for a Path B capture set.  Closes T22 P0-3.

Writes `attestation.json` next to the raw captures.  Every field is READ FROM THE
RUNNING SERVER, its container, its deployed bytecode, or its PostgreSQL rows.  Nothing
is copied from a plan, a report, or an earlier attestation, and nothing is defaulted:
a fact that cannot be read is recorded as null with a `_unread` note, never guessed.

It also DRIVES the capture, so the request/response digests and the UTC timestamps
describe one single run rather than being attached to files after the fact.  The
fail-the-run preconditions (T22 P0-4) execute first; a breach aborts before any capture.

RAW OBSERVED.  This sidecar makes a capture set ADMISSIBLE for review; it does not
promote anything to the parity vector store — DEC-1 is unratified (gate G-1) and
promotion is a separate, non-agent decision.

Usage: python3 attest.py [tenant]     (default: gerege)
"""
import datetime
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PATHB = os.path.normpath(os.path.join(HERE, '..'))
TENANT = sys.argv[1] if len(sys.argv) > 1 else 'gerege'
# Which capture set to attest.  'pathb' = the four committed B-0x sets (T22 P0-6 re-capture);
# 'emiloop' = the T36 EMI re-adjust-loop probes (T22 P1-11, second clause).
CAPTURE_SET = sys.argv[2] if len(sys.argv) > 2 else 'pathb'
OUT = os.path.join(HERE, 'out',
                   'recapture-%s' % TENANT if CAPTURE_SET == 'pathb' else CAPTURE_SET)
FIN, DB = 'fineract-fineract-1', 'fineract-db-1'
BASE = 'https://localhost:8443/fineract-provider'

# Ratified tenant parameters (CLAUDE.md).  Asserted, never assumed.
WANT_ROUNDING_ORDINAL = 4          # RoundingMode.valueOf(4) == HALF_UP
WANT_PRECISION = 19                # MoneyHelper.PRECISION
# java.math.RoundingMode ordinals, as consumed by MoneyHelper.validateAndConvertRoundingMode
# (MoneyHelper.java:182-190 -> RoundingMode.valueOf(int), legacy BigDecimal constants).
ROUNDING_ORDINALS = {0: 'UP', 1: 'DOWN', 2: 'CEILING', 3: 'FLOOR',
                     4: 'HALF_UP', 5: 'HALF_DOWN', 6: 'HALF_EVEN'}

PATHB_CAPTURES = [
    ('B-01', 'baseline',            'req', 'calc-B-01-baseline.json',           'B-01-baseline-raw.json'),
    ('B-02', 'multiplesOf 100',     'req', 'calc-B-02-multiplesof100.json',     'B-02-multiplesof100-raw.json'),
    ('B-03', 'DIYCS FULL_LEAP_YEAR','req', 'calc-B-03-diycs-fullleapyear.json', 'B-03-diycs-fullleapyear-raw.json'),
    ('B-04', 'DIYCS FEB_29_PERIOD_ONLY', 'req', 'calc-B-04-diycs-feb29only.json','B-04-diycs-feb29only-raw.json'),
]
# T22 P1-11 second clause: principals selected so the EMI re-adjust loop's entry condition
# |emiDifference| * 100 > Money(floor(n/2)) is crossed (n = 12 -> 6.00).
EMILOOP_PRINCIPALS = [1200000, 1200001, 1200004, 1200027, 1200033, 1200039, 1200045, 1200054, 1200189]
EMILOOP_CAPTURES = [('EL-%d' % p, 'EMI re-adjust-loop probe, principal %d MNT' % p,
                     't36/req-emiloop', 'calc-emiloop-%d.json' % p, 'emiloop-%d-raw.json' % p)
                    for p in EMILOOP_PRINCIPALS]
CAPTURES = PATHB_CAPTURES if CAPTURE_SET == 'pathb' else EMILOOP_CAPTURES

notes = []


def sh(cmd):
    """Run a command, return stdout stripped, or None if it fails."""
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=180)
    except Exception as exc:                                     # noqa: BLE001
        notes.append('command failed (%s): %s' % (exc, cmd))
        return None
    if p.returncode != 0:
        notes.append('command exit %d: %s :: %s' % (p.returncode, cmd, p.stderr.strip()[:200]))
        return None
    return p.stdout.strip()


def unread(field, why):
    notes.append('UNREAD %s — %s' % (field, why))
    return None


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


# --------------------------------------------------------------- preconditions
canary = os.path.join(PATHB, 't22-audit', 'req', 'calc-pmode2-gerege.json')
pre = subprocess.run('CANARY_REQ=%s sh %s %s' % (canary, os.path.join(HERE, 'preconditions.sh'), TENANT),
                     shell=True, capture_output=True, text=True)
os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, 'preconditions.txt'), 'w') as fh:
    fh.write(pre.stdout + pre.stderr)
if pre.returncode != 0:
    sys.stderr.write(pre.stdout + pre.stderr)
    sys.stderr.write('\nABORT: preconditions breached — no capture attempted, no attestation written.\n')
    sys.exit(1)

# ------------------------------------------------------------------ the oracle
image_id = sh("docker image inspect fineract:latest --format '{{.Id}}'")
image_created = sh("docker image inspect fineract:latest --format '{{.Created}}'")
image_repodigests = sh("docker image inspect fineract:latest --format '{{json .RepoDigests}}'")
container_started = sh("docker inspect %s --format '{{.State.StartedAt}}'" % FIN)
gitprops = sh("docker exec %s sh -c 'unzip -p /app/fineract-provider.jar "
              "BOOT-INF/classes/git.properties'" % FIN) or ''
gp = {}
for line in gitprops.splitlines():
    if '=' in line and not line.startswith('#'):
        k, _, v = line.partition('=')
        gp[k.strip()] = v.strip()
jvm = sh("docker exec -e JAVA_TOOL_OPTIONS= %s sh -c 'java -version' 2>&1" % FIN)
if jvm:
    jvm = ' / '.join(l.strip() for l in jvm.splitlines() if 'Picked up' not in l)

# MoneyHelper.PRECISION, read from the DEPLOYED bytecode inside the running container.
sh("docker exec %s sh -c 'mkdir -p /tmp/t36at && cd /tmp/t36at && unzip -o -q "
   "/app/fineract-provider.jar \"BOOT-INF/lib/fineract-core-*.jar\"'" % FIN)
javap = sh("docker exec -e JAVA_TOOL_OPTIONS= %s sh -c 'cd /tmp/t36at && javap -p -constants -cp "
           "BOOT-INF/lib/fineract-core-*.jar "
           "org.apache.fineract.organisation.monetary.domain.MoneyHelper'" % FIN) or ''
precision = None
for line in javap.splitlines():
    if 'PRECISION' in line:
        precision = int(line.split('=')[1].strip().rstrip(';'))
if precision is None:
    unread('MoneyHelper.PRECISION', 'javap over the deployed fineract-core jar produced no constant')

# ---------------------------------------------------------------- the database
pg_version = sh("docker exec %s psql -U root -t -c 'select version();'" % DB)
pg_version_num = sh("docker exec %s psql -U root -At -c 'show server_version_num;'" % DB)
pg_image = sh("docker inspect %s --format '{{.Config.Image}}'" % DB)
pg_image_id = sh("docker inspect %s --format '{{.Image}}'" % DB)
env = sh("docker inspect %s --format '{{range .Config.Env}}{{println .}}{{end}}'" % FIN) or ''
driver_class = next((l.split('=', 1)[1] for l in env.splitlines()
                     if 'DRIVER_SOURCE_CLASS_NAME' in l), None)
jdbc_url = next((l.split('=', 1)[1] for l in env.splitlines()
                 if l.startswith('FINERACT_HIKARI_JDBC_URL=')), None)
# grep exits 1 on zero matches, which here is the GOOD outcome — `|| true` keeps the
# count readable instead of turning a clean result into an unread field.
banned_env = sh("docker inspect %s --format '{{range .Config.Env}}{{println .}}{{end}}' "
                "| grep -icE 'ojdbc|oracle\\.jdbc|:1521|com\\.mysql\\.cj|mariadb|go-sql-driver' "
                "|| true" % FIN)
banned_jar = sh("docker exec %s sh -c 'unzip -l /app/fineract-provider.jar' "
                "| grep -icE 'ojdbc|oracle-jdbc|mysql-connector|mariadb-java' || true" % FIN)

# ------------------------------------------------------------------ the tenant
def q(db, sql):
    return sh('docker exec %s psql -U root -d %s -At -c "%s"' % (DB, db, sql.replace('"', '\\"')))


schema = q('fineract_tenants',
           "select c.schema_name from tenants t join tenant_server_connections c on c.id=t.oltp_id "
           "where t.identifier='%s';" % TENANT)
tz = q('fineract_tenants', "select timezone_id from tenants where identifier='%s';" % TENANT)
tname = q('fineract_tenants', "select name from tenants where identifier='%s';" % TENANT)
scp = q('fineract_tenants',
        "select coalesce(c.schema_connection_parameters,'') from tenants t "
        "join tenant_server_connections c on c.id=t.oltp_id where t.identifier='%s';" % TENANT)
sport = q('fineract_tenants',
          "select c.schema_server_port from tenants t join tenant_server_connections c on c.id=t.oltp_id "
          "where t.identifier='%s';" % TENANT)
rm_row = q(schema, "select value from c_configuration where name='rounding-mode';")
rm_enabled = q(schema, "select enabled from c_configuration where name='rounding-mode';")
rounding_ordinal = int(rm_row) if rm_row and rm_row.isdigit() else None

# What the RUNNING process actually initialized — MoneyHelper caches per tenant at startup,
# so a row edited after boot is inert.  Read back from the container's own log.
logline = sh("docker logs --since %s %s 2>&1 | grep -F 'Initialized rounding mode for tenant "
             "`%s`' | tail -1" % (container_started, FIN, TENANT))
mode_in_force = logline.strip().split(':')[-1].strip() if logline else \
    unread('mode_in_force', 'no MoneyHelper init line for this tenant since container start')

mnt_dp = q(schema, "select decimal_places from m_currency where code='MNT';")
mnt_enabled = q(schema, "select count(*) from m_organisation_currency where code='MNT';")

# ------------------------------------------------- effective-mode canary (behavioural)
with open(canary, 'rb') as fh:
    canary_bytes = fh.read()
canary_out = os.path.join(OUT, 'canary-halfcent-raw.json')
canary_code = sh("curl -sk -X POST '%s/api/v1/loans?command=calculateLoanSchedule' "
                 "-H 'Authorization: Basic bWlmb3M6cGFzc3dvcmQ=' "
                 "-H 'Fineract-Platform-TenantId: %s' -H 'Content-Type: application/json' "
                 "-d @%s -o %s -w '%%{http_code}'" % (BASE, TENANT, canary, canary_out))
canary_p1 = None
if canary_code == '200':
    with open(canary_out, 'rb') as fh:
        cj = json.loads(fh.read().decode())
    canary_p1 = str(cj['periods'][1]['interestOriginalDue'])

# --------------------------------------------------------- products, from the rows
products = []
for pid in (1, 2, 3, 4):
    row = q(schema, "select to_jsonb(t) from m_product_loan t where id=%d;" % pid)
    if not row:
        products.append({'id': pid, '_unread': 'no m_product_loan row'})
        continue
    # parse_float=str keeps every decimal literal as its EXACT TEXT. Parsing a money
    # column to a binary float — even only to re-serialise it — would put a float in a
    # monetary artefact, which CLAUDE.md forbids outright.
    r = json.loads(row, parse_float=str)
    products.append({
        'id': r['id'], 'name': r['name'], 'short_name': r['short_name'],
        'currency_code': r['currency_code'], 'currency_digits': r['currency_digits'],
        'principal_amount': r['principal_amount'],
        'nominal_interest_rate_per_period': r['nominal_interest_rate_per_period'],
        'number_of_repayments': r['number_of_repayments'],
        'installment_amount_in_multiples_of': r.get('installment_amount_in_multiples_of'),
        'days_in_year_custom_strategy': r.get('days_in_year_custom_strategy'),
        'days_in_year_enum': r.get('days_in_year_enum'),
        'days_in_month_enum': r.get('days_in_month_enum'),
        'loan_schedule_type': r.get('loan_schedule_type'),
        'persisted_row_sha256': sha256(row.encode('utf-8')),
    })

# ------------------------------------------------------------------- the captures
committed_digests = {}
for cid, _l, _rd, _rq, resp in CAPTURES:
    p = os.path.join(PATHB, 'out', resp)
    if os.path.exists(p):
        with open(p, 'rb') as fh:
            committed_digests[cid] = sha256(fh.read())

captures = []
for cid, label, reqdir, reqname, respname in CAPTURES:
    reqpath = os.path.join(PATHB, reqdir, reqname)
    with open(reqpath, 'rb') as fh:
        reqbytes = fh.read()
    resppath = os.path.join(OUT, respname)
    started = now()
    code = sh("curl -sk -X POST '%s/api/v1/loans?command=calculateLoanSchedule' "
              "-H 'Authorization: Basic bWlmb3M6cGFzc3dvcmQ=' "
              "-H 'Fineract-Platform-TenantId: %s' -H 'Content-Type: application/json' "
              "-d @%s -o %s -w '%%{http_code}'" % (BASE, TENANT, reqpath, resppath))
    with open(resppath, 'rb') as fh:
        respbytes = fh.read()
    if code != '200':
        sys.stderr.write('CAPTURE FAILED: %s returned HTTP %s — that file is an ERROR BODY, '
                         'not a capture. Aborting; no attestation written.\n' % (cid, code))
        sys.exit(1)
    rsha = sha256(respbytes)
    captures.append({
        'id': cid, 'label': label,
        'endpoint': 'POST /loans?command=calculateLoanSchedule',
        'http_status': int(code),
        'request_file': '%s/%s' % (reqdir, reqname), 'request_sha256': sha256(reqbytes),
        'request_bytes': len(reqbytes),
        'response_file': os.path.relpath(resppath, PATHB), 'response_sha256': rsha,
        'response_bytes': len(respbytes),
        'captured_at_utc': started,
        'committed_corpus_sha256': committed_digests.get(cid),
        # None, not False, when there is no committed counterpart — absence of a prior
        # capture is not a mismatch, and must not read as one.
        'matches_committed_corpus_bytes': (None if committed_digests.get(cid) is None
                                           else committed_digests[cid] == rsha),
    })

att = {
    '_schema': 'gerege-nbfi/pathb-attestation/v1',
    '_status': 'RAW OBSERVED — admissibility attestation only. NOTHING PROMOTED to the parity '
               'vector store; DEC-1 is at revision 6 and UNRATIFIED (gate G-1).',
    '_closes': ['T22 P0-3 (attestation sidecar)', 'T22 P0-4 (fail-the-run preconditions)',
                'T22 P0-6 (production-settings tenant re-capture)'],
    'capture_set': 'pathb-B01..B04' if CAPTURE_SET == 'pathb' else 'pathb-emiloop-probes',
    'capture_path': 'Path B — running Fineract server (REST + PostgreSQL)',
    'produced_by': {'task': 'T36', 'branch': 'softhouse/T36-pathb-admissibility',
                    'generated_at_utc': now(),
                    'generator': 't36/attest.py',
                    'preconditions_script': 't36/preconditions.sh',
                    'preconditions_result': 'ALL PASS (transcript: %s)'
                                            % os.path.relpath(os.path.join(OUT, 'preconditions.txt'), PATHB)},
    'oracle': {
        'image_tag': 'fineract:latest',
        'image_id': image_id,
        'image_created': image_created,
        'image_repo_digests': json.loads(image_repodigests) if image_repodigests else None,
        'container': FIN,
        'container_started_at': container_started,
        'jar_git_commit_id': gp.get('git.commit.id'),
        'jar_git_dirty': gp.get('git.dirty'),
        'jar_build_version': gp.get('git.build.version'),
        'jar_branch': gp.get('git.branch'),
        'jvm': jvm,
        'health': 'UP (asserted by preconditions P4)',
    },
    'database': {
        'engine': 'PostgreSQL',
        'prohibited_engines_asserted_absent': ['Oracle Database', 'MySQL', 'MariaDB'],
        'version': pg_version,
        'server_version_num': pg_version_num,
        'container': DB, 'image': pg_image, 'image_id': pg_image_id,
        'driver_class': driver_class,
        'jdbc_url': jdbc_url,
        'prohibited_engine_hits_container_env': int(banned_env) if banned_env is not None else None,
        'prohibited_driver_jars_in_boot_jar': int(banned_jar) if banned_jar is not None else None,
    },
    'tenant': {
        'identifier': TENANT,
        'name': tname,
        'timezone_id': tz,
        'timezone_note': 'zone id asserted, offset never hard-coded; Asia/Ulaanbaatar is +08 with no DST',
        'schema_name': schema,
        'schema_server_port': sport,
        'schema_connection_parameters': scp,
        'schema_connection_parameters_empty': scp == '',
        'rounding_mode_ordinal': rounding_ordinal,
        'rounding_mode_name': ROUNDING_ORDINALS.get(rounding_ordinal),
        'rounding_mode_row_enabled': rm_enabled == 't',
        'rounding_mode_source_row': 'c_configuration.rounding-mode in %s' % schema,
        'rounding_mode_in_force_logline': logline,
        'rounding_mode_in_force': mode_in_force,
        'currency_MNT_decimal_places': int(mnt_dp) if mnt_dp and mnt_dp.isdigit() else None,
        'currency_MNT_enabled': mnt_enabled == '1',
    },
    'effective_math_context': {
        'precision': precision,
        'precision_source': 'MoneyHelper.PRECISION read by javap from the DEPLOYED '
                            'fineract-core jar inside the running container',
        'rounding_mode': mode_in_force,
        'rounding_mode_source': 'MoneyHelper init line emitted by THIS JVM run for THIS tenant',
        'notation': 'MathContext(%s, %s)' % (precision, mode_in_force),
        'matches_ratified_production_setting': (precision == WANT_PRECISION
                                                and rounding_ordinal == WANT_ROUNDING_ORDINAL
                                                and mode_in_force == 'HALF_UP'),
        'ratified_production_setting': 'MathContext(19, HALF_UP)  [CLAUDE.md — ratified tenant parameters]',
    },
    'effective_mode_canary': {
        'purpose': 'behavioural proof of the rounding mode actually in force: period-1 interest is an '
                   'exact half-cent tie (1,162,502.50 x 0.018 = 20,925.045)',
        'request_file': 't22-audit/req/calc-pmode2-gerege.json',
        'request_sha256': sha256(canary_bytes),
        'response_file': os.path.relpath(canary_out, PATHB),
        'http_status': int(canary_code) if canary_code else None,
        'observed_period1_interest': canary_p1,
        'expected_under_HALF_UP': '20925.05',
        'expected_under_HALF_EVEN': '20925.04',
        'verdict': 'HALF_UP confirmed behaviourally' if canary_p1 == '20925.05' else
                   'MODE NOT CONFIRMED — see observed value',
    },
    'products_as_persisted': products,
    'captures': captures,
    'does_not_license': [
        'promotion to the parity vector store (DEC-1 unratified, gate G-1)',
        'any claim about cutover, which is a hard user gate',
        'any claim about behaviour not exercised here: multi-disbursement, charges, down payments, '
        'repayments, delinquency, COB or anything clock-sensitive',
    ],
    'notes': notes,
}

path = os.path.join(OUT, 'attestation.json')
with open(path, 'w') as fh:
    json.dump(att, fh, indent=1, sort_keys=False)
    fh.write('\n')
print('wrote %s' % path)
print('effective MathContext: %s   matches ratified: %s'
      % (att['effective_math_context']['notation'],
         att['effective_math_context']['matches_ratified_production_setting']))
for c in captures:
    print('  %s  HTTP %s  sha256 %s  matches committed corpus: %s'
          % (c['id'], c['http_status'], c['response_sha256'][:16], c['matches_committed_corpus_bytes']))
if notes:
    print('NOTES / UNREAD FIELDS:')
    for n in notes:
        print('  - %s' % n)
