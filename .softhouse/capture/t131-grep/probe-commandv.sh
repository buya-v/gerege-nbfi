#!/bin/bash
# T131 - does `command -v` bypass shell functions?  T108's ruling table and its
# proposed P-29 both assert that it does.  POSIX says command -v REPORTS functions.
echo "--- bash ---"
bash -c 'foo(){ echo fn; }; echo "command -v foo -> [$(command -v foo)]"; echo "type -a foo ->"; type -a foo'
echo "--- zsh ---"
zsh -c 'foo(){ echo fn; }; echo "command -v foo -> [$(command -v foo)]"; echo "type -a foo ->"; type -a foo'
echo "--- and `command foo` (no -v) really does bypass: ---"
bash -c 'grep(){ echo "FUNCTION RAN"; }; echo "bare grep:"; grep --version 2>&1|head -1; echo "command grep:"; command grep --version 2>&1|head -1; echo "command -v grep: [$(command -v grep)]"'
