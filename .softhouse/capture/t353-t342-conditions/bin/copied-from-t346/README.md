# Copied verbatim from `softhouse/T346-review-t342:.softhouse/reviews/t346-review-t342/bin/`

Per the T114 convention the reviewer's drives are COPIED here and RE-RUN against T353's tree,
rather than cited across a branch or believed from T346's transcripts (the brief's
instruction: *"Regenerate T346's transcripts; do not accept them."*).
`git show softhouse/T346-review-t342:.softhouse/reviews/t346-review-t342/bin/<file>`
reproduces the originals; nothing in this directory was edited.

`t346-mutate-driver.zsh` resolves the 192-state driver relative to its OWN location
(`${0:A:h}/../../../capture/t279-lock-partition/drive-wrapper-vs-skill.zsh`). From this
directory that path does not resolve, so it is invoked from a shim in the parent directory
rather than edited — see `../run-t346-mutate.zsh`.

Outputs are in `../../out/`. "before" means this branch's base,
`softhouse/T342-releasedat-failopen` @ `d870db1d`.
