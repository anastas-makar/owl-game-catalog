#!/usr/bin/env sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(dirname "$SCRIPT_DIR")

cd "$REPO_ROOT"

python3 -m py_compile scripts/build_catalog.py

python3 scripts/build_catalog.py \
  --catalog-dir catalog \
  --output build/catalog-release.json \
  --version local \
  --commit-sha local \
  --require-image-keys

printf '\nCatalog strict validation OK\n'
