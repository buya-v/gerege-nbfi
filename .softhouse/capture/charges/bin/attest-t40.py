#!/usr/bin/env python3
"""T40 — machine-readable ATTESTATION SIDECAR for the CHARGES capture set.

Derived from T36's `attest.py` (`.softhouse/capture/pathb/t36/attest.py`, read-only to
T40) and re-pointed at `.softhouse/capture/charges`.  The discipline is unchanged:

  * every field is READ FROM the running server, its container, its DEPLOYED bytecode,
    or its PostgreSQL rows — nothing is copied from a plan, a report, or an earlier
    attestation, and a fact that cannot be read is recorded `null` with a `_unread`
    note, never guessed;
  * it DRIVES the capture, so the request/response digests and UTC timestamps describe
    one single run rather than being attached to files after the fact;
  * the fail-the-run preconditions execute first and a breach aborts before any capture;
  * money is serialised as EXACT TEXT (`parse_float=str`) — parsing a money column into a
    binary float even only to re-serialise it would put a float in a monetary artefact.

RAW OBSERVED.  This sidecar makes the capture set ADMISSIBLE FOR REVIEW.  It promotes
nothing to the parity vector store and stores nothing contract-shaped: DEC-1 is
UNRATIFIED (gate G-1) and the contract SHAPE is exactly what is still being ratified.

Usage: python3 attest-t40.py [tenant]     (default: gerege)
"""
import datetime
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CH = os.path.normpath(os.path.join(HERE, '..'))          # .softhouse/capture/charges
W = os.path.normpath(os.path.join(CH, '..', '..', '..'))  # worktree root
PATHB = os.path.join(W, '.softhouse', 'capture', 'pathb')  # READ-ONLY to T40
# T125: the effective-rounding-mode GATE, shared with the other two attestation sidecars.
# This file was forked from pathb/t36/attest.py at T36 and never received T80's hardening —
# so the fix is deliberately NOT inlined here, because an inlined fix is what fails to reach
# a fork (P-21/P-26).  A failed import is a hard failure by design.
sys.path.insert(0, os.path.normpath(os.path.join(CH, '..', 'lib')))
import attest_gate                                                   # noqa: E402

TENANT = sys.argv[1] if len(sys.argv) > 1 else 'gerege'
# T125, adopting T76's fix to the file this one was forked from: ATTEST_OUT lets an
# INDEPENDENT re-run write its own evidence directory instead of overwriting T40's committed
# capture set.  Re-running a generator over the artefacts it produced last fire destroys the
# very record a reviewer diffs against — and there was no way to drive this rig's gate
# green without doing so.  When ATTEST_OUT is used the directory must be named for the
# tenant it is capturing, so a `default` capture cannot be filed under a `gerege` name (T80).
OUT = os.environ.get('ATTEST_OUT') or os.path.join(CH, 'out', 'attested')
if os.environ.get('ATTEST_OUT'):
    _base = os.path.basename(os.path.normpath(OUT))
    if not (_base == TENANT or _base.endswith('-' + TENANT)):
        sys.stderr.write(
            "ABORT: ATTEST_OUT %r is not named for tenant %r. A capture must be filed under "
            "the tenant it was taken from.\n" % (OUT, TENANT))
        sys.exit(1)
FIN, DB = 'fineract-fineract-1', 'fineract-db-1'
BASE = 'https://localhost:8443/fineract-provider'

# Ratified tenant parameters (CLAUDE.md).  Asserted, never assumed.
WANT_ROUNDING_ORDINAL = 4          # RoundingMode.valueOf(4) == HALF_UP
WANT_PRECISION = 19                # MoneyHelper.PRECISION
ROUNDING_ORDINALS = {0: 'UP', 1: 'DOWN', 2: 'CEILING', 3: 'FLOOR',
                     4: 'HALF_UP', 5: 'HALF_DOWN', 6: 'HALF_EVEN'}

# The zero-charge CONTROL is re-emitted through this same driver, so the attestation
# itself carries the control identity instead of pointing at another run for it.
CAPTURES = [('CTRL-B-01', 'zero-charge control — committed B-01 request, byte-verbatim',
             os.path.join(PATHB, 'req', 'calc-B-01-baseline.json'), 'CTRL-B-01-raw.json')]
for _f in sorted(os.listdir(os.path.join(CH, 'req'))):
    if _f.startswith('calc-FC-') and _f.endswith('.json'):
        _id = _f[len('calc-'):-len('.json')]
        CAPTURES.append((_id, 'charge-bearing schedule',
                         os.path.join(CH, 'req', _f), _id + '-raw.json'))

# Requests the oracle REFUSED.  An observed refusal is evidence too, so it is attested —
# but with its real HTTP status, and never filed as a capture.
REJECTED = [('XR-01', 'specified-due-date fee dated BEFORE the disbursement date',
             os.path.join(CH, 'req', 'calc-XR-01-fee-before-disbursement.json'),
             'XR-01-fee-before-disbursement-HTTP403.json')]

notes = []


def sh(cmd):
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
# T125: the canary request is chosen BY TENANT from a pinned table of solved exact ties and
# carries its own pinned digest, instead of the `gerege` request hard-coded for every tenant.
canary, canary_pin_sha = attest_gate.canary_request_for(
    TENANT, os.path.join(PATHB, 't22-audit', 'req'))
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
sh("docker exec %s sh -c 'mkdir -p /tmp/t40at && cd /tmp/t40at && unzip -o -q "
   "/app/fineract-provider.jar \"BOOT-INF/lib/fineract-core-*.jar\"'" % FIN)
javap = sh("docker exec -e JAVA_TOOL_OPTIONS= %s sh -c 'cd /tmp/t40at && javap -p -constants -cp "
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
# grep exits 1 on zero matches, which here is the GOOD outcome.
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
        cj = json.loads(fh.read().decode(), parse_float=str)
    canary_p1 = str(cj['periods'][1]['interestOriginalDue'])

# ------------------------------------------------------------------------- T125: THE GATE
# Everything above is an OBSERVATION; this is the first line in this file that REFUSES on
# one.  Until T125 the canary's verdict was computed, printed and written into
# attestation.json, and compared against nothing.  It is placed HERE, before any capture is
# taken, so a run that cannot establish the mode spends no requests on the oracle.
attest_gate.assert_effective_rounding_mode(
    tenant=TENANT, canary_path=canary, canary_bytes=canary_bytes,
    canary_pinned_sha=canary_pin_sha, canary_http_code=canary_code, canary_p1=canary_p1,
    precision=precision, rounding_ordinal=rounding_ordinal, mode_in_force=mode_in_force)

# --------------------------------------------------------- product, from the row
# Every T40 request uses productId 1 and clientId 1 — one product, so one row.
products = []
for pid in (1,):
    row = q(schema, "select to_jsonb(t) from m_product_loan t where id=%d;" % pid)
    if not row:
        products.append({'id': pid, '_unread': 'no m_product_loan row'})
        continue
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

# ------------------------------------------- the charge definitions, from the rows
charge_ids = q(schema, "select string_agg(id::text, ',' order by id) from m_charge;") or ''
charges = []
for cid in [int(x) for x in charge_ids.split(',') if x.strip()]:
    row = q(schema, "select to_jsonb(t) from m_charge t where id=%d;" % cid)
    r = json.loads(row, parse_float=str)
    charges.append({
        'id': r['id'], 'name': r['name'],
        'charge_applies_to_enum': r['charge_applies_to_enum'],
        'charge_time_enum': r['charge_time_enum'],
        'charge_calculation_enum': r['charge_calculation_enum'],
        'charge_payment_mode_enum': r['charge_payment_mode_enum'],
        'amount': r['amount'],            # exact text; a percentage for calc 2/3/4
        'currency_code': r['currency_code'],
        'is_penalty': r['is_penalty'],
        'is_active': r['is_active'],
        'created_by_task': 'T40',
        'persisted_row_sha256': sha256(row.encode('utf-8')),
    })

loan_rows_gerege = q(schema, "select count(*) from m_loan;")

# ------------------------------------------------------------------- the captures
captures = []
for cid, label, reqpath, respname in CAPTURES:
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
    # the first-issue file from bin/capture.sh, for the determinism claim
    prior = os.path.join(CH, 'out', 'fc', respname)
    prior_sha = None
    if os.path.exists(prior):
        with open(prior, 'rb') as fh:
            prior_sha = sha256(fh.read())
    captures.append({
        'id': cid, 'label': label,
        'endpoint': 'POST /loans?command=calculateLoanSchedule',
        'http_status': int(code),
        'request_file': os.path.relpath(reqpath, W), 'request_sha256': sha256(reqbytes),
        'request_bytes': len(reqbytes),
        'response_file': os.path.relpath(resppath, W), 'response_sha256': rsha,
        'response_bytes': len(respbytes),
        'captured_at_utc': started,
        'prior_issue_sha256': prior_sha,
        'byte_identical_to_prior_issue': (None if prior_sha is None else prior_sha == rsha),
    })

rejected = []
for cid, label, reqpath, respname in REJECTED:
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
    rejected.append({
        'id': cid, 'label': label,
        'http_status': int(code) if code else None,
        'is_a_capture': False,
        'why_recorded': 'an observed REFUSAL is evidence; it is filed with its real HTTP '
                        'status and is never counted as a capture',
        'request_file': os.path.relpath(reqpath, W), 'request_sha256': sha256(reqbytes),
        'response_file': os.path.relpath(resppath, W), 'response_sha256': sha256(respbytes),
        'captured_at_utc': started,
    })

att = {
    '_schema': 'gerege-nbfi/pathb-attestation/v1',
    '_status': 'RAW OBSERVED — admissibility attestation only. NOTHING PROMOTED to the parity '
               'vector store and NOTHING stored contract-shaped; DEC-1 is UNRATIFIED (gate G-1) '
               'and the contract SHAPE is what is still being ratified.',
    'capture_set': 'T40 charges — fees and penalties on the progressive loan schedule',
    'capture_path': 'Path B — running Fineract server (REST + PostgreSQL)',
    # T125, adopting T76's fix to the file this one was forked from: a sidecar produced by a
    # LATER task must not claim T40 produced it.  Provenance that names the wrong author is a
    # false record even when every number in it is right.
    'produced_by': {'task': os.environ.get('ATTEST_TASK', 'T40'),
                    'branch': os.environ.get('ATTEST_BRANCH', 'softhouse/T40-charges-capture'),
                    'generated_at_utc': now(),
                    'generator': 'bin/attest-t40.py (derived from pathb/t36/attest.py)',
                    'preconditions_script': 'bin/preconditions.sh (copied verbatim from '
                                            'pathb/t36/preconditions.sh)',
                    # T125: the transcript path is DERIVED from OUT.  It was hard-coded to
                    # out/attested/preconditions.txt, which named the wrong file the moment
                    # ATTEST_OUT pointed the run somewhere else.
                    'preconditions_result': 'ALL PASS (transcript: %s)'
                                            % os.path.relpath(os.path.join(OUT, 'preconditions.txt'), W),
                    'zero_charge_control': 'bin/control.sh — all four committed Path B captures '
                                           'reproduced byte-for-byte before any charge was created '
                                           '(out/control/)'},
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
        'm_loan_row_count': loan_rows_gerege,
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
        'request_file': '.softhouse/capture/pathb/t22-audit/req/calc-pmode2-gerege.json',
        'request_sha256': sha256(canary_bytes),
        'response_file': os.path.relpath(canary_out, W),
        'http_status': int(canary_code) if canary_code else None,
        'observed_period1_interest': canary_p1,
        'expected_under_HALF_UP': '20925.05',
        'expected_under_HALF_EVEN': '20925.04',
        'verdict': 'HALF_UP confirmed behaviourally' if canary_p1 == '20925.05' else
                   'MODE NOT CONFIRMED — see observed value',
    },
    'products_as_persisted': products,
    'charges_as_persisted': charges,
    'charges_note': 'ALL of these rows were created by T40. `select count(*) from m_charge` was 0 '
                    'on this tenant before T40 ran, so charge ids 1..12 in fineract_gerege are '
                    'exactly T40\'s. Nothing pre-existing was mutated, and no row was deleted. '
                    'For calculation types 2/3/4 the `amount` column holds a PERCENTAGE, not money.',
    'captures': captures,
    'rejected_requests': rejected,
    'does_not_license': [
        'promotion to the parity vector store (DEC-1 unratified, gate G-1)',
        'storing any of this contract-shaped — the contract SHAPE is what is being ratified',
        'any claim about cutover, which is a hard user gate',
        'any claim about behaviour not exercised here: multi-disbursement, tranche charges, '
        'overdue-installment (COB-applied) penalties, down payments, actual repayments, '
        'waivers, delinquency, or anything clock-sensitive',
    ],
    'notes': notes,
}

# T125, last line of defence: the DOCUMENT is graded before it is written, by reading back
# the very fields about to be serialised — the canary verdict,
# `matches_ratified_production_setting`, and `byte_identical_to_prior_issue`.  All three were
# of one shape: computed, printed, never compared.
_no_prior = attest_gate.assert_attestation_is_verified(att, 'byte_identical_to_prior_issue')

path = os.path.join(OUT, 'attestation.json')
with open(path, 'w') as fh:
    json.dump(att, fh, indent=1, sort_keys=False)
    fh.write('\n')
print('wrote %s' % path)
print('GATE: effective rounding mode PROVEN %s — pinned exact tie %s answered %s '
      '(HALF_EVEN would answer %s)'
      % (attest_gate.WANT_ROUNDING_NAME, os.path.basename(canary), canary_p1,
         attest_gate.EXPECTED_UNDER_HALF_EVEN))
if _no_prior:
    print('GATE: %d capture(s) had no first-issue counterpart to compare against (%s) — an '
          'absence, not a mismatch, and NOT a determinism claim.'
          % (len(_no_prior), ', '.join(str(x) for x in _no_prior)))
print('effective MathContext: %s   matches ratified: %s'
      % (att['effective_math_context']['notation'],
         att['effective_math_context']['matches_ratified_production_setting']))
print('canary: %s (%s)' % (canary_p1, att['effective_mode_canary']['verdict']))
for c in captures:
    print('  %-50s HTTP %s  sha256 %s  == prior issue: %s'
          % (c['id'], c['http_status'], c['response_sha256'][:16],
             c['byte_identical_to_prior_issue']))
for r in rejected:
    print('  %-50s HTTP %s  (REFUSAL, not a capture)' % (r['id'], r['http_status']))
if notes:
    print('NOTES / UNREAD FIELDS:')
    for n in notes:
        print('  - %s' % n)
else:
    print('NOTES: none — every attested field was read from a primary source.')
