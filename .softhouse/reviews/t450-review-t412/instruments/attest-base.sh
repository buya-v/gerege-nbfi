cd /tmp/t450/clone || exit 9
S=$(date +%s)
bash .softhouse/hooks/bar-attest.sh HEAD > /tmp/t450/attest-base.log 2>&1
RC=$?
E=$(date +%s)
echo "RC=$RC WALL=$((E-S))" >> /tmp/t450/attest-base.log
echo "RC=$RC WALL=$((E-S))" > /tmp/t450/attest-base-done.txt
