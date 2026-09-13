#!/bin/bash
# =============================================================================
# dsbalance.sh -- the DeepSeek balance and the runway it buys, BEFORE a dispatch.
#
# WHY. On 2026-09-12 23:41 the balance ran out; the next run died on its first call
# ("Insufficient Balance") and the loop sat idle for 9.5 hours. A top-up is Buyan's
# decision (it spends money), so the driver must see the runway coming, not after.
#
# Reads the key OpenHands already uses (never prints it) and asks DeepSeek's own
# read-only balance endpoint. Prints the balance, the runway at the measured pace,
# and exits 1 when the balance cannot fund one more run (so a dispatch can gate on it).
#
#   bash .softhouse/briefs/tools/dsbalance.sh [usd-per-day] [usd-per-run]
# Defaults are the 2026-09-13 daily review's measurements: $10/day at two slots, $0.38/run.
# =============================================================================
set -u
PER_DAY=${1:-10}
PER_RUN=${2:-0.38}
KEY=$(python3 - <<'EOF'
import json,glob,os
for f in glob.glob(os.path.expanduser('~/.openhands/*.json'))+glob.glob(os.path.expanduser('~/.openhands/**/*settings*.json'),recursive=True):
    try: j=json.load(open(f))
    except Exception: continue
    def walk(o):
        if isinstance(o,dict):
            for k,v in o.items():
                if 'api_key' in k.lower() and isinstance(v,str) and v.startswith('sk-'): print(v); raise SystemExit
                walk(v)
        elif isinstance(o,list):
            for v in o: walk(v)
    walk(j)
EOF
)
[ -n "$KEY" ] || { echo "dsbalance: no DeepSeek key found in ~/.openhands settings"; exit 2; }
curl -s --max-time 20 -H "Authorization: Bearer $KEY" https://api.deepseek.com/user/balance |
  python3 -c "
import json,sys
per_day,per_run=float(sys.argv[1]),float(sys.argv[2])
try: j=json.load(sys.stdin)
except Exception: print('dsbalance: no answer from the balance endpoint'); sys.exit(2)
usd=sum(float(b.get('total_balance') or 0) for b in j.get('balance_infos',[]) if b.get('currency')=='USD')
ok=j.get('is_available') and usd>=per_run
print('DeepSeek balance \$%.2f  available=%s  runway ~%.1f days at \$%.0f/day  (~%d runs)'%(usd,j.get('is_available'),usd/per_day if per_day else 0,per_day,int(usd/per_run) if per_run else 0))
if not ok: print('dsbalance: CANNOT fund another run -- a top-up is a user gate (Buyan); do not switch models'); sys.exit(1)
if usd<2*per_day: print('dsbalance: LOW -- under two days of runway; tell Buyan')
" "$PER_DAY" "$PER_RUN"
