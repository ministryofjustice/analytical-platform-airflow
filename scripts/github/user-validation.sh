#!/usr/bin/env bash

set -euo pipefail

GITHUB_SECRET="${GITHUB_SECRET:-"github/airflow-github-app"}"
WORKFLOW_FILE="${1:-}"
AWS_REGION="${AWS_REGION:-eu-west-2}"

if [[ -z "${WORKFLOW_FILE}" ]]; then
  echo "Usage: $0 <workflow.yml>"
  exit 1
fi

# Get GitHub App credentials from AWS Secrets Manager
githubAppId=$(aws secretsmanager get-secret-value --region "${AWS_REGION}" --secret-id "${GITHUB_SECRET}" --query SecretString --output text | jq -r '.app_id')
export githubAppId

githubAppInstallationId=$(aws secretsmanager get-secret-value --region "${AWS_REGION}" --secret-id "${GITHUB_SECRET}" --query SecretString --output text | jq -r '.installation_id')
export githubAppInstallationId

githubAppPrivateKey=$(aws secretsmanager get-secret-value --region "${AWS_REGION}" --secret-id "${GITHUB_SECRET}" --query SecretString --output text | jq -r '.private_key')
export githubAppPrivateKey

# Generate installation access token using Python helper
GH_TOKEN=$(python scripts/github/auth_helper.py)
export GH_TOKEN

# Extract GitHub usernames from the maintainers array in the workflow file
usernames=$(yq '.maintainers[]' "${WORKFLOW_FILE}")

for memberGitHub in ${usernames}; do
  echo "Processing user [ ${memberGitHub} ]"
  githubMembershipStatus=$(gh api /orgs/ministryofjustice/memberships/"${memberGitHub}")

  # Check if the user is an active member
  if [[ "$(echo "${githubMembershipStatus}" | jq -r '.state')" == "active" ]]; then
    echo "  User found in GitHub organisation"
  elif [[ "$(echo "${githubMembershipStatus}" | jq -r '.status')" == "404" ]]; then
    echo "  User not found in GitHub organisation"
    exit 1
  else
    echo "  Unexpected response for user [ ${memberGitHub} ]"
    exit 1
  fi
done
