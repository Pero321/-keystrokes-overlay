#!/usr/bin/env bash
# Regenerate the textures and zip src/ into a ready-to-install resource pack.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
name="SleepyPillows-1.21.11.zip"

python3 "$here/tools/generate_textures.py"

mkdir -p "$here/dist"
rm -f "$here/dist/$name"
# zip from inside src/ so pack.mcmeta sits at the root of the archive
(cd "$here/src" && zip -r -X -9 "$here/dist/$name" . -x '.*')

echo
echo "built $here/dist/$name"
