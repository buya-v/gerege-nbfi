#!/bin/sh
# Repo-local Go toolchain for the gerege-nbfi migration.
# Installed by local fire 20260819-170001. NOT on Buyan's PATH and NOT committed
# (.gitignore'd) — `rm -rf .softhouse/toolchain` fully reverses it.
#
# Usage from any checkout OR worktree:
#     . /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh
#     go build ./...      # from nexus/
#
# GOROOT is deliberately an ABSOLUTE path into the main checkout so isolated
# worktrees share one toolchain and one module cache.
GEREGE_TOOLCHAIN=/Users/buv/gerege-nbfi/.softhouse/toolchain
export GOROOT="$GEREGE_TOOLCHAIN/go"
export GOPATH="$GEREGE_TOOLCHAIN/gopath"
export GOCACHE="$GEREGE_TOOLCHAIN/gocache"
export GOMODCACHE="$GEREGE_TOOLCHAIN/gomodcache"
export PATH="$GOROOT/bin:$PATH"
