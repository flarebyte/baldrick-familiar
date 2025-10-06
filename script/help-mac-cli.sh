#!/bin/bash

DEST_FILE="./temp/data/mac-os-terminal-cli.md"
mkdir -p ./temp/data/
echo "# MacOS terminal commands" > "$DEST_FILE"

echo "## fd" >> "$DEST_FILE"
fd --help >> "$DEST_FILE"
echo "---" >> "$DEST_FILE"

clingy  --help >> "$DEST_FILE"
dart --help
dust --help
gh --help
brew --help
go --help
jd --help
jq --help
rg --help
scc --help
python --help
tree --help
trivy --help
xsv --help
yq --help
zig --help
node --help
yarn --help
npm --help
uv --help
npx zx --help