package conformance

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"os"
	"path/filepath"
)

// CaptureProvenance is the subset of a vector's provenance fields that every
// parity-admission check reads. Each context's Provenance struct carries at
// least these four, whatever else its schema adds on top.
type CaptureProvenance struct {
	Kind          string
	CaptureRef    string
	CaptureSHA256 string
	CaptureCaseID string
}

// AdmitCaptureProvenance returns the refusal problems for the provenance fields
// that are shared by every parity harness.
//
// A parity vector is a transcription of a committed capture. The kind is the
// only admissible one, the capture must resolve to a real committed file, the
// cited content hash must RECOMPUTE from that file's bytes, and the capture
// case id must be named. Any failure here makes the vector INADMISSIBLE — never
// merely skipped, and never graded against a value the harness could not audit
// back to a file on disk.
//
// repoRoot, when empty, skips the file-resolution and hash checks (they cannot
// run without a checkout) while keeping the structural ones.
func AdmitCaptureProvenance(p CaptureProvenance, repoRoot string) []string {
	var problems []string
	if p.Kind != ProvenanceKindOracleCapture {
		problems = append(problems, fmt.Sprintf(
			"provenance.kind %q: only %q vectors may be graded by this harness",
			p.Kind, ProvenanceKindOracleCapture))
	}
	if p.CaptureRef == "" {
		problems = append(problems, "provenance.capture_ref is empty: a parity vector must cite the committed capture artefact it was transcribed from")
	} else if repoRoot != "" {
		abs := filepath.Join(repoRoot, filepath.FromSlash(p.CaptureRef))
		info, err := os.Stat(abs)
		switch {
		case err != nil:
			problems = append(problems, fmt.Sprintf(
				"provenance.capture_ref %q does not resolve to a file in this repository: %v",
				p.CaptureRef, err))
		case info.IsDir():
			problems = append(problems, fmt.Sprintf(
				"provenance.capture_ref %q is a directory, not a capture artefact", p.CaptureRef))
		case p.CaptureSHA256 != "":
			raw, rerr := os.ReadFile(abs)
			if rerr != nil {
				problems = append(problems, fmt.Sprintf(
					"provenance.capture_ref %q unreadable: %v", p.CaptureRef, rerr))
			} else {
				sum := sha256.Sum256(raw)
				if got := hex.EncodeToString(sum[:]); got != p.CaptureSHA256 {
					problems = append(problems, fmt.Sprintf(
						"provenance.capture_sha256 %s does not match the referenced capture (%s)",
						p.CaptureSHA256, got))
				}
			}
		}
	}
	if p.CaptureSHA256 == "" {
		problems = append(problems, "provenance.capture_sha256 is empty: a parity vector must carry the content hash of its capture artefact")
	}
	if p.CaptureCaseID == "" {
		problems = append(problems, "provenance.capture_case_id is empty: a parity vector must identify the observation within its capture artefact")
	}
	return problems
}
