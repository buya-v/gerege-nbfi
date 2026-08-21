#!/bin/sh
# GL-account UPDATE and DELETE probes.
#
# Delete targets were chosen so that most isolate ONE guard, and one deliberately
# trips several at once so the guard ORDER is observed rather than assumed:
#   GL 3  — has child 4; no product mapping; no journal entry   -> children guard alone
#   GL 13 — mapped to products; no journal entry, no children   -> product-mapping guard alone
#   GL 2  — mapped to products AND has journal entries AND is a financial-activity
#           target: three guards at once. Which message comes back is the ordering fact.
#   GL 6  — mapped to a product AND to financial activity 200
#   GL 21 — no children, no mapping, no entries                 -> the SUCCESS path
DIR=$(cd "$(dirname "$0")" && pwd)

sh "$DIR/cap.sh" A2-110-update-header-to-detail   PUT /glaccounts/1  req/upd-110-header-to-detail.json || exit 1
sh "$DIR/cap.sh" A2-111-update-retype-mapped      PUT /glaccounts/2  req/upd-111-retype-mapped-account.json || exit 1
sh "$DIR/cap.sh" A2-112-update-disable-mapped     PUT /glaccounts/2  req/upd-112-disable-mapped.json || exit 1
sh "$DIR/cap.sh" A2-113-update-nomanual           PUT /glaccounts/2  req/upd-113-nomanual.json || exit 1
sh "$DIR/cap.sh" A2-114-finactivity-update        PUT /financialactivityaccounts/1 req/fin-107-update.json || exit 1

sh "$DIR/cap.sh" A2-120-delete-has-children       DELETE /glaccounts/3 || exit 1
sh "$DIR/cap.sh" A2-121-delete-product-mapped     DELETE /glaccounts/13 || exit 1
sh "$DIR/cap.sh" A2-122-delete-three-guards       DELETE /glaccounts/2 || exit 1
sh "$DIR/cap.sh" A2-123-delete-finactivity-mapped DELETE /glaccounts/6 || exit 1
sh "$DIR/cap.sh" A2-124-delete-clean-success      DELETE /glaccounts/21 || exit 1
sh "$DIR/cap.sh" A2-125-delete-not-found          DELETE /glaccounts/99999 || exit 1
