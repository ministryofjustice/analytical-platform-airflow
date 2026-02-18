#!/usr/bin/env bash

MODE="${1}"
PATH_FILTER_CONFIGURATION_FILE=".github/path-filter/${MODE}.yml"

case ${MODE} in
workflows)
  FOLDER_PREFIX="environments"
  SEARCH_PATTERN="workflow.yml"
  SKIP_FILE=".workflow-path-filter-ignore"
  ;;
*)
  echo "Usage: ${0} [workflows]"
  exit 1
  ;;
esac

mkdir --parents ".github/path-filter"
touch "${PATH_FILTER_CONFIGURATION_FILE}"

# Find existing workflow folders
folders=$(find "${FOLDER_PREFIX}" -type f -name "${SEARCH_PATTERN}" -exec dirname {} \; | sort -h | uniq)

# Also find deleted workflow folders by checking git diff against origin/main
deleted_folders=""
if git rev-parse --verify origin/main >/dev/null 2>&1; then
  deleted_folders=$(git diff --name-status origin/main -- "${FOLDER_PREFIX}" | \
    grep "^D.*${SEARCH_PATTERN}$" | \
    awk '{print $2}' | \
    xargs -I {} dirname {} 2>/dev/null | \
    sort -h | uniq)

  if [[ -n "${deleted_folders}" ]]; then
    echo "=== Deleted Folders ==="
    echo "${deleted_folders}"
    # Combine existing and deleted folders
    folders=$(echo -e "${folders}\n${deleted_folders}" | sort -h | uniq | grep -v '^$')
  fi
fi

export folders
export deleted_folders

echo "=== Folders ==="
echo "${folders}"

echo "Generating ${PATH_FILTER_CONFIGURATION_FILE}"
cat >"${PATH_FILTER_CONFIGURATION_FILE}" <<EOL
---
EOL

for folder in ${folders}; do

  if [[ -f "${folder}/${SKIP_FILE}" ]]; then
    echo "Ignoring ${folder}"
    continue
  fi

  if [[ "${MODE}" == "workflows" ]]; then
    baseName=$(echo "${folder}" | sed 's|/|-|g' | sed 's|environments-||')
  else
    baseName=$(basename "${folder}")
  fi

  echo "${baseName}: ${folder}/**" >>"${PATH_FILTER_CONFIGURATION_FILE}"
done
