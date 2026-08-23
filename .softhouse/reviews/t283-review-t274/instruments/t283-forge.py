#!/usr/bin/env python3
"""T283 -- FORGE A SIDECAR THE T274 RE-DERIVATION REPRODUCES.

T274 replaced a four-way fail-open verifier with a ROOT repair: `verify`
re-derives the WHOLE sidecar from the wire records and the committed artefacts
with the same builder `derive` uses, and compares exactly and in order.  An
OMITTED assertion is therefore no longer an attack -- T274's own GREEN arms
measure that, and this review reproduced all 18 of them.

The attack that is LEFT is a sidecar the re-derivation REPRODUCES.  This tool
builds one, by asking the verifier's OWN builder what it wants to see and
writing exactly that.  No string is guessed: `forge()` calls
`wire_attestation.request_extras` / `response_extras` / `build_sidecar` in the
same `"verify"` mode `cmd_verify` uses, so nothing here can be dismissed as a
shape unrepresentative of what `verify` computes.

A forgery constructed this way is accepted BY CONSTRUCTION.  So the only
interesting questions -- and the whole finding -- are:

  (a) WHICH ARTEFACTS did the forger have to touch, and
  (b) is the accepted text one `derive` COULD EVER HAVE WRITTEN?

(b) is the discriminator this review turns on.  `derive` REFUSES to write a
`MISMATCH (...)` crosscheck line; `verify` renders one and then compares it
against a sidecar that says the same thing, and returns 0.  And the SAME-LENGTH
modes below need no MISMATCH line at all: they produce a sidecar that is
indistinguishable from an honest one.

PROVENANCE: modes forge-only / body-swap / body-swap-naive / status-swap /
resp-swap / reqhdr-tenant / drop-response come from the WIP of the killed T283
worker, rescued onto `softhouse/rescued-agent-af19d6f14414d32f0-20260822-140002`.
That worker never wrote a handoff and its arms are re-run here from scratch, not
quoted.  Modes body-swap-samelen, resp-swap-samelen and reqhdr-case are new to
this review, and they are the ones that leave no confession behind.

MONEY: no monetary value is parsed here and there is no float in this file.  The
forged bodies are valid JSON carrying no amount, so the harness's wire-float
round-trip guard has nothing to refuse (it refused T274's first red-drive, which
is recorded in T274's handoff as the guard working).

Usage:  t283-forge.py LIBDIR DIR NAME MODE [ARG]
"""
import os
import sys


def load(libdir):
    sys.path.insert(0, libdir)
    import wire_attestation as W
    return W


def paths(d, name):
    return {k: os.path.join(d, name + "." + k)
            for k in ("http", "reqhdr", "req", "json", "resphdr", "status")}


def captured_at(sidecar):
    with open(sidecar) as fh:
        for line in fh:
            if line.startswith("captured-at-utc:"):
                return line.rstrip("\n")
    raise SystemExit("no captured-at-utc: in %s" % sidecar)


def forge(W, p, schema=2):
    """Write the sidecar the T274 verifier will re-derive from these artefacts."""
    cap = captured_at(p["http"])
    record = W._read_text(p["reqhdr"], "request header record")
    body = p["req"] if os.path.isfile(p["req"]) else ""
    extras = W.request_extras(record, p["reqhdr"], body, "verify")
    if schema == 2:
        resp_record = W._read_text(p["resphdr"], "response header record")
        extras += W.response_extras(resp_record, p["resphdr"], p["json"],
                                    p["status"], "verify")
    extras.append(cap)
    text = W.build_sidecar(record, extras, schema)
    with open(p["http"], "w") as fh:
        fh.write(text)
    return text


# Different bytes, DIFFERENT length, still valid JSON, no monetary token.
FORGED_BODY = b'{"forged":"THIS-BODY-WAS-NEVER-ON-THE-WIRE-not-even-close"}\n'


def same_length_json(nbytes):
    """Valid JSON of EXACTLY nbytes bytes that was never on the wire."""
    head = b'{"forged":"'
    tail = b'"}\n'
    fill = nbytes - len(head) - len(tail)
    if fill < 1:
        raise SystemExit("cannot build a same-length forgery at %d bytes" % nbytes)
    return head + (b"F" * fill) + tail


def main(argv):
    if len(argv) < 4:
        raise SystemExit(__doc__)
    libdir, d, name, mode = argv[0], argv[1], argv[2], argv[3]
    arg = argv[4] if len(argv) > 4 else ""
    W = load(libdir)
    p = paths(d, name)

    if mode == "forge-only":
        forge(W, p)
        print("  forge: sidecar rebuilt from the artefacts exactly as they stand")

    elif mode == "body-swap":
        old = os.path.getsize(p["req"])
        with open(p["req"], "wb") as fh:
            fh.write(FORGED_BODY)
        forge(W, p)
        print("  forge: NAME.req %d bytes -> %d bytes (DIFFERENT length, different "
              "bytes); NAME.reqhdr UNTOUCHED" % (old, len(FORGED_BODY)))

    elif mode == "body-swap-samelen":
        old = os.path.getsize(p["req"])
        data = same_length_json(old)
        with open(p["req"], "wb") as fh:
            fh.write(data)
        forge(W, p)
        print("  forge: NAME.req %d bytes -> %d bytes, SAME LENGTH, different bytes; "
              "NAME.reqhdr UNTOUCHED" % (old, len(data)))

    elif mode == "body-swap-naive":
        old = os.path.getsize(p["req"])
        with open(p["req"], "wb") as fh:
            fh.write(FORGED_BODY)
        print("  forge: NAME.req %d -> %d bytes, sidecar NOT patched (naive control)"
              % (old, len(FORGED_BODY)))

    elif mode == "status-swap":
        with open(p["status"]) as fh:
            old = fh.read().strip()
        with open(p["status"], "w") as fh:
            fh.write(arg + "\n")
        forge(W, p)
        print("  forge: NAME.status %s -> %s; NAME.resphdr UNTOUCHED" % (old, arg))

    elif mode == "resp-swap":
        old = os.path.getsize(p["json"])
        with open(arg, "rb") as fh:
            data = fh.read()
        with open(p["json"], "wb") as fh:
            fh.write(data)
        forge(W, p)
        print("  forge: NAME.json %d bytes -> %d bytes (a DIFFERENT real oracle "
              "response); NAME.resphdr UNTOUCHED" % (old, len(data)))

    elif mode == "resp-swap-samelen":
        old = os.path.getsize(p["json"])
        data = same_length_json(old)
        with open(p["json"], "wb") as fh:
            fh.write(data)
        forge(W, p)
        print("  forge: NAME.json %d bytes -> %d bytes, SAME LENGTH, an answer the "
              "oracle NEVER GAVE; NAME.resphdr UNTOUCHED" % (old, len(data)))

    elif mode == "reqhdr-tenant":
        rec = W._read_text(p["reqhdr"], "request header record")
        out, hit = [], 0
        for line in rec.split("\n"):
            if line.lower().startswith("fineract-platform-tenantid:"):
                out.append("Fineract-Platform-TenantId: " + arg)
                hit += 1
            else:
                out.append(line)
        if hit != 1:
            raise SystemExit("expected exactly one tenant line, found %d" % hit)
        with open(p["reqhdr"], "w") as fh:
            fh.write("\n".join(out))
        forge(W, p)
        print("  forge: the WIRE RECORD's tenant rewritten to %r, then the sidecar "
              "re-derived from it" % arg)

    elif mode == "reqhdr-case":
        # The header-set-vs-sequence route, attacked from the RECORD side: the
        # sidecar's wire block is a verbatim copy of the record, so a record
        # whose header NAMES have been case-varied and whose ORDER has been
        # permuted re-derives clean.
        rec = W._read_text(p["reqhdr"], "request header record")
        lines = rec.split("\n")
        head = [l for l in lines if l.startswith("#") or not l.strip()]
        hdrs = [l for l in lines if l not in head]
        if len(hdrs) < 3:
            raise SystemExit("too few header lines to permute")
        first, rest = hdrs[0], hdrs[1:]
        rest = list(reversed(rest))
        varied = []
        for l in rest:
            n, s, v = l.partition(":")
            varied.append((n.upper() + s + v) if s else l)
        with open(p["reqhdr"], "w") as fh:
            fh.write("\n".join(head[:1] + [first] + varied +
                               [l for l in head[1:]]))
        forge(W, p)
        print("  forge: the WIRE RECORD's header lines REVERSED and their names "
              "UPPER-CASED, then the sidecar re-derived from it")

    elif mode == "drop-response":
        forge(W, p, schema=1)
        print("  forge: sidecar DOWNGRADED to schema 1 -- `attestation-schema: 2` "
              "and every response assertion removed")

    else:
        raise SystemExit("unknown mode %r" % mode)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
