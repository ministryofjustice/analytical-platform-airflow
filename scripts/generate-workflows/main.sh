#!/usr/bin/env bash

set -euo pipefail

ENVIRONMENT="${1:-"development"}"
FOLDER_PREFIX="environments/${ENVIRONMENT}"
SEARCH_PATTERN="workflow.yml"

workflows=$(find "${FOLDER_PREFIX}" -type f -name "${SEARCH_PATTERN}" -exec dirname {} \;)
export workflows

echo "=== Workflows ==="
echo "${workflows}"

for workflow in ${workflows}; do
  echo "Generating ${workflow}"
  python scripts/workflow_generator/main.py "${workflow}/workflow.yml"
done
