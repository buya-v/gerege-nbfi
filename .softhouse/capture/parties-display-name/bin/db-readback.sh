#!/usr/bin/env bash
# db-readback.sh — read-only m_client corroboration for OH-NAMECAP-AW.
#
# Sourced by each step script. Reads the SAME seven columns the brief names, from
# the gerege tenant database on the gerege-oracle-db container (never fineract-db-1).
# One form is written:
#   * <name>-m-client.json — a JSON array (row_to_json), the citable record.
# The brief is explicit that a psql dump cannot be cited; so no plain-text dump is
# produced at all, only JSON.
#
# Every statement here is a SELECT. Nothing is inserted.

NC_DB_CONTAINER='gerege-oracle-db'
NC_DB_NAME='fineract_gerege'
NC_DB_USER='postgres'

# nc_readback OUTNAME IDS
nc_readback() {
    local name="${1:?}" ids="${2:?}"
    docker exec "$NC_DB_CONTAINER" psql -U "$NC_DB_USER" -d "$NC_DB_NAME" -At -c \
        "SELECT json_agg(row_to_json(t)) FROM (SELECT id, firstname, middlename, lastname, fullname, display_name, legal_form_enum FROM m_client WHERE id IN ($ids) ORDER BY id) t;" \
        | python3 -c 'import json,sys; d=json.load(sys.stdin); json.dump(d, sys.stdout, ensure_ascii=False, indent=2); sys.stdout.write("\n")' \
        > "$OHS_OUT/$name-m-client.json"
}
