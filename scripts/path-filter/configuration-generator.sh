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


folders=$(find "${FOLDER_PREFIX}" -type f -name "${SEARCH_PATTERN}" -exec dirname {} \; | sort -h | uniq)

export folders

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
