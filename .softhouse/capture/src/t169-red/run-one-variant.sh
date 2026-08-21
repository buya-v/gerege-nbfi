#!/bin/bash
# T169 driver wrapper: run one variant and keep a verbatim console transcript.
REPO="$1"; VARIANT="$2"
bash "$REPO/.softhouse/capture/src/t169-red/run-t169.sh" "$REPO" "$VARIANT" > "/tmp/t169probe/console-$VARIANT.txt" 2>&1
RC=$?
echo "=== run-t169.sh $VARIANT exited $RC ==="
cat "/tmp/t169probe/console-$VARIANT.txt"
exit $RC
