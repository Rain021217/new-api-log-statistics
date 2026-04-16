#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_DIR="${1:-}"

if [[ -z "${TARGET_DIR}" ]]; then
  VERSION="$(awk -F= '/^APP_VERSION=/{print $2}' "${ROOT_DIR}/.env.example" | head -n1)"
  VERSION="${VERSION:-0.2.0}"
  TARGET_DIR="${ROOT_DIR}/dist/new-api-log-statistics-${VERSION}-github"
fi

if [[ ! -d "${TARGET_DIR}" ]]; then
  echo "GitHub-ready directory not found: ${TARGET_DIR}" >&2
  exit 1
fi

required_paths=(
  "README.md"
  "LICENSE"
  "CHANGELOG.md"
  "CONTRIBUTING.md"
  "SECURITY.md"
  ".gitignore"
  ".github/workflows/ci.yml"
  ".github/pull_request_template.md"
  ".github/ISSUE_TEMPLATE/bug_report.yml"
  ".github/ISSUE_TEMPLATE/feature_request.yml"
  ".github/ISSUE_TEMPLATE/config.yml"
  "docs/github-auth-faq.zh-CN.md"
  "docs/maintainer-publishing.zh-CN.md"
  "docs/github-web-repository-setup.zh-CN.md"
  "docs/release-notes-v${VERSION}.md"
  "app/main.py"
  "deploy/docker-compose.yml"
  "config/sources.example.yml"
)

for path in "${required_paths[@]}"; do
  if [[ ! -e "${TARGET_DIR}/${path}" ]]; then
    echo "Missing required GitHub file: ${path}" >&2
    exit 1
  fi
done

forbidden_paths=(
  ".env"
  "config/sources.yml"
  "get_token.py"
  "TASKLIST.md"
  "new-api-log-statistics-plan.zh-CN.md"
  "database-access-and-onboarding.zh-CN.md"
  "export.csv"
)

for path in "${forbidden_paths[@]}"; do
  if [[ -e "${TARGET_DIR}/${path}" ]]; then
    echo "Forbidden GitHub file exists: ${path}" >&2
    exit 1
  fi
done

required_gitignore_patterns=(
  ".env"
  "config/sources.yml"
  "runtime/"
  "dist/"
)

for pattern in "${required_gitignore_patterns[@]}"; do
  if ! grep -Fqx "${pattern}" "${TARGET_DIR}/.gitignore"; then
    echo "Missing .gitignore pattern: ${pattern}" >&2
    exit 1
  fi
done

if find "${TARGET_DIR}/runtime" -type f | grep -q .; then
  echo "Runtime directory must be empty in GitHub-ready repo" >&2
  exit 1
fi

echo "GitHub-ready repo verified: ${TARGET_DIR}"
