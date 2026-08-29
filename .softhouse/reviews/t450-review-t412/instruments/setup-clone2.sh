#!/bin/bash
set -e
rm -rf /tmp/t450/clone2 /tmp/t450/remote2.git
git clone -q --local /tmp/t450/clone /tmp/t450/clone2
cd /tmp/t450/clone2
git checkout -q -B drive origin/drive
bash .softhouse/hooks/install-driver-push-gate.sh
git init -q --bare /tmp/t450/remote2.git
git remote add bare /tmp/t450/remote2.git
# seed the FULL attestation for the base tree -- it is the same tree bar-attest graded
# EXIT 0 / probe up / VERDICT PASS in clone1 (transcript /tmp/t450/attest-base.log).
mkdir -p .git/softhouse-driver-gate
cp /tmp/t450/clone/.git/softhouse-driver-gate/attest.tsv .git/softhouse-driver-gate/attest.tsv
grep -c FULL .git/softhouse-driver-gate/attest.tsv
git rev-parse HEAD
git rev-parse HEAD^{tree}
