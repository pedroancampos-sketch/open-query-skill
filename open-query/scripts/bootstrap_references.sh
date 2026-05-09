#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python3 "$SCRIPT_DIR/search_open_query.py" fetch-source
python3 "$SCRIPT_DIR/search_open_query.py" build-index
python3 "$SCRIPT_DIR/search_open_query.py" stats
