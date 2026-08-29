set -e
C=/tmp/t450/clone
cd "$C"
git checkout -q drive 2>/dev/null || git checkout -q -b drive 8a08f8f9
# bring in the T412 gate files from the T412 branch (present in the clone's object db)
mkdir -p .softhouse/hooks
for f in driver-push-gate.sh cheap-subset.sh bar-attest.sh install-driver-push-gate.sh; do
  git show origin/softhouse/T412-driver-selfgrading:.softhouse/hooks/$f > .softhouse/hooks/$f
done
chmod +x .softhouse/hooks/*.sh
git add -A .softhouse/hooks
git -c user.name=T450 -c user.email=t450@local commit -q -m "T450 drive: install T412 gate files in throwaway clone"
BASE=$(git rev-parse HEAD)
echo "BASE=$BASE"
echo "BASETREE=$(git rev-parse HEAD^{tree})"
bash .softhouse/hooks/install-driver-push-gate.sh
rm -rf /tmp/t450/remote.git
git init -q --bare /tmp/t450/remote.git
git remote add bare /tmp/t450/remote.git
