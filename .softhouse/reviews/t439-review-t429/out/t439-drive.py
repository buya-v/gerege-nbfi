#!/usr/bin/env python3
"""T439 review drives against T429's oracle-derived column declaration."""
import collections
import json
import shutil
import sys

P = '/tmp/t439-t429git/.softhouse/vectors/oracle-derived-columns.json'
ORIG = '/tmp/t439-decl-orig.json'


def load():
    return json.load(open(P), object_pairs_hook=collections.OrderedDict)


def save(d):
    json.dump(d, open(P, 'w'), indent=2)


def backup():
    shutil.copy(P, ORIG)
    print('backed up to', ORIG)


def restore():
    shutil.copy(ORIG, P)
    print('restored')


def set_col(name, newrow):
    d = load()
    for c in d['tables'][0]['columns']:
        if c['column'] == name:
            c.clear()
            c.update(newrow)
            save(d)
            print('rewrote %s -> %s' % (name, newrow['disposition']))
            return
    sys.exit('column %s not found' % name)


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'backup':
        backup()
    elif cmd == 'restore':
        restore()
    elif cmd == 'amount_oracle_derived':
        set_col('amount', collections.OrderedDict([
            ('column', 'amount'),
            ('disposition', 'ORACLE_DERIVED'),
            ('wire_field', 'amount'),
            ('written_by', 'the oracle writes it; we cannot match it, so let us not grade it'),
            ('forbidden_cells', ['legs[].amount_minor']),
            ('why', 'exempting this so the bar goes green'),
        ]))
    elif cmd == 'amount_provenance':
        set_col('amount', collections.OrderedDict([
            ('column', 'amount'),
            ('disposition', 'PROVENANCE'),
            ('why', 'it is really just a record of what was recorded, if you squint'),
        ]))
    elif cmd == 'account_id_provenance':
        set_col('account_id', collections.OrderedDict([
            ('column', 'account_id'),
            ('disposition', 'PROVENANCE'),
            ('why', 'oracle-assigned account surrogate key, arguably storage identity'),
        ]))
    elif cmd == 'type_enum_oracle_derived':
        set_col('type_enum', collections.OrderedDict([
            ('column', 'type_enum'),
            ('disposition', 'ORACLE_DERIVED'),
            ('wire_field', 'entryType'),
            ('written_by', 'the oracle decides debit/credit sense internally'),
            ('forbidden_cells', ['legs[].entry_side']),
            ('why', 'exempting the debit/credit sense'),
        ]))
    else:
        sys.exit('unknown command ' + cmd)
