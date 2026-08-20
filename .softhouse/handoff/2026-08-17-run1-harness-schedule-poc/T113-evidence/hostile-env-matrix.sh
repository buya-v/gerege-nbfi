#!/bin/bash
# T113 — hostile-ENVIRONMENT matrix against the interpreter guard.
# usage: bash T113-hostile.sh <harness> [--kill-devfd]
# Prints one line per attack: <label> exit=<code>
h="$1"
[ "${2:-}" = "--kill-devfd" ] && rm -f /dev/fd
echo "bash: $(bash --version | head -1)"
echo "harness: $h"
psubok=$(bash -c 'IFS= read -r v < <(printf "%s\n" CAP); printf %s "$v"' 2>/dev/null)
echo "psub capability of this bash: [${psubok}]"

r() { local label="$1"; shift; "$@" >/dev/null 2>&1; echo "  exit=$? $label"; }

# 0. baselines
r "baseline clean"                                     bash "$h" --help
r "_conformance_psub_line=TOKEN exported"              env _conformance_psub_line=conformance-psub-live bash "$h" --help
r "_conformance_psub_line=garbage exported"            env _conformance_psub_line=zzz bash "$h" --help
r "CONFORMANCE_PSUB_TOKEN=zzz exported"                env CONFORMANCE_PSUB_TOKEN=zzz bash "$h" --help
r "both TOKEN and line set to zzz"                     env CONFORMANCE_PSUB_TOKEN=zzz _conformance_psub_line=zzz bash "$h" --help
r "IFS=oc exported"                                    env IFS=oc bash "$h" --help
r "POSIXLY_CORRECT=1"                                  env POSIXLY_CORRECT=1 bash "$h" --help
r "BASH_ENV=/dev/null"                                 env BASH_ENV=/dev/null bash "$h" --help

# 1. exported function hijacks
hijack() { # hijack <label> <name> <body>
  local label="$1" name="$2" body="$3" code
  code=$(bash -c "
    $name() { $body }
    export -f '$name' 2>/dev/null || { echo 99; exit; }
    bash \"\$1\" --help >/dev/null 2>&1; echo \$?
  " _ "$h" 2>/dev/null | tail -1)
  echo "  exit=$code $label"
}
hijack "[() { return 1; }"                         '['       'return 1;'
hijack "[() { return 0; }"                         '['       'return 0;'
hijack "builtin() { return 1; }"                   builtin   'return 1;'
hijack "builtin() { echo conformance-psub-live; }" builtin   'echo conformance-psub-live;'
hijack "eval() { return 1; }"                      eval      'return 1;'
hijack "eval() { echo conformance-psub-live; }"    eval      'echo conformance-psub-live;'
hijack "read() { return 1; }"                      read      'return 1;'
hijack "printf() { return 1; }"                    printf    'return 1;'
hijack "printf() { echo conformance-psub-live; }"  printf    'echo conformance-psub-live;'
