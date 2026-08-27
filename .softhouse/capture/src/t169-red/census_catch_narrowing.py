#!/usr/bin/env python3
"""T169 — P-26 census: sweep the CONCEPT (a handler that cannot see what it must record), not the
sentence, across every rig in the repository.

Three shapes are counted, because they are three spellings of one defect:

  JAVA-NARROW      `catch (RuntimeException ...)` / `catch (Exception ...)`. Blind to
                   java.lang.Error, which is what the reference oracle actually throws.
  PY-SWALLOW       `except Exception:` (or bare `except:`) whose body neither re-raises nor records
                   -- specifically the `except Exception: continue` / `: pass` shape. This exact
                   pattern produced a false gate decision in G-9 by silently swallowing every .txt
                   dump it could not json.load.
  PY-RECORDING     `except Exception as e:` whose body RECORDS the failure (appends to a list,
                   prints it, counts it) before continuing. Not a defect: it is the fix, in Python.

Each JAVA-NARROW site is additionally classified LOAD-BEARING or INCIDENTAL by whether the guarded
try block contains a call into the measured seam. A handler around `getResourceAsStream` cannot
hide a measurement; a handler around `generator.generate(...)` is the whole defect.

This script READS. It changes nothing. Usage: census_catch_narrowing.py <repo-root>
"""
import json
import os
import re
import sys

ROOT = os.path.abspath(sys.argv[1])

SEAM_MARKERS = ('generator.generate(', 'ProgressiveLoanScheduleGenerator', 'calculateRepaymentSchedule',
                'MoneyHelper.getMathContext', '.generate(mc,')

JAVA_CATCH = re.compile(r'\bcatch\s*\(\s*(RuntimeException|Exception)\b')
JAVA_ANY_CATCH = re.compile(r'\bcatch\s*\(')
PY_EXCEPT = re.compile(r'^\s*except\s*(Exception|BaseException)?\s*(as\s+\w+)?\s*:')


def walk(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ('.git', 'node_modules', 'build', '.gradle')]
        for fn in filenames:
            yield os.path.join(dirpath, fn)


def try_block_for(lines, catch_idx):
    """Rough but honest: walk back to the matching `try {` and return the guarded text."""
    depth = 0
    i = catch_idx
    while i >= 0:
        line = lines[i]
        depth += line.count('}') - line.count('{')
        if re.search(r'\btry\s*\{', line) and depth <= 0:
            return '\n'.join(lines[i:catch_idx + 1])
        i -= 1
    return ''


def main():
    java_sites, py_swallow, py_recording, java_broad = [], [], [], []

    for path in walk(ROOT):
        rel = os.path.relpath(path, ROOT)
        if path.endswith('.java'):
            lines = open(path, errors='replace').read().split('\n')
            for n, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith('*') or stripped.startswith('//') or stripped.startswith('/*'):
                    continue          # a comment ABOUT the defect is not an instance of it
                if JAVA_CATCH.search(line):
                    guarded = try_block_for(lines, n)
                    load_bearing = any(m in guarded for m in SEAM_MARKERS)
                    java_sites.append({'file': rel, 'line': n + 1, 'text': line.strip(),
                                       'loadBearing': load_bearing})
                elif 'catch (Throwable' in line or 'StackOverflowError' in line and 'catch' in line:
                    java_broad.append({'file': rel, 'line': n + 1, 'text': line.strip()})
        elif path.endswith('.py') or path.endswith('.sh'):
            lines = open(path, errors='replace').read().split('\n')
            for n, line in enumerate(lines):
                if PY_EXCEPT.match(line):
                    # Read only the handler's OWN body — lines indented deeper than the `except`,
                    # up to the first dedent. Anything past the dedent belongs to other code and
                    # must not be credited to this handler.
                    indent = len(line) - len(line.lstrip())
                    body = []
                    for m in range(n + 1, len(lines)):
                        nxt = lines[m]
                        if not nxt.strip():
                            continue
                        if len(nxt) - len(nxt.lstrip()) <= indent:
                            break
                        body.append(nxt.strip())
                    joined = '\n'.join(body)
                    records = any(tok in joined for tok in
                                  ('print(', '.append(', 'raise', 'sys.exit', 'exit(', 'logging',
                                   'notes', 'fail(', 'check(', 'errors'))
                    entry = {'file': rel, 'line': n + 1, 'text': line.strip(), 'body': body[:4]}
                    (py_recording if records else py_swallow).append(entry)

    print('T169 P-26 CENSUS — catch-narrowing across every rig in the repository')
    print('=' * 78)
    lb = [s for s in java_sites if s['loadBearing']]
    inc = [s for s in java_sites if not s['loadBearing']]
    print()
    print('JAVA-NARROW  catch (RuntimeException|Exception): %d sites in %d files'
          % (len(java_sites), len({s['file'] for s in java_sites})))
    print('  LOAD-BEARING (the guarded block calls the measured seam): %d' % len(lb))
    for s in lb:
        print('    %s:%d  %s' % (s['file'], s['line'], s['text']))
    print('  INCIDENTAL (guarded block does not reach the seam): %d' % len(inc))
    for s in inc:
        print('    %s:%d  %s' % (s['file'], s['line'], s['text']))

    print()
    print('JAVA-BROAD  catch (Throwable) / catch (... | StackOverflowError): %d sites' % len(java_broad))
    for s in java_broad:
        print('    %s:%d  %s' % (s['file'], s['line'], s['text']))

    print()
    print('PY-SWALLOW  except Exception / bare except with NO record in the next 4 lines: %d sites'
          % len(py_swallow))
    for s in py_swallow:
        print('    %s:%d  %s   -> %s' % (s['file'], s['line'], s['text'], '; '.join(s['body'])))

    print()
    print('PY-RECORDING  except ... that records before continuing (not a defect): %d sites'
          % len(py_recording))
    for s in py_recording:
        print('    %s:%d  %s   -> %s' % (s['file'], s['line'], s['text'], '; '.join(s['body'])))

    out = {'javaNarrowLoadBearing': lb, 'javaNarrowIncidental': inc, 'javaBroad': java_broad,
           'pySwallow': py_swallow, 'pyRecording': py_recording}
    print()
    print('MACHINE-READABLE: %d keys, %d total sites'
          % (len(out), sum(len(v) for v in out.values())))
    return out


if __name__ == '__main__':
    result = main()
    dest = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'p26-census.json')
    with open(dest, 'w') as fh:
        json.dump(result, fh, indent=1, sort_keys=True)
    print('wrote %s' % dest)
