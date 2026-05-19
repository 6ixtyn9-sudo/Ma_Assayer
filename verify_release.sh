set -euo pipefail

cd "$(dirname "$0")"

echo "== Orchestrator =="
git fetch origin
echo "branch: $(git rev-parse --abbrev-ref HEAD)"
git log -n 1 --oneline

echo
echo "== Submodules =="
git submodule status

echo
echo "== Ma_Assayer =="
cd Ma_Assayer
git rev-parse HEAD
git describe --tags --exact-match
git fetch origin
git merge-base --is-ancestor dc21fab origin/main && echo "dc21fab is on origin/main"
