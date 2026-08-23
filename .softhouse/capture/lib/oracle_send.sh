# shellcheck shell=sh
# oracle_send.sh -- capture one oracle exchange and derive its sidecar FROM THE WIRE.
#
# T250, from T245's F-2.  This is the successor SHAPE for the tierA-a2 `cap*.sh`
# chain (cap.sh -> cap8.sh -> cap9.sh -> cap10.sh), all four of which send the
# tenant as `-H "$T"` and then write the sidecar line as a hard-coded literal
# `echo "Fineract-Platform-TenantId: gerege"`.  Measured population for that
# class is in `.softhouse/capture/t250-tenant-attestation/`.
#
# THE ONE RULE THIS LIBRARY EXISTS TO ENFORCE
#   Nothing writes an attestation line.  The attestation is DERIVED, by
#   `wire_attestation.py`, from curl's own `--trace-ascii` record of the bytes it
#   actually put on the wire.  There is no code path in which a value can be
#   attested without having been sent, because no value is ever typed twice.
#
# WHY NOT `echo "$T"` (T245's proposed item 2).  `$T` is what the author believed
# would be sent.  Curl's argument grammar has at least two shapes where that is
# false -- a later `-H` for the same header wins, and `-H "Name:"` REMOVES the
# header rather than sending an empty one.  Both are driven red under
# `.softhouse/capture/t250-tenant-attestation/`; `echo "$T"` attests wrongly in
# both and this library attests correctly in both.
#
# T114 COMPLIANCE.  This is a NEW file.  `cap.sh`, `cap8.sh`, `cap9.sh` and
# `cap10.sh` produced committed evidence, are pinned byte-for-byte by
# `.softhouse/capture/tierA-a2/MANIFEST.sha256`, and are NOT touched by T250 --
# not their code and not the sidecars they wrote.  A historical sidecar rewritten
# now to look derived would be an invented record replacing an honest weak one.
#
# NO PIPES, AND DELIBERATELY NO `set -o pipefail` HERE.  This file is SOURCED;
# setting shell options in a sourced library silently mutates the caller's shell
# and is its own fail-open.  Instead the library contains no pipeline at all and
# checks every command's exit status explicitly, so it is correct under `sh`,
# `bash`, `dash`, `zsh` and `ksh` and under any combination of -e/-u/pipefail.
#
# T274.  BOTH LEGS ARE NOW ATTESTED.  T250 derived the REQUEST from the trace and
# left the RESPONSE -- the half a golden vector is actually graded on -- entirely
# unattested, with that limit stated nowhere (T261 F-6: swapping NAME.json for
# another capture's response verified clean).  `derive` now also writes
# NAME.resphdr from the trace's `<= Recv header` blocks and puts the response
# digest, byte count, final status line and a cross-check of NAME.status into the
# sidecar.  Sidecars written before T274 carry no `attestation-schema:` line, are
# schema 1, are NOT retro-edited, and remain verifiable as request-only -- but
# presenting a response artefact against one is REFUSED, so deleting the schema
# line does not buy a pass.
#
# CALLER CONTRACT
#   OS_BASE     base URL, e.g. https://localhost:8443/fineract-provider/api/v1
#   OS_OUTDIR   directory for
#               out/NAME.{json,status,http,reqhdr,resphdr,req,req.sha256}
#   OS_HEADERS  newline-separated request headers, verbatim as they go to curl
#   oracle_send NAME METHOD RPATH [BODYFILE]
#
# Semantics carried over verbatim from the cap*.sh chain, because they are right:
#   * a non-2xx is an OBSERVATION, recorded as data in out/NAME.status, never an
#     error -- in slice A2 a refusal is the thing being captured;
#   * a TRANSPORT failure is an error: NOTHING is written under out/, and any
#     pre-existing artefact is NAMED rather than overwritten, so a failed retry
#     cannot stamp a fresh timestamp on stale bytes (A2-5's fix for D-2);
#   * `--data-binary`, never `-d`: `-d` strips newlines out of a file body, so
#     the wire bytes would not be the file bytes (T163's measurement);
#   * the body is snapshotted BEFORE the send and moved into place only AFTER it
#     completed, so out/NAME.req is exactly what out/NAME.json answers;
#   * the scratch-dir trap covers QUIT as well as EXIT HUP INT TERM (T216).

oracle_send() {
    os_name=${1-}
    os_method=${2-}
    os_rpath=${3-}
    os_body=${4-}

    if [ -z "$os_name" ] || [ -z "$os_method" ] || [ -z "$os_rpath" ]; then
        echo "usage: oracle_send NAME METHOD RPATH [BODYFILE]" >&2
        return 2
    fi
    if [ -z "${OS_BASE-}" ] || [ -z "${OS_OUTDIR-}" ] || [ -z "${OS_HEADERS-}" ]; then
        echo "REFUSING: OS_BASE, OS_OUTDIR and OS_HEADERS must all be set." >&2
        echo "  An unset OS_HEADERS would send an unauthenticated, tenant-less request" >&2
        echo "  and the sidecar would faithfully record that -- but the caller plainly" >&2
        echo "  did not mean to, so this refuses rather than capturing something else." >&2
        return 2
    fi
    if [ ! -d "$OS_OUTDIR" ]; then
        echo "REFUSING: OS_OUTDIR does not exist: $OS_OUTDIR" >&2
        return 2
    fi

    os_lib=${OS_LIB_DIR:-}
    if [ -z "$os_lib" ]; then
        echo "REFUSING: OS_LIB_DIR is unset; cannot locate wire_attestation.py." >&2
        return 2
    fi
    if [ ! -f "$os_lib/wire_attestation.py" ]; then
        echo "REFUSING: $os_lib/wire_attestation.py not found -- without it no" >&2
        echo "  attestation can be DERIVED, and this library will not fall back to" >&2
        echo "  writing one from what it believes it sent." >&2
        return 2
    fi

    os_out="$OS_OUTDIR/$os_name.json"
    os_status="$OS_OUTDIR/$os_name.status"
    os_http="$OS_OUTDIR/$os_name.http"
    os_reqhdr="$OS_OUTDIR/$os_name.reqhdr"
    os_resphdr="$OS_OUTDIR/$os_name.resphdr"
    os_req="$OS_OUTDIR/$os_name.req"
    os_reqsha="$OS_OUTDIR/$os_name.req.sha256"

    if [ -n "$os_body" ] && [ ! -f "$os_body" ]; then
        echo "REFUSING: body file $os_body does not exist -- nothing to send and" >&2
        echo "  nothing to record." >&2
        return 2
    fi

    os_tmpd=$(mktemp -d "${TMPDIR:-/tmp}/oracle_send.XXXXXX") || return 2
    trap 'rm -rf "$os_tmpd"' EXIT HUP INT TERM QUIT
    os_tmpbody="$os_tmpd/body"
    os_tmpreq="$os_tmpd/req"
    os_trace="$os_tmpd/trace"

    if [ -n "$os_body" ]; then
        cp "$os_body" "$os_tmpreq" || { rm -rf "$os_tmpd"; trap - EXIT; return 2; }
    fi

    os_ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)

    # Build the curl argument vector.  `set --` is the POSIX stand-in for an
    # array; the headers go on VERBATIM, exactly as the caller wrote them, so
    # whatever curl does with them is what the trace will show.
    os_saved_ifs=$IFS
    set -- -sk -X "$os_method" "$OS_BASE$os_rpath" --trace-ascii "$os_trace" \
           -o "$os_tmpbody" -w '%{http_code}'
    IFS='
'
    for os_h in $OS_HEADERS; do
        [ -n "$os_h" ] || continue
        set -- "$@" -H "$os_h"
    done
    IFS=$os_saved_ifs
    if [ -n "$os_body" ]; then
        set -- "$@" --data-binary @"$os_tmpreq"
    fi

    os_rc=0
    os_code=$(curl "$@") || os_rc=$?

    if [ "$os_rc" -ne 0 ]; then
        echo "TRANSPORT FAILURE (curl rc=$os_rc) for $os_name -- NO OBSERVATION WAS MADE." >&2
        echo "  NOTHING was written under $OS_OUTDIR for $os_name by this fire." >&2
        for os_f in "$os_http" "$os_out" "$os_status" "$os_reqhdr" "$os_resphdr" \
                    "$os_req" "$os_reqsha"; do
            if [ -e "$os_f" ]; then
                echo "  PRE-EXISTING from an EARLIER fire, left intact, NOT this fire's output: ${os_f##*/}" >&2
            fi
        done
        if [ -e "$os_http" ]; then
            echo "  that earlier artefact's own captured-at-utc: $(sed -n 's/^captured-at-utc: //p' "$os_http")" >&2
        fi
        rm -rf "$os_tmpd"
        trap - EXIT
        return 1
    fi

    # The exchange completed.  Commit the body artefact FIRST, because the
    # derivation cross-checks the sent Content-Length against its byte count and
    # must refuse if the body changed between snapshot and send.
    if [ -n "$os_body" ]; then
        if command -v shasum >/dev/null 2>&1; then
            os_sha=$(shasum -a 256 "$os_tmpreq") || { rm -rf "$os_tmpd"; trap - EXIT; return 2; }
        else
            os_sha=$(sha256sum "$os_tmpreq") || { rm -rf "$os_tmpd"; trap - EXIT; return 2; }
        fi
        os_sha=${os_sha%% *}
        mv "$os_tmpreq" "$os_req" || { rm -rf "$os_tmpd"; trap - EXIT; return 2; }
        printf '%s  %s\n' "$os_sha" "$os_name.req" > "$os_reqsha"
        os_derive_body="$os_req"
    else
        os_derive_body=""
    fi

    # T274.  The RESPONSE is committed BEFORE the derivation, because the
    # derivation now attests it: its digest, its byte count, its status line and
    # the `.status` file are part of the sidecar (T261 F-6 -- T250 attested the
    # REQUEST only, and a golden vector is graded on the oracle's ANSWER).  The
    # ordering invariant T250 set is preserved by the failure path below, which
    # removes the response again: an observation whose request cannot be attested
    # is still not evidence, and nothing is left behind pretending to be one.
    mv "$os_tmpbody" "$os_out" || { rm -rf "$os_tmpd"; trap - EXIT; return 2; }
    echo "$os_code" > "$os_status"

    # THE ATTESTATION.  Note what is NOT passed here: no method, no path, no
    # tenant, no auth, no content type, no status code.  Every one of those comes
    # out of the trace.  There is no argument this call could be given that would
    # make it attest something that was not sent or not received.
    if ! python3 "$os_lib/wire_attestation.py" derive \
            --trace "$os_trace" \
            --headers-out "$os_reqhdr" \
            --sidecar-out "$os_http" \
            --body-file "$os_derive_body" \
            --response-file "$os_out" \
            --response-headers-out "$os_resphdr" \
            --status-file "$os_status" \
            --captured-at "$os_ts"; then
        echo "REFUSING to record $os_name: the sidecar could not be derived from the" >&2
        echo "  wire trace.  The response body is NOT committed, because an" >&2
        echo "  observation whose request cannot be attested is not evidence." >&2
        rm -f "$os_http" "$os_reqhdr" "$os_req" "$os_reqsha" "$os_out" "$os_status" \
              "$os_resphdr"
        rm -rf "$os_tmpd"
        trap - EXIT
        return 1
    fi

    # Self-check on every capture: the sidecar just written must verify against
    # the records and artefacts written in the same breath.  If this ever fails
    # the artefacts disagree at birth, which would mean the derivation itself is
    # broken.  EVERY attested artefact is presented -- a schema 2 sidecar with an
    # artefact withheld is REFUSED (exit 2) rather than partially checked.
    if ! python3 "$os_lib/wire_attestation.py" verify \
            --sidecar "$os_http" --headers "$os_reqhdr" --req "$os_derive_body" \
            --resp "$os_out" --resphdr "$os_resphdr" --status "$os_status" >/dev/null; then
        echo "SELF-CHECK FAILED for $os_name: the sidecar does not verify against the" >&2
        echo "  header record written in the same breath.  Treat every artefact for" >&2
        echo "  $os_name as void." >&2
        rm -rf "$os_tmpd"
        trap - EXIT
        return 1
    fi

    rm -rf "$os_tmpd"
    trap - EXIT
    printf '%-44s HTTP %s\n' "$os_name" "$os_code"
    return 0
}
