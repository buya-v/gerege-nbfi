#!/bin/sh
# A2-26 / group A -- G-10 option (c) PRODUCT ADMISSIBILITY, OBSERVED.
#
# G-10(c) binds A2-15: promote vectors ONLY from products whose mappings the reference
# oracle would still accept today. A2-7 measured why inference is not allowed here --
# GL account 2 was retyped ASSET->INCOME underneath live product mappings, the oracle
# serves those mappings without complaint, and `GET /loanproducts/{id}` returns
# {id, name, glCode} per slot with NO type, so THE READ-BACK STRUCTURALLY CANNOT REVEAL
# THE INCONSISTENCY.
#
# The only test that can decide it is to RE-SEND the mapping and record what comes back.
# That is what this script does, for every product that carries an accounting mapping in
# acc_product_mapping, not only the ones a previous task happened to mention.
#
# The bodies are byte-identical to the ones the oracle originally accepted apart from
# `shortName` and `name`, which MUST change or a duplicate-name refusal would mask the
# verdict. mkreq-a2-26.sh verify proves that is the only difference.
#
# SIDE EFFECT, DISCLOSED: a body the oracle still accepts CREATES A NEW LOAN PRODUCT.
# That is additive (this rig has been additive-only throughout) and it is unavoidable --
# a re-admission probe that did not actually re-admit would prove nothing. The new
# product ids are in the .json bodies recorded here.
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)
C="$DIR/cap8.sh"

sh "$DIR/mkreq-a2-26.sh" verify

# State of the world at probe time, so the verdicts below are interpretable.
sh "$C" A2-300-glaccount2-classification-today   GET /glaccounts/2                || exit 1
sh "$C" A2-301-glaccount16-classification-today  GET /glaccounts/16               || exit 1
sh "$C" A2-302-loanproduct22-readback-today      GET /loanproducts/22             || exit 1
sh "$C" A2-303-loanproduct46-readback-today      GET /loanproducts/46             || exit 1

# The re-admission probes themselves.
sh "$C" A2-310-readmit-product22 POST /loanproducts req/a2-26-admit-p22.json || exit 1
sh "$C" A2-311-readmit-product23 POST /loanproducts req/a2-26-admit-p23.json || exit 1
sh "$C" A2-312-readmit-product24 POST /loanproducts req/a2-26-admit-p24.json || exit 1
sh "$C" A2-313-readmit-product27 POST /loanproducts req/a2-26-admit-p27.json || exit 1
sh "$C" A2-314-readmit-product28 POST /loanproducts req/a2-26-admit-p28.json || exit 1
sh "$C" A2-315-readmit-product46 POST /loanproducts req/a2-26-admit-p46.json || exit 1
