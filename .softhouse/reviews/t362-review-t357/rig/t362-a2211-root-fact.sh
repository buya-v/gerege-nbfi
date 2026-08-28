#!/bin/bash
# Root derived from $0, never hard-coded: this file sits four levels below the
# checkout root, under .softhouse/reviews/t362-review-t357/rig.
W="$(cd "$(dirname "$0")/../../../.." && pwd)"
F="$W/.softhouse/capture/tierA-a2/out/A2-211-read-product-nine-mandatory.json"
echo "file: $F"
wc -c < "$F"
shasum -a 256 "$F"
for k in paymentChannelToFundSourceMappings feeToIncomeAccountMappings penaltyToIncomeAccountMappings null; do
  printf '  %-40s occurrences=%s\n' "$k" "$(grep -o -- "$k" "$F" | wc -l | tr -d ' ')"
done
python3 -c "
import json,sys
d=json.load(open('$F'))
print('  keys whose value is None:',[k for k,v in d.items() if v is None])
print('  top-level key count:',len(d))
print('  keys matching Account/Mapping:',sorted(k for k in d if 'ccount' in k or 'apping' in k))
"
