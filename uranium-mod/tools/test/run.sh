#!/bin/bash
# Runs the standalone logic tests. These deliberately depend on nothing from
# Minecraft, so they need no Gradle, no mappings and no game -- just javac. The
# point is that the parts of the mod with actual decisions in them can be
# checked in a second, without launching a server.
set -e
cd "$(dirname "$0")/../.."
OUT=$(mktemp -d)
trap 'rm -rf "$OUT"' EXIT
javac -d "$OUT" \
    src/main/java/net/pero/uraniummod/effect/RadiationMath.java \
    tools/test/RadiationMathTest.java
java -cp "$OUT" RadiationMathTest
