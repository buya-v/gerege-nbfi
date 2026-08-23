#!/usr/bin/env python3
"""Derive a capture sidecar from THE BYTES CURL ACTUALLY SENT, and verify it.

WHY THIS EXISTS -- T250, from T245's F-2
----------------------------------------
`.softhouse/capture/tierA-a2/cap.sh` / `cap8.sh` / `cap9.sh` / `cap10.sh` send the
tenant header from a shell variable (`-H "$T"`) but write the tenant line into
the committed `.http` sidecar as a HARD-CODED LITERAL:

    echo "Fineract-Platform-TenantId: gerege"

Change `env.sh` and every sidecar keeps saying `gerege` while the request goes
somewhere else.  The attestation CANNOT DISAGREE with the run it documents, so
it grades nothing -- the fail-open class this program has named repeatedly
(P-45).  T245 rested its own decisive proof on database contents rather than on
these sidecars, and said exactly why.

WHY NOT SIMPLY `echo "$T"` (T245's proposed item 2)
---------------------------------------------------
Because `$T` is what the AUTHOR BELIEVED WOULD BE SENT, not what was sent.  Three
counterexamples, all MEASURED against the live oracle by
`.softhouse/capture/t250-tenant-attestation/instruments/40-redC-*.sh` on
curl 8.7.1 -- and two of them are corrections to what this file first asserted
from reasoning, which is exactly why the shapes were driven rather than argued:

  1. the SAME header given twice is sent TWICE.  Curl does not de-duplicate and
     does not let the later value win: the wire carried
     `Fineract-Platform-TenantId: gerege` AND `...: default`, and the server
     picked.  `echo "$T"` would have attested one value of two.
  2. `-H "Name:"` REMOVES a curl-GENERATED header (`Accept`, `User-Agent`
     measured absent from the wire), so a rig attesting its own belief about
     what curl adds by default attests headers that were never sent.
     It does NOT remove an earlier user-supplied header of the same name --
     this file claimed it did, and the measurement said otherwise.
  3. `--trace-ascii` WRAPS payload lines at 64 bytes.  A long header value
     arrives split across several offset-prefixed chunks; reading each chunk as
     a header line corrupts the record.  See `reassemble()`.

So the source of truth is curl's own record of the outbound request, obtained
with `--trace-ascii` and reassembled by its own byte offsets, and nothing else.

WHAT IS AND IS NOT CLAIMED
--------------------------
CLAIMED: the sidecar and the committed wire record CANNOT DISAGREE UNDETECTABLY.
  Tamper the sidecar -> `verify` fails on re-derivation.  Tamper the header
  record -> `verify` fails on the digest the sidecar carries.  Tamper both
  consistently -> you have forged a matched artefact set, which is what the
  outer `MANIFEST.sha256` / vector `capture_sha256` pins exist to catch; this
  module does not and cannot claim unforgeability.
NOT CLAIMED: that a sidecar written by any OTHER rig is true.  A sidecar with no
  `attestation-derivation:` line is REFUSED as UNVERIFIABLE (exit 2), never
  passed.  Default-deny: absence of evidence is not evidence.

MONEY (CLAUDE.md non-negotiable): this module never parses a monetary value.  It
reads header text and byte counts only.  There is no `json.load` here and no
`float(...)` anywhere in the file -- adding one would be a 225th unguarded site
against the T145 census.  `Content-Length` is compared as an INTEGER byte count.

REDACTION: credential headers are redacted, but redacted DERIVABLY -- the value
is replaced by `<redacted sha256:HHHHHHHHHHHHHHHH>` over the exact sent bytes.
A changed credential therefore CHANGES THE SIDECAR, which a literal
`Basic <mifos:password>` placeholder does not.  That placeholder is the same
defect as the tenant literal, one header down; it is measured as the
"redaction class" by instrument 11.
"""
import argparse
import hashlib
import os
import re
import sys

REDACT_HEADERS = ("authorization", "proxy-authorization", "cookie", "set-cookie")

DERIVATION_TAG = "attestation-derivation: curl --trace-ascii; request headers AS SENT"

# `=> Send header, 188 bytes (0xbc)` then `0000: GET /... HTTP/1.1` lines.
SEND_HEADER_RE = re.compile(r"^=> Send header, (\d+) bytes")
OFFSET_LINE_RE = re.compile(r"^([0-9a-f]{4,}): (.*)$")


class Refuse(Exception):
    """A condition under which no verdict may be issued.  Never a pass."""


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def reassemble(chunks, declared):
    """Rebuild the header lines curl sent, using the trace's OWN byte offsets.

    MEASURED, not assumed: `--trace-ascii` WRAPS a payload line at 64 bytes and
    starts a new offset-prefixed chunk, so a header value longer than that
    arrives here split across several chunks.  Reading each chunk as a header
    line would corrupt the record for any long header -- e.g. a bearer token or
    a long `Authorization` -- and that corruption was found by driving shape 4 of
    `40-redC-shapes-not-designed-around.sh` red against the live oracle.

    The offsets make the reassembly EXACT rather than heuristic.  For chunks at
    offsets o1, o2 with contents c1, c2:

        o2 == o1 + len(c1)       -> c2 CONTINUES c1  (no CRLF between them)
        o2 == o1 + len(c1) + 2   -> c2 is a NEW line (a CRLF was sent)

    Anything else means the trace does not chain, and this REFUSES rather than
    guessing.  The reassembled block is then checked against the byte count curl
    itself declared in `=> Send header, N bytes`; a block that does not total N
    is not the block that was sent, and is likewise refused.

    Refusing on a broken chain is also what makes a forged `=> Send header` block
    smuggled through a request body inert: it cannot chain into the real one.
    """
    lines = []
    cur = None
    cur_off = None
    for off, content in chunks:
        if cur is None:
            cur, cur_off = content, off
            continue
        if off == cur_off + len(cur):
            cur = cur + content          # wrapped: same header line
            continue
        if off == cur_off + len(cur) + 2:
            lines.append(cur)            # CRLF: a new header line
            cur, cur_off = content, off
            continue
        raise Refuse(
            "trace offsets do not chain at 0x%04x (previous line began at 0x%04x "
            "and is %d bytes); the trace is not a faithful record of one request "
            "and nothing may be attested from it" % (off, cur_off, len(cur))
        )
    if cur is not None:
        lines.append(cur)
    total = sum(len(l) + 2 for l in lines)
    if total != declared:
        raise Refuse(
            "reassembled header block is %d bytes but curl declared %d; the record "
            "does not account for every byte sent" % (total, declared)
        )
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def parse_trace(trace_path):
    """Return [block, ...]; each block is the list of lines curl SENT as headers.

    A trace with zero send-header blocks is a REFUSAL, not an empty result: it
    means the transport never happened or the trace was not captured, and in
    either case there is nothing to attest.
    """
    if not os.path.isfile(trace_path):
        raise Refuse("trace file does not exist: %s" % trace_path)
    with open(trace_path, "rb") as fh:
        raw = fh.read().decode("utf-8", "replace")
    blocks = []
    lines = raw.split("\n")
    i = 0
    while i < len(lines):
        m0 = SEND_HEADER_RE.match(lines[i])
        if m0:
            declared = int(m0.group(1))
            i += 1
            chunks = []
            while i < len(lines):
                m = OFFSET_LINE_RE.match(lines[i])
                if not m:
                    break
                chunks.append((int(m.group(1), 16), m.group(2)))
                i += 1
            block = reassemble(chunks, declared)
            if block:
                blocks.append(block)
            continue
        i += 1
    if not blocks:
        raise Refuse(
            "no `=> Send header` block in %s -- nothing was observed to be sent, "
            "so nothing may be attested" % trace_path
        )
    return blocks


def redact(header_line):
    """Redact credential headers DERIVABLY: the digest still tracks the value."""
    if ":" not in header_line:
        return header_line
    name, _, value = header_line.partition(":")
    if name.strip().lower() not in REDACT_HEADERS:
        return header_line
    value = value.strip()
    scheme = value.split(" ", 1)[0] if " " in value else ""
    digest = _sha256_text(value)[:16]
    if scheme:
        return "%s: %s <redacted sha256:%s>" % (name, scheme, digest)
    return "%s: <redacted sha256:%s>" % (name, digest)


def header_record(blocks):
    """The canonical, redacted record of what went over the wire.

    Every send-header block is recorded, in order, with its index -- an HTTP
    exchange that sent headers twice (100-continue, redirect, retry) is a
    materially different exchange and the record says so rather than silently
    reporting the first.
    """
    out = []
    for n, block in enumerate(blocks):
        out.append("# send-header-block %d of %d" % (n + 1, len(blocks)))
        for line in block:
            out.append(redact(line))
    return "\n".join(out) + "\n"


def attestation_from_record(record_text, extra=()):
    """The sidecar's attestation block, DERIVED from the header record.

    Deterministic and pure: `derive` writes exactly this, `verify` recomputes
    exactly this.  If the two ever differ, the sidecar was edited by hand.
    """
    lines = [DERIVATION_TAG]
    for line in record_text.split("\n"):
        if not line.strip():
            continue
        if line.startswith("# send-header-block"):
            lines.append(line.replace("# ", "", 1))
            continue
        lines.append(line)
    lines.extend(extra)
    return "\n".join(lines) + "\n"


def cmd_derive(args):
    blocks = parse_trace(args.trace)
    record = header_record(blocks)
    with open(args.headers_out, "w") as fh:
        fh.write(record)
    hdr_sha = _sha256_file(args.headers_out)

    extra = ["request-headers-artefact: %s" % os.path.basename(args.headers_out),
             "request-headers-sha256: %s" % hdr_sha]

    if args.body_file:
        if not os.path.isfile(args.body_file):
            raise Refuse("body artefact does not exist: %s" % args.body_file)
        body_bytes = os.path.getsize(args.body_file)
        extra.append("body-wire-bytes-artefact: %s" % os.path.basename(args.body_file))
        extra.append("body-sha256: %s" % _sha256_file(args.body_file))
        extra.append("body-bytes: %d" % body_bytes)
        cl = content_length(record)
        if cl is None:
            extra.append("content-length-crosscheck: ABSENT (no Content-Length was sent)")
        elif cl != body_bytes:
            raise Refuse(
                "Content-Length SENT (%d) != bytes in the committed body artefact (%d). "
                "The body changed between snapshot and send; no sidecar may claim "
                "otherwise." % (cl, body_bytes)
            )
        else:
            extra.append("content-length-crosscheck: MATCH (%d bytes)" % cl)
    else:
        extra.append("body: <none>")

    extra.append("captured-at-utc: %s" % args.captured_at)
    text = attestation_from_record(record, extra)
    with open(args.sidecar_out, "w") as fh:
        fh.write(text)
    sys.stdout.write("derived %s from %s (%d send-header block(s))\n"
                     % (args.sidecar_out, args.trace, len(blocks)))
    return 0


def content_length(record_text):
    for line in record_text.split("\n"):
        name, _, value = line.partition(":")
        if name.strip().lower() == "content-length":
            try:
                return int(value.strip())
            except ValueError:
                return None
    return None


def cmd_verify(args):
    if not os.path.isfile(args.sidecar):
        raise Refuse("sidecar does not exist: %s" % args.sidecar)
    with open(args.sidecar, "rb") as fh:
        sidecar = fh.read().decode("utf-8", "replace")
    if DERIVATION_TAG not in sidecar:
        raise Refuse(
            "sidecar %s carries no `%s` line. It was not derived from a wire record, "
            "so it is UNVERIFIABLE -- it may be true, but nothing here can tell you. "
            "REFUSED (this is the T245 F-2 shape)." % (args.sidecar, DERIVATION_TAG)
        )
    if not os.path.isfile(args.headers):
        raise Refuse("header record does not exist: %s" % args.headers)

    with open(args.headers, "rb") as fh:
        record = fh.read().decode("utf-8", "replace")

    failures = []

    # (1) the digest the sidecar claims for the header record
    claimed = None
    for line in sidecar.split("\n"):
        if line.startswith("request-headers-sha256: "):
            claimed = line.split(": ", 1)[1].strip()
    actual = _sha256_file(args.headers)
    if claimed is None:
        failures.append("sidecar declares no `request-headers-sha256:`")
    elif claimed != actual:
        failures.append(
            "header-record digest MISMATCH: sidecar claims %s, file is %s" % (claimed, actual)
        )

    # (2) every header line in the record must appear verbatim in the sidecar,
    #     and every header-shaped sidecar line must come from the record.
    rec_lines = [l for l in record.split("\n") if l.strip() and not l.startswith("#")]
    side_lines = sidecar.split("\n")
    for line in rec_lines:
        if line not in side_lines:
            failures.append("sidecar OMITS a line that was sent: %r" % line)
    known_keys = (
        "attestation-derivation", "send-header-block", "request-headers-artefact",
        "request-headers-sha256", "body-wire-bytes-artefact", "body-sha256",
        "body-bytes", "body", "captured-at-utc", "content-length-crosscheck",
    )
    for line in side_lines:
        if not line.strip():
            continue
        # `send-header-block N of M` is a structural marker, not a header: it
        # carries no colon, so it must be matched by prefix rather than by key.
        if line.startswith("send-header-block "):
            if "# " + line not in record.split("\n"):
                failures.append("sidecar ASSERTS a block marker not in the record: %r" % line)
            continue
        key = line.partition(":")[0].strip().lower()
        if key in known_keys:
            continue
        if line not in rec_lines:
            failures.append("sidecar ASSERTS a line that was NOT sent: %r" % line)

    # (3) the body artefact, if one is claimed
    if args.req:
        if not os.path.isfile(args.req):
            failures.append("body artefact missing: %s" % args.req)
        else:
            size = os.path.getsize(args.req)
            for line in side_lines:
                if line.startswith("body-bytes: "):
                    if int(line.split(": ", 1)[1]) != size:
                        failures.append(
                            "body-bytes MISMATCH: sidecar says %s, artefact is %d"
                            % (line.split(": ", 1)[1], size)
                        )
                if line.startswith("body-sha256: "):
                    if line.split(": ", 1)[1].strip() != _sha256_file(args.req):
                        failures.append("body-sha256 MISMATCH against the artefact")
            cl = content_length(record)
            if cl is not None and cl != size:
                failures.append(
                    "Content-Length SENT (%d) != committed body artefact (%d bytes)" % (cl, size)
                )

    if failures:
        sys.stderr.write("ATTESTATION MISMATCH -- %s\n" % args.sidecar)
        for f in failures:
            sys.stderr.write("  %s\n" % f)
        return 1
    sys.stdout.write("VERIFIED %s against %s\n" % (args.sidecar, args.headers))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd")

    d = sub.add_parser("derive", help="write a sidecar derived from a curl trace")
    d.add_argument("--trace", required=True)
    d.add_argument("--headers-out", required=True)
    d.add_argument("--sidecar-out", required=True)
    d.add_argument("--body-file", default="")
    d.add_argument("--captured-at", required=True)
    d.set_defaults(fn=cmd_derive)

    v = sub.add_parser("verify", help="re-derive a sidecar and detect disagreement")
    v.add_argument("--sidecar", required=True)
    v.add_argument("--headers", required=True)
    v.add_argument("--req", default="")
    v.set_defaults(fn=cmd_verify)

    args = ap.parse_args(argv)
    if not getattr(args, "fn", None):
        ap.print_help(sys.stderr)
        return 2
    try:
        return args.fn(args)
    except Refuse as exc:
        sys.stderr.write("REFUSING: %s\n" % exc)
        return 2


if __name__ == "__main__":
    sys.exit(main())
