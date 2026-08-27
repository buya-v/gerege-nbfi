#!/usr/bin/env python3
"""Derive a capture sidecar from THE BYTES CURL ACTUALLY SENT AND RECEIVED, and verify it.

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

WHY THIS FILE WAS REWRITTEN -- T274, from T261's F-4/F-5/F-6/F-7
----------------------------------------------------------------
T250 built the derivation correctly and then wrote a verifier that
**checked only the assertions that happened to be PRESENT**, inside a module
whose own docstring says *absence of evidence is not evidence*.  T261 drove five
shapes through it and all five passed:

  R1  delete `body-sha256:` from the sidecar and swap the committed body for
      DIFFERENT BYTES OF THE SAME LENGTH  -> `VERIFIED` rc=0.  Deleting the
      assertion deleted the check.
  R2a reorder the header lines in the sidecar                    -> rc=0
  R2b send an identical header TWICE, delete ONE copy from the
      sidecar                                                    -> rc=0
      (the comparison was SET MEMBERSHIP, and T250's own red-drive C had already
      proved that two `-H` flags put BOTH values on the wire, so multiplicity
      and order are exactly the facts this sidecar exists to record)
  R3  invent `content-length-crosscheck: MATCH (99999 bytes)`     -> rc=0
      (`known_keys` was an EXEMPTION LIST: a recognised key was skipped rather
      than validated -- default-ALLOW in an evidence verifier)
  R4  swap the response `.json` for another capture's             -> rc=0
      (the response leg was entirely unattested, and that limit was stated
      NOWHERE in the module)

THE RULE THIS FILE NOW OBEYS, WHICH REMOVES ALL FIVE AT THE ROOT
---------------------------------------------------------------
`verify` does not inspect the sidecar's assertions one at a time.  It
**RE-DERIVES THE ENTIRE SIDECAR** from the wire records and the committed
artefacts using the SAME function `derive` used -- `build_sidecar()` -- and
compares the two texts EXACTLY, line by line, in order.

  * an assertion that is ABSENT changes the text          -> FAIL   (kills R1)
  * a line out of order changes the text                  -> FAIL   (kills R2a)
  * a dropped duplicate changes the text                  -> FAIL   (kills R2b)
  * an invented or altered value changes the text         -> FAIL   (kills R3)
  * a swapped response changes `response-sha256:`         -> FAIL   (kills R4)

There is no list of "things we check", so there is nothing an attacker can fall
outside of.  The required assertion set is DERIVED from the wire record (not
from the sidecar, which is the artefact under suspicion), is enumerable, and is
PRINTED on every run, pass or fail.

WHAT DECIDES WHETHER A BODY MUST BE ATTESTED
--------------------------------------------
The WIRE, never the sidecar and never the caller.  If the request record carries
`Content-Length`, a body was sent, so `body-wire-bytes-artefact:`, `body-sha256:`,
`body-bytes:` and `content-length-crosscheck:` are REQUIRED and the body artefact
must be supplied (`--req`); omitting it is a REFUSAL, not a skipped check.  If the
record carries no `Content-Length`, those assertions are FORBIDDEN and `body:
<none>` is required.  A sidecar cannot elect its own obligations.

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

So the source of truth is curl's own record of the exchange, obtained with
`--trace-ascii` and reassembled by its own byte offsets, and nothing else.

THE ATTESTATION SCHEMA, AND WHY THERE IS A VERSION NUMBER
---------------------------------------------------------
Schema 2 sidecars carry `attestation-schema: 2` as their SECOND line and attest
BOTH legs of the exchange.  Sidecars written before T274 carry no schema line and
attest the REQUEST ONLY; they are schema 1.  They remain verifiable, byte for
byte, and are NOT retro-edited (T114) -- but the version is not decoration, and it
is not a downgrade route:

  * schema 1 sidecar + any response artefact (`--resp`/`--resphdr`/`--status`)
    -> REFUSED (exit 2).  This sidecar attests nothing about a response, so no
    verdict about that response is available from it.
    **THE PRECONDITION, which T283 measured and the first wording of this bullet
    left out:** that refusal fires only when the CALLER still presents a response
    artefact.  Delete the schema line AND withhold `--resp/--resphdr/--status`
    and the call verifies clean as schema 1, with the response artefacts sitting
    unmentioned in the same directory.  So "deleting the schema line buys a
    refusal, not a pass" is true of the caller `oracle_send` makes -- which
    presents every artefact it holds -- and NOT of the general case.  [MEASURED,
    arm FE of `.softhouse/reviews/t283-review-t274/evidence/10-forgery-arms.txt`.]
    A CALLER MUST PRESENT EVERY ARTEFACT IT HAS; this module cannot tell that an
    artefact exists if it is not handed one, and `RESPONSE LEG: NOT ATTESTED` in
    the verdict is the only warning a schema 1 pass carries.
  * schema 2 sidecar with any response artefact missing -> REFUSED (exit 2).
  * any other schema value -> REFUSED (exit 2).

`derive` only ever writes schema 2.

WHAT IS AND IS NOT CLAIMED
--------------------------
CLAIMED: the sidecar, the two committed wire records, the request body artefact,
  the RESPONSE BODY artefact and the `.status` file CANNOT DISAGREE
  UNDETECTABLY.  Tamper any one of them -> re-derivation differs -> exit 1.
  Omit an assertion -> re-derivation differs -> exit 1.  Reorder or drop a
  duplicate header -> re-derivation differs -> exit 1.
NOT CLAIMED, and each of these is a real limit, stated HERE rather than in a
review, because a limit written only into a review is the exact failure this
whole class is named for:
  * UNFORGEABILITY.  Tamper the sidecar AND the artefacts CONSISTENTLY and you
    have forged a matched set; that is what the outer `MANIFEST.sha256` and the
    vectors' `capture_sha256` pins exist to catch, not this module.
    T283 CORRECTED THE PRICE OF THAT, because the first wording of this bullet
    said "the sidecar AND the records AND the digests", which reads as four
    edits and is wrong in the direction that flatters this module.  THE RECORDS
    DO NOT HAVE TO BE TOUCHED.  Nothing committed digests either BODY: the
    `.reqhdr` / `.resphdr` records carry `Content-Length` and no more.  So
    replacing the request body -- or the RESPONSE BODY, the half a golden vector
    is actually graded on -- with the SAME NUMBER OF DIFFERENT BYTES and
    re-deriving the sidecar costs TWO file edits, produces a sidecar
    indistinguishable in shape from an honest one, and verifies clean.
    [MEASURED, arms FA2 and FC2 of
    `.softhouse/reviews/t283-review-t274/evidence/10-forgery-arms.txt`.]
    What `verify` therefore establishes is SELF-CONSISTENCY, not authenticity:
    it catches a PARTIAL tamper -- drift, rot, an artefact edited without its
    sidecar -- and it cannot catch a whole-set forgery by anyone who can write
    the sidecar.  Read a `VERIFIED` as "these six files agree", never as "this
    is what the oracle was asked and answered".
  * `captured-at-utc:` is NOT DERIVABLE.  It is the one assertion taken from the
    sidecar on trust; nothing here can tell you WHEN the exchange happened.  Its
    absence is still a failure.
  * SCHEMA 1 sidecars say NOTHING about the response.  `verify` prints that in
    its verdict rather than letting a reader assume the capture is attested.
  * The TRACE ITSELF IS NOT COMMITTED (it holds the un-redacted `Authorization`
    header).  The two `.reqhdr` / `.resphdr` records are the committed derivation
    of it; a forged trace that produces a self-consistent pair is the
    unforgeability limit above.
  * TLS parameters, timing, and the BODIES of redirect hops are not attested.
    The response HEADERS are attested in full via the `.resphdr` record's digest;
    only the final status line is additionally echoed into the sidecar so that a
    reader can see it without opening a second file.
  * A sidecar written by any OTHER rig is not trusted: one whose first line is
    not `attestation-derivation:` is REFUSED as UNVERIFIABLE (exit 2), never
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

EXIT STATUS
-----------
  0  VERIFIED / derived
  1  ATTESTATION MISMATCH -- a verdict was reached and it is NO
  2  REFUSED -- no verdict may be issued (missing artefact, unusable trace,
     unverifiable sidecar, schema violation).  NEVER a pass.
"""
import argparse
import difflib
import hashlib
import os
import re
import sys

REDACT_HEADERS = ("authorization", "proxy-authorization", "cookie", "set-cookie")

DERIVATION_TAG = "attestation-derivation: curl --trace-ascii; request headers AS SENT"
SCHEMA_KEY = "attestation-schema"
SCHEMA_CURRENT = "2"
SCHEMA_LINE = "%s: %s" % (SCHEMA_KEY, SCHEMA_CURRENT)

# `=> Send header, 188 bytes (0xbc)` then `0000: GET /... HTTP/1.1` lines.
SEND_HEADER_RE = re.compile(r"^=> Send header, (\d+) bytes")
# `<= Recv header, 15 bytes (0xf)` then `0000: HTTP/1.1 400 ` lines.
RECV_HEADER_RE = re.compile(r"^<= Recv header, (\d+) bytes")
OFFSET_LINE_RE = re.compile(r"^([0-9a-f]{4,}): (.*)$")

DIRECTIONS = {
    "send": (SEND_HEADER_RE, "send-header-block", "=> Send"),
    "recv": (RECV_HEADER_RE, "recv-header-block", "<= Recv"),
}


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


def _read_text(path, what):
    if not path:
        raise Refuse("no path was supplied for the %s" % what)
    if not os.path.isfile(path):
        raise Refuse("%s does not exist: %s" % (what, path))
    with open(path, "rb") as fh:
        return fh.read().decode("utf-8", "replace")


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

    T274 NOTE: this function is UNCHANGED in substance from T250 and is the
    strongest part of that work -- T261 re-swept the 64-byte wrap boundary live
    (1, 10, 60-66, 127-129, 200, 300, 1000, 4000 bytes and a 360-byte
    colon-laden value) and every one attested EXACT.  The T274 sweep repeats it,
    because a rewrite that quietly broke it would be worse than the fail-opens.
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


def parse_trace(trace_path, direction):
    """Return [block, ...]; each block is the list of header lines for `direction`.

    `direction` is "send" (the request, `=> Send header`) or "recv" (the
    response, `<= Recv header`).  A trace with zero blocks in the requested
    direction is a REFUSAL, not an empty result: it means that leg of the
    exchange never happened or was not captured, and in either case there is
    nothing to attest.

    Note the discrimination that matters here: `=> Send SSL data` and
    `<= Recv SSL data` blocks are also offset-prefixed, carry binary rendered as
    dots, and would poison the record if matched.  The anchored regexes match the
    word `header` and nothing else, and that was checked against a live TLS
    trace in which the SSL-data blocks outnumber the header blocks.
    """
    if direction not in DIRECTIONS:
        raise Refuse("unknown trace direction %r" % direction)
    rx, _, arrow = DIRECTIONS[direction]
    raw = _read_text(trace_path, "trace file")
    blocks = []
    lines = raw.split("\n")
    i = 0
    while i < len(lines):
        m0 = rx.match(lines[i])
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
            "no `%s header` block in %s -- nothing was observed on that leg of the "
            "exchange, so nothing may be attested" % (arrow, trace_path)
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


def header_record(blocks, direction):
    """The canonical, redacted record of what went over the wire on one leg.

    Every block is recorded, in order, with its index -- an HTTP exchange that
    sent headers twice (100-continue, redirect, retry) is a materially different
    exchange and the record says so rather than silently reporting the first.
    """
    _, marker, _arrow = DIRECTIONS[direction]
    out = []
    for n, block in enumerate(blocks):
        out.append("# %s %d of %d" % (marker, n + 1, len(blocks)))
        for line in block:
            out.append(redact(line))
    return "\n".join(out) + "\n"


def record_body_lines(record_text):
    """The record's lines with `# ` stripped from block markers, blanks dropped.

    This is the part of the sidecar that is a verbatim transcription of the wire
    record.  ORDER AND MULTIPLICITY ARE PART OF IT: it is compared as a sequence.
    """
    out = []
    for line in record_text.split("\n"):
        if not line.strip():
            continue
        if line.startswith("# "):
            out.append(line.replace("# ", "", 1))
            continue
        out.append(line)
    return out


def header_values(record_text, name):
    """Every value of header `name` in a record, in wire order."""
    want = name.strip().lower()
    vals = []
    for line in record_text.split("\n"):
        if line.startswith("#") or not line.strip():
            continue
        hname, sep, value = line.partition(":")
        if not sep:
            continue
        if hname.strip().lower() == want:
            vals.append(value.strip())
    return vals


def content_length(record_text, leg):
    """The single `Content-Length` on this leg as an INTEGER, or None.

    Two Content-Length headers, or one that is not an integer, make the record
    ambiguous about how many body bytes were on the wire.  T250 returned None for
    a non-integer value, which made the sidecar state
    `ABSENT (no Content-Length was sent)` about a request that plainly sent one:
    a false assertion manufactured out of a parse failure.  Both cases REFUSE.
    """
    vals = header_values(record_text, "content-length")
    if not vals:
        return None
    if len(vals) > 1:
        raise Refuse(
            "%s record carries %d `Content-Length` headers (%s); the number of body "
            "bytes on the wire is ambiguous and nothing may be attested about it"
            % (leg, len(vals), ", ".join(repr(v) for v in vals))
        )
    try:
        return int(vals[0])
    except ValueError:
        raise Refuse(
            "%s record carries a non-integer `Content-Length: %s`; it cannot be "
            "cross-checked against a byte count" % (leg, vals[0])
        )


def status_line(record_text):
    """The FINAL HTTP status line in a response record.

    Final, not first: a redirect or retry chain records several, and the body
    curl wrote to `-o` is the answer to the LAST one.  Refuses when there is
    none, because a response record with no status line is not a response record.
    """
    found = None
    for line in record_text.split("\n"):
        if line.startswith("HTTP/"):
            found = line.rstrip()
    if found is None:
        raise Refuse(
            "response record carries no `HTTP/...` status line; it is not a record "
            "of a response and no status may be attested"
        )
    return found


def status_code(line):
    parts = line.split()
    if len(parts) < 2 or not parts[1].isdigit():
        raise Refuse("response status line %r carries no numeric status code" % line)
    return parts[1]


def _crosscheck(prefix, cl, actual, mode, leg, encodings):
    """One `...content-length-crosscheck:` line, or a Refuse when deriving.

    In DERIVE mode a disagreement between the Content-Length on the wire and the
    committed artefact is a REFUSAL: the artefact is not what was on the wire, so
    no sidecar may be written claiming otherwise.  In VERIFY mode it must be a
    VERDICT (exit 1), not a refusal -- so the disagreement is rendered as a line
    that can never equal what `derive` wrote, and the comparison reports it.
    """
    if encodings:
        return ("%s: NOT-APPLICABLE (Content-Encoding: %s -- the committed artefact "
                "is curl's DECODED body, so its length is not the wire length)"
                % (prefix, "; ".join(encodings)))
    if cl is None:
        return "%s: ABSENT (no Content-Length was sent)" % prefix
    if cl != actual:
        if mode == "derive":
            raise Refuse(
                "Content-Length on the %s leg (%d) != bytes in the committed artefact "
                "(%d). The body changed between snapshot and send; no sidecar may "
                "claim otherwise." % (leg, cl, actual)
            )
        return "%s: MISMATCH (Content-Length %d, artefact %d bytes)" % (prefix, cl, actual)
    return "%s: MATCH (%d bytes)" % (prefix, cl)


def request_extras(record_text, headers_path, body_path, mode):
    """The request-leg assertions, DERIVED.  The SAME code runs in derive and verify.

    THE OBLIGATION IS SET BY THE WIRE.  `Content-Length` in the record means a
    body was sent, so the body assertions are REQUIRED and the artefact must be
    supplied; no `Content-Length` means they are FORBIDDEN and `body: <none>` is
    required.  Neither the sidecar nor the caller gets a vote -- and that vote is
    exactly what T261's F-4 took.
    """
    extras = ["request-headers-artefact: %s" % os.path.basename(headers_path),
              "request-headers-sha256: %s" % _sha256_file(headers_path)]
    cl = content_length(record_text, "request")
    if body_path:
        if not os.path.isfile(body_path):
            raise Refuse("body artefact does not exist: %s" % body_path)
        if cl is None:
            raise Refuse(
                "a body artefact was supplied (%s) but the request record carries no "
                "`Content-Length`; the record does not show that body going out and "
                "no sidecar may assert that it did" % body_path
            )
        nbytes = os.path.getsize(body_path)
        extras.append("body-wire-bytes-artefact: %s" % os.path.basename(body_path))
        extras.append("body-sha256: %s" % _sha256_file(body_path))
        extras.append("body-bytes: %d" % nbytes)
        extras.append(_crosscheck("content-length-crosscheck", cl, nbytes, mode,
                                  "request",
                                  header_values(record_text, "content-encoding")))
    else:
        if cl is not None:
            raise Refuse(
                "the request record shows `Content-Length: %d`, so a body WAS sent, "
                "but no body artefact was supplied. Absence of the artefact is not "
                "absence of a body: nothing may be attested or verified about it. "
                "Pass the committed body artefact (--body-file / --req)." % cl
            )
        extras.append("body: <none>")
    return extras


def response_extras(record_text, resphdr_path, resp_path, status_path, mode):
    """The response-leg assertions, DERIVED.  T274, from T261's F-6.

    The response is the material half of a capture: a golden vector is graded on
    THE ORACLE'S ANSWER, not on the request.  T250 attested the request only and
    said so nowhere, so a reader met a module that looked like it attested the
    capture.  Both legs are attested now, and the residual limits are in the
    module docstring where a reader meets them rather than in a review.
    """
    sline = status_line(record_text)
    code = status_code(sline)
    if not resp_path or not os.path.isfile(resp_path):
        raise Refuse("response artefact does not exist: %s" % resp_path)
    nbytes = os.path.getsize(resp_path)
    extras = ["response-headers-artefact: %s" % os.path.basename(resphdr_path),
              "response-headers-sha256: %s" % _sha256_file(resphdr_path),
              "response-status-line: %s" % sline,
              "response-artefact: %s" % os.path.basename(resp_path),
              "response-sha256: %s" % _sha256_file(resp_path),
              "response-bytes: %d" % nbytes]
    cl = content_length(record_text, "response")
    extras.append(_crosscheck("response-content-length-crosscheck", cl, nbytes, mode,
                              "response", header_values(record_text, "content-encoding")))
    recorded = _read_text(status_path, "status file").strip()
    if recorded != code:
        if mode == "derive":
            raise Refuse(
                "the status file says %r but the wire status line is %r; curl's own "
                "two accounts of the same exchange disagree and nothing may be "
                "attested" % (recorded, sline)
            )
        extras.append("response-status-crosscheck: MISMATCH (status file %r, wire %s)"
                      % (recorded, code))
    else:
        extras.append("response-status-crosscheck: MATCH (%s)" % code)
    extras.append("response-status-artefact: %s" % os.path.basename(status_path))
    return extras


def build_sidecar(record_text, extras, schema):
    """THE ONE PLACE a sidecar's text is defined.

    `derive` writes exactly this; `verify` recomputes exactly this and compares.
    Because there is one builder and not two lists, there is no assertion
    `verify` can fail to know about -- which is the root repair for F-4/F-5/F-7.
    """
    lines = [DERIVATION_TAG]
    if schema == 2:
        lines.append(SCHEMA_LINE)
    lines.extend(record_body_lines(record_text))
    lines.extend(extras)
    return "\n".join(lines) + "\n"


def assertion_key(line):
    """The key of an assertion line, lowercased.  Block markers carry no colon."""
    return line.partition(":")[0].strip().lower()


def cmd_derive(args):
    send_blocks = parse_trace(args.trace, "send")
    recv_blocks = parse_trace(args.trace, "recv")

    record = header_record(send_blocks, "send")
    with open(args.headers_out, "w") as fh:
        fh.write(record)
    resp_record = header_record(recv_blocks, "recv")
    with open(args.response_headers_out, "w") as fh:
        fh.write(resp_record)

    extras = request_extras(record, args.headers_out, args.body_file, "derive")
    extras += response_extras(resp_record, args.response_headers_out,
                              args.response_file, args.status_file, "derive")
    extras.append("captured-at-utc: %s" % args.captured_at)

    text = build_sidecar(record, extras, 2)
    with open(args.sidecar_out, "w") as fh:
        fh.write(text)
    sys.stdout.write(
        "derived %s from %s (schema %s; %d send-header block(s), "
        "%d recv-header block(s))\n"
        % (args.sidecar_out, args.trace, SCHEMA_CURRENT,
           len(send_blocks), len(recv_blocks)))
    return 0


def sidecar_schema(lines, sidecar_path):
    """The declared schema, default-deny.  See the docstring's downgrade note."""
    if not lines or lines[0] != DERIVATION_TAG:
        raise Refuse(
            "sidecar %s does not begin with `%s`. It was not derived from a wire "
            "record, so it is UNVERIFIABLE -- it may be true, but nothing here can "
            "tell you. REFUSED (this is the T245 F-2 shape)."
            % (sidecar_path, DERIVATION_TAG)
        )
    if len(lines) > 1 and assertion_key(lines[1]) == SCHEMA_KEY:
        declared = lines[1].partition(":")[2].strip()
        if declared != SCHEMA_CURRENT:
            raise Refuse(
                "sidecar %s declares `%s: %s`, which this verifier does not "
                "implement. An unknown schema is refused, never assumed compatible."
                % (sidecar_path, SCHEMA_KEY, declared))
        return 2
    return 1


def cmd_verify(args):
    sidecar_text = _read_text(args.sidecar, "sidecar")
    side_lines = sidecar_text.split("\n")
    while side_lines and not side_lines[-1].strip():
        side_lines.pop()

    schema = sidecar_schema(side_lines, args.sidecar)
    resp_args = [("--resp", args.resp), ("--resphdr", args.resphdr),
                 ("--status", args.status)]
    supplied = [n for n, v in resp_args if v]
    absent = [n for n, v in resp_args if not v]

    if schema == 1:
        if supplied:
            raise Refuse(
                "sidecar %s is SCHEMA 1: it attests the REQUEST ONLY and says nothing "
                "about any response, but %s was supplied. No verdict about that "
                "response is available from this sidecar, so this REFUSES rather than "
                "returning a pass that would silently cover the request leg only. "
                "(Deleting the `%s:` line from a schema 2 sidecar lands here too -- a "
                "downgrade buys a refusal, not a pass.)"
                % (args.sidecar, "/".join(supplied), SCHEMA_KEY))
    elif absent:
        raise Refuse(
            "sidecar %s is SCHEMA %s and attests a response, but %s was not supplied. "
            "An attested artefact that is not presented cannot be checked, and an "
            "unchecked assertion is not a passed one."
            % (args.sidecar, SCHEMA_CURRENT, "/".join(absent)))

    record = _read_text(args.headers, "request header record")
    extras = request_extras(record, args.headers, args.req, "verify")
    if schema == 2:
        resp_record = _read_text(args.resphdr, "response header record")
        extras += response_extras(resp_record, args.resphdr, args.resp,
                                  args.status, "verify")

    failures = []

    # `captured-at-utc` is the ONE assertion that cannot be re-derived: it is
    # taken from the sidecar on trust.  Its ABSENCE is still a failure.
    caps = [l for l in side_lines if assertion_key(l) == "captured-at-utc"]
    if len(caps) == 1:
        extras.append(caps[0])
    else:
        failures.append(
            "sidecar carries %d `captured-at-utc:` lines; exactly one is required. "
            "It is the one assertion this verifier cannot re-derive, so its presence "
            "is the most that can be demanded of it -- and it IS demanded." % len(caps))
        extras.append("captured-at-utc: <ABSENT>")

    # T283 (review of T274).  A CROSSCHECK THAT COMES BACK `MISMATCH (...)` IS A
    # VERDICT OF NO ABOUT THE ARTEFACTS, AND IT DOES NOT BECOME A PASS BECAUSE
    # THE SIDECAR AGREES WITH IT.
    #
    # `_crosscheck` renders a wire/artefact disagreement as a line in VERIFY mode
    # so that it can be reported as a verdict (exit 1) rather than a refusal.  Its
    # comment says such a line "can never equal what `derive` wrote" -- true, and
    # beside the point, because `verify` does not compare against what `derive`
    # wrote.  It compares against what IT re-derives, and the sidecar is the
    # artefact under suspicion.  A forger who rewrites the sidecar with the
    # verifier's own builder therefore gets `MISMATCH` on both sides, an exact
    # match, and `VERIFIED` rc=0 -- over an artefact set whose own derivation says
    # the wire record and the committed artefact DISAGREE.  Measured three ways
    # against the shipped T274 rig (a request body of a different length; a
    # forged `.status`; another capture's response body):
    # `.softhouse/reviews/t283-review-t274/evidence/10-forgery-arms.txt`.
    #
    # `derive` REFUSES to write one of these lines, so its presence in a sidecar is
    # by construction proof that the set is not the one that was captured.  This is
    # therefore a verdict, never a refusal: the artefacts are all present and
    # readable, and what they say is NO.
    for line in extras:
        if line.partition(":")[2].strip().startswith("MISMATCH ("):
            failures.append(
                "the wire record and a committed artefact DISAGREE -- %s. `derive` "
                "REFUSES to write this line, so a sidecar that repeats it does not "
                "settle it: a disagreement the sidecar agrees with is still a "
                "disagreement" % line)

    expected = build_sidecar(record, extras, schema)
    exp_lines = expected.rstrip("\n").split("\n")

    required = [assertion_key(l) for l in extras]
    wire_n = len(record_body_lines(record))
    sys.stdout.write(
        "REQUIRED ASSERTIONS (%d), DERIVED FROM THE WIRE RECORD -- not read off the "
        "sidecar, which is the artefact under suspicion:\n" % len(required))
    for key in required:
        sys.stdout.write("  %s\n" % key)
    sys.stdout.write(
        "VERBATIM WIRE LINES REQUIRED, IN ORDER AND WITH MULTIPLICITY: %d\n" % wire_n)
    sys.stdout.write("RESPONSE LEG: %s\n" % (
        "ATTESTED (schema 2) -- headers record digest, final status line, status "
        "file, body digest and byte count"
        if schema == 2 else
        "NOT ATTESTED. This is a SCHEMA 1 sidecar, written before T274: it says "
        "NOTHING about the response body or status, and neither can this verifier. "
        "Do not read a pass here as 'the capture is attested' -- only the request is."))

    # Present-key diagnostics.  These do NOT decide the verdict -- the exact
    # re-derivation below does -- but they name the defect instead of leaving a
    # reader to diff two blocks by eye.
    #
    # They are computed ONLY when the verbatim wire block matched, because the
    # tail's position is defined relative to that block: a deleted or inserted
    # WIRE line shifts the boundary, and a boundary read off a shifted sidecar
    # manufactures assertion-level findings that are not true.  A diagnostic that
    # is confidently wrong is worse than one that is withheld, so this says which
    # it is doing.
    head_n = wire_n + (2 if schema == 2 else 1)
    if side_lines[:head_n] == exp_lines[:head_n]:
        seen = {}
        for line in side_lines[head_n:]:
            k = assertion_key(line)
            seen[k] = seen.get(k, 0) + 1
        for key in required:
            if seen.get(key, 0) == 0:
                failures.append(
                    "REQUIRED assertion ABSENT: `%s:` -- absence of the assertion is "
                    "not absence of the thing asserted" % key)
        for key in sorted(seen):
            if key not in required:
                failures.append(
                    "sidecar ASSERTS `%s:`, which this exchange does not license "
                    "(unknown here, or forbidden for this exchange); an unrecognised "
                    "assertion is REFUSED, never ignored" % key)
            elif seen[key] > 1:
                failures.append("assertion `%s:` appears %d times; exactly one is "
                                "required" % (key, seen[key]))
    elif side_lines != exp_lines:
        failures.append(
            "the VERBATIM WIRE BLOCK itself disagrees with the record (see the "
            "line-level findings below); assertion-level diagnostics are WITHHELD "
            "because their position is defined relative to that block")

    # THE VERDICT: exact, ordered, whole-text re-derivation, reported as the
    # MINIMAL EDIT between the two.  A positional line-by-line walk would turn one
    # deleted line into a cascade of N spurious findings, which buries the actual
    # defect under its own consequences.
    if side_lines != exp_lines:
        sm = difflib.SequenceMatcher(None, exp_lines, side_lines, autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                continue
            if tag in ("delete", "replace"):
                for k in range(i1, i2):
                    failures.append(
                        "sidecar OMITS a line the wire record and the committed "
                        "artefacts derive (expected at line %d): %r" % (k + 1, exp_lines[k]))
            if tag in ("insert", "replace"):
                for k in range(j1, j2):
                    failures.append(
                        "sidecar ASSERTS a line nothing derives (sidecar line %d): %r"
                        % (k + 1, side_lines[k]))
        if len(side_lines) != len(exp_lines):
            failures.append("sidecar has %d lines; re-derivation yields %d"
                            % (len(side_lines), len(exp_lines)))

    if failures:
        sys.stderr.write("ATTESTATION MISMATCH -- %s\n" % args.sidecar)
        for f in failures:
            sys.stderr.write("  %s\n" % f)
        sys.stderr.write("--- re-derived (expected) vs sidecar (actual) ---\n")
        for dl in difflib.unified_diff(exp_lines, side_lines, "re-derived",
                                       os.path.basename(args.sidecar),
                                       lineterm="", n=1):
            sys.stderr.write("  %s\n" % dl)
        return 1
    sys.stdout.write("VERIFIED %s against %s%s\n"
                     % (args.sidecar, args.headers,
                        (" and " + args.resphdr) if schema == 2 else ""))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd")

    d = sub.add_parser("derive", help="write a sidecar derived from a curl trace")
    d.add_argument("--trace", required=True)
    d.add_argument("--headers-out", required=True)
    d.add_argument("--sidecar-out", required=True)
    d.add_argument("--body-file", default="")
    d.add_argument("--response-file", required=True)
    d.add_argument("--response-headers-out", required=True)
    d.add_argument("--status-file", required=True)
    d.add_argument("--captured-at", required=True)
    d.set_defaults(fn=cmd_derive)

    v = sub.add_parser("verify", help="re-derive a sidecar and detect disagreement")
    v.add_argument("--sidecar", required=True)
    v.add_argument("--headers", required=True)
    v.add_argument("--req", default="")
    v.add_argument("--resp", default="")
    v.add_argument("--resphdr", default="")
    v.add_argument("--status", default="")
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
    except OSError as exc:
        # T283.  An artefact that EXISTS but cannot be READ used to raise, and a
        # Python traceback exits 1 -- which this module's own exit-status contract
        # reads as "a verdict was reached and it is NO".  No verdict was reached.
        # An I/O error is a REFUSAL.  Measured: a sidecar at mode 000 exited 1 with
        # a traceback against the shipped T274 rig -- arm E1 of
        # `.softhouse/reviews/t283-review-t274/evidence/20-sidecar-shapes.txt`.
        sys.stderr.write(
            "REFUSING: an artefact could not be read: %s -- an I/O error is not a "
            "verdict, and an unreadable file is not a clean one\n" % exc)
        return 2


if __name__ == "__main__":
    sys.exit(main())
