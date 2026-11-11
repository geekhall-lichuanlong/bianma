#!/usr/bin/env bash
set -euo pipefail

# Keep the old location working, but delegate to the project-level stopper so
# disease, surgery, database, backend, frontend, and model leftovers are handled together.
/opt/qianyi/kill.sh "$@"
