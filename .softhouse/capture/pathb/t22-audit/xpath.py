"""T22 audit: cross-path check. Compare pass-3 Path A capture P-MNT-1M2 against
Path B B-01, using exact decimal (never float)."""
import json
import re
from decimal import Decimal

A = '/Users/buv/gerege-nbfi/.claude/worktrees/agent-acea9b5e2faae26c3/.softhouse/capture/out/capture-prod-raw.json'
B = '/Users/buv/gerege-nbfi/.claude/worktrees/agent-acea9b5e2faae26c3/.softhouse/capture/pathb/out/B-01-baseline-raw.json'

pa = json.load(open(A))
cap = [c for c in pa['captures'] if c['id'] == 'P-MNT-1M2'][0]
obs = cap['observed']
print('observed keys:', sorted(obs.keys()))
print(json.dumps(obs, indent=1)[:4000])
