# T320 reviewer probe — how to reproduce

`t320_summed_contra_probe.go.txt` is a mutant THE REVIEWER wrote, not the author.
It is NOT registered in the committed store and must not be added to it without a
task of its own (see FINDING T320-6).

To reproduce (nothing is written to the repo, nothing is written to the oracle):

    rm -rf /tmp/T320-scratch && mkdir -p /tmp/T320-scratch
    cp -R <repo>/nexus /tmp/T320-scratch/nexus
    cp t320_summed_contra_probe.go.txt \
       /tmp/T320-scratch/nexus/internal/apps/ledger/conformance/t320_probe.go
    mkdir -p /tmp/T320-scratch/.softhouse
    cp -R <repo>/.softhouse/vectors  /tmp/T320-scratch/.softhouse/vectors   # COPY, not symlink
    ln -s  <repo>/.softhouse/capture /tmp/T320-scratch/.softhouse/capture   # symlink is fine here
    cd /tmp/T320-scratch/nexus
    go build -o /tmp/T320-conf ./internal/apps/loanschedule/conformance/cmd/conformance
    /tmp/T320-conf -oracle-probe=up -ledger-impl=t320-probe-openingbalance-summed-contra

The vector store must be a REAL directory: the harness's store-file census does not
walk a symlinked store root and correctly refuses with `VERDICT: UNUSABLE (exit 2)`
["THE STORE FILE CENSUS SAW ZERO .json FILES"]. That refusal is the guard working;
it is recorded here because a reader who symlinks will meet it. The capture tree may
be symlinked because provenance resolution stats through the link.

RUN-*.txt are the transcripts this review cites.
